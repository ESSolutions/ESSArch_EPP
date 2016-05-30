'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2016  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
else:
    __version__ = epp.__version__ 
    
import os, thread, datetime, time, logging, sys, ESSPGM, shutil
from configuration.models import Path, ESSConfig, ESSProc
from essarch.models import ArchiveObject
from django import db

import django
django.setup()

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logging.info('Starting ' + ProcName)
        while 1:
                if self.mDieFlag==1: break      # Request for death
                self.mLock.acquire()
                PauseTime, self.Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Run')[0]
                if self.Run == '0':
                    logging.info('Stopping ' + ProcName)
                    ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                    self.RunFlag=0
                    self.mLock.release()
                    if Debug: logging.info('RunFlag: 0')
                    time.sleep(2)
                    continue
                # Process Item 
                lock=thread.allocate_lock()
                self.IngestTable = 'IngestObject'
                self.path_gate_reception = Path.objects.get(entity = 'path_gate_reception').value
                self.PreIngestPath = Path.objects.get(entity = 'path_control').value
                if ExtDBupdate:
                    self.ext_IngestTable = self.IngestTable
                else:
                    self.ext_IngestTable = ''
                #if Debug: logging.info('Start to list worklist (ArchiveObject_objs)')
                ArchiveObject_objs = ArchiveObject.objects.filter(StatusProcess__range=(1999,2001), StatusActivity=0)
                for ArchiveObject_obj in ArchiveObject_objs:
                    if ESSProc.objects.get(Name=ProcName).Run=='0':
                        logging.info('Stopping ' + ProcName)
                        ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                        thread.interrupt_main()
                        break
                    self.ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
                    self.ObjectUUID = ArchiveObject_obj.ObjectUUID
                    self.ObjectPackageName = ArchiveObject_obj.ObjectPackageName
                    self.DataObjectSize = ArchiveObject_obj.DataObjectSize
                    ArchivePolicy_obj = ArchiveObject_obj.PolicyId
                    self.AIPpath = ArchivePolicy_obj.AIPpath
                    self.metatype = ArchivePolicy_obj.IngestMetadata
                    self.ObjectPath=os.path.join(self.AIPpath,self.ObjectPackageName)
                    if self.metatype in [1,2,3]:
                        self.CMetaObjectPath = os.path.join(self.AIPpath,self.ObjectIdentifierValue + '_Content_METS.xml')
                    elif self.metatype in [4]:
                        self.CMetaObjectPath = ''
                    self.PMetaObjectPath = os.path.join(self.AIPpath,self.ObjectIdentifierValue + '_Package_METS.xml')
                    self.AICmets_objpath = None
                    self.AIC_GatePath = None
                    self.IP_PreIngestPath = None
                    self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 2000, 5)
                    if errno: logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    # AIC fix - start
                    aic_obj = ArchiveObject.objects.filter(relaic_set__UUID=self.ObjectUUID)[:1]
                    if aic_obj:
                        self.AIC_UUID = aic_obj.get().ObjectUUID
                        logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
                        self.AICObjectDIR,AICObjectFILE = os.path.split(self.ObjectPath)
                        if ArchiveObject.objects.filter(StatusProcess__range=(0,1999), reluuid_set__AIC_UUID=self.AIC_UUID).exists():
                            self.AICmets_objpath = os.path.join(self.AICObjectDIR,self.AIC_UUID + '_AIC_METS.xml')
                            logging.info('Another IP is in progress to preserve, skip to remove AIC mets object: %s' % self.AICmets_objpath)
                            self.AICmets_objpath = None
                        else:
                            self.AICmets_objpath = os.path.join(self.AICObjectDIR,self.AIC_UUID + '_AIC_METS.xml')
                            if not os.path.exists(self.AICmets_objpath):
                                logging.warning('AIC mets object not found, %s' % self.AICmets_objpath)
                                self.AICmets_objpath = None
                        #TODO parameter for "logs" / "lobby"
                        self.AIC_GatePath = os.path.join(self.path_gate_reception, self.AIC_UUID)
                        if not os.path.exists(self.AIC_GatePath):
                            logging.warning('AIC not found in gate area, %s' % self.AIC_GatePath)
                            self.AIC_GatePath = None
                        self.AIC_path_control = os.path.join(self.PreIngestPath,self.AIC_UUID)
                        self.IP_PreIngestPath = os.path.join(self.AIC_path_control, self.ObjectUUID)
                        if not os.path.exists(self.IP_PreIngestPath):
                            logging.warning('IP not found in control area, %s' % self.IP_PreIngestPath)
                            self.IP_PreIngestPath = None
                    else:
                        logging.warning('AIC not found for IP object: %s' % self.ObjectUUID)
                    # AIC fix - end
                    try:
                        if self.CMetaObjectPath: 
                            logging.info('Try to purge AIP content_mets object: %s' % self.CMetaObjectPath)
                            os.remove(self.CMetaObjectPath)
                        if self.ObjectPath: 
                            logging.info('Try to purge AIP object: %s' % self.ObjectPath)
                            os.remove(self.ObjectPath)
                        if self.PMetaObjectPath: 
                            logging.info('Try to purge AIP package_mets object: %s' % self.PMetaObjectPath)
                            os.remove(self.PMetaObjectPath)
                        if self.AICmets_objpath: 
                            logging.info('Try to purge AIC mets object: %s' % self.AICmets_objpath)
                            os.remove(self.AICmets_objpath)
                        if self.AIC_GatePath: 
                            logging.info('Try to purge AIC in gate area: %s' % self.AIC_GatePath)
                            shutil.rmtree(self.AIC_GatePath)
                        if self.IP_PreIngestPath: 
                            logging.info('Try to purge IP from control area: %s' % self.IP_PreIngestPath)
                            shutil.rmtree(self.IP_PreIngestPath)
                            if os.listdir(self.AIC_path_control) == []:
                                logging.info('Try to purge AIC from control area: %s' % self.AIC_path_control)
                                shutil.rmtree(self.AIC_path_control)
                    except (IOError,os.error), why:
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 2001, 4)
                        if errno: 
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else:
                            if self.CMetaObjectPath and self.PMetaObjectPath:
                                self.event_info = 'Problem to purge AIP ObjectPath: ' + self.ObjectPath + ' and ' + self.CMetaObjectPath + ' and ' + self.PMetaObjectPath
                            elif self.PMetaObjectPath:
                                self.event_info = 'Problem to purge AIP ObjectPath: ' + self.ObjectPath + ' and ' + self.PMetaObjectPath
                            else:
                                self.event_info = 'Problem to purge AIP ObjectPath: ' + self.ObjectPath
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1150','','ESSArch AIPPurge',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    else:
                        self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        self.ProcTime = self.stopTime-self.startTime
                        if self.ProcTime.seconds < 1: self.ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                        self.DataObjectSizeMB = self.DataObjectSize/1048576
                        self.ProcMBperSEC = int(self.DataObjectSizeMB)/int(self.ProcTime.seconds)
                        logging.info('Succeeded to purge AIP ObjectPath: ' + self.ObjectPath + ' , ' + str(self.ProcMBperSEC) + ' MB/Sec and Time: ' + str(self.ProcTime))
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 3000, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else:
                            ESSPGM.Events().create('1150','','ESSArch AIPPurge',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                db.close_old_connections()
                self.mLock.release()
                time.sleep(int(PauseTime))
        self.mDieFlag=0

    ################################################
    def __init__(self,ProcName):
            self.RunFlag=1
            self.mDieFlag=0                 #Flag to let thread die
            self.mQueue=[]
            self.mLock=thread.allocate_lock()
            thread.start_new_thread(WorkingThread.ThreadMain,(self,ProcName))

    #################################################
    def Die(self):
            self.mDieFlag=1
            while self.mDieFlag==1: pass

    ##################################################
    def AddItem(self,item):
            self.mLock.acquire()
            self.mQueue.append(item)
            self.mLock.release()
            return 1

#######################################################################################################
# Dep:
# Table: ESSProc with Name: AIPPurge, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPPurge'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSProc.objects.filter(Name=ProcName).values_list('LogFile','Time','Status','Run')[0]
    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 0
    Console = 0

    ##########################
    # Log format
    if MultiProc:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
    else:
        essFormatter1 = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
        essFormatter2 = logging.Formatter('%(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
    ###########################
    # LocalFileHandler
    essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    essLocalFileHandler.setLevel(LogLevel)
    essLocalFileHandler.setFormatter(essFormatter1)
    #essLocalFileHandler.doRollover()
    ###########################
    # LocalConsoleHandler
    essConsoleHandler = logging.StreamHandler(sys.stdout)
    essConsoleHandler.setLevel(LogLevel)
    essConsoleHandler.setFormatter(essFormatter2)
    ##########################
    # Add handlers to default logger
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    logging = logging.getLogger('')
    logging.setLevel(0)
    logging.addHandler(essLocalFileHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        logging.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)

    logging.debug('LogFile: ' + str(LogFile))
    logging.debug('Time: ' + str(Time))
    logging.debug('Status: ' + str(Status))
    logging.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
    ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            if Debug: logging.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            if Debug: logging.info('test2: ' + str(x.RunFlag))
            x.Die()
            break
        time.sleep(5)
    if Debug: logging.info('test3: ' + str(x.RunFlag))
    del x

# ./AIPPurge.py

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

import os, thread, datetime, time, logging, sys, shutil, ESSDB, ESSPGM
from configuration.models import ESSConfig, ESSProc, ArchivePolicy

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
                self.Time, self.Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Run')[0]
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
                self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
                if ExtDBupdate:
                    self.ext_IngestTable = self.IngestTable
                else:
                    self.ext_IngestTable = ''
                if Debug: logging.info('Start to list worklist (self.dbget)')
                self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectUUID',
                                                                                  'ObjectIdentifierValue',
                                                                                  'PolicyId',
                                                                                  'DataObjectSize'),
                                                                                 ('StatusProcess','BETWEEN',59,'AND',61,'AND',
                                                                                  'StatusActivity','=',0))
                if errno: logging.error('Failed to access Local DB, error: ' + str(why))
                for self.obj in self.dbget:
                    if ESSProc.objects.get(Name=ProcName).Run == '0':
                        logging.info('Stopping ' + ProcName)
                        ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                        thread.interrupt_main()
                        break
                    self.ObjectUUID = self.obj[0]
                    self.ObjectIdentifierValue = self.obj[1]
                    self.PolicyId = self.obj[2]
                    self.DataObjectSize = self.obj[3]
                    ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyStat=1, PolicyID=self.PolicyId)
                    self.metatype = ArchivePolicy_obj.IngestMetadata
                    self.RemoveFlag = ArchivePolicy_obj.IngestDelete
                    self.IngestPath = ArchivePolicy_obj.IngestPath
                    self.dirpath=os.path.join(self.IngestPath,self.ObjectIdentifierValue)
                    if Debug: 
                        logging.info('self.obj: '+str(self.obj))
                        logging.info('InPath (IngestPath + self.ObjectIdentifierValue): '+str(self.dirpath))
                    #self.RemoveFlag='1' #If self.RemoveFlag = 1 then remove self.dirpath
                    if self.RemoveFlag == 1: 
                        self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 60, 5)
                        if errno: logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Try to remove IngestObjectPath: ' + self.dirpath)
                        try:
                            shutil.rmtree(self.dirpath)
                            if self.metatype == 1:
                                os.remove(os.path.join(self.IngestPath,self.ObjectIdentifierValue + '.tar'))
                                os.remove(os.path.join(self.IngestPath,self.ObjectIdentifierValue + '_Content_METS.xml'))
                                os.remove(os.path.join(self.IngestPath,self.ObjectIdentifierValue + '_Package_METS.xml'))
                        except (IOError,os.error), why:
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 61, 4)
                            if errno: 
                                logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else:
                                self.event_info = 'Problem to remove IngestObjectPath: %s, Error: %s' % (self.dirpath,str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1060','','ESSArch SIPRemove',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        else:
                            self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                            self.ProcTime = self.stopTime-self.startTime
                            if self.ProcTime.seconds < 1: self.ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                            self.DataObjectSizeMB = self.DataObjectSize/1048576
                            self.ProcMBperSEC = int(self.DataObjectSizeMB)/int(self.ProcTime.seconds)
                            logging.info('Succeeded to remove IngestObjectPath: ' + self.dirpath + ' , ' + str(self.ProcMBperSEC) + ' MB/Sec and Time: ' + str(self.ProcTime))
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 69, 0)
                            if errno:
                                logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else:
                                ESSPGM.Events().create('1060','','ESSArch SIPRemove',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                    else:
                        logging.info('Skip to remove IngestObjectPath: ' + self.dirpath)
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 69, 0)
                        if errno:
                            logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else:
                            ESSPGM.Events().create('1060','','ESSArch SIPRemove',ProcVersion,'0','Skip to remove IngestObjectPath',2,self.ObjectIdentifierValue)
                self.mLock.release()
                time.sleep(int(self.Time))
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
# Table: ESSProc with Name: SIPRemove, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=0
    ProcName = 'SIPRemove'
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

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

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

# ./SIPRemove.py

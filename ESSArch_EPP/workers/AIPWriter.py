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

import django
django.setup()

import thread, time, logging, sys, ESSlogging, traceback

from essarch.models import ArchiveObject
from configuration.models import ESSConfig, ESSProc, ArchivePolicy
from Storage.models import IOQueue
from Storage.libs import StorageMethodWrite
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from essarch.libs import ESSArchSMError

class WorkingThread:
    tz = timezone.get_default_timezone()
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        ############################################################################
        try:
            PauseIngestWhenActiveWrites_flag = int(ESSConfig.objects.get(Name='PauseIngestWhenActiveWrites').Value)
        except ObjectDoesNotExist:
            PauseIngestWhenActiveWrites_flag = 1
        # Check if any active Write IO exist to set puase flags for ingest of new objects
        if IOQueue.objects.filter(ReqType__in=[10, 15], Status__in = [1,19]).exists() and PauseIngestWhenActiveWrites_flag:
            #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
            ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
        else:
            #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
            ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
        # Get active queue depth for self.TapeIOpool._cache.
        #TapeIOactv = len(self.TapeIOpool._cache)
        #TapeIOactv = 0
        #TapeReadIOtags = 4
        #TapeWriteIOtags = 2
        #ReadTapeIO_flag = 0
        #ActiveTapeIOs = [i[0] for i in IOQueue.objects.filter(ReqType=10).order_by('storagemethodtarget__target__id').values_list('storagemethodtarget__target__id').distinct()]
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            PauseTime, self.Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Run')[0]
            if self.Run == '0':
                logger.info('Stopping ' + ProcName)
                ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()
            if ExtDBupdate:
                ext_IngestTable = ESSConfig.objects.get(Name='IngestTable').Value
            else:
                ext_IngestTable = ''
            ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1)
            for ArchivePolicy_obj in ArchivePolicy_objs:
                if ESSProc.objects.get(Name=ProcName).Run == '0':
                    logger.info('Stopping ' + ProcName)
                    ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                    break
                PolicyID = ArchivePolicy_obj.PolicyID
                ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = PolicyID),
                                                  Q(StatusProcess__range = [69,1000]),
                                                  Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                  )
                try:
                    StorageMethodWrite_obj = StorageMethodWrite()
                    StorageMethodWrite_obj.logger = logger
                    StorageMethodWrite_obj.ArchiveObject_objs = ArchiveObject_objs
                    StorageMethodWrite_obj.add_to_ioqueue()
                    StorageMethodWrite_obj.apply_ios_to_transfer()
                    StorageMethodWrite_obj.apply_ios_to_write()
                except ESSArchSMError as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Problem to write objects for policyID %s, error: %s line: %s' % (PolicyID, e, exc_traceback.tb_lineno)
                    logger.error(msg)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Unknown error to write objects for policyID %s, error: %s trace: %s' % (PolicyID, e, repr(traceback.format_tb(exc_traceback)))
                    logger.error(msg)
                for ArchiveObject_obj in ArchiveObject_objs:
                    try:
                        StorageMethodWrite_obj.get_write_status(ArchiveObject_obj)
                        StorageMethodWrite_obj.handle_write_status(ArchiveObject_obj)
                    except ESSArchSMError as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        msg = 'Problem to write object %s, error: %s line: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, exc_traceback.tb_lineno)
                        logger.error(msg)
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        msg = 'Unknown error to write object %s, error: %s trace: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)))
                        logger.error(msg)
            ############################################################################
            try:
                PauseIngestWhenActiveWrites_flag = int(ESSConfig.objects.get(Name='PauseIngestWhenActiveWrites').Value)
            except ObjectDoesNotExist:
                PauseIngestWhenActiveWrites_flag = 1
            # Check if any active Write IO exist to set puase flags for ingest of new objects
            if IOQueue.objects.filter(ReqType__in=[10, 15], Status__in = [1,19]).exists() and PauseIngestWhenActiveWrites_flag:
                ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
            else:
                ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
            self.mLock.release()
            time.sleep(int(PauseTime))
        self.RunFlag=0
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
# Table: ESSProc with Name: AIPWriter, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPWriter'
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
    ###########################
    # SocketHandler
    essSocketHandler = ESSlogging.ESSSocketHandler('localhost',60100)
    ##########################
    # Add handlers to default logger
#    if MultiProc:
#        logger = multiprocessing.get_logger()
#        logger.setLevel(LogLevel)
    esslogger = logging.getLogger('')
    esslogger.setLevel(0)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
#    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        esslogger.addHandler(essConsoleHandler)
#        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
    ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            break
        time.sleep(5)
    logger.info('test3: ' + str(x.RunFlag))
    del x

# ./AIPWriter.py

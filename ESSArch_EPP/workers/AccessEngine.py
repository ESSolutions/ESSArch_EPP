#!/usr/bin/env /ESSArch/pd/python/bin/python
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

import thread, multiprocessing, time, logging, sys, ESSDB, ESSPGM, ESSlogging, os, tarfile, datetime, ESSMD, traceback

from essarch.models import AccessQueue, ArchiveObject
from essarch.libs import calcsum, unicode2str
from django.db import connection
from Storage.models import storage, storageMedium, IOQueue
from Storage.libs import StorageMethodRead
from StorageMethodDisk.tasks import ReadStorageMethodDisk
from StorageMethodTape.tasks import ReadStorageMethodTape
from celery.result import AsyncResult

import django
django.setup()

class AccessError(Exception):
    def __init__(self, value):
        self.value = value
        super(AccessError, self).__init__(value)

class Access:
    def ProcessAccessRequest(self,ReqUUID):
        """Process access request
        
        :param ReqUUID: ReqUUID in database table AccessQueue
        
        """
        try:
            logger.debug('Start ProcessAccessRequest')
            logger.debug('ReqUUID: %s' % ReqUUID)
            connection.close() # Fix (2006, 'MySQL server has gone away')
            AccessQueue_obj = AccessQueue.objects.get(ReqUUID = ReqUUID)
            process_name = multiprocessing.current_process().name
            logger.debug('process_name: %s' % process_name)
            process_pid = multiprocessing.current_process().pid
            logger.debug('process_pid: %s' % process_pid)

            AccessQueue_obj.Status = 5
            AccessQueue_obj.save()

            if AccessQueue_obj.ReqType in (1,3,4,5):
                event_info = 'Start Generate DIP Process for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1202',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Start quickverify storageMediumID Process for storageMediumID: %s, ReqUUID: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2202',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)

            StorageMethodRead_obj = StorageMethodRead()
            StorageMethodRead_obj.logger = logger
            StorageMethodRead_obj.AccessQueue_obj = AccessQueue_obj

            if AccessQueue_obj.ReqType == 1:
                StorageMethodRead_obj.get_object_to_read()
                StorageMethodRead_obj.add_to_ioqueue()
                StorageMethodRead_obj.apply_ios_to_read()
                StorageMethodRead_obj.wait_for_all_reads()
                StorageMethodRead_obj.ip_unpack()
                StorageMethodRead_obj.ip_validate()
            elif AccessQueue_obj.ReqType == 3:
                StorageMethodRead_obj.get_object_to_read()
                StorageMethodRead_obj.add_to_ioqueue()
                StorageMethodRead_obj.apply_ios_to_read()
                StorageMethodRead_obj.wait_for_all_reads()
            elif AccessQueue_obj.ReqType in [4,5]:
                StorageMethodRead_obj.get_object_to_read()
                StorageMethodRead_obj.add_to_ioqueue()
                StorageMethodRead_obj.apply_ios_to_read()
                StorageMethodRead_obj.wait_for_all_reads()
                StorageMethodRead_obj.ip_unpack()
                StorageMethodRead_obj.ip_validate()
                StorageMethodRead_obj.delete_retrieved_ios()
            elif AccessQueue_obj.ReqType == 2:
                StorageMethodRead_obj.get_objects_to_verify()
                StorageMethodRead_obj.add_to_ioqueue()
                StorageMethodRead_obj.apply_ios_to_read()
                StorageMethodRead_obj.wait_for_all_reads()
                StorageMethodRead_obj.delete_retrieved_ios()

        except AccessError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()            
            AccessQueue_obj.refresh_from_db()
            if AccessQueue_obj.ReqType in (1,3,4,5):
                event_info = 'Problem to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, error: %s, line: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID, e, exc_traceback.tb_lineno)
                logger.error(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Problem to quickverify storageMediumID: %s, ReqUUID: %s, error: %s line: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID, e, exc_traceback.tb_lineno)
                logger.error(event_info)
                ESSPGM.Events().create('2203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,storageMediumID=AccessQueue_obj.storageMediumID)
            AccessQueue_obj.Status = 100
            AccessQueue_obj.save(update_fields=['Status'])
            #raise e
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))            
            logger.error(msg)
            AccessQueue_obj.refresh_from_db()
            msg = 'Unknown error with access ReqUUID: %s, error: %s trace: %s' % (AccessQueue_obj.ReqUUID, e, repr(traceback.format_tb(exc_traceback)))
            logger.error(msg)
            AccessQueue_obj.Status = 100
            AccessQueue_obj.save(update_fields=['Status'])
            #raise e
        except:
            msg = 'Unexpected error: %s %s' % (sys.exc_info()[0], sys.exc_info()[1])
            logger.error(msg)
            print msg
            #raise
        else:
            if AccessQueue_obj.ReqType in (1,3,4):
                event_info = 'Success to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 5:
                event_info = 'Success to get AIP to ControlArea for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
                # Update IP in ArchiveObject DBtable
                ArchiveObject_upd = ArchiveObject.objects.get(ObjectIdentifierValue = AccessQueue_obj.ObjectIdentifierValue)
                setattr(ArchiveObject_upd, 'StatusActivity', 7)
                # Commit DB updates
                ArchiveObject_upd.save(update_fields=['StatusActivity'])
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Success to quickverify storageMediumID: %s, ReqUUID: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,storageMediumID=AccessQueue_obj.storageMediumID)
            AccessQueue_obj.Status = 20
            AccessQueue_obj.save(update_fields=['Status'])      

def GenerateDIPProc(DbRow):
    logger.debug('FuncStart GenerateDIPProc')
    return Access().ProcessAccessRequest(DbRow)

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        # Start Process pool with 2 process
        self.ReqTags = 2
        self.ProcPool = multiprocessing.Pool(self.ReqTags)
        jobs = []
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            self.ProcPoolProblemFlag = 0
            for self.worker in self.ProcPool._pool: 
                if not self.worker.is_alive(): 
                    self.ProcPoolProblemFlag = 1
                    logger.error('Problem with process_name: %s, process_pid: %s, process_exitcode: %s',self.worker.name,self.worker.pid,self.worker.exitcode)
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0' or self.ProcPoolProblemFlag == 1:
                logger.info('Stopping ' + ProcName)
                if self.ProcPoolProblemFlag:
                    self.ProcPool.terminate()
                else:
                    self.ProcPool.close()
                self.ProcPool.join()
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                time.sleep(1)
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()

            AccessQueue_DbRows = AccessQueue.objects.filter(Status = 0).all()
            for AccessQueue_DbRow in AccessQueue_DbRows:
                ##############################################################################################Y
                # if self.ProcPool._state == 0 then pool is working.
                if self.ProcPool._state == 0:
                    # Get active queue depth for self.ProcPool._cache.
                    self.ActiveProcQueue = len(self.ProcPool._cache)
                    ###########################################################################################
                    # If self.ActiveProcQueue < self.ReqTags start DIPRequest process
                    if self.ActiveProcQueue < self.ReqTags:
                        AccessQueue_DbRow.Status = 2
                        #model.meta.Session.commit()
                        AccessQueue_DbRow.save()
                        logger.info('Add ReqUUID: %s to GenerateDIPProc' % AccessQueue_DbRow.ReqUUID)
                        res = self.ProcPool.apply_async(GenerateDIPProc, (AccessQueue_DbRow.ReqUUID,))
                        jobs.append(res)
            for job in jobs:
                try:
                    msg = 'Result from GenerateDIPProc: %s' % repr(job.get(timeout=1))
                except multiprocessing.TimeoutError as e:
                    msg = 'Timeout wait for result from GenerateDIPProc'
                logger.debug(msg)
            if len(self.ProcPool._cache) == 0:
                jobs = []
            logger.debug('ProcPool_cache: %r',self.ProcPool._cache)
            connection.close()
            time.sleep(5)
            self.mLock.release()
        time.sleep(10)
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
# Table: ESSProc with Name: IOEngine, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AccessEngine'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]
    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 1
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
    #essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    essLocalFileHandler = logging.FileHandler(LogFile)
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
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    #logging = logging.getLogger('')
    esslogger = logging.getLogger('')
    #logging.setLevel(0)
    esslogger.setLevel(0)
    #logging.addHandler(essLocalFileHandler)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        #logging.addHandler(essConsoleHandler)
        esslogger.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])
    
    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            time.sleep(10) 
            break
        time.sleep(1)
    logger.info('test3: ' + str(x.RunFlag))
    del x


# ./AccessEngine.py

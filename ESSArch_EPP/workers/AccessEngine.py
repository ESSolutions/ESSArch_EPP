#!/usr/bin/env /ESSArch/pd/python/bin/python
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB, Henrik Ek

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
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))

import thread, multiprocessing, time, logging, sys, ESSDB, ESSPGM, ESSlogging

from essarch.models import AccessQueue, ArchiveObject
from django import db

class Functions:
    def GenerateDIPProc(self,ReqUUID):
        "Generate DIP for request in Accessqueue"
        try:
            DbRow = AccessQueue.objects.filter(ReqUUID = ReqUUID)[:1].get()
            self.run = 1
            self.unpack = 0
            self.delete = 0
            self.process_name = multiprocessing.current_process().name
            self.process_pid = multiprocessing.current_process().pid
            aic_support = False
            DbRow.Status = 5
            DbRow.save()

            if DbRow.ReqType in (1,3,4,5):
                event_info = 'Start Generate DIP Process for ObjectIdentifierValue: %s, ReqUUID: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1202',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
            elif DbRow.ReqType == 2:
                event_info = 'Start quickverify storageMediumID Process for storageMediumID: %s, ReqUUID: %s' % (DbRow.storageMediumID,DbRow.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2202',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)

            if DbRow.ReqType == 1:
                self.unpack = 1
                self.delete = 0
            elif DbRow.ReqType == 3:
                self.unpack = 0
                self.delete = 0
            elif DbRow.ReqType == 4:
                self.unpack = 1
                self.delete = 1
            elif DbRow.ReqType == 5:
                self.unpack = 1
                self.delete = 1
                aic_support = True
            elif DbRow.ReqType == 2:
                self.unpack = 0
                self.delete = 1

            self.cmdres,self.errno,self.why = ESSPGM.Check().AIPextract(storageMediumID=DbRow.storageMediumID, 
                                                                        ObjectIdentifierValue=DbRow.ObjectIdentifierValue,
                                                                        delete=self.delete,
                                                                        prefix=None,
                                                                        target=DbRow.Path,
                                                                        unpack=self.unpack,
                                                                        aic_support=aic_support,
                                                                        )
            if self.errno:
                if DbRow.ReqType in (1,3,4,5):
                    event_info = 'Problem to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, errorcode: %s, errormessage: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.errno),str(self.why))
                    logger.error(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,DbRow.ObjectIdentifierValue)
                elif DbRow.ReqType == 2:
                    event_info = 'Problem to quickverify storageMediumID: %s, ReqUUID: %s, errorcode: %s, errormessage: %s' % (DbRow.storageMediumID,DbRow.ReqUUID,str(self.errno),str(self.why))
                    logger.error(event_info)
                    ESSPGM.Events().create('2203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,storageMediumID=DbRow.storageMediumID)
                DbRow.Status = 100
                DbRow.save()
            else:
                if DbRow.ReqType in (1,3,4):
                    event_info = 'Success to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, cmdres: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                elif DbRow.ReqType == 5:
                    event_info = 'Success to get AIP to ControlArea for ObjectIdentifierValue: %s, ReqUUID: %s, cmdres: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                    # Update IP in ArchiveObject DBtable
                    ArchiveObject_upd = ArchiveObject.objects.filter(ObjectIdentifierValue = DbRow.ObjectIdentifierValue)[:1].get()
                    setattr(ArchiveObject_upd, 'StatusActivity', 7)
                    # Commit DB updates
                    ArchiveObject_upd.save()
                elif DbRow.ReqType == 2:
                    event_info = 'Success to quickverify storageMediumID: %s, ReqUUID: %s, cmdres: %s' % (DbRow.storageMediumID,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('2203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,storageMediumID=DbRow.storageMediumID)
                DbRow.Status = 20
                DbRow.save()
            db.close_old_connections()
        except:
            logger.error('Unexpected error: %s %s' % (sys.exc_info()[0], sys.exc_info()[1]))
            print "Unexpected error:", sys.exc_info()[0], sys.exc_info()[1]
            raise

def GenerateDIPProc(DbRow):
    return Functions().GenerateDIPProc(DbRow)

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        # Start Process pool with 2 process
        self.ReqTags = 2
        self.ProcPool = multiprocessing.Pool(self.ReqTags)
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
                        self.ProcPool.apply_async(GenerateDIPProc, (AccessQueue_DbRow.ReqUUID,))
            logger.debug('ProcPool_cache: %r',self.ProcPool._cache)
            db.close_old_connections()
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

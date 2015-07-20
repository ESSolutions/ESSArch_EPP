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

import subprocess, thread, datetime, time, logging, logging.handlers, sys, ESSDB, ESSMSSQL, ESSPGM, multiprocessing, tarfile,pytz
from Queue import Empty
from lxml import etree
from django.utils import timezone
from essarch.models import robotQueue, robotdrives, robot
from django import db
#from essarch.libs import flush_transaction

class WorkingThread:
    tz=timezone.get_default_timezone()
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        while 1:
            try:
                if self.mDieFlag==1: break      # Request for death
                self.mLock.acquire()
                self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
                if self.Run == '0':
                    logger.info('Stopping ' + ProcName)
                    ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                    self.RunFlag=0
                    self.mLock.release()
                    if Debug: logger.info('RunFlag: 0')
                    time.sleep(2)
                    continue
                # Process Item 
                lock=thread.allocate_lock()
                self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
                if Debug: logger.info('Start to list worklist')
                #######################################
                # Start to list robot req
                self.worklist = robotQueue.objects.filter(ReqType__in=[50,51,52], Status=0) #Get pending robot requests
                for self.item in self.worklist:
                    if ESSDB.DB().action('ESSProc','GET',('Run',),('Name',ProcName))[0][0]=='0':
                        logger.info('Stopping ' + ProcName)
                        ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                        thread.interrupt_main()
                        break
                    self.id=self.item.id
                    self.req_type=self.item.ReqType
                    self.t_id=self.item.MediumID
                    self.work_uuid=self.item.ReqUUID
                    if self.req_type == 50: #Mount
                        ##########################################
                        # Check if tape is already mounted
                        self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id','drive_lock'),('t_id',self.t_id,'AND','status','Mounted'))
                        if self.robotdrive:
                            self.drive_id = self.robotdrive[0][0]
                            self.current_lock = self.robotdrive[0][1]
                            ##########################################
                            # Tape is mounted, check if locked
                            if len(self.current_lock) > 0:
                                ########################################
                                # Tape is locked, check if req work_uuid = lock
                                if self.current_lock == self.work_uuid:
                                    ########################################
                                    # Tape is already locked with req work_uuid
                                    logger.info('Already Mounted: ' + str(self.t_id) + ' and locked by req work_uuid: ' + str(self.work_uuid))
                                    self.item.delete()
                                else:
                                    ########################################
                                    # Tape is locked with another work_uuid
                                    logger.info('Tape: ' + str(self.t_id) + ' is busy and locked by: ' + str(self.current_lock) + ' and not req work_uuid: ' + str(self.work_uuid))
                            else:
                                ########################################
                                # Tape is not locked, lock the drive with req work_uuid
                                ESSDB.DB().action('robotdrives','UPD',('drive_lock',self.work_uuid),('drive_id',self.drive_id))
                                logger.info('Tape: ' + str(self.t_id) + ' is available set lock to req work_uuid: ' + str(self.work_uuid))
                                self.item.delete()
                        else:
                            ##########################################
                            # Tape is not mounted, check for available tape drives
                            self.robotdrives=ESSDB.DB().action('robotdrives','GET',('num_mounts','drive_id'),('status','Ready'))      #Get avilable tape drives
                            if self.robotdrives:
                                self.drive_id = self.robotdrives[0][1]
                                ########################################
                                # Tapedrives is available try to mount tape
                                self.item.Status=5
                                self.item.save(update_fields=['Status'])
                                self.mountout, self.returncode = Robot().Mount(self.t_id,self.drive_id,self.work_uuid)
                                if self.returncode == 0:
                                    #ESSDB.DB().action('robotreq','DEL',('id',self.id))
                                    self.item.delete()
                                    ######################################################
                                    # Update StorageMediumTable with num of mounts
                                    self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
                                    self.MediaMountDBget,errno,why = ESSDB.DB().action(self.StorageMediumTable,'GET3',('storageMediumMounts',),('storageMediumID',self.t_id))
                                    if errno: logger.error('Failed to access Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                                    elif self.MediaMountDBget:
                                        self.storageMediumMounts = int(self.MediaMountDBget[0][0]) + 1
                                        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumLocationStatus',50,
                                                                                                         'storageMediumMounts',self.storageMediumMounts,
                                                                                                         'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                                         'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                                        ('storageMediumID',self.t_id))
                                        if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                                        if errno == 0 and ExtDBupdate:
                                            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumLocationStatus',50,
                                                                                                                            'storageMediumMounts',self.storageMediumMounts,
                                                                                                                            'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                                           ('storageMediumID',self.t_id))
                                            if ext_errno: logger.error('Failed to update External DB: ' + str(self.t_id) + ' error: ' + str(ext_why))
                                            else:
                                                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                                                if errno: logger.error('Failed to update Local DB: ' + str(self.t_id) + ' error: ' + str(why))
                                else:
                                    logger.error('Problem to mount tape: ' + self.t_id + ' Message: ' + str(self.mountout))
                                    self.item.Status=100
                                    self.item.save(update_fields=['Status'])
                    elif self.req_type == 51: # Unmount
                        ######################################
                        # Check if tape is mounted
                        self.robotdrives=ESSDB.DB().action('robotdrives','GET',('drive_id','drive_lock'),('t_id',self.t_id))      #Get tape drive that is mounted
                        if self.robotdrives:
                            ################################################
                            # Tape is mounted, check if tape is locked(busy)
                            self.drive_id = self.robotdrives[0][0]
                            self.current_lock = self.robotdrives[0][1]
                            if len(self.current_lock) == 0:
                                ###################################################
                                # Tape is not locked, try to unmount
                                self.item.Status=5
                                self.item.save(update_fields=['Status'])
                                ESSDB.DB().action('robotdrives','UPD',('status','Unmounting'),('drive_id',self.drive_id))
                                self.mountout, self.returncode = Robot().Unmount(self.t_id,self.drive_id)
                                if self.returncode == 0:
                                    self.item.delete()
                                else:
                                    logger.error('Problem to unmount tape: ' + self.t_id + ' Message: ' + str(self.mountout))
                                    self.item.Status=100
                                    self.item.save(update_fields=['Status'])
                            else:
                                #################################################
                                # Tape is locked, skip to unmount
                                logger.info('Tape ' + self.t_id + ' is locked, skip to unmount')
                        else:
                            ################################################
                            # Tape is not mounted, skip to try to unmount
                            logger.info('Tape ' + self.t_id + ' is not mounted')
                            self.item.delete()
                    elif self.req_type == 52: # F_Unmount
                        ######################################
                        # Check if tape is mounted
                        self.robotdrives=ESSDB.DB().action('robotdrives','GET',('drive_id','drive_lock'),('t_id',self.t_id))      #Get tape drive that is mounted
                        if self.robotdrives:
                            ################################################
                            # Tape is mounted, check if tape is locked(busy)
                            self.drive_id = self.robotdrives[0][0]
                            self.current_lock = self.robotdrives[0][1]
                            if len(self.current_lock) == 0:
                                ###################################################
                                # Tape is not locked, try to unmount
                                self.item.Status=5
                                self.item.save(update_fields=['Status'])
                                ESSDB.DB().action('robotdrives','UPD',('status','Unmounting'),('drive_id',self.drive_id))
                                self.mountout, self.returncode = Robot().Unmount(self.t_id,self.drive_id)
                                if self.returncode == 0:
                                    self.item.delete()
                                else:
                                    logger.error('Problem to unmount tape: ' + self.t_id + 'Message: ' + str(self.mountout))
                                    self.item.Status=100
                                    self.item.save(update_fields=['Status'])
                            else:
                                #################################################
                                # Tape is locked, try to unmount anyway
                                logger.info('Tape %s is locked with work_uuid %s, try to force unmount',self.t_id,self.current_lock)
                                self.item.Status=5
                                self.item.save(update_fields=['Status'])
                                ESSDB.DB().action('robotdrives','UPD',('status','Unmounting'),('drive_id',self.drive_id))
                                self.mountout, self.returncode = Robot().Unmount(self.t_id,self.drive_id)
                                if self.returncode == 0:
                                    self.item.delete()
                                else:
                                    logger.error('Problem to unmount tape: ' + self.t_id + 'Message: ' + str(self.mountout))
                                    self.item.Status=100
                                    self.item.save(update_fields=['Status'])
                        else:
                            ################################################
                            # Tape is not mounted, skip to try to unmount
                            logger.info('Tape ' + self.t_id + ' is not mounted')
                            self.item.delete()
                db.close_old_connections()
                self.mLock.release()
                time.sleep(int(self.Time))
            except:
                logger.error('Unexpected error: %s' % (str(sys.exc_info())))
                raise
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

class Robot:
    ###############################################
    "Mount tape"
    ###############################################
    def Mount(self, volser, drive_id=None, work_uuid=''):
        logger.info('Mount tape: ' + volser)
        robotdev = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','Robotdev'))[0][0]
        robot_db = ESSDB.DB().action('robot','GET',('slot_id',),('t_id',volser))
        if robot_db:
            robot_db = robot_db[0]
        else:
            self.mountout = 'Missing MediumID: %s in robot' % str(volser)
            self.returncode = 1
            return self.mountout, self.returncode
        if drive_id:
            self.drive_id = drive_id
        else:
            self.drive_id = 0
        self.num_mounts, tapedev = ESSDB.DB().action('robotdrives','GET',('num_mounts','drive_dev'),('drive_id',self.drive_id))[0]
        #self.storageMediumFormat = ESSDB.DB().action('storageMedium','GET',('storageMediumFormat',),('storageMediumID',volser))[0][0]
        self.mount = subprocess.Popen(['mtx -f ' + str(robotdev) + ' load ' + str(robot_db[0]) + ' ' + str(drive_id)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.mountout = self.mount.communicate()
        self.returninfo = str(self.mountout)
        self.returncode = self.mount.returncode
        if self.returncode == 0:
            logger.info('Mount tape: %s Successful (work_uuid: %s), start to verify tape identity', volser, work_uuid)
            exitcode, why = Robot().check_tape(tapedev,volser)
            if exitcode in [0, 1, 2]:
                logger.info('Tape identity verify result: %s (work_uuid: %s)', why, work_uuid)
                ESSPGM.Events().create('2000','','ESSArch TLD',ProcVersion,'0','Tapedrive: '+str(self.drive_id),2,storageMediumID=volser)
                self.num_mounts = int(self.num_mounts) + 1
                ESSDB.DB().action('robotdrives','UPD',('num_mounts',self.num_mounts,'status','Mounted','t_id',volser,'slot_id',robot_db[0],'drive_lock',work_uuid),('drive_id',self.drive_id))
                ESSDB.DB().action('robot','UPD',('status','Mounted','drive_id',self.drive_id),('slot_id',robot_db[0]))
            else:
                logger.error('Problem to verify tapeid: ' + volser + ' Message: ' + str(why))
                ESSDB.DB().action('robotdrives','UPD',('status','Fail','t_id','??????','slot_id',robot_db[0],'drive_lock',work_uuid),('drive_id',self.drive_id))
                ESSDB.DB().action('robot','UPD',('status','Fail','drive_id',self.drive_id),('slot_id',robot_db[0]))
        else:
            logger.error('Problem to mount tape: ' + volser + ' Message: ' + str(self.returninfo))
            ESSDB.DB().action('robotdrives','UPD',('status','Fail','t_id','??????','slot_id',robot_db[0],'drive_lock',work_uuid),('drive_id',self.drive_id))
            ESSDB.DB().action('robot','UPD',('status','Fail','drive_id',self.drive_id),('slot_id',robot_db[0]))
            self.returncode = 1 
        if Debug: print 'Mountout:', self.returninfo
        return self.returninfo, self.returncode

    "Unmount tape"
    ###############################################
    def Unmount(self, volser, drive_id=None):
        logger.info('Unmount tape: ' + volser)
        robotdev = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','Robotdev'))[0][0]
        robot_db = ESSDB.DB().action('robot','GET',('slot_id',),('t_id',volser))
        if robot_db:
            robot_db = robot_db[0]
        else:
            self.unmountout = 'Missing MediumID: %s in robot' % str(volser)
            self.returncode = 1
            return self.unmountout, self.returncode
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        if drive_id:
            self.drive_id = drive_id
        else:
            self.drive_id = 0
        self.unmount = subprocess.Popen(['mtx -f ' + str(robotdev) + ' unload ' + str(robot_db[0]) + ' ' + str(drive_id)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.unmountout = self.unmount.communicate()
        if self.unmount.returncode == 0:
            logger.info('Unmount tape: ' + volser + ' Successful')
            ESSPGM.Events().create('2010','','ESSArch TLD',ProcVersion,'0','Tapedrive: '+str(self.drive_id),2,storageMediumID=volser)
            ESSDB.DB().action('robotdrives','UPD',('status','Ready','t_id','','slot_id','0','drive_lock',''),('drive_id',self.drive_id))
            StorageMedium_list = ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumID','storageMediumStatus'),('storageMediumID',volser))
            if len(StorageMedium_list) > 0:
                if StorageMedium_list[0][1] == 0:
                    ESSDB.DB().action('robot','UPD',('status','InactiveTape','drive_id','99'),('slot_id',robot_db[0]))
                elif StorageMedium_list[0][1] == 20:
                    ESSDB.DB().action('robot','UPD',('status','WriteTape','drive_id','99'),('slot_id',robot_db[0]))
                else:
                    ESSDB.DB().action('robot','UPD',('status','ArchTape','drive_id','99'),('slot_id',robot_db[0]))
            else:
                ESSDB.DB().action('robot','UPD',('status','Ready','drive_id','99'),('slot_id',robot_db[0]))
        else:
            logger.error('Problem to unmount tape: ' + volser + 'Message: ' + str(self.unmountout))
            ESSDB.DB().action('robotdrives','UPD',('status','Fail','t_id','??????','slot_id',robot_db[0]),('drive_id',self.drive_id))
            ESSDB.DB().action('robot','UPD',('status','Fail','drive_id',self.drive_id),('slot_id',robot_db[0]))
        if Debug: print 'Unmountout:',self.unmountout
        return self.unmountout, self.unmount.returncode

    "Idle tapedrive unmount process"
    ###############################################
    def IdleUnmountProc(self, q):
        while 1:
            try:                
                try:
                    if q.get_nowait() == 'STOP':
                        break
                except Empty:
                    pass
                #flush_transaction()
                robotdrives_objs = robotdrives.objects.filter(status='Mounted')
                if robotdrives_objs:
                    #################################################
                    # Found mounted tape
                    #flush_transaction()
                    self.nummountreq = robotQueue.objects.filter(ReqType=50, Status=0).count()
                    for robotdrives_obj in robotdrives_objs:
                        if len(robotdrives_obj.drive_lock) == 0: 
                            #################################################
                            # Tape is not locked
                            if int(robotdrives_obj.IdleTime) > 5 and self.nummountreq:
                                ##################################################################################################
                                # Pendning mount request in RobotReqQueue. Set IdleTime to 5 sec.
                                robotdrives_obj.IdleTime = 5
                                robotdrives_obj.save(update_fields=['IdleTime'])
                                logger.info('Setting IdleTime to ' + str(robotdrives_obj.IdleTime) + ' sec, for tape id: ' + str(robotdrives_obj.t_id))
                            elif int(robotdrives_obj.IdleTime) == 9999:
                                ##################################################################
                                # Tape is new_unlocked(9999). Set IdleTime to 120 sec.
                                robotdrives_obj.IdleTime = 120
                                robotdrives_obj.save(update_fields=['IdleTime'])
                                logger.info('Setting IdleTime to ' + str(robotdrives_obj.IdleTime) + ' sec, for tape id: ' + str(robotdrives_obj.t_id))
                            if int(robotdrives_obj.IdleTime) < 9999:
                                ########################################################################
                                # Tape is already discoverd as unlocked(<9999). Count down IdleTime with 1 sec.
                                robotdrives_obj.IdleTime -= 1
                                robotdrives_obj.save(update_fields=['IdleTime'])
                                logger.debug('Count down -1 sec setting IdleTime to ' + str(robotdrives_obj.IdleTime) + ' sec, for tape id: ' + str(robotdrives_obj.t_id))
                            if int(robotdrives_obj.IdleTime) <= 0:
                                ####################################################
                                # Tape IdleTime is zero(0). Try to unmount the tape
                                logger.info('Start to unmount tape: ' + str(robotdrives_obj.t_id))
                                robotQueue_obj = robotQueue()
                                robotQueue_obj.ReqType = 51 # Unmount
                                robotQueue_obj.ReqPurpose = 'TLD - IdleUnmountProc'
                                robotQueue_obj.Status = 0 # Pending
                                robotQueue_obj.MediumID = robotdrives_obj.t_id
                                robotQueue_obj.save()
                                while 1:
                                    #flush_transaction()
                                    robot_objs = robot.objects.filter(t_id=robotdrives_obj.t_id, drive_id='99')
                                    if robot_objs:
                                        logger.info('Success to unmount tape: ' + str(robotdrives_obj.t_id))
                                        break
                                    else:
                                        if not robotQueue.objects.filter(id=robotQueue_obj.id).exists():
                                            logger.warning('Add a second unmount request for: %s' % robotdrives_obj.t_id)
                                            robotQueue_obj = robotQueue()
                                            robotQueue_obj.ReqType = 51 # Unmount
                                            robotQueue_obj.ReqPurpose = 'TLD - IdleUnmountProc'
                                            robotQueue_obj.Status = 0 # Pending
                                            robotQueue_obj.MediumID = robotdrives_obj.t_id
                                            robotQueue_obj.save()
                                            time.sleep(1)
                                        else:
                                            logger.debug('Wait for unmounting of: ' + str(robotdrives_obj.t_id))
                                            time.sleep(10)
                        else:
                            #################################################
                            # Tape is locked. Set IdleTime to 9999.                            
                            robotdrives_obj.IdleTime = 9999
                            robotdrives_obj.save(update_fields=['IdleTime'])
                            logger.debug('Tape is locked setting IdleTime to ' + str(robotdrives_obj.IdleTime) + ' sec, for tape id: ' + str(robotdrives_obj.t_id))
                db.close_old_connections()
                time.sleep(1)
            except:
                logger.error('Unexpected error: %s' % (str(sys.exc_info())))
                raise
        logger.info('Idle Unmount Process stopped')

    ###############################################
    "Read XML string and returns values"
    ###############################################
    def getTapeLabel(self,labelstring=None,DOC=None,FILENAME=None):
        if FILENAME:
            try:
                DOC  =  etree.ElementTree ( file=FILENAME )
            except etree.XMLSyntaxError, detail:
                return [None,None,None,None,None],10,str(detail)
            except IOError, detail:
                return [None,None,None,None,None],20,str(detail)
            EL_root = DOC.getroot()
        if DOC:
            EL_root = DOC.getroot()
        if labelstring:
            try:
                EL_root  =  etree.fromstring(labelstring)
            except etree.XMLSyntaxError, detail:
                return [None,None,None,None,None],10,str(detail)
            except IOError, detail:
                return [None,None,None,None,None],20,str(detail)
        EL_tape = EL_root.find("tape")
        a_storageMediumID = EL_tape.get('id')
        a_CreateDate = EL_tape.get('date')
        EL_format = EL_root.find("format")
        a_storageMediumBlockSize = EL_format.get('blocksize')
        a_storageMedium = EL_format.get('drivemanufacture')
        a_storageMediumFormat = EL_format.get('format')
        return [a_storageMediumID,a_CreateDate,a_storageMediumBlockSize,a_storageMedium,a_storageMediumFormat],0,''

    ###############################################
    "Check if tape is online"
    ###############################################
    def check_online_tape(self, tapedev):
        mt_proc = subprocess.Popen(['mt -f ' + str(tapedev) + ' status'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mt_proc_out = mt_proc.communicate()
        if mt_proc.returncode == 0 and 'ONLINE' in mt_proc_out[0]:
            return 0,''
        else:
            return 1,str(mt_proc_out)

    ###############################################
    "Rewind tape"
    ###############################################
    def rewind_tape(self, tapedev):
        mt_proc = subprocess.Popen(['mt -f ' + str(tapedev) + ' rewind'], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mt_proc_out = mt_proc.communicate()
        if mt_proc.returncode == 0:
            return 0,''
        else:
            return 1,str(mt_proc_out)

    ###############################################
    "Check tape"
    ###############################################
    def check_tape(self, tapedev, volser=None, timeout=120):
        test_num = 0
        while 1:
            exitcode_stat, why_stat = Robot().check_online_tape(tapedev)
            if exitcode_stat == 0 or test_num == timeout:
                break
            time.sleep(1)
            test_num+=1
            logger.info('Wait for tapedev %s to go online with tapeid %s, test_num: %s ' % (tapedev,volser,test_num))
            #print ('Wait for tapedev %s to go online with tapeid %s, test_num: %s ' % (tapedev,volser,test_num))
        exitcode, why = Robot().rewind_tape(tapedev)
        if exitcode == 0:
            try:
                with open(tapedev,'rb') as file:
                    file_content = file.read(20000)
                file.close()
            except IOError, (errno,detail):
                if errno == 5 and detail == 'Input/output error':
                    exitcode, why = Robot().rewind_tape(tapedev)
                    if exitcode == 0:
                        return 0, 'Tape with tapeid: %s is empty(new) in tapedev: %s' % (volser,tapedev)
                    else:
                        return 10, why
                elif errno == 12 and detail == 'Cannot allocate memory':
                    logger.debug('IOError errno: %s, detail: %s' % (errno,detail))
                    #print ('debug: IOError errno: %s, detail: %s' % (errno,detail))
                else:
                    logger.error('IOError errno: %s, detail: %s' % (errno,detail))
                    #print ('IOError errno: %s, detail: %s' % (errno,detail))
            except:
                logger.error('Problem to read first byte from tapedev: %s, errno: %s' % (tapedev,str(sys.exc_info())))

            exitcode, why = Robot().rewind_tape(tapedev)
            if exitcode == 0:
                try:
                    tarf = tarfile.open(tapedev,'r|')
                    tarfile_members = tarf.getmembers()
                    tarf.close()
                    if tarfile_members[0].name[-10:] == '_label.xml':
                        exitcode, why = Robot().rewind_tape(tapedev)
                        if exitcode == 0:
                            tarf = tarfile.open(tapedev,'r|')
                            label_file = tarf.extractfile(tarfile_members[0]).read()
                            tarf.close()
                            res, exitcode, why = Robot().getTapeLabel(labelstring=label_file)
                            exitcode, why = Robot().rewind_tape(tapedev)
                            if exitcode == 0 and volser == res[0]:
                                return 1, 'Found ESSArch labelfile with tapeid: %s that match requested tapeid: %s in tapedev: %s' % (res[0],volser,tapedev)
                            elif exitcode == 0:
                                return 11, 'Found ESSArch labelfile with tapeid: %s that not match requested tapeid: %s in tapedev: %s' % (res[0],volser,tapedev)
                            else:
                                return 12, why
                        else:
                            return 13, why
                    elif tarfile_members[0].name == 'reuse':
                        exitcode, why = Robot().rewind_tape(tapedev)
                        if exitcode == 0:
                            return 2, 'Found reuse flaged tapeid: %s in tapedev: %s' % (volser,tapedev)
                        else:
                            return 19, why
                    else:
                        exitcode, why = Robot().rewind_tape(tapedev)
                        if exitcode == 0:
                            return 18, 'First file on tape is a tarfile but not a ESSArch label file'
                        else:
                            return 14, why
                except:
                    return 15, 'Tape is not empty and problem to read file, error: %s' % str(sys.exc_info())
            else:
                return 16, why
        else:
            return 17, why

#######################################################################################################
# Dep:
# Table: ESSProc with Name: TLD, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: xx Value: yy
# Table: ESSConfig with Name: xx Value: yy
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=0
    ProcName = 'TLD'
    ProcVersion = __version__
    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 1
    Console = 0

    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]

    ##########################
    # Log format
    if MultiProc:
        formatter = logging.Formatter('%(asctime)s %(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
        formatter2 = logging.Formatter('%(levelname)s/%(processName)-8s %(message)s','%d %b %Y %H:%M:%S')
    else:
        formatter = logging.Formatter('%(asctime)s %(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
        formatter2 = logging.Formatter('%(levelname)-8s %(message)s','%d %b %Y %H:%M:%S')
    #create logger default "root"
    rootlogger = logging.getLogger('')
    rootlogger.setLevel(0)
    # create logger
    if MultiProc:
        logger_multi = multiprocessing.get_logger()
        logger_multi.setLevel(0)
    #else:
        #logger = logging.getLogger('pyftpdlib')
    logger = logging.getLogger(ProcName)
    logger.setLevel(0)
    # create file handler and set log level and formatter
    fh = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    fh.setLevel(LogLevel)
    fh.setFormatter(formatter)
    # create console handler and set log level and formatter
    ch = logging.StreamHandler()
    ch.setLevel(LogLevel)
    ch.setFormatter(formatter2)
    # Null handler and set log level and formatter
    nh = logging.NullHandler()
    nh.setLevel(0)
    # add the handlers to the logger
    logger.addHandler(fh)
    if MultiProc:
        logger_multi.addHandler(fh)
    if Console:
        rootlogger.addHandler(ch)
    else:
        rootlogger.addHandler(nh)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

    q1 = multiprocessing.Queue()
    p1 = multiprocessing.Process(target=Robot().IdleUnmountProc, args=(q1,))
    p1.start()

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            if Debug: logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            if Debug: logger.info('test2: ' + str(x.RunFlag))
            x.Die()
            q1.put('STOP')
            break
        if not p1.is_alive():
            logger.info('Idle Unmount Process is not running, flag TLD to stop')
            x.Die()
            break
        time.sleep(5)
    if Debug: logger.info('test3: ' + str(x.RunFlag))
    del x

# ./TLD.py
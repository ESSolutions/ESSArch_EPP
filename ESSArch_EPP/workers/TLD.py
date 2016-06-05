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

import subprocess, thread, datetime, time, logging, logging.handlers, sys, ESSMSSQL, ESSPGM, multiprocessing, tarfile,pytz
from Queue import Empty
from lxml import etree
from django.utils import timezone
from essarch.models import robotQueue, robotdrives, robot
from Storage.models import storageMedium
from configuration.models import ESSProc, ESSConfig
from django import db
from retrying import retry

import django
django.setup()

class RobotException(Exception):
    """
    There was an ambiguous exception that occurred while handling your
    robot.
    """
    def __init__(self, value):
        """
        Initialize RobotException.
        """
        self.value = value
        super(RobotException, self).__init__(value)

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
                PauseTime, self.Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Run')[0]
                if self.Run == '0':
                    logger.info('Stopping ' + ProcName)
                    ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                    self.RunFlag=0
                    self.mLock.release()
                    if Debug: logger.info('RunFlag: 0')
                    time.sleep(2)
                    continue
                # Process Item 
                lock=thread.allocate_lock()
                if Debug: logger.info('Start to list worklist')
                #######################################
                # Start to list robot req
                robotQueue_objs = robotQueue.objects.filter(ReqType__in=[50,51,52], Status=0) #Get pending robot requests
                for robotQueue_obj in robotQueue_objs:
                    if ESSProc.objects.get(Name=ProcName).Run=='0':
                        logger.info('Stopping ' + ProcName)
                        ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                        thread.interrupt_main()
                        break
                    t_id=robotQueue_obj.MediumID
                    if robotQueue_obj.ReqType == 50: #Mount
                        ##########################################
                        # Check if tape is already mounted
                        robotdrives_objs = robotdrives.objects.filter(t_id=t_id, status='Mounted')
                        if robotdrives_objs:
                            robotdrives_obj = robotdrives_objs[0]
                            ##########################################
                            # Tape is mounted, check if locked
                            if len(robotdrives_obj.drive_lock) > 0:
                                ########################################
                                # Tape is locked, check if req work_uuid = lock
                                if robotdrives_obj.drive_lock == robotQueue_obj.ReqUUID:
                                    ########################################
                                    # Tape is already locked with req work_uuid
                                    logger.info('Already Mounted: ' + str(t_id) + ' and locked by req work_uuid: ' + str(robotQueue_obj.ReqUUID))
                                    robotQueue_obj.delete()
                                else:
                                    ########################################
                                    # Tape is locked with another work_uuid
                                    logger.info('Tape: ' + str(t_id) + ' is busy and locked by: ' + str(robotdrives_obj.drive_lock) + ' and not req work_uuid: ' + str(robotQueue_obj.ReqUUID))
                            else:
                                ########################################
                                # Tape is not locked, lock the drive with req work_uuid
                                robotdrives_obj.drive_lock=robotQueue_obj.ReqUUID
                                robotdrives_obj.save(update_fields=['drive_lock'])
                                logger.info('Tape: ' + str(t_id) + ' is available set lock to req work_uuid: ' + str(robotQueue_obj.ReqUUID))
                                robotQueue_obj.delete()
                        else:
                            ##########################################
                            # Tape is not mounted, check for available tape drives
                            robotdrives_objs = robotdrives.objects.filter(status='Ready') #Get available tape drives      
                            if robotdrives_objs:
                                robotdrives_obj=robotdrives_objs[0]
                                ########################################
                                # Tapedrives is available try to mount tape
                                robotQueue_obj.Status=5
                                robotQueue_obj.save(update_fields=['Status'])
                                try:
                                    Robot().Mount(t_id,robotdrives_obj.drive_id,robotQueue_obj.ReqUUID)
                                except RobotException as e:
                                    logger.error('Problem to mount tape: ' + t_id + ' Message: ' + e)
                                    robotQueue_obj.Status=100
                                    robotQueue_obj.save(update_fields=['Status'])
                                else:
                                #if returncode == 0:
                                    robotQueue_obj.delete()
                                    if storageMedium.objects.filter(storageMediumID=t_id).exists():
                                        ######################################################
                                        # Update StorageMediumTable with num of mounts
                                        storageMedium_obj=storageMedium.objects.get(storageMediumID=t_id)
                                        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                        timestamp_dst = timestamp_utc.astimezone(self.tz)
                                        storageMedium_obj.storageMediumMounts += 1
                                        storageMedium_obj.storageMediumLocationStatus = 50
                                        storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                                        storageMedium_obj.LocalDBdatetime = timestamp_utc
                                        storageMedium_obj.save(update_fields=['storageMediumMounts','storageMediumLocationStatus','linkingAgentIdentifierValue','LocalDBdatetime'])
                                        if ExtDBupdate:
                                            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumLocationStatus',50,
                                                                                                                            'storageMediumMounts',storageMedium_obj.storageMediumMounts,
                                                                                                                            'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                                           ('storageMediumID',t_id))
                                            if ext_errno: logger.error('Failed to update External DB: ' + str(t_id) + ' error: ' + str(ext_why))
                                            else:
                                                storageMedium_obj.ExtDBdatetime = timestamp_utc
                                                storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                                #else:
                                    #logger.error('Problem to mount tape: ' + t_id + ' Message: ' + str(mountout))
                                    #robotQueue_obj.Status=100
                                    #robotQueue_obj.save(update_fields=['Status'])
                    elif robotQueue_obj.ReqType in [51, 52]: # Unmount(51), F_Unmount(52)
                        ######################################
                        # Check if tape is mounted
                        robotdrives_objs = robotdrives.objects.filter(t_id=t_id) #Get tape drive that is mounted
                        if robotdrives_objs:
                            robotdrives_obj = robotdrives_objs[0]
                            ################################################
                            # Tape is mounted, check if tape is locked(busy)
                            if len(robotdrives_obj.drive_lock) == 0 or robotQueue_obj.ReqType == 52:
                                if len(robotdrives_obj.drive_lock) > 0 and robotQueue_obj.ReqType == 52:
                                    logger.info('Tape %s is locked with work_uuid %s, try to force unmount',t_id,robotdrives_obj.drive_lock)
                                ###################################################
                                # Try to unmount
                                robotQueue_obj.Status=5
                                robotQueue_obj.save(update_fields=['Status'])
                                robotdrives_obj.status='Unmounting'
                                robotdrives_obj.save(update_fields=['status'])
                                try:
                                    Robot().Unmount(t_id,robotdrives_obj.drive_id)
                                except RobotException as e:
                                    logger.error('Problem to unmount tape: ' + t_id + ' Message: ' + e)
                                    robotQueue_obj.Status=100
                                    robotQueue_obj.save(update_fields=['Status'])
                                else:
                                #if returncode == 0:
                                    robotQueue_obj.delete()
                                #else:
                                    #logger.error('Problem to unmount tape: ' + t_id + ' Message: ' + str(mountout))
                                    #robotQueue_obj.Status=100
                                    #robotQueue_obj.save(update_fields=['Status'])
                            else:
                                #################################################
                                # Tape is locked, skip to unmount
                                logger.info('Tape ' + t_id + ' is locked, skip to unmount')
                        else:
                            ################################################
                            # Tape is not mounted, skip to try to unmount
                            logger.info('Tape ' + t_id + ' is not mounted')
                            robotQueue_obj.delete()
                db.close_old_connections()
                self.mLock.release()
                time.sleep(int(PauseTime))
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
    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def Mount(self, volser, drive_id=None, work_uuid=''):
        logger.info('Mount tape: ' + volser)
        robotdev = ESSConfig.objects.get(Name='Robotdev').Value
        robot_objs = robot.objects.filter(t_id=volser)
        if robot_objs:
            robot_obj = robot_objs[0]
        else:
            mountout = 'Missing MediumID: %s in robot' % str(volser)
            raise RobotException(mountout)
            #returncode = 1
            #return mountout, returncode
        if not drive_id:
            drive_id = 0
        robotdrives_obj = robotdrives.objects.get(drive_id=drive_id)
        mount_proc = subprocess.Popen(['mtx -f ' + str(robotdev) + ' load ' + str(robot_obj.slot_id) + ' ' + str(drive_id)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        mountout = mount_proc.communicate()
        returncode = mount_proc.returncode
        returninfo = '%s, code: %s' % (str(mountout), returncode)
        if returncode == 0:
            logger.info('Mount tape: %s Successful (work_uuid: %s), start to verify tape identity', volser, work_uuid)
            tapestatus, why = Robot().check_tape(robotdrives_obj.drive_dev, volser)
            if tapestatus in [0, 1, 2]:
                logger.info('Tape identity verify result: %s (work_uuid: %s)', why, work_uuid)
                ESSPGM.Events().create('2000','','ESSArch TLD',ProcVersion,'0','Tapedrive: '+str(drive_id),2,storageMediumID=volser)
                robotdrives_obj.num_mounts += 1
                robotdrives_obj.status='Mounted'
                robotdrives_obj.t_id=volser
                robotdrives_obj.slot_id = robot_obj.slot_id
                robotdrives_obj.drive_lock = work_uuid
                robotdrives_obj.IdleTime = 9999
                robotdrives_obj.save(update_fields=['num_mounts', 'status', 't_id', 'slot_id', 'drive_lock', 'IdleTime'])
                robot_obj.status='Mounted'
                robot_obj.drive_id=drive_id
                robot_obj.save(update_fields=['status', 'drive_id'])
            else:
                logger.error('Problem to verify tapeid: ' + volser + ' Message: ' + str(why))
                robotdrives_obj.status='Fail'
                robotdrives_obj.t_id='??????'
                robotdrives_obj.slot_id = robot_obj.slot_id
                robotdrives_obj.drive_lock = work_uuid
                robotdrives_obj.IdleTime = 9999
                robotdrives_obj.save(update_fields=['status', 't_id', 'slot_id', 'drive_lock', 'IdleTime'])
                robot_obj.status='Fail'
                robot_obj.drive_id=drive_id
                robot_obj.save(update_fields=['status', 'drive_id'])
        else:
            logger.error('Problem to mount tape: ' + volser + ' Message: ' + returninfo)
            robotdrives_obj.status='Fail'
            robotdrives_obj.t_id='??????'
            robotdrives_obj.slot_id = robot_obj.slot_id
            robotdrives_obj.drive_lock = work_uuid
            robotdrives_obj.IdleTime = 9999
            robotdrives_obj.save(update_fields=['status', 't_id', 'slot_id', 'drive_lock', 'IdleTime'])
            robot_obj.status='Fail'
            robot_obj.drive_id=drive_id
            robot_obj.save(update_fields=['status', 'drive_id'])
            #returncode = 1 
            raise RobotException(returninfo)
        #if Debug: print 'Mountout:', returninfo
        #return returninfo, returncode, tapestatus

    "Unmount tape"
    ###############################################
    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def Unmount(self, volser, drive_id=None):
        logger.info('Unmount tape: ' + volser)
        robotdev = ESSConfig.objects.get(Name='Robotdev').Value
        robot_objs = robot.objects.filter(t_id=volser)
        if robot_objs:
            robot_obj = robot_objs[0]
        else:
            unmountout = 'Missing MediumID: %s in robot' % str(volser)
            raise RobotException(unmountout)
            #returncode = 1
            #return unmountout, returncode
        if not drive_id:
            drive_id = 0
        robotdrives_obj = robotdrives.objects.get(drive_id=drive_id)
        unmount_proc = subprocess.Popen(['mtx -f ' + str(robotdev) + ' unload ' + str(robot_obj.slot_id) + ' ' + str(drive_id)], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        unmountout = unmount_proc.communicate()
        returncode = unmount_proc.returncode
        returninfo = '%s, code: %s' % (str(unmountout), returncode)
        if returncode == 0:
            logger.info('Unmount tape: ' + volser + ' Successful')
            ESSPGM.Events().create('2010','','ESSArch TLD',ProcVersion,'0','Tapedrive: '+str(drive_id),2,storageMediumID=volser)
            robotdrives_obj.status='Ready'
            robotdrives_obj.t_id=''
            robotdrives_obj.slot_id = '0'
            robotdrives_obj.drive_lock = ''
            robotdrives_obj.save(update_fields=['status', 't_id', 'slot_id', 'drive_lock'])
            storageMedium_objs = storageMedium.objects.filter(storageMediumID=volser)
            if storageMedium_objs:
                storageMedium_obj = storageMedium_objs[0]
                if storageMedium_obj.storageMediumStatus==0:
                    robot_obj.status='Inactive'
                    robot_obj.drive_id='99'
                elif storageMedium_obj.storageMediumStatus==20:
                    robot_obj.status='Write'
                    robot_obj.drive_id='99'
                else:
                    robot_obj.status='Full'
                    robot_obj.drive_id='99'
            else:
                robot_obj.status='New'
                robot_obj.drive_id='99'
            robot_obj.save(update_fields=['status', 'drive_id'])
        else:
            logger.error('Problem to unmount tape: ' + volser + 'Message: ' + returninfo)
            robotdrives_obj.status='Fail'
            robotdrives_obj.t_id='??????'
            robotdrives_obj.slot_id = robot_obj.slot_id
            robotdrives_obj.save(update_fields=['status', 't_id', 'slot_id'])
            robot_obj.status='Fail'
            robot_obj.drive_id=drive_id
            robot_obj.save(update_fields=['status', 'drive_id'])
            raise RobotException(returninfo)
        #if Debug: print 'Unmountout:',unmountout
        #return unmountout, unmount_proc.returncode

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
                numreadydrives = robotdrives.objects.filter(status='Ready').count()
                robotdrives_objs = robotdrives.objects.filter(status='Mounted')
                if robotdrives_objs:
                    #################################################
                    # Found mounted tape
                    nummountreq = robotQueue.objects.filter(ReqType=50, Status=0).count()
                    for robotdrives_obj in robotdrives_objs:
                        if len(robotdrives_obj.drive_lock) == 0: 
                            #################################################
                            # Tape is not locked
                            if int(robotdrives_obj.IdleTime) > 10 and nummountreq > 0 and numreadydrives == 0:
                                ##################################################################################################
                                # Pendning mount request in RobotReqQueue. Set IdleTime to 10 sec.
                                robotdrives_obj.IdleTime = 10
                                robotdrives_obj.save(update_fields=['IdleTime'])
                                logger.info('Setting IdleTime to ' + str(robotdrives_obj.IdleTime) + ' sec, for tape id: ' + str(robotdrives_obj.t_id))
                            elif int(robotdrives_obj.IdleTime) == 9999:
                                ##################################################################
                                # Tape is new_unlocked(9999). Set IdleTime to 3600 sec.
                                robotdrives_obj.IdleTime = 3600
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
                                robotQueue_obj.user = 'sys'
                                robotQueue_obj.save()
                                while 1:
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
                                            robotQueue_obj.user = 'sys'
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
                else:
                    logger.error('IOError errno: %s, detail: %s' % (errno,detail))
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
    LogFile,Time,Status,Run = ESSProc.objects.filter(Name=ProcName).values_list('LogFile','Time','Status','Run')[0]

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
    #fh = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    fh = logging.FileHandler(LogFile)
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

    AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
    ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

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
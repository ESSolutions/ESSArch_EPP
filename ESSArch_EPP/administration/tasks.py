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
    
from jobtastic import JobtasticTask
import ESSPGM, datetime, uuid, time, os, shutil, logging, subprocess, db_sync_ais, pytz, sys, traceback, re
from configuration.models import ESSConfig
from essarch.models import MigrationQueue, AccessQueue, ArchiveObject, robotQueue, robot, robotdrives
from Storage.models import storageMedium
from Storage.libs import StorageMethodWrite
from administration.models import robot_info, robot_drive, robot_slot, robot_export
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from essarch.libs import ESSArchSMError

logger = logging.getLogger('essarch.storagemaintenance')

class MigrationTask(JobtasticTask):
    """
    Mediamigration tasks.
    """
    
    significant_kwargs = [
        ('obj_list', str),
        ('mig_pk', str),
    ]
    herd_avoidance_timeout = 120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self, obj_list, mig_pk): 
        logger = logging.getLogger('essarch.storagemaintenance')
        migtask = MigrationQueue.objects.get(pk=mig_pk)
        if obj_list == migtask.ObjectIdentifierValue:
            event_info = 'obj_list is OK!'
            logger.debug(event_info)
        tasks = list(migtask.ObjectIdentifierValue)
        tasks_todo = list(tasks)
        num_tasks = len(tasks)

        # Let folks know we started
        self.update_progress(0, num_tasks)
        migtask.Status = 5
        migtask.save()
           
        # Create all tasks
        ok_flag = 1
        for counter, task in enumerate(tasks):
            if ok_flag == 1:
                #result = self.createcopytest(task, migtask.TargetMediumID, migtask.Path, migtask.CopyPath, migtask.CopyOnlyFlag)
                result = self.createcopy(task, migtask.TargetMediumID, migtask.Path, migtask.CopyPath, migtask.CopyOnlyFlag)
                if result == 0:
                    if task == tasks_todo.pop(0):
                        event_info = 'Success to copy ObjectUUID: %s' % task
                        logger.info(event_info)
                        migtask.ObjectIdentifierValue = tasks_todo
                        migtask.save()
                    else:
                        event_info = 'copy ObjectUUID: %s but task not match pop...' % task
                        logger.error(event_info)
                else:
                    ok_flag = 0
                    event_info = 'Problem to migrate ObjectUUID: %s' % task
                    logger.error(event_info)
            else:
                event_info = 'Unable to migrate ObjectUUID: %s' % task
                logger.error(event_info)
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(10)
            self.update_progress(counter, num_tasks, update_frequency=1)
        
        if ok_flag == 1:
            migtask.Status = 20
            migtask.save()
        else:
            migtask.Status = 100
            migtask.save()
                
    def createcopytest(self, ObjectUUID, TargetMediumID, TmpPath, CopyPath, CopyOnlyFlag):
        logger = logging.getLogger('essarch.storagemaintenance')
        # MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value
        print CopyOnlyFlag
        if CopyOnlyFlag == True:
            event_info = 'object %s copied to %s' % (ObjectUUID, CopyPath)
            logger(event_info)
            
        else:
            event_info = 'Migrate object: %s to new media target: %s' % (ObjectUUID, TargetMediumID)
            logger.info(event_info)
        
        arch_obj_list = ArchiveObject.objects.filter(ObjectUUID=ObjectUUID)
        if arch_obj_list.exists():
            arch_obj = arch_obj_list[0]
        else:
            event_info = 'Error ArchiveObject not found for ObjectUUID: %s' % ObjectUUID
            logger.error(event_info)
        
        event_info = 'TmpPath: %s, CopyPath: %s' % (TmpPath, CopyPath)
        logger.debug(event_info)
        
        return 0

    def createcopy(self, ObjectUUID, TargetMediumID, TmpPath, CopyPath, CopyOnlyFlag):
        logger = logging.getLogger('essarch.storagemaintenance')
        MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value
            
        event_info = 'Migrate object: %s to new media target: %s' % (ObjectUUID, TargetMediumID)
        logger.info(event_info)
        
        ArchiveObject_objs = ArchiveObject.objects.filter(ObjectUUID=ObjectUUID)
        if ArchiveObject_objs.exists():
            ArchiveObject_obj = ArchiveObject_objs[0]
        else:
            event_info = 'Error ArchiveObject not found for ObjectUUID: %s' % ObjectUUID
            logger.error(event_info)
        
        ReqUUID = uuid.uuid1()
        ReqType = u'3'
        ReqPurpose = u'migrate'
        ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
        storageMediumID = u''
        user = u'system'
        
        # Log Access Order request for ObjectIdentifierValue
        event_info = 'User: %s has create a Access Order Request for ObjectIdentifierValue: %s' % (str(user),str(ObjectIdentifierValue))
        logger.info(event_info)
        #ESSPGM.Events().create('1201',ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,ObjectIdentifierValue)
        
        # Add Access Order request to AccessQueue database table
        AccessQueue_obj = AccessQueue()
        setattr(AccessQueue_obj, 'ReqUUID', ReqUUID)
        setattr(AccessQueue_obj, 'ReqType', ReqType)
        setattr(AccessQueue_obj, 'ReqPurpose', ReqPurpose)
        setattr(AccessQueue_obj, 'user', user)
        setattr(AccessQueue_obj, 'ObjectIdentifierValue', ObjectIdentifierValue)
        setattr(AccessQueue_obj, 'storageMediumID', storageMediumID)
        setattr(AccessQueue_obj, 'Status', 0)
        setattr(AccessQueue_obj, 'Path', TmpPath)
        AccessQueue_obj.save()
        
        # Wait for access request to success
        loop_num = 0
        while 1:
            DbRows = AccessQueue.objects.filter(ReqUUID=ReqUUID)
            if DbRows.exists():
                DbRow = DbRows[0]
                if DbRow.Status==20:
                    event_info = 'Success to access object: %s ReqUUID: %s' % (ObjectIdentifierValue,ReqUUID)
                    logger.info(event_info)
                    DbRow.delete()
                    break
                elif loop_num == 15:
                    event_info = 'Access for object: %s RequUID: %s Status: %s' % (ObjectIdentifierValue, ReqUUID, DbRow.Status)
                    logger.info(event_info)
                    loop_num = 0
            else:
                event_info = 'Access for object: %s with ReqUUID: %s does not exists' % (ObjectIdentifierValue, ReqUUID)
                logger.info(event_info)
                return 1
            loop_num += 1
            time.sleep(1)
        
        # Write request
        if CopyOnlyFlag == False:
            try:
                StorageMethodWrite_obj = StorageMethodWrite()
                StorageMethodWrite_obj.logger = logger
                StorageMethodWrite_obj.ArchiveObject_objs = ArchiveObject_objs
                StorageMethodWrite_obj.target_list = TargetMediumID
                StorageMethodWrite_obj.TempPath = TmpPath
                StorageMethodWrite_obj.force_write_flag = 1
                StorageMethodWrite_obj.add_to_ioqueue()
                StorageMethodWrite_obj.apply_ios_to_write()
                StorageMethodWrite_obj.wait_for_all_writes()
            except ESSArchSMError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Problem to write object %s, error: %s line: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, exc_traceback.tb_lineno)
                logger.error(msg)
                return 1
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error to write object %s, error: %s trace: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)))
                logger.error(msg)
                return 1

        # Remove object from tmp area or move to CopyPath
        Pmets_objpath = os.path.join(TmpPath,ObjectIdentifierValue + '_Package_METS.xml')
        ObjectPath = os.path.join(TmpPath,ObjectIdentifierValue + '.tar')
        if CopyPath:
            copy_Pmets_objpath = os.path.join(CopyPath,ObjectIdentifierValue + '_Package_METS.xml')
            copy_ObjectPath = os.path.join(CopyPath,ObjectIdentifierValue + '.tar')
        MetaObjectSize = os.stat(Pmets_objpath)[6]
        ObjectSize = int(ArchiveObject_obj.ObjectSize)
        WriteSize = ObjectSize + MetaObjectSize
        RemoveFlag='1'
        if RemoveFlag == '1' and CopyPath:
            startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            if CopyOnlyFlag == True: 
                event_info = 'CopyOnly: Try to move ObjectPath: %s to %s and move PackageMets: %s to %s' % (ObjectPath, copy_ObjectPath, Pmets_objpath, copy_Pmets_objpath)
            else:
                event_info = 'Try to move ObjectPath: %s to %s and move PackageMets: %s to %s' % (ObjectPath, copy_ObjectPath, Pmets_objpath, copy_Pmets_objpath)
            logger.info(event_info)
            try:
                shutil.move(ObjectPath,copy_ObjectPath)
                shutil.move(Pmets_objpath,copy_Pmets_objpath)
            except (IOError,os.error), why:
                if CopyOnlyFlag == True:
                    event_info = 'CopyOnly: Problem to move ObjectPath: ' + ObjectPath + ' and ' + Pmets_objpath
                else:
                    event_info = 'Problem to move ObjectPath: ' + ObjectPath + ' and ' + Pmets_objpath
                logger.error(event_info)
                return 1
            else:
                stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                ProcTime = stopTime-startTime
                if ProcTime.seconds < 1: ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                ProcMBperSEC = int(WriteSize)/int(ProcTime.seconds)
                if CopyOnlyFlag == True:
                    event_info = 'CopyOnly: Succeeded to move ObjectPath: ' + ObjectPath + ' , ' + str(ProcMBperSEC) + ' MB/Sec and Time: ' + str(ProcTime)
                else:
                    event_info = 'Succeeded to move ObjectPath: ' + ObjectPath + ' , ' + str(ProcMBperSEC) + ' MB/Sec and Time: ' + str(ProcTime)
                logger.info(event_info)
                return 0
        elif RemoveFlag == '1':    
            startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            event_info = 'Try to remove ObjectPath: ' + ObjectPath + ' and ' + Pmets_objpath
            logger.info(event_info)
            try:
                os.remove(ObjectPath)
                os.remove(Pmets_objpath)
            except (IOError,os.error), why:
                event_info = 'Problem to remove ObjectPath: ' + ObjectPath + ' and ' + Pmets_objpath
                logger.error(event_info)
                return 1
            else:
                stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                ProcTime = stopTime-startTime
                if ProcTime.seconds < 1: ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                ProcMBperSEC = int(WriteSize)/int(ProcTime.seconds)
                event_info = 'Succeeded to remove ObjectPath: ' + ObjectPath + ' , ' + str(ProcMBperSEC) + ' MB/Sec and Time: ' + str(ProcTime)
                logger.info(event_info)
                return 0
                
class RobotInventoryTask(JobtasticTask):
    """
    RobotInventory tasks.
    """
    
    significant_kwargs = [
        ('req_pk', str),
    ]
    herd_avoidance_timeout = 120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400
    
    TimeZone = timezone.get_default_timezone_name()
    tz=timezone.get_default_timezone()

    def calculate_result(self, req_pk, CentralDB=1):
        logger = logging.getLogger('essarch.administration')
        taskobj = robotQueue.objects.get(pk=req_pk)
        status_code = 0
        res, robot_status_code, robot_status_detail = self.get_robot_content()        
        if robot_status_code:
            logger.error('Problem to get robot content information, details: %s' % robot_status_detail)
            status_code = 1
        robot_info_obj ,robot_drive_list, robot_slot_list, robot_export_list = res
        tasks = robot_slot_list
        tasks_todo = list(tasks)
        num_tasks = len(tasks)

        # Let folks know we started
        self.update_progress(0, num_tasks)
        taskobj.Status = 5
        taskobj.save()
        
        #robot_slot_list[5].status = 'Full'
        #robot_slot_list[5].volume_id = 'ESA002'
        #robot_slot_list[6].status = 'Full'
        
        # Create all tasks
        tmp_error_list , result = self.validate_volume_id(robot_slot_list)
        if result:
            taskobj.Status = 100
            taskobj.save()
            event_info = 'Invalid media in robot. Detail: %s' % tmp_error_list
            logger.critical(event_info)
            raise Exception(tmp_error_list)
        result = self.prepare_robot_table(robot_info_obj)
        if result: status_code = 2
        result = self.prepare_robotdrives_table(robot_drive_list)
        if result: status_code = 3
        result = self.update_robotdrives(robot_drive_list)
        if result: status_code = 4
        for counter, task in enumerate(tasks):
            result = self.update_robotslots([task,], CentralDB=CentralDB)
            if result == 0:
                event_info = 'Success to get mediumID: %s, slot: %s' % (task.volume_id, task.slot_id)
                logger.info(event_info)
            else:
                status_code = 5
                event_info = 'Problem to inventory robot with mediumID: %s, slot: %s' % (task.volume_id, task.slot_id)
                logger.error(event_info)
            if not task == tasks_todo.pop(0):
                event_info = 'Task list not in sync, mediumID: %s' % task.volume_id
                logger.error(event_info)
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(1)
            self.update_progress(counter, num_tasks, update_frequency=1)
        
        if status_code == 0:
            taskobj.Status = 20
        else:
            logger.error('Problem to inventory robot, status_code: %s' % status_code)
            taskobj.Status = 100
        taskobj.save()
    
    def validate_volume_id(self,obj_list):
        """
        Validate that volume_ids is unique
        """
        status_code = 0
        res = []
        
        tmp_list = []
        for i in obj_list:
            if i.status == 'Full':
                if i.volume_id == '':
                    status_code = 1
                    res.append('No volume_id found for slot_id: %s' % i.slot_id)
                elif i.status == 'Full' and i.volume_id in tmp_list:
                    status_code = 2
                    res.append('Volume_id: %s is not unique' % i.volume_id)
                else:
                    tmp_list.append(i.volume_id)
        return res, status_code
        
    def prepare_robot_table(self,robot_info_obj):
        """
        Prepare robot table
        """
        if not robot.objects.count() == robot_info_obj.slots:
            robot.objects.all().delete()
            for slot_id in range(1, robot_info_obj.slots+1):
                robot_obj = robot()
                robot_obj.status = 'None'
                robot_obj.t_id = ''
                robot_obj.drive_id = '99'
                robot_obj.slot_id = slot_id
                robot_obj.save()
        return 0
    
    def prepare_robotdrives_table(self,robot_info_obj):
        """
        Prepare robotdrives table
        """
        # TODO: function "prepare_robotdrives"
        pass
        return 0             

    def update_robotdrives(self,robot_drive_list):
        """
        update robotdrives table
        """
        logger = logging.getLogger('essarch.administration')
        for rd in robot_drive_list:
            try:
                robotdrives_obj = robotdrives.objects.get(drive_id=rd.drive_id)
                if rd.status == 'Full':
                    robotdrives_obj.status = 'Mounted'
                    robotdrives_obj.t_id = rd.volume_id
                    robotdrives_obj.slot_id = rd.slot_id
                elif rd.status == 'Empty':
                    robotdrives_obj.status = 'Ready'
                    robotdrives_obj.t_id = ''
                    robotdrives_obj.slot_id = 0
                robotdrives_obj.save()
            except robotdrives.DoesNotExist,why:
                logger.warning('ESSArch has no tapedrive configuration for drive_id: %s' % rd.drive_id)

    def update_robotslots(self,robot_slot_list, CentralDB=1, set_storageMediumLocation='', set_storageMediumLocationStatus=''):
        """
        update robot (slot) table
        """
        logger = logging.getLogger('essarch.administration')
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value
        ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

        for rs in robot_slot_list:
            if rs.status == 'Full':
                #######################################################
                # Slot is occupied
                if CentralDB == 1 and ExtDBupdate == 1:
                    logger.info('Try to sync local DB from central DB for mediaID: %s' % rs.volume_id)
                    errno = db_sync_ais.work().sync_from_centralDB(storageMediumID=rs.volume_id,
                                                                   set_storageMediumLocation=set_storageMediumLocation,
                                                                   set_storageMediumLocationStatus=set_storageMediumLocationStatus)
                    if errno == 0:
                        ######################################################
                        # Succeed to update local DB for storageMediaID
                        logger.info('Success to sync objects for mediaID: %s from centralDB to localDB' % rs.volume_id) 
                    elif errno == 1:
                        ######################################################
                        # storageMediaID not found in central "storageMedium" DB 
                        logger.info('mediaID: %s not found in centralDB' % rs.volume_id)
                    elif errno == 2 or errno == 3:
                        logger.info('No archive objects to sync for mediaID: %s from central DB, exit code: %s' % (rs.volume_id,str(errno)))
                    elif errno > 3:
                        logger.error('Failed to sync mediaID: %s from central DB, errno: %s' % (rs.volume_id,str(errno)))
                        return 30
                    
                logger.info('Check if mediaID: %s exist in local DB' % rs.volume_id)
                storageMedium_objs = storageMedium.objects.filter(storageMediumID=rs.volume_id)
                
                if len(storageMedium_objs) > 1:
                    logger.error('To many storagemedias found in local "storageMedium" DB for %s' % rs.volume_id)
                    TapeExistFlag = 1
                elif len(storageMedium_objs) == 1:
                    logger.info('Found storageMedia %s in local DB' % rs.volume_id)
                    TapeExistFlag = 1
                else:
                    TapeExistFlag = 0
                    
                robot_obj = robot.objects.get(slot_id=rs.slot_id)
                robot_obj.t_id = rs.volume_id
                robot_obj.drive_id = '99'
                UpdateTapeLocationFlag = 0    
                if TapeExistFlag:
                    if storageMedium_objs[0].storageMediumStatus == 0:
                        robot_obj.status = 'Inactive'
                        UpdateTapeLocationFlag = 0
                    elif storageMedium_objs[0].storageMediumStatus == 20:
                        robot_obj.status = 'Write'
                        UpdateTapeLocationFlag = 1
                    else:
                        robot_obj.status = 'Full'
                        UpdateTapeLocationFlag = 1
                    if UpdateTapeLocationFlag == 1:
                        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                        timestamp_dst = timestamp_utc.astimezone(self.tz)
                        if ExtDBupdate == 1:
                            ext_storageMediumTable = 'storageMedium'
                        else:
                            ext_storageMediumTable = ''
                        errno,why = ESSPGM.DB().SetStorageMediumLocation(local_table='storageMedium',
                                                                         ext_table=ext_storageMediumTable,
                                                                         AgentIdentifierValue=AgentIdentifierValue,
                                                                         storageMediumID=rs.volume_id,
                                                                         storageMediumLocation=MediumLocation,
                                                                         storageMediumLocationStatus=50,
                                                                         storageMediumDate=timestamp_utc)
                        if errno:
                            logger.error('Failed to update location for MediumID: %s , error: %s' % (rs.volume_id,str(why)))
                else:
                    robot_obj.status = 'Empty'
                robot_obj.save()

            elif rs.status == 'Empty':
                robotdrives_objs = robotdrives.objects.filter(slot_id=rs.slot_id)
                robot_obj = robot.objects.get(slot_id=rs.slot_id)
                if len(robotdrives_objs) == 1:
                    robotdrives_obj = robotdrives_objs[0]
                    robot_obj.status = 'Mounted'
                    robot_obj.t_id = robotdrives_obj.t_id
                    robot_obj.drive_id = robotdrives_obj.drive_id
                    robot_obj.save()
                else:
                    robot_obj.status = 'None'
                    robot_obj.t_id = ''
                    robot_obj.drive_id = '99'
                    robot_obj.save()
        return 0
                                                  
    def get_robot_content(self):
        """
        Get robot content information
        """
        logger = logging.getLogger('essarch.administration')
        logger.info('Get robot content information')
        
        robot_info_obj = None
        robot_drive_list = []
        robot_slot_list = []
        robot_export_list = []
        status_code = 0
        status_list = []
        error_list = []
        res = []
        
        robotdev = ESSConfig.objects.get(Name='Robotdev').Value
        
        RobotStat = subprocess.Popen(["mtx -f " + str(robotdev) + " status"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        RobotStat_result = RobotStat.communicate()
        if RobotStat.returncode:
            info_message = 'Failed to get status from robot, error: %s' % str(RobotStat_result)
            logger.error(info_message)
            error_list.append(info_message)
            status_code = 1
        else:
            logger.debug('Robot status output: %s',str(RobotStat_result))
            result_row = ''
            re_word = re.compile(r'\W+')
            for i in RobotStat_result[0]:
                if i == '\n':
                    if re.match('  Storage Changer',result_row):             #Grep Storage Changer information
                        info_el = re_word.split(result_row)
                        logger.debug('Info: %s' % info_el)
                        robot_info_obj = robot_info()
                        robot_info_obj.drives = int(info_el[5])
                        robot_info_obj.slots = int(info_el[7])
                    if re.match('Data Transfer Element',result_row):         #Grep Robot drive status
                        dt_el = re_word.split(result_row)
                        logger.debug('Data Transfer Element: %s' % dt_el)
                        robot_drive_obj = robot_drive()
                        robot_drive_obj.drive_id = dt_el[3]
                        robot_drive_obj.status = dt_el[4]
                        if robot_drive_obj.status == 'Full':
                            robot_drive_obj.slot_id = dt_el[7]
                            robot_drive_obj.volume_id = dt_el[10][:6]
                        robot_drive_list.append(robot_drive_obj)
                    if re.match('      Storage Element',result_row):         #Grep Robot slot status
                        if not re.search('EXPORT',result_row):
                            s_el = re_word.split(result_row)
                            logger.debug('Storage Element: %s' % s_el)
                            robot_slot_obj = robot_slot()
                            robot_slot_obj.slot_id = s_el[3]
                            robot_slot_obj.status = s_el[4]
                            if robot_slot_obj.status == 'Full':
                                robot_slot_obj.volume_id = s_el[6][:6]
                                robot_slot_obj.volume_ver = s_el[6][6:]
                            robot_slot_list.append(robot_slot_obj)
                        else:                                               #If robot slot is Import/Export slot (Not used)
                            e_el = re_word.split(result_row)
                            logger.info('Export/Import Element: %s' % e_el)
                            robot_export_obj = robot_export()
                            robot_export_obj.slot_id = e_el[3]
                            robot_export_obj.status = e_el[6]
                            if robot_export_obj.status == 'Full':
                                robot_export_obj.volume_id = e_el[8][:6]
                                robot_export_obj.volume_ver = e_el[8][6:]
                            robot_export_list.append(robot_export_obj)
                    result_row = ''
                    continue
                result_row = result_row + i
            res = [robot_info_obj, robot_drive_list, robot_slot_list, robot_export_list]
        return res, status_code, [status_list, error_list] 
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB

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
from jobtastic import JobtasticTask
import ESSPGM, datetime, uuid, time, os, shutil, logging
from configuration.models import ESSConfig
from essarch.models import MigrationQueue, AccessQueue, ArchiveObject, IOqueue

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
        for counter, task in enumerate(tasks):
            #result = self.createcopytest(task, migtask.TargetMediumID, migtask.Path, migtask.CopyPath)
            result = self.createcopy(task, migtask.TargetMediumID, migtask.Path, migtask.CopyPath)
            if result == 0:
                if task == tasks_todo.pop(0):
                    event_info = 'Success to copy ObjectUUID: %s' % task
                    logger.info(event_info)
                    migtask.ObjectIdentifierValue = tasks_todo
                    migtask.save()
                else:
                    event_info = 'copy ObjectUUID: %s but task not match pop...' % task
                    logger.error(event_info)
            #event_info = 'sleep 10'
            #logger.debug(event_info)
            #time.sleep(10)
            self.update_progress(counter, num_tasks, update_frequency=1)
        
        migtask.Status = 20
        migtask.save()
                
    def createcopytest(self, ObjectUUID, TargetMediumID, TmpPath, CopyPath):
        MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value
            
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

    def createcopy(self, ObjectUUID, TargetMediumID, TmpPath, CopyPath):
        MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value
            
        event_info = 'Migrate object: %s to new media target: %s' % (ObjectUUID, TargetMediumID)
        logger.info(event_info)
        
        arch_obj_list = ArchiveObject.objects.filter(ObjectUUID=ObjectUUID)
        if arch_obj_list.exists():
            arch_obj = arch_obj_list[0]
        else:
            event_info = 'Error ArchiveObject not found for ObjectUUID: %s' % ObjectUUID
            logger.error(event_info)
        
        ReqUUID = uuid.uuid1()
        ReqType = u'3'
        ReqPurpose = u'migrate'
        ObjectIdentifierValue = arch_obj.ObjectIdentifierValue
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
                    break
                elif loop_num == 15:
                    event_info = 'Access for object: %s RequUID: %s Status: %s' % (ObjectIdentifierValue, ReqUUID, DbRow.Status)
                    logger.info(event_info)
                    loop_num = 0
            else:
                event_info = 'Access for object: %s with ReqUUID: %s does not exists' % (ObjectIdentifierValue, ReqUUID)
                logger.info(event_info)
            loop_num += 1
            time.sleep(1)
        
        # Prepare write request
        self.ObjectUUID = arch_obj.ObjectUUID
        self.Pmets_objpath = os.path.join(TmpPath,ObjectIdentifierValue + '_Package_METS.xml')
        self.ObjectPath = os.path.join(TmpPath,ObjectIdentifierValue + '.tar')
        if CopyPath:
            self.copy_Pmets_objpath = os.path.join(CopyPath,ObjectIdentifierValue + '_Package_METS.xml')
            self.copy_ObjectPath = os.path.join(CopyPath,ObjectIdentifierValue + '.tar')
        self.MetaObjectSize = os.stat(self.Pmets_objpath)[6]
        self.ObjectSize = int(arch_obj.ObjectSize)
        self.WriteSize = self.ObjectSize + self.MetaObjectSize
        
        try:
            p = arch_obj.PolicyId
        except:
            event_info = 'Error Policy not fond for object: %s' % ObjectIdentifierValue
            logger.error(event_info)
        
        self.sm_num = 0
        self.sm_list = []
        for self.sm in [(p.sm_1,p.sm_type_1,p.sm_format_1,p.sm_blocksize_1,p.sm_maxCapacity_1,p.sm_minChunkSize_1,p.sm_minContainerSize_1,p.sm_target_1),
                        (p.sm_2,p.sm_type_2,p.sm_format_2,p.sm_blocksize_2,p.sm_maxCapacity_2,p.sm_minChunkSize_2,p.sm_minContainerSize_2,p.sm_target_2),
                        (p.sm_3,p.sm_type_3,p.sm_format_3,p.sm_blocksize_3,p.sm_maxCapacity_3,p.sm_minChunkSize_3,p.sm_minContainerSize_3,p.sm_target_3),
                        (p.sm_4,p.sm_type_4,p.sm_format_4,p.sm_blocksize_4,p.sm_maxCapacity_4,p.sm_minChunkSize_4,p.sm_minContainerSize_4,p.sm_target_4)]:
            self.sm_num += 1
            # Check if PolicyID is active (1)
            if self.sm[0] == 1 and self.sm[7] == TargetMediumID:
                self.sm_type = self.sm[1]
                self.sm_format = self.sm[2]
                self.sm_blocksize = self.sm[3]
                self.sm_maxCapacity = self.sm[4]
                self.sm_minChunkSize = self.sm[5]
                self.sm_minContainerSize = self.sm[6]
                self.sm_target = self.sm[7]
                self.sm_location = MediumLocation
                self.sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location]
        
        # Execute write request
        event_info = ('CreateWriteReq:',TmpPath, self.ObjectUUID, ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
        logger.debug(event_info)
        self.ReqUUID,errno,why = ESSPGM.DB().CreateWriteReq(TmpPath, self.ObjectUUID, ObjectIdentifierValue, self.ObjectSize, self.MetaObjectSize,self.sm_list)
        if errno:
            event_info='Problem to Create WriteReq for Object: %s , error: %s, why: %s' % (ObjectIdentifierValue,str(errno),str(why))
            logger.error(event_info)
        event_info='Add WriteReq with storage method type: %s for object: %s , IO_uuid: %s' % (str(self.sm_type),ObjectIdentifierValue,str(self.ReqUUID))
        logger.info(event_info)
        
        # Wait for write request to success
        loop_num = 0
        while 1:
            IOqueue_obj_list = IOqueue.objects.filter(work_uuid=self.ReqUUID) 
            if IOqueue_obj_list.exists():
                DbRow_IOqueue = IOqueue_obj_list[0]
                if DbRow_IOqueue.Status==20:
                    event_info = 'Succedd WriteReq IO_uuid: ' + str(self.ReqUUID) + ' for: ' + str(ObjectIdentifierValue)
                    logger.info(event_info)
                    # Delete request row in database
                    DbRow_IOqueue.delete()
                    # If self.RemoveFlag = 1 then remove self.ObjectPath (self.Pmets_objpath) OR if CopyPath exists move object to CopyPath
                    self.RemoveFlag='1'
                    if self.RemoveFlag == '1' and CopyPath:
                        self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        event_info = 'Try to move ObjectPath: %s to %s and move PackageMets: %s to %s' % (self.ObjectPath, self.copy_ObjectPath, self.Pmets_objpath, self.copy_Pmets_objpath)
                        logger.info(event_info)
                        try:
                            shutil.move(self.ObjectPath,self.copy_ObjectPath)
                            shutil.move(self.Pmets_objpath,self.copy_Pmets_objpath)
                        except (IOError,os.error), why:
                            event_info = 'Problem to move ObjectPath: ' + self.ObjectPath + ' and ' + self.Pmets_objpath
                            logger.error(event_info)
                        else:
                            self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                            self.ProcTime = self.stopTime-self.startTime
                            if self.ProcTime.seconds < 1: self.ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                            self.ProcMBperSEC = int(self.WriteSize)/int(self.ProcTime.seconds)
                            event_info = 'Succeeded to move ObjectPath: ' + self.ObjectPath + ' , ' + str(self.ProcMBperSEC) + ' MB/Sec and Time: ' + str(self.ProcTime)
                            logger.info(event_info)
                            return 0
                    elif self.RemoveFlag == '1':    
                        self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        event_info = 'Try to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.Pmets_objpath
                        logger.info(event_info)
                        try:
                            os.remove(self.ObjectPath)
                            os.remove(self.Pmets_objpath)
                        except (IOError,os.error), why:
                            event_info = 'Problem to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.Pmets_objpath
                            logger.error(event_info)
                        else:
                            self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                            self.ProcTime = self.stopTime-self.startTime
                            if self.ProcTime.seconds < 1: self.ProcTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                            self.ProcMBperSEC = int(self.WriteSize)/int(self.ProcTime.seconds)
                            event_info = 'Succeeded to remove ObjectPath: ' + self.ObjectPath + ' , ' + str(self.ProcMBperSEC) + ' MB/Sec and Time: ' + str(self.ProcTime)
                            logger.info(event_info)
                            return 0
                    break
                elif  DbRow_IOqueue.Status>20:
                    return 1
                elif loop_num == 15:
                    event_info = 'Writerequeast for object: %s RequUID: %s Status: %s' % (ObjectIdentifierValue, self.ReqUUID, DbRow_IOqueue.Status)
                    logger.info(event_info)
                    loop_num = 0
            else:
                event_info = 'Writerequest for object: %s with ReqUUID: %s does not exists' % (ObjectIdentifierValue, self.ReqUUID)
                logger.error(event_info)
            loop_num += 1
            time.sleep(1)
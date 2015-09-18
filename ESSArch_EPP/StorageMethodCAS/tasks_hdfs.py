'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2015  ES Solutions AB

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
import logging, time, os, stat, datetime, shutil, pytz, uuid
from celery import Task, shared_task
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from Storage.models import storage, storageMedium, IOQueue
from configuration.models import ESSConfig
from essarch.libs import GetSize, ESSArchSMError, calcsum
from django.utils import timezone
import hdfs_storage_client

@shared_task()
def add(x, y):
    return x + y

class WriteStorageMethodDisk(Task):
    """
    Write IP with IO_uuid to disk
    
    IOQueue fields:
    storagemethodtarget - Specifies the target of writing
    archiveobject - Specifies the IP to be written
    ObjectPath - Specifies the source path for IP to be written
    ReqType - ReqType shall be set to 15 for writing to disk
    Status - Status shall be set to 0
    
    File "IP" structure in the path ObjectPath:
    "ObjectPath"/"ObjectIdentifierValue".tar
    "ObjectPath"/"ObjectIdentifierValue"_Package_METS.xml
    "ObjectPath"/"aic_uuid"_AIC_METS.xml
    
    Example:
    from StorageMethodDisk.tasks import WriteStorageMethodDisk
    result = WriteStorageMethodDisk().apply_async(('03a33829bad6494e990fe08bfdfb4f6b',), queue='smdisk')
    result.status
    result.result
    """
    tz = timezone.get_default_timezone()

    def run(self, req_pk, *args, **kwargs):
        logger = logging.getLogger('StorageMethodDisk')
        IO_obj = IOQueue.objects.get(pk=req_pk)

        # Let folks know we started
        IO_obj.Status = 5
        IO_obj.save()

        try:
            result = self._WriteDiskProc(req_pk)
        except ESSArchSMError as e:
            IO_obj.refresh_from_db()
            msg = 'Problem to write object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            IO_obj.Status = 100
            IO_obj.save()
            raise self.retry(exc=e, countdown=10, max_retries=2)
        except Exception as e:
            IO_obj.refresh_from_db()
            msg = 'Unknown error to write object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            IO_obj.Status = 100
            IO_obj.save()
            raise e
        else:
            IO_obj.refresh_from_db()
            MBperSEC = int(result.get('WriteSize'))/int(result.get('WriteTime').seconds)
            msg = 'Success to write IOuuid: %s for object %s to disk, WriteSize: %s, WriteTime: %s (%s MB/Sec)' % (IO_obj.id, 
                                                                                                                                                                       result.get('ObjectIdentifierValue'), 
                                                                                                                                                                       result.get('WriteSize'), 
                                                                                                                                                                       result.get('WriteTime'), 
                                                                                                                                                                       MBperSEC,
                                                                                                                                                                       )
            logger.info(msg)            
            IO_obj.Status = 20
            IO_obj.save()
            return result

    #def on_failure(self, exc, task_id, args, kwargs, einfo):
    #    logger = logging.getLogger('StorageMethodDisk')
    #    logger.exception("Something happened when trying"
    #                     " to resolve %s" % args[0])

    def _WriteDiskProc(self,IO_obj_uuid):
        """
        This function writes IP (Information Package) to a disk filepath
        """
        logger = logging.getLogger('StorageMethodDisk')
        runflag = 1
        contentLocationValue = ''
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        error_list = []
        IO_obj = IOQueue.objects.get(id=IO_obj_uuid)
        st_obj = IO_obj.storagemethodtarget
        target_obj = st_obj.target
        target_obj_target = target_obj.target
        sm_obj = st_obj.storagemethod
        ArchiveObject_obj = IO_obj.archiveobject
        ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
        source_path = IO_obj.ObjectPath
        WriteSize = IO_obj.WriteSize
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        MediumLocation = ESSConfig.objects.get(Name='storageMediumLocation').Value

        logger.info('Start Disk Write Process for object: %s, target: %s, IOuuid: %s', ObjectIdentifierValue,target_obj_target,IO_obj_uuid)

        ########################################################
        # Check access to ip_tar_path and verify WriteSize
        ########################################################
        
        aic_obj_uuid = ''
        aic_mets_path_source = ''
        aic_mets_size = 0
        # If storage method format is AIC type (103)
        if target_obj.format == 103:
            try:
                aic_obj_uuid=ArchiveObject_obj.reluuid_set.get().AIC_UUID
            except ObjectDoesNotExist as e:
                logger.warning('Problem to get AIC info for ObjectUUID: %s, error: %s' % (ObjectIdentifierValue, e))
            else:
                logger.info('Succeeded to get AIC_UUID: %s from DB' % aic_obj_uuid)
            
            # Check aic_mets_path_source
            aic_mets_path_source = os.path.join(source_path,'%s_AIC_METS.xml' % aic_obj_uuid)
            try:
                aic_mets_size = GetSize(aic_mets_path_source)
            except OSError as oe:
                msg = 'Problem to access AIC METS object: %s, IOuuid: %s, error: %s' % (aic_mets_path_source, IO_obj_uuid, oe)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0

        # Check ip_tar_path_source
        ip_tar_filename = '%s.tar' % ArchiveObject_obj.ObjectIdentifierValue
        ip_tar_path_source = os.path.join(source_path, ip_tar_filename)
        try:
            ip_tar_size = GetSize(ip_tar_path_source)
        except OSError as oe:
            msg = 'Problem to access object: %s, IOuuid: %s, error: %s' % (ip_tar_path_source, IO_obj_uuid, oe)
            logger.error(msg)
            error_list.append(msg)            
            runflag = 0
            ip_tar_size = 0

        # Check ip_p_mets_path_source
        ip_p_mets_path_source = ip_tar_path_source[:-4] + '_Package_METS.xml'
        try:
            ip_p_mets_size = GetSize(ip_p_mets_path_source)
        except OSError as oe:
            msg = 'Problem to access metaobject: %s, IOuuid: %s, error: %s' % (ip_p_mets_path_source, IO_obj_uuid, oe)
            logger.error(msg)
            error_list.append(msg)
            runflag = 0
            ip_p_mets_size = 0

        # Check WriteSize
        if WriteSize:
            if not int(WriteSize) == int(ip_tar_size) + int(ip_p_mets_size) + int(aic_mets_size):
                msg = 'Problem defined WriteSize does not match actual filesizes for object: ' + ip_tar_path_source + ', IOuuid: ' + str(IO_obj_uuid)
                logger.error(msg)
                error_list.append(msg)
                msg = 'WriteSize: ' + str(WriteSize)
                logger.error(msg)
                error_list.append(msg)
                msg = 'ip_tar_size: ' + str(ip_tar_size)
                logger.error(msg)
                error_list.append(msg)
                msg = 'ip_p_mets_size: ' + str(ip_p_mets_size)
                logger.error(msg)
                error_list.append(msg)
                if aic_mets_path_source:
                    msg = 'aic_mets_size: ' + str(aic_mets_size)
                    logger.error(msg)
                    error_list.append(msg)
                runflag = 0
        else:
            WriteSize = int(ip_tar_size) + int(ip_p_mets_size)
            if aic_mets_path_source:
                WriteSize += int(aic_mets_size)
            logger.info('WriteSize not defined, setting write size for object: ' + ObjectIdentifierValue + ' WriteSize: ' + str(WriteSize))

        # Check if StorageMediumID 'disk' exist, if exist get current target size.
        try:
            storageMedium_obj = storageMedium.objects.get(storageMediumID=target_obj.name)
        except storageMedium.DoesNotExist as e:
            logger.warning('storageMediumID %s not found for IOuuid: %s, try to and new storageMedium' % (target_obj.name, IO_obj_uuid))
            timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            MediumUUID = uuid.uuid4()
            storageMedium_obj = storageMedium()
            storageMedium_obj.id = MediumUUID
            storageMedium_obj.storageMediumUUID=unicode(MediumUUID)
            storageMedium_obj.storageMedium=target_obj.type
            storageMedium_obj.storageMediumID=target_obj.name
            storageMedium_obj.storageMediumDate=timestamp_utc
            storageMedium_obj.storageMediumLocation=MediumLocation
            storageMedium_obj.storageMediumLocationStatus=50
            storageMedium_obj.storageMediumBlockSize=128
            storageMedium_obj.storageMediumStatus=20
            storageMedium_obj.storageMediumUsedCapacity=0
            storageMedium_obj.storageMediumFormat=target_obj.format
            storageMedium_obj.storageMediumMounts=0
            storageMedium_obj.linkingAgentIdentifierValue=AgentIdentifierValue
            storageMedium_obj.CreateDate=timestamp_utc
            storageMedium_obj.CreateAgentIdentifierValue=AgentIdentifierValue
            storageMedium_obj.LocalDBdatetime=timestamp_utc
            storageMedium_obj.storagetarget=target_obj
            storageMedium_obj.save()
        
        #new_storageMediumUsedCapacity = storageMedium_obj.storageMediumUsedCapacity + int(WriteSize)     

        # Check write access to target directory
        if not os.access(target_obj_target, 7): 
            logger.error('Problem to access target directory: ' + target_obj_target + ', IOuuid: ' + str(IO_obj_uuid))
            runflag = 0
            
        startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        if runflag:
            ########################################################
            # Write AIP package to disk
            ########################################################
            try:
                logger.info('Try to write %s to storage method disk target: %s, IOuuid: %s', ObjectIdentifierValue, target_obj_target, IO_obj_uuid)
                target_obj.target = hdfs_storage_client.copy_to_hdfs(ip_tar_path_source)
                #shutil.copy2(ip_p_mets_path_source,target_obj_target)
                #if aic_mets_path_source is not None:
                #    shutil.copy2(aic_mets_path_source,target_obj_target)
                contentLocationValue = target_obj.name
            except (IOError, OSError) as e:
                msg = 'Problem to write %s to storage method disk target: %s, IOuuid: %s, error: %s' % (ObjectIdentifierValue, target_obj_target, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            else:
                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                #timestamp_dst = timestamp_utc.astimezone(self.tz)
                ##########################
                # Insert StorageTable
                storage_obj = storage()
                storage_obj.contentLocationType = sm_obj.type #200
                storage_obj.contentLocationValue = contentLocationValue
                storage_obj.LocalDBdatetime = timestamp_utc
                storage_obj.archiveobject = ArchiveObject_obj
                storage_obj.storagemedium = storageMedium_obj
                storage_obj.ObjectUUID = ArchiveObject_obj
                storage_obj.save()
        else:
            msg = 'Because of the previous problems it is not possible to store the object %s to storage method target: %s, IOuuid: %s' % (ObjectIdentifierValue, target_obj_target, IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
        
        stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        WriteTime = stopTime-startTime
        if WriteTime.seconds < 1: WriteTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.

        res_dict = {
                    'ObjectIdentifierValue': ArchiveObject_obj.ObjectIdentifierValue,
                    'ObjectUUID': ArchiveObject_obj.ObjectUUID,
                    'sm_obj_uuid': sm_obj.id,
                    'contentLocationValue': contentLocationValue,
                    'storageMediumID': storageMedium_obj.storageMediumID,
                    'storageMediumUUID': storageMedium_obj.storageMediumUUID,
                    'AgentIdentifierValue': AgentIdentifierValue,
                    'WriteSize': WriteSize,
                    'WriteTime': WriteTime,
                    'timestamp_utc': timestamp_utc,
                    'error_list': error_list,        
                    'status': runflag,
                    }
        
        IO_obj.result = res_dict
        IO_obj.save()

        if not runflag:
            raise ESSArchSMError(error_list)
        else:
            return res_dict   

class ReadStorageMethodDisk(Task):
    """
    Read IP with IO_uuid from disk
    
    IOQueue fields:
    archiveobject - Specifies the IP to be read
    storage - Specifies the source of the IP to be read
    ObjectPath - Specifies path where the IP should be written
    ReqType - ReqType shall be set to 25 for read from disk
    Status - Status shall be set to 0    
    
    Example:
    from StorageMethodDisk.tasks import ReadStorageMethodDisk
    result = ReadStorageMethodDisk().apply_async(('0de502d5-b7aa-493a-8df6-547768a9aac6',), queue='smdisk')
    result.status
    result.result
    """
    tz = timezone.get_default_timezone()

    def run(self, req_pk, *args, **kwargs):
        logger = logging.getLogger('StorageMethodDisk')
        IO_obj = IOQueue.objects.get(pk=req_pk)

        # Let folks know we started
        IO_obj.Status = 5
        IO_obj.save()

        try:
            result = self._ReadDiskProc(req_pk)
        except ESSArchSMError as e:
            IO_obj.refresh_from_db()
            msg = 'Problem to read object %s from disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            IO_obj.Status = 100
            IO_obj.save()
            raise self.retry(exc=e, countdown=10, max_retries=2)
        except Exception as e:
            IO_obj.refresh_from_db()
            msg = 'Unknown error to read object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            IO_obj.Status = 100
            IO_obj.save()
            raise e
        else:
            IO_obj.refresh_from_db()
            MBperSEC = int(result.get('ReadSize'))/int(result.get('ReadTime').seconds)
            msg = 'Success to read IOuuid: %s for object %s from disk, ReadSize: %s, ReadTime: %s (%s MB/Sec)' % (IO_obj.id, 
                                                                                                                                                                       result.get('ObjectIdentifierValue'), 
                                                                                                                                                                       result.get('ReadSize'), 
                                                                                                                                                                       result.get('ReadTime'), 
                                                                                                                                                                       MBperSEC,
                                                                                                                                                                       )
            logger.info(msg)            
            IO_obj.Status = 20
            IO_obj.save()
            return result

    "Read IOuuid from disk"
    ###############################################
    def _ReadDiskProc(self,IO_obj_uuid):
        logger = logging.getLogger('StorageMethodDisk')
        runflag = 1
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        error_list = []
        IO_obj = IOQueue.objects.get(id=IO_obj_uuid)
        ArchiveObject_obj = IO_obj.archiveobject
        ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
        target_path = IO_obj.ObjectPath
        ip_tar_filename = ArchiveObject_obj.ObjectPackageName
        ArchiveObject_obj_ObjectMessageDigest = ArchiveObject_obj.ObjectMessageDigest
        ArchiveObject_obj_ObjectMessageDigestAlgorithm = ArchiveObject_obj.ObjectMessageDigestAlgorithm
        storage_obj = IO_obj.storage
        storageMedium_obj = storage_obj.storagemedium
        target_obj = storageMedium_obj.storagetarget
        contentLocationValue = target_obj.target
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value

        logger.debug('ReadDiskProc start with IOuuid: %s, Object: %s, ObjectPath: %s', IO_obj_uuid, ObjectIdentifierValue, target_path)
        logger.info('Start Disk Read Process for object: %s, IOuuid: %s', ObjectIdentifierValue,IO_obj_uuid)
        
        ip_p_mets_filename = ip_tar_filename[:-4] + '_Package_METS.xml'
        aic_obj_uuid = ''
        aic_mets_filename = ''
        # If storage method format is AIC type (103)
        if target_obj.format == 103:
            try:
                aic_obj_uuid=ArchiveObject_obj.reluuid_set.get().AIC_UUID
            except ObjectDoesNotExist as e:
                msg = 'Problem to get AIC info for ObjectUUID: %s, error: %s' % (ObjectIdentifierValue, e)
                logger.warning(msg)
                error_list.append(msg)
            else:
                logger.info('Succeeded to get AIC_UUID: %s from DB' % aic_obj_uuid)
                aic_mets_filename = '%s_AIC_METS.xml' % aic_obj_uuid

        startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        tmp_target_path = os.path.join(target_path,'.tmpextract')
        # Check write access to DIP directory
        if not os.access(target_path, 7):
            #ESSDB.DB().action('IOqueue','UPD',('Status','114'),('work_uuid',IO_obj_uuid))
            msg = 'Problem to access DIP directory: %s, IOuuid: %s' % (target_path, IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
            #ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'1',msg,2,ObjectIdentifierValue)
            runflag = 0
        # Check if temp DIP directory exist, if not create tempDIR
        if runflag and not os.path.exists(tmp_target_path):
            os.mkdir(tmp_target_path)
        if runflag:
            ########################################################
            # Get AIP package to DIP directory
            ########################################################
            try:
                logger.info('Try to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s', ObjectIdentifierValue, contentLocationValue, tmp_target_path,  IO_obj_uuid)
                ip_tar_path_source = os.path.join(contentLocationValue, ip_tar_filename)
                ip_tar_path_tmp_target = os.path.join(tmp_target_path, ip_tar_filename)
                hdfs_storage_client.copy_from_hdfs(contentLocationValue, tmp_target_path)
                #ip_p_mets_path_source = os.path.join(contentLocationValue,ip_p_mets_filename)
                #ip_p_mets_path_tmp_target = os.path.join(tmp_target_path,ip_p_mets_filename)                
                #shutil.copy2(ip_p_mets_path_source, ip_p_mets_path_tmp_target)
                #if target_obj.format == 103:
                #    aic_mets_path_source = os.path.join(contentLocationValue, aic_mets_filename)
                #    aic_mets_path_tmp_target = os.path.join(tmp_target_path, aic_mets_filename)
                #    shutil.copy2(aic_mets_path_source, aic_mets_path_tmp_target)
            except (IOError, OSError) as e:
                #ESSDB.DB().action('IOqueue','UPD',('Status','115'),('work_uuid',IO_obj_uuid))
                msg = 'Problem to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s, Error: %s' % (ObjectIdentifierValue, contentLocationValue, tmp_target_path, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                #ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'1',msg,2,ObjectIdentifierValue)
                runflag = 0
            else:
                msg = 'Success to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s' % (ObjectIdentifierValue, contentLocationValue, tmp_target_path,  IO_obj_uuid)
                logger.info(msg)
                #ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'0',msg,2,ObjectIdentifierValue)
        if runflag:
            #############################################
            # Checksum Check
            #############################################
            try:
                tp_sum = calcsum(ip_tar_path_tmp_target, ArchiveObject_obj_ObjectMessageDigestAlgorithm)
            except IOError as e:
                #ESSDB.DB().action('IOqueue','UPD',('Status','116'),('work_uuid',IO_obj_uuid))
                msg = 'Failed to get checksum for: %s, Error: %s' % (ip_tar_path_tmp_target,e)
                logger.error(msg)
                error_list.append(msg)
                #ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'1',msg,2,ObjectIdentifierValue)
                runflag = 0
            else:
                msg = 'Success to get checksum for: %s, Checksum: %s' % (ip_tar_path_tmp_target,tp_sum)
                logger.info(msg)
                #ESSPGM.Events().create('1041','','IOEngine',ProcVersion,'0',msg,2,ObjectIdentifierValue)
        if runflag:
            if str(tp_sum) == str(ArchiveObject_obj_ObjectMessageDigest):
                msg = 'Success to verify checksum for Object %s in tmpDIP: %s, IOuuid: %s' % (ObjectIdentifierValue, tmp_target_path, IO_obj_uuid)
                logger.info(msg)
                #ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'0',msg,2,ObjectIdentifierValue)
            else:
                msg = 'Checksum verify mismatch for Object %s in tmpDIP: %s, IOuuid: %s, tape_checksum: %s, meta_checksum: %s' % (ObjectIdentifierValue, tmp_target_path, IO_obj_uuid, tp_sum, ArchiveObject_obj_ObjectMessageDigest)
                logger.error(msg)
                error_list.append(msg)
                #ESSPGM.Events().create('1042','','IOEngine',ProcVersion,'1',msg,2,ObjectIdentifierValue)
                runflag = 0
        if runflag:
            #############################
            # Move files to req path
            #############################
            try:
                ip_tar_path_target = os.path.join(target_path, ip_tar_filename)
                ip_p_mets_path_target = os.path.join(target_path, ip_p_mets_filename)
                shutil.move(ip_tar_path_tmp_target, ip_tar_path_target)
                #shutil.move(ip_p_mets_path_tmp_target, ip_p_mets_path_target)
                #if target_obj.format == 103:
                #    aic_mets_path_target = os.path.join(target_path, aic_mets_filename)
                #    shutil.move(aic_mets_path_tmp_target, aic_mets_path_target)
            except (IOError, OSError) as e:
                #ESSDB.DB().action('IOqueue','UPD',('Status','115'),('work_uuid',IO_obj_uuid))
                msg = 'Problem to move Object %s from tmpdir: %s to target path: %s, IOuuid: %s, Error: %s' % (ObjectIdentifierValue, tmp_target_path, target_path, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                #ESSPGM.Events().create('1103','','IOEngine',ProcVersion,'1',msg,2,ObjectIdentifierValue)
                runflag = 0            
        
        ReadSize = 0
        if runflag:                
            aic_mets_size = 0
            if target_obj.format == 103:
                # Check aic_mets_path
                try:
                    aic_mets_size = GetSize(aic_mets_path_target)
                except OSError as oe:
                    msg = 'Problem to access AIC METS object: %s, IOuuid: %s, error: %s' % (aic_mets_path_target, IO_obj_uuid, oe)
                    logger.error(msg)
                    error_list.append(msg)
                    runflag = 0

            # Check ip_tar_path
            try:
                ip_tar_size = GetSize(ip_tar_path_target)
            except OSError as oe:
                msg = 'Problem to access object: %s, IOuuid: %s, error: %s' % (ip_tar_path_target, IO_obj_uuid, oe)
                logger.error(msg)
                error_list.append(msg)            
                runflag = 0
                ip_tar_size = 0
    
            # Check ip_p_mets_path
            try:
                ip_p_mets_size = GetSize(ip_p_mets_path_target)
            except OSError as oe:
                msg = 'Problem to access metaobject: %s, IOuuid: %s, error: %s' % (ip_p_mets_path_target, IO_obj_uuid, oe)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
                ip_p_mets_size = 0

            ReadSize = int(ip_tar_size) + int(ip_p_mets_size)
            if target_obj.format == 103:
                ReadSize += int(aic_mets_size)

        stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        ReadTime = stopTime-startTime
        if ReadTime.seconds < 1: ReadTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.

        res_dict = {
                    'ObjectIdentifierValue': ArchiveObject_obj.ObjectIdentifierValue,
                    'ObjectUUID': ArchiveObject_obj.ObjectUUID,
                    'target_path': target_path,
                    'contentLocationValue': contentLocationValue,
                    'storageMediumID': storageMedium_obj.storageMediumID,
                    'storageMediumUUID': storageMedium_obj.storageMediumUUID,
                    'AgentIdentifierValue': AgentIdentifierValue,
                    'ReadSize': ReadSize,
                    'ReadTime': ReadTime,
                    'timestamp_utc': timestamp_utc,
                    'error_list': error_list,        
                    'status': runflag,
                    }
        
        IO_obj.result = res_dict
        IO_obj.save()

        if not runflag:
            raise ESSArchSMError(error_list)
        else:
            return res_dict   

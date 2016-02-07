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

import logging, time, os, stat, datetime, shutil, pytz, uuid, ESSMSSQL, ESSPGM, sys, traceback
from celery import Task, shared_task
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db import IntegrityError
from Storage.models import storage, storageMedium, IOQueue
from Storage.tasks import TransferReadIO
from configuration.models import ESSConfig
from essarch.libs import GetSize, ESSArchSMError, calcsum
from django.utils import timezone
import requests
from rest_framework.renderers import JSONRenderer
from urlparse import urljoin
from api.serializers import IOQueueNestedReadSerializer, IOQueueSerializer
from retrying import retry

# Disable https insecure warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

@shared_task()
def add(x, y):
    return x + y

class apply_result(object):
    def __init__(self, task_id):
        """
        Initialize apply_sync result
        """
        self.task_id = task_id

class DatabasePostRestException(Exception):
    """
    There was an ambiguous exception that occurred while handling your
    request.
    """
    def __init__(self, value):
        """
        Initialize DatabasePostRestException
        """
        self.value = value
        super(DatabasePostRestException, self).__init__(value)

class DatabasePostRestError(DatabasePostRestException):
    """An post request error occurred."""

class ApplyPostRestException(Exception):
    """
    There was an ambiguous exception that occurred while handling your
    request.
    """
    def __init__(self, value):
        """
        Initialize ApplyPostRestException
        """
        self.value = value
        super(ApplyPostRestException, self).__init__(value)

class ApplyPostRestError(ApplyPostRestException):
    """An post request error occurred."""

class WriteStorageMethodDisk(Task):
    """Write IP with IO_uuid to disk
    
    Requires the following fields in IOQueue database table:
    storagemethodtarget - Specifies the target of writing
    archiveobject - Specifies the IP to be written
    ObjectPath - Specifies the source path for IP to be written
    ReqType - ReqType shall be set to 15 for writing to disk
    Status - Status shall be set to 0
    
    File "IP" structure in the path ObjectPath:
    "ObjectPath"/"ObjectIdentifierValue".tar
    "ObjectPath"/"ObjectIdentifierValue"_Package_METS.xml
    "ObjectPath"/"aic_uuid"_AIC_METS.xml
    
    :param req_pk: Primary key to IOQueue database table to be performed
    
    Example:
    from StorageMethodDisk.tasks import WriteStorageMethodDisk
    result = WriteStorageMethodDisk().apply_async(('03a33829bad6494e990fe08bfdfb4f6b',), queue='smdisk')
    result.status
    result.result
    
    """
    tz = timezone.get_default_timezone()
    time_limit = 86400
    logger = logging.getLogger('StorageMethodDisk')

    def run(self, req_pk, *args, **kwargs):
        """The body of the task executed by workers."""
        logger = self.logger
        IO_obj = IOQueue.objects.get(pk=req_pk)

        # Let folks know we started
        IO_obj.Status = 5
        IO_obj.save(update_fields=['Status'])

        try:
            target_obj = IO_obj.storagemethodtarget.target
            master_server = target_obj.master_server.split(',')
            if len(master_server) == 3:
                remote_io = True
            else:         
                remote_io = False
            result = self._WriteDiskProc(req_pk)
        except ESSArchSMError as e:
            IO_obj.refresh_from_db()
            msg = 'Problem to write object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            ESSPGM.Events().create('1102','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.Status = 100
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            #raise self.retry(exc=e, countdown=10, max_retries=2)
            raise e
        except Exception as e:
            IO_obj.refresh_from_db()
            msg = 'Unknown error to write object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            ESSPGM.Events().create('1102','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.Status = 100
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            raise e
        else:
            IO_obj.refresh_from_db()
            ObjectSizeMB = int(result.get('WriteSize'))/1048576
            MBperSEC = ObjectSizeMB/int(result.get('WriteTime').seconds)
            msg = 'Success to write IOuuid: %s for object %s to %s, WriteSize: %s, WriteTime: %s (%s MB/Sec)' % (IO_obj.id, 
                                                                                                                                                                       result.get('ObjectIdentifierValue'),
                                                                                                                                                                       result.get('storageMediumID'),
                                                                                                                                                                       result.get('WriteSize'), 
                                                                                                                                                                       result.get('WriteTime'), 
                                                                                                                                                                       MBperSEC,
                                                                                                                                                                       )
            logger.info(msg)
            ESSPGM.Events().create('1102','',self.__name__,__version__,'0',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)       
            IO_obj.Status = 20
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)        
            return result

    #def on_failure(self, exc, task_id, args, kwargs, einfo):
    #    logger = logging.getLogger('StorageMethodDisk')
    #    logger.exception("Something happened when trying"
    #                     " to resolve %s" % args[0])

    @retry(stop_max_attempt_number=5, wait_fixed=60000)    
    def _update_master_ioqueue(self, master_server, IO_obj):
        """ Call REST service on master to update IOQueue with nested storage, storageMedium
        
        :param master_server: example: [https://servername:port, user, password]
        :param IO_obj: IOQueue database instance to be performed
        
        """
        logger = self.logger
        base_url, ruser, rpass = master_server
        IOQueue_rest_endpoint_base = urljoin(base_url, '/api/ioqueuenested/')
        IOQueue_rest_endpoint = urljoin(IOQueue_rest_endpoint_base, '%s/' % str(IO_obj.id))
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        IO_obj_data = IOQueueNestedReadSerializer(IO_obj).data
        IO_obj_json = JSONRenderer().render(IO_obj_data)
        try:
            r = requests_session.patch(IOQueue_rest_endpoint,
                                        headers={'Content-Type': 'application/json'}, 
                                        data=IO_obj_json)
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to master server and update IOQueue for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              IO_obj.archiveobject.ObjectIdentifierValue,
                                                                                                                                              e,
                                                                                                                                              IO_obj.id)
            logger.warning(msg)
            raise DatabasePostRestError(e)
        if not r.status_code == 200:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to update master server IOQueue, storage, storageMedium for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              IO_obj.archiveobject.ObjectIdentifierValue,
                                                                                                                                              e,
                                                                                                                                              IO_obj.id)
            logger.warning(msg)
            raise DatabasePostRestError(e)

    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def remote_write_disk_apply_async(self, remote_server, IOQueue_obj_id, ArchiveObject_obj_ObjectUUID, queue='smdisk'):
        """Remote REST call to appy_async
        
        :param remote_server: example: [https://servername:port/api/write_storage_method_tape_apply, user, password]
        :param IOQueue_obj_id: Primary key to IOQueue database table to be performed, ex 'id1'
        :param ArchiveObject_obj_ObjectUUID: ObjectUUID key to ArchiveObject database table to be performed, ex 'id1'
        :param queue: celery queue name, ex 'smdisk'
        
        """
        logger = logging.getLogger('Storage')
        base_url, ruser, rpass = remote_server
        write_disk_rest_endpoint = urljoin(base_url, '/api/write_storage_method_disk_apply/')
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        data = {'queue': queue, 
                'IOQueue_obj_id': IOQueue_obj_id, 
                'ArchiveObject_obj_ObjectUUID': ArchiveObject_obj_ObjectUUID}
        try:
            r = requests_session.post(write_disk_rest_endpoint,
                                  headers={'Content-Type': 'application/json'},
                                  data=JSONRenderer().render(data))
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to remote server and apply write task for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_obj_ObjectUUID,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        if not r.status_code == 201:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to apply write task to remote server for ObjectUUID: %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_obj_ObjectUUID,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        return apply_result(r.json()['task_id'])

    def _WriteDiskProc(self,IO_obj_uuid):
        """Writes IP (Information Package) to a disk filepath
        
        :param IO_obj_uuid: Primary key to entry in IOQueue database table
        
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
        ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)
        storage_obj = None
        storageMedium_obj = None

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
                if target_obj.format == 103:
                    msg = 'aic_mets_size: ' + str(aic_mets_size)
                    logger.error(msg)
                    error_list.append(msg)
                runflag = 0
        else:
            WriteSize = int(ip_tar_size) + int(ip_p_mets_size)
            if target_obj.format == 103:
                WriteSize += int(aic_mets_size)
            logger.info('WriteSize not defined, setting write size for object: ' + ObjectIdentifierValue + ' WriteSize: ' + str(WriteSize))

        # Check if StorageMediumID 'disk' exist, if exist get current target size.
        try:
            storageMedium_obj = storageMedium.objects.get(storageMediumID=target_obj.name)
        except storageMedium.DoesNotExist as e:
            try:
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
            except IntegrityError as e:
                if e.args[0] == 1062: # 1062 = Duplicate entry, try to get object instead
                    storageMedium_obj = storageMedium.objects.get(storageMediumID=target_obj.name)
                else:
                    raise e
        
        IO_obj.storagemedium =  storageMedium_obj
        
        #new_storageMediumUsedCapacity = storageMedium_obj.storageMediumUsedCapacity + int(WriteSize)     

        # Check write access to target directory
        if not os.access(target_obj_target, 7):
            msg = 'Problem to access target directory: %s (IOuuid: %s)' % (target_obj_target, IO_obj_uuid)
            error_list.append(msg)    
            logger.error(msg)
            runflag = 0
            
        startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        if runflag:
            ########################################################
            # Write AIP package to disk
            ########################################################
            try:
                logger.info('Try to write %s to storage method disk target: %s, IOuuid: %s', ObjectIdentifierValue, target_obj_target, IO_obj_uuid)
                shutil.copy2(ip_tar_path_source,target_obj_target)
                shutil.copy2(ip_p_mets_path_source,target_obj_target)
                if target_obj.format == 103:
                    shutil.copy2(aic_mets_path_source,target_obj_target)
                contentLocationValue = target_obj.name
            except (IOError, OSError) as e:
                msg = 'Problem to write %s to storage method disk target: %s, IOuuid: %s, error: %s' % (ObjectIdentifierValue, target_obj_target, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            else:
                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                ##########################
                # Insert StorageTable
                storage_obj = storage()
                storage_obj.contentLocationType = sm_obj.type #200
                storage_obj.contentLocationValue = contentLocationValue
                storage_obj.LocalDBdatetime = timestamp_utc
                storage_obj.archiveobject = ArchiveObject_obj
                storage_obj.storagemedium = storageMedium_obj
                storage_obj.save()
                IO_obj.storage =  storage_obj
                if ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storage', 'INS', ('ObjectIdentifierValue',storage_obj.archiveobject.ObjectIdentifierValue,
                                                                                              'contentLocationType',storage_obj.contentLocationType,
                                                                                              'contentLocationValue',storage_obj.contentLocationValue,
                                                                                              'storageMediumID',storage_obj.storagemedium.storageMediumID))
                    if ext_errno: logger.error('Failed to insert to External DB: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                    else:
                        storage_obj.ExtDBdatetime = timestamp_utc
                        storage_obj.save(update_fields=['ExtDBdatetime'])                
                
        if not runflag:
            msg = 'Because of the previous problems it is not possible to store the object %s to storage method target: %s, IOuuid: %s' % (ObjectIdentifierValue, target_obj_target, IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
        
        stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        WriteTime = stopTime-startTime
        if WriteTime.seconds < 1: WriteTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
        
        if storage_obj is not None:
            storage_obj_id = storage_obj.id
        else:
            storage_obj_id = ''

        if storageMedium_obj is not None:
            storageMedium_obj_storageMediumID = storageMedium_obj.storageMediumID
            storageMedium_obj_storageMediumUUID = storageMedium_obj.storageMediumUUID
        else:
            storageMedium_obj_storageMediumID = ''
            storageMedium_obj_storageMediumUUID = ''

        res_dict = {
                    'ObjectIdentifierValue': ArchiveObject_obj.ObjectIdentifierValue,
                    'ObjectUUID': ArchiveObject_obj.ObjectUUID,
                    'sm_obj_id': sm_obj.id,
                    'storage_obj_id': storage_obj_id,
                    'contentLocationValue': contentLocationValue,
                    'storageMediumID': storageMedium_obj_storageMediumID,
                    'storageMediumUUID': storageMedium_obj_storageMediumUUID,
                    'AgentIdentifierValue': AgentIdentifierValue,
                    'WriteSize': WriteSize,
                    'WriteTime': WriteTime,
                    'timestamp_utc': timestamp_utc,
                    'error_list': error_list,        
                    'status': runflag,
                    }
        
        IO_obj.result = res_dict
        IO_obj.save(update_fields=['result', 'storagemedium', 'storage'])

        if not runflag:
            raise ESSArchSMError(error_list)
        else:
            return res_dict   

class ReadStorageMethodDisk(Task):
    """Read IP with IO_uuid from disk
    
    Requires the following fields in IOQueue database table:
    archiveobject - Specifies the IP to be read
    storage - Specifies the source of the IP to be read
    ObjectPath - Specifies path where the IP should be written
    ReqType - ReqType shall be set to 25 for read from disk
    Status - Status shall be set to 0    
    
    :param req_pk: List of primary keys to IOQueue database table to be performed
    
    Example:
    from StorageMethodDisk.tasks import ReadStorageMethodDisk
    result = ReadStorageMethodDisk().apply_async(('0de502d5-b7aa-493a-8df6-547768a9aac6',), queue='smdisk')
    result.status
    result.result
    
    """
    tz = timezone.get_default_timezone()
    time_limit = 86400
    logger = logging.getLogger('StorageMethodDisk')

    def run(self, req_pk, *args, **kwargs):
        """The body of the task executed by workers."""
        logger = self.logger
        IO_obj = IOQueue.objects.get(pk=req_pk)

        # Let folks know we started
        IO_obj.Status = 5
        IO_obj.save(update_fields=['Status'])

        try:
            target_obj = IO_obj.storage.storagemedium.storagetarget
            master_server = target_obj.master_server.split(',')
            if len(master_server) == 3:
                remote_io = True
            else:         
                remote_io = False
            
            # Read disk
            result = self._ReadDiskProc(req_pk)
            IO_obj.refresh_from_db()
            ObjectSizeMB = int(result.get('ReadSize'))/1048576
            MBperSEC = ObjectSizeMB/int(result.get('ReadTime').seconds)
            msg = 'Success to read IOuuid: %s for object %s from %s, ReadSize: %s, ReadTime: %s (%s MB/Sec)' % (IO_obj.id, 
                                                                                                                                                                       result.get('ObjectIdentifierValue'),
                                                                                                                                                                       result.get('storageMediumID'),
                                                                                                                                                                       result.get('ReadSize'), 
                                                                                                                                                                       result.get('ReadTime'), 
                                                                                                                                                                       MBperSEC,
                                                                                                                                                                       )
            logger.info(msg)
            ESSPGM.Events().create('1103','',self.__name__,__version__,'0',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)     

            if remote_io:
                # Transfer to master
                result = TransferReadIO().apply_async((IO_obj.id,), queue='default')
                self.logger.info('Apply new transfer readIO process for IOQueue_obj: %s with transfer_task: %s' % (
                                                                                                                    IO_obj.id, 
                                                                                                                    result.task_id))
                IO_obj.refresh_from_db()
                IO_obj.transfer_task_id = result.task_id
                IO_obj.save(update_fields=['transfer_task_id'])
                self._update_master_ioqueue(master_server, IO_obj)
                result.wait(timeout=86400)
                self.logger.info('Success to transfer readIO process for IOQueue_obj: %s with transfer_task: %s' % (
                                                                                                                    IO_obj.id, 
                                                                                                                    result.task_id))
                # Move files to accesspath on master
                filename_list = result.result['filename_list']
                move_task_result = self._move_to_accesspath(master_server, filename_list, IO_obj.id)
                self.logger.info('Start to move files to accesspath on master server IOuuid: %s with task_id: %s' % (
                                                                                                                    IO_obj.id, 
                                                                                                                    move_task_result.task_id))    
                self._wait_for_move_to_accesspath(master_server, move_task_result.task_id)
        except ESSArchSMError as e:
            IO_obj.refresh_from_db()
            msg = 'Problem to read object %s from disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            ESSPGM.Events().create('1103','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.Status = 100
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            #raise self.retry(exc=e, countdown=10, max_retries=2)
            raise e
        except Exception as e:
            IO_obj.refresh_from_db()
            msg = 'Unknown error to read object %s to disk, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            ESSPGM.Events().create('1103','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.Status = 100
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            raise e
        else:
            IO_obj.refresh_from_db()
            IO_obj.Status = 20
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            return result
    
    @retry(stop_max_attempt_number=5, wait_fixed=60000)    
    def _update_master_ioqueue(self, master_server, IO_obj):
        """ Call REST service on master to update IOQueue
        
        :param master_server: example: [https://servername:port, user, password]
        :param IO_obj: IOQueue database instance to be performed
        
        """
        logger = self.logger
        base_url, ruser, rpass = master_server
        IOQueue_rest_endpoint_base = urljoin(base_url, '/api/ioqueue/')
        IOQueue_rest_endpoint = urljoin(IOQueue_rest_endpoint_base, '%s/' % str(IO_obj.id))
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        IO_obj_data = IOQueueSerializer(IO_obj).data
        del IO_obj_data['accessqueue']
        del IO_obj_data['task_id']
        IO_obj_json = JSONRenderer().render(IO_obj_data)
        try:
            r = requests_session.patch(IOQueue_rest_endpoint,
                                        headers={'Content-Type': 'application/json'}, 
                                        data=IO_obj_json)

        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to master server and update IOQueue for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              IO_obj.archiveobject.ObjectIdentifierValue,
                                                                                                                                              e,
                                                                                                                                              IO_obj.id)
            logger.warning(msg)
            raise DatabasePostRestError(e)
        if not r.status_code == 200:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to update master server IOQueue for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              IO_obj.archiveobject.ObjectIdentifierValue,
                                                                                                                                              e,
                                                                                                                                              IO_obj.id)
            logger.warning(msg)
            raise DatabasePostRestError(e)

    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def remote_read_disk_apply_async(self, remote_server, IOQueue_obj_id, ArchiveObject_obj_ObjectUUID, queue='smdisk'):
        """Remote REST call to appy_async
        
        :param remote_server: example: [https://servername:port/api/write_storage_method_tape_apply, user, password]
        :param IOQueue_obj_id: Primary key to IOQueue database table to be performed, ex 'id1'
        :param ArchiveObject_obj_ObjectUUID: ObjectUUID key to ArchiveObject database table to be performed, ex 'id1'
        :param queue: celery queue name, ex 'smdisk'
        
        """
        logger = logging.getLogger('Storage')
        base_url, ruser, rpass = remote_server
        read_disk_rest_endpoint = urljoin(base_url, '/api/read_storage_method_disk_apply/')
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        data = {'queue': queue, 
                'IOQueue_obj_id': IOQueue_obj_id, 
                'ArchiveObject_obj_ObjectUUID': ArchiveObject_obj_ObjectUUID}
        try:
            r = requests_session.post(read_disk_rest_endpoint,
                                  headers={'Content-Type': 'application/json'},
                                  data=JSONRenderer().render(data))
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to remote server and apply read task for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_obj_ObjectUUID,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        if not r.status_code == 201:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to apply read task to remote server for ObjectUUID: %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_obj_ObjectUUID,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        return apply_result(r.json()['task_id'])

    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def _move_to_accesspath(self, master_server, filename_list, IOQueue_obj_id, queue='default'):
        """Remote REST call to apply_async MoveToAccessPath
        
        :param remote_server: example: [https://servername:port, user, password]
        :param filename_list: List of filenames to move, ex ['id1', 'id2']
        :param queue: celery queue name, ex 'smtape'
        
        """
        logger = logging.getLogger('Storage')
        base_url, ruser, rpass = master_server
        read_tape_rest_endpoint = urljoin(base_url, '/api/move_to_access_path/')
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        data = {'queue': queue, 
                'IOQueue_obj_id': IOQueue_obj_id, 
                'filename_list': filename_list}
        try:
            r = requests_session.post(read_tape_rest_endpoint,
                                  headers={'Content-Type': 'application/json'},
                                  data=JSONRenderer().render(data))
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to master server and apply move_to_accesspath for filename_list %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              filename_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        if not r.status_code == 201:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to apply move_to_accesspath task on master server for filename_list: %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              filename_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_obj_id)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        return apply_result(r.json()['task_id'])

    @retry(stop_max_attempt_number=5, wait_fixed=60000)
    def _wait_for_move_to_accesspath(self, master_server, task_id):
        """ Call REST service on master to get state for task_id
        
        :param master_server: example: [https://servername:port, user, password]
        :param task_id: task_id to move_to_accesspath task
        
        """
        logger = self.logger
        base_url, ruser, rpass = master_server
        IOQueue_rest_endpoint_base = urljoin(base_url, '/api/move_to_access_path/')
        IOQueue_rest_endpoint = urljoin(IOQueue_rest_endpoint_base, '%s/' % str(task_id))
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        
        loop_num_total = 0
        loop_num = 0
        while True:
            try:
                r = requests_session.get(IOQueue_rest_endpoint,
                                            headers={'Content-Type': 'application/json'}, 
                                            )
            except requests.ConnectionError as e:
                e = [1, 'ConnectionError', repr(e)]
                msg = 'Problem to connect to server and get status for task_id: %s, error: %s' % (
                                                                                                                                                  task_id,
                                                                                                                                                e)
                logger.warning(msg)
                raise DatabasePostRestError(e)
            if not r.status_code == 200:
                e = [r.status_code, r.reason, r.text]
                msg = 'Problem to get status for task_id: %s, error: %s' % (
                                                                            task_id,
                                                                            e)
                logger.warning(msg)
                raise DatabasePostRestError(e)
            else:
                state = r.json()['state']
                if state == 'SUCCESS':
                    logger.info('Success - Status is %s for move to accesspath task_id: %s' % (
                                                                                     state,
                                                                                     task_id))
                    break
                elif state == 'FAILURE':
                    msg = 'Failed to move files to accesspath, error: %s' % repr(r.json())
                    logger.error(msg)
                    raise ESSArchSMError(msg)
                elif loop_num == 10:
                    logger.info('Status is %s for move to accesspath task_id: %s' % (
                                                                                     state,
                                                                                     task_id))
                    loop_num = 0
            if loop_num_total == 3600:
                raise  ESSArchSMError('Timeout 1h to wait for move to accesspath task_id: %s' % task_id)
            loop_num += 1
            loop_num_total += 1
            time.sleep(1)

    def _ReadDiskProc(self,IO_obj_uuid):
        """Read IOuuid from disk
        
        :param IO_obj_uuid: Primary key to entry in IOQueue database table
        
        """
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
        # If storageMediumFormat is AIC type (103)
        if storageMedium_obj.storageMediumFormat == 103:
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

        # Create DIP directory if not exists
        if runflag and not os.path.exists(tmp_target_path):
            try:
                os.makedirs(tmp_target_path)
            except OSError as e:
                msg = 'Problem to create / access DIP directory: %s, IOuuid: %s' % (target_path, IO_obj_uuid)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0

        # Check write access to DIP directory
        if not os.access(target_path, 7):
            msg = 'Problem to access DIP directory: %s, IOuuid: %s' % (tmp_target_path, IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
            runflag = 0

        if runflag:
            ########################################################
            # Get AIP package to DIP directory
            ########################################################
            try:
                logger.info('Try to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s', ObjectIdentifierValue, contentLocationValue, tmp_target_path,  IO_obj_uuid)
                ip_tar_path_source = os.path.join(contentLocationValue, ip_tar_filename)
                ip_tar_path_tmp_target = os.path.join(tmp_target_path, ip_tar_filename)
                shutil.copy2(ip_tar_path_source, ip_tar_path_tmp_target)
                ip_p_mets_path_source = os.path.join(contentLocationValue,ip_p_mets_filename)
                ip_p_mets_path_tmp_target = os.path.join(tmp_target_path,ip_p_mets_filename)                
                shutil.copy2(ip_p_mets_path_source, ip_p_mets_path_tmp_target)
                if storageMedium_obj.storageMediumFormat == 103:
                    aic_mets_path_source = os.path.join(contentLocationValue, aic_mets_filename)
                    aic_mets_path_tmp_target = os.path.join(tmp_target_path, aic_mets_filename)
                    shutil.copy2(aic_mets_path_source, aic_mets_path_tmp_target)
            except (IOError, OSError) as e:
                msg = 'Problem to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s, Error: %s' % (ObjectIdentifierValue, contentLocationValue, tmp_target_path, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            else:
                msg = 'Success to get Object %s from SM: %s to tmpDIP: %s, IOuuid: %s' % (ObjectIdentifierValue, contentLocationValue, tmp_target_path,  IO_obj_uuid)
                logger.info(msg)
        if runflag:
            #############################################
            # Checksum Check
            #############################################
            try:
                tp_sum = calcsum(ip_tar_path_tmp_target, ArchiveObject_obj_ObjectMessageDigestAlgorithm)
            except IOError as e:
                msg = 'Failed to get checksum for: %s, Error: %s' % (ip_tar_path_tmp_target,e)
                logger.error(msg)
                error_list.append(msg)
                ESSPGM.Events().create('1041','',self.__name__,__version__,'1',msg,2,ObjectIdentifierValue)
                runflag = 0
            else:
                msg = 'Success to get checksum for: %s, Checksum: %s' % (ip_tar_path_tmp_target,tp_sum)
                logger.info(msg)
                ESSPGM.Events().create('1041','',self.__name__,__version__,'0',msg,2,ObjectIdentifierValue)
        if runflag:
            if str(tp_sum) == str(ArchiveObject_obj_ObjectMessageDigest):
                msg = 'Success to verify checksum for Object %s in tmpDIP: %s, IOuuid: %s' % (ObjectIdentifierValue, tmp_target_path, IO_obj_uuid)
                logger.info(msg)
                ESSPGM.Events().create('1042','',self.__name__,__version__,'0',msg,2,ObjectIdentifierValue)
            else:
                msg = 'Checksum verify mismatch for Object %s in tmpDIP: %s, IOuuid: %s, tape_checksum: %s, meta_checksum: %s' % (ObjectIdentifierValue, tmp_target_path, IO_obj_uuid, tp_sum, ArchiveObject_obj_ObjectMessageDigest)
                logger.error(msg)
                error_list.append(msg)
                ESSPGM.Events().create('1042','',self.__name__,__version__,'1',msg,2,ObjectIdentifierValue)
                runflag = 0
        if runflag:
            #############################
            # Move files to req path
            #############################
            try:
                ip_tar_path_target = os.path.join(target_path, ip_tar_filename)
                ip_p_mets_path_target = os.path.join(target_path, ip_p_mets_filename)
                shutil.move(ip_tar_path_tmp_target, ip_tar_path_target)
                shutil.move(ip_p_mets_path_tmp_target, ip_p_mets_path_target)
                if storageMedium_obj.storageMediumFormat == 103:
                    aic_mets_path_target = os.path.join(target_path, aic_mets_filename)
                    shutil.move(aic_mets_path_tmp_target, aic_mets_path_target)
            except (IOError, OSError) as e:
                msg = 'Problem to move Object %s from tmpdir: %s to target path: %s, IOuuid: %s, Error: %s' % (ObjectIdentifierValue, tmp_target_path, target_path, IO_obj_uuid, e)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0            
        
        ReadSize = 0
        if runflag:                
            aic_mets_size = 0
            if storageMedium_obj.storageMediumFormat == 103:
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
            if storageMedium_obj.storageMediumFormat == 103:
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
        IO_obj.save(IO_obj.save(update_fields=['result']))

        if not runflag:
            raise ESSArchSMError(error_list)
        else:
            return res_dict   
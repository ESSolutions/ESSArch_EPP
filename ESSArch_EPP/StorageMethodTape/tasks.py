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

import logging, time, os, stat, datetime, shutil, pytz, uuid, ESSPGM, ESSMSSQL, tarfile, subprocess, sys, traceback
from xml.dom.minidom import Document
from celery import Task, shared_task
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from Storage.models import storage, storageMedium, IOQueue
from Storage.tasks import TransferReadIO
from configuration.models import ESSConfig, StorageTargets
from essarch.libs import GetSize, ESSArchSMError, calcsum, SMTapeFull
from essarch.models import robotdrives, robotQueue, robot, AccessQueue
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

class WriteStorageMethodTape(Task):
    """Write IP with IO_uuid to tape
    
    Requires the following fields in IOQueue database table:
    storagemethodtarget - Specifies the target of writing
    archiveobject - Specifies the IP to be written
    ObjectPath - Specifies the source path for IP to be written
    ReqType - ReqType shall be set to 10 for writing to tape
    Status - Status shall be set to 0
    
    File "IP" structure in the path ObjectPath:
    "ObjectPath"/"ObjectIdentifierValue".tar
    "ObjectPath"/"ObjectIdentifierValue"_Package_METS.xml
    "ObjectPath"/"aic_uuid"_AIC_METS.xml
    
    :param req_pk_list: List of primary keys to IOQueue database table to be performed
    
    Example:
    from StorageMethodTape.tasks import WriteStorageMethodTape
    result = WriteStorageMethodTape().apply_async((['03a33829bad6494e990fe08bfdfb4f6b'],), queue='smtape')
    result.status
    result.result
    
    """
    tz = timezone.get_default_timezone()
    time_limit = 86400
    logger = logging.getLogger('StorageMethodTape')

    def run(self, req_pk_list, *args, **kwargs):
        """The body of the task executed by workers."""
        logger = self.logger
        IO_objs = IOQueue.objects.filter(pk__in=req_pk_list)
        NumberOfTasks = IO_objs.count()
        logger.debug('Initiate write task, NumberOfTasks: %s' % NumberOfTasks)
        
        for TaskNum, IO_obj in enumerate(IO_objs):          
            logger.debug('Prepare to start WriteTapeProc for IOuuid: %s' % IO_obj.id)
            # Let folks know we started
            IO_obj.Status = 5
            IO_obj.save(update_fields=['Status'])
            self.update_state(state='PROGRESS',
                meta={'current': TaskNum, 'total': NumberOfTasks})
            try:
                target_obj = IO_obj.storagemethodtarget.target
                master_server = target_obj.master_server.split(',')
                if len(master_server) == 3:
                    remote_io = True
                else:         
                    remote_io = False
                result = self._WriteTapeProc(IO_obj.id)
            except SMTapeFull as e:
                logger.info(e)
                try:
                    msg = 'Retry to write object: %s to new tape (IOuuid: %s)' % (IO_obj.archiveobject.ObjectIdentifierValue, IO_obj.id) 
                    logger.info(msg)
                    result = self._WriteTapeProc(IO_obj.id)
                except ESSArchSMError as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    IO_obj.refresh_from_db()
                    msg = 'Problem to write object %s to tape, error: %s line: %s (IOuuid: %s)' % (IO_obj.archiveobject.ObjectIdentifierValue, e, exc_traceback.tb_lineno, IO_obj.id)
                    logger.error(msg)
                    ESSPGM.Events().create('1104','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
                    IO_obj.Status = 100
                    IO_obj.save(update_fields=['Status'])
                    if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                    #raise self.retry(exc=e, countdown=10, max_retries=2)
                    raise e
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    IO_obj.refresh_from_db()
                    msg = 'Unknown error to write object %s to tape, error: %s trace: %s (IOuuid: %s)' % (IO_obj.archiveobject.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)), IO_obj.id)
                    logger.error(msg)
                    ESSPGM.Events().create('1104','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
                    IO_obj.Status = 100
                    IO_obj.save(update_fields=['Status'])
                    if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                    raise e
            except ESSArchSMError as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                IO_obj.refresh_from_db()
                msg = 'Problem to write object %s to tape, error: %s line: %s (IOuuid: %s)' % (IO_obj.archiveobject.ObjectIdentifierValue, e, exc_traceback.tb_lineno, IO_obj.id)
                logger.error(msg)
                ESSPGM.Events().create('1104','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
                IO_obj.Status = 100
                IO_obj.save(update_fields=['Status'])
                if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                #raise self.retry(exc=e, countdown=10, max_retries=2)
                raise e
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                IO_obj.refresh_from_db()
                msg = 'Unknown error to write object %s to tape, error: %s trace: %s (IOuuid: %s)' % (IO_obj.archiveobject.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)), IO_obj.id)
                logger.error(msg)
                ESSPGM.Events().create('1104','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)       
                IO_obj.Status = 100
                IO_obj.save(update_fields=['Status'])
                if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                raise e

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
            ESSPGM.Events().create('1104','',self.__name__,__version__,'0',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)      
            IO_obj.Status = 20
            IO_obj.save(update_fields=['Status'])
            if remote_io: self._update_master_ioqueue(master_server, IO_obj)
            #return result

    #def on_failure(self, exc, task_id, args, kwargs, einfo):
    #    logger = logging.getLogger('StorageMethodTape')
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
    def remote_write_tape_apply_async(self, remote_server, IOQueue_objs_id_list, ArchiveObject_objs_ObjectUUID_list, queue='smtape'):
        """Remote REST call to appy_async
        
        :param remote_server: example: [https://servername:port, user, password]
        :param IOQueue_objs_id_list: List of primary keys to IOQueue database table to be performed, ex ['id1', 'id2']
        :param ArchiveObject_objs_ObjectUUID_list: List of ObjectUUID keys to ArchiveObject database table to be performed, ex ['id1', 'id2']
        :param queue: celery queue name, ex 'smtape'
        
        """
        logger = logging.getLogger('Storage')
        base_url, ruser, rpass = remote_server
        write_tape_rest_endpoint = urljoin(base_url, '/api/write_storage_method_tape_apply/')
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        data = {'queue': queue, 
                'IOQueue_objs_id_list': IOQueue_objs_id_list, 
                'ArchiveObject_objs_ObjectUUID_list': ArchiveObject_objs_ObjectUUID_list}
        try:
            r = requests_session.post(write_tape_rest_endpoint,
                                  headers={'Content-Type': 'application/json'},
                                  data=JSONRenderer().render(data))
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to remote server and apply write task for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_objs_ObjectUUID_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_objs_id_list)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        if not r.status_code == 201:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to apply write task to remote server for ObjectUUID: %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_objs_ObjectUUID_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_objs_id_list)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        return apply_result(r.json()['task_id'])

    def _WriteTapeProc(self,IO_obj_uuid):
        """Writes IP (Information Package) to a tape
        
        :param IO_obj_uuid: Primary key to entry in IOQueue database table
        
        """
        logger = logging.getLogger('StorageMethodTape')
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

        logger.info('Start Tape Write Process for object: %s, target: %s, IOuuid: %s', ObjectIdentifierValue,target_obj_target,IO_obj_uuid)

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

        if runflag:
            ########################################################
            # Mount write tape
            ########################################################
            Mount_exitcode, storageMediumID, tapedev, t_pos = self._MountWritePos(target_obj_id=target_obj.id, MediumLocation=MediumLocation, IO_obj_id=IO_obj_uuid)
            if Mount_exitcode==0: 
                logger.info('Succedd to mount write tape id: ' + storageMediumID + ' dev: ' + tapedev + ' pos: ' + str(t_pos))
            elif Mount_exitcode==1:
                msg = 'Problem to mount tape. (IOuuid: %s)' % IO_obj_uuid
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            elif Mount_exitcode==2:
                msg = 'No empty tapes are available in robot with prefix: %s (IOuuid: %s)' % (target_obj.target, IO_obj_uuid)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            elif Mount_exitcode==3:
                msg = 'Failed to verify tape after full write. (IOuuid: %s)' % IO_obj_uuid
                logger.error(msg)
                error_list.append(msg)
                runflag = 0

        if runflag:    
            ########################################################
            # Verify tape position and check write/tape size
            ########################################################
            storageMedium_obj = storageMedium.objects.get(storageMediumID=storageMediumID)
            IO_obj.storagemedium =  storageMedium_obj
            new_t_size = storageMedium_obj.storageMediumUsedCapacity + int(WriteSize)
            if new_t_size > target_obj.maxCapacity and target_obj.maxCapacity > 0:
                logger.info('Tape id: %s has reached maximum configured tape size: %s bytes. (IOuuid: %s)',storageMediumID,str(target_obj.maxCapacity),str(IO_obj_uuid))
                ###################################################
                # Release lock for tapedrive
                res, errno = ReleaseTapeLock(IO_obj_uuid)
                if errno == 0:
                    logger.info(res)
                else:
                    msg = '%s (IOuuid: %s)' % (res, IO_obj_uuid)
                    logger.error(msg)
                    error_list.append(msg)
                    runflag = 0
                
                if runflag:
                    ########################################################
                    # Tape is full quickverify tape and retry job
                    ########################################################
                    res, errno = self._VerifyAndFlagTapeFull(storageMediumID)
                    if errno == 0:
                        logger.info('Success to verify storageMediumID: %s and flag as full "archivetape"' % storageMediumID)
                        raise SMTapeFull('No space left on storageMediumID %s restart write for object: %s (IOuuid: %s)' % (storageMediumID, ObjectIdentifierValue, IO_obj.id))
                    else:
                        msg = '%s (IOuuid: %s)' % (res, IO_obj_uuid)
                        logger.error(msg)
                        error_list.append(msg)
                        runflag = 0
        if runflag:    
            logger.info('New tape size for t_id: ' + storageMediumID + ' is: '+str(new_t_size))
            current_t_pos,errno,why = MTFilenum(tapedev)
            if errno:
                msg = 'Problem to get current tape position. errno: %s error: %s (IOuuid: %s)' % (errno, why, IO_obj_uuid)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0

        if runflag:
            logger.info('Current t_pos: ' + str(current_t_pos) + ' for t_id: '+str(storageMediumID))
            latest_storage_qs = storage.objects.filter(storagemedium__storageMediumID=storageMediumID).extra(
                                                                     select={'contentLocationValue_int': 'CAST(contentLocationValue AS UNSIGNED)'}
                                                                     ).order_by('-contentLocationValue_int')[:1]
            if latest_storage_qs.exists():
                db_t_pos = int(latest_storage_qs[0].contentLocationValue) + 1
            else:
                db_t_pos = 1                        
            if not current_t_pos ==  db_t_pos:
                msg = 'Current t_pos: %s for t_id: %s does not match db_t_pos: %s' % (current_t_pos, storageMediumID, db_t_pos)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
        
        startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        if runflag:
            logger.info('Start to write object: %s to t_pos: %s and t_id: %s' % (ObjectIdentifierValue, t_pos, storageMediumID))
            if current_t_pos == t_pos:
                ########################################################
                # Write AIP package to tape
                ########################################################
                
                contentLocationValue = t_pos
                Write_cmdres = self._WritePackage(tapedev,target_obj.blocksize,ObjectIdentifierValue,ip_tar_path_source,ip_p_mets_path_source,aic_mets_path_source)
                logger.info('WritePackage cmdres: ' + str(Write_cmdres) + ' for t_id: '+str(storageMediumID))
                if Write_cmdres[0]==0:
                    timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    ##########################
                    # Insert StorageTable
                    storage_obj = storage()
                    storage_obj.contentLocationType = 300 #sm_obj.type or 300
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
                            
                    ###################################################
                    # Release lock for tapedrive
                    res, errno = ReleaseTapeLock(IO_obj_uuid)
                    if errno == 0:
                        logger.info(res)
                    else:
                        msg = '%s (IOuuid: %s)' % (res, IO_obj_uuid)
                        logger.error(msg)
                        error_list.append(msg)
                        runflag = 0                                        
    
                #elif self.cmdres[0]==28: # 28=full tape with python tar
                elif Write_cmdres[0]==2: # 2=full tape with SUSE tar
                    #Tape is full
                    #Hardclose writeobject (Only used with "FunctionThread().WritePackage")
                    #self.cmdres = writer().hardclose(self.writeobject)
                    ###################################################
                    # Release lock for tapedrive
                    res, errno = ReleaseTapeLock(IO_obj_uuid)
                    if errno == 0:
                        logger.info(res)
                    else:
                        msg = '%s (IOuuid: %s)' % (res, IO_obj_uuid)
                        logger.error(msg)
                        error_list.append(msg)
                        runflag = 0                                           
                    ########################################################
                    # Tape is full quickverify tape and retry job
                    ########################################################
                    res, errno = self._VerifyAndFlagTapeFull(storageMediumID)
                    if errno == 0:
                        logger.info('Success to verify storageMediumID: %s and flag as full "archivetape"' % storageMediumID)
                        raise SMTapeFull('No space left on storageMediumID %s restart write for object: %s (IOuuid: %s)' % (storageMediumID, ObjectIdentifierValue, IO_obj.id))
                    else:
                        msg = '%s (IOuuid: %s)' % (res, IO_obj_uuid)
                        logger.error(msg)
                        error_list.append(msg)
                        runflag = 0
                else:
                    msg = 'Problem to write a copy of object: %s to tape: %s (IOuuid: %s)' % (ObjectIdentifierValue, storageMediumID, IO_obj_uuid)
                    logger.error(msg)
                    error_list.append(msg)
                    runflag = 0
            else:
                msg = 'Current-tape position and DB-tape position missmatch for object: %s and tape: %s (IOuuid: %s)' % (ObjectIdentifierValue, storageMediumID, IO_obj_uuid)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            

        if not runflag:
            msg = 'Because of the previous problems it is not possible to store the object %s to storage method target: %s (IOuuid: %s)' % (ObjectIdentifierValue, target_obj_target, IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
        
        stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        WriteTime = stopTime-startTime
        if WriteTime.seconds < 1: WriteTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
        
        if storage_obj is not None:
            storage_obj_id = storage_obj.id
        else:
            storage_obj_id = None
        
        if storageMedium_obj is not None:
            storageMedium_obj_storageMediumID = storageMedium_obj.storageMediumID
            storageMedium_obj_storageMediumUUID = storageMedium_obj.storageMediumUUID
        else:
            storageMedium_obj_storageMediumID = None
            storageMedium_obj_storageMediumUUID = None

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

    def _WritePackage(self,tapedev,t_block,ObjectIdentifierValue,ObjectPath,PMetaObjectPath,AICmets_objpath):
        """Prepares to write the information package with tar Command
        
        :param tapedev: SCSI tape device name
        :param t_block: Block size
        :param ObjectIdentifierValue: ObjectIdentifierValue
        :param ObjectPath: File Path to the information package tarfile
        :param PMeteObjectPath: File Path to the "package" METS file
        :param AICmets_objpath: File Path to the AIC METS file
        """
        ObjectDIR,ObjectFILE = os.path.split(ObjectPath)
        MetaObjectDIR,MetaObjectFILE = os.path.split(PMetaObjectPath)
        if AICmets_objpath is not '':
            AICObjectDIR,AICObjectFILE = os.path.split(AICmets_objpath)
        else:
            AICObjectDIR = None
            AICObjectFILE = None
        # Open writeobject
        writeresult = writer().subtar(tapedev,t_block,ObjectDIR,ObjectFILE,MetaObjectFILE,AICObjectFILE)
        return writeresult[0],writeresult[1],writeresult[2]

    def _VerifyAndFlagTapeFull(self, storageMediumID='', work_uuid=''):
        """Verifies the tape and sets media status
        
        Verifies that an object in the beginning of the tape, an object in the
        middle of the tape and an object at the end of the tape. 
        If all objects exist and have the correct checksum so marked 
        the tape is marked with the status full and complete..
        
        :param storageMediumID: storageMediumID to verify
        :param work_uuid: primary key in IOQueue database table
        
        """
        logger = logging.getLogger('StorageMethodTape')
        res = ''
        exitstatus = 0
        failed_flag = 0
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)
        verifydir = ESSConfig.objects.get(Name='verifydir').Value

        
        storageMedium_obj = storageMedium.objects.get(storageMediumID=storageMediumID)
        TmpPath = os.path.join(verifydir, storageMedium_obj.storagetarget.target)
        if not os.path.exists(TmpPath):
            os.mkdir(TmpPath)
        
        ReqUUID = uuid.uuid1()
        ReqType = u'2'
        ReqPurpose = u'verify'
        ObjectIdentifierValue = u''
        user = u'system'
        
        # Log Access Order request
        event_info = 'User: %s has create a Access Order Request to verify storageMediumID: %s' % (user, storageMediumID)
        logger.info(event_info)
        
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
                    event_info = 'Success to verify storageMediumID: %s ReqUUID: %s' % (storageMediumID, ReqUUID)
                    logger.info(event_info)
                    DbRow.delete()
                    break
                elif loop_num == 15:
                    event_info = 'Access to verify storageMediumID: %s RequUID: %s Status: %s' % (storageMediumID, ReqUUID, DbRow.Status)
                    logger.info(event_info)
                    loop_num = 0
                elif DbRow.Status==100:
                    event_info = 'Failed to verify storageMediumID: %s ReqUUID: %s' % (storageMediumID, ReqUUID)
                    logger.error(event_info)
                    DbRow.delete()
                    failed_flag = 1
                    break
            else:
                event_info = 'Access to verify storageMediumID: %s with ReqUUID: %s does not exists' % (storageMediumID, ReqUUID)
                logger.info(event_info)
                failed_flag = 1
                break
            loop_num += 1
            time.sleep(1)

        if failed_flag:
            # Mark tape as failed in StorageMediumTable
            timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            storageMedium_obj.storageMediumStatus = 100
            storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
            storageMedium_obj.LocalDBdatetime = timestamp_utc
            storageMedium_obj.save(update_fields=['storageMediumStatus', 'linkingAgentIdentifierValue', 'LocalDBdatetime'])
            if ExtDBupdate:
                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium', 'UPD',('storageMediumStatus','100',
                                                                                                'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                               ('storageMediumID',storageMediumID))
                if ext_errno: logger.error('Failed to update External DB: ' + str(storageMediumID) + ' error: ' + str(ext_why))
                else:
                    storageMedium_obj.ExtDBdatetime = timestamp_utc
                    storageMedium_obj.save(update_fields=['ExtDBdatetime'])
            exitstatus = 1
            res = 'Problem to verify mediumID: %s' % (storageMediumID)
        else:
            # Mark tape as full in StorageMediumTable
            timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            storageMedium_obj.storageMediumStatus = 30
            storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
            storageMedium_obj.LocalDBdatetime = timestamp_utc
            storageMedium_obj.save(update_fields=['storageMediumStatus', 'linkingAgentIdentifierValue', 'LocalDBdatetime'])
            if ExtDBupdate:
                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium', 'UPD',('storageMediumStatus','30',
                                                                                                'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                               ('storageMediumID',storageMediumID))
                if ext_errno: logger.error('Failed to update External DB: ' + str(storageMediumID) + ' error: ' + str(ext_why))
                else:
                    storageMedium_obj.ExtDBdatetime = timestamp_utc
                    storageMedium_obj.save(update_fields=['ExtDBdatetime'])
            
        return res, exitstatus

    def _MountWritePos(self,target_obj_id, MediumLocation, IO_obj_id, full_t_id=''):
        """Mount tape at last write position and return OK or Fail
        
        :param target_obj_id: PRIMARY KEY to the object in StorageTargets model
        :param MediumLocation: Which location storage medium, according to the 
                        configuration i ESSConfig model storageMediumLocation
        :param full_t_id: Set to medium id to VerifyAndFlagTapeFull
        :param IO_obj_id: primary key in IOQueue database table
        
        """
        logger = logging.getLogger('StorageMethodTape')
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

        # If tape is full verify tape and then unmount
        if len(full_t_id) == 6:
            self._VerifyAndFlagTapeFull(storageMediumID=full_t_id, work_uuid=IO_obj_id)

        target_obj = StorageTargets.objects.get(id=target_obj_id)

        #Check if a write tape exist
        storageMedium_objs = storageMedium.objects.filter(storageMediumStatus=20, storagetarget=target_obj)
        if not storageMedium_objs.exists():
            t_id = ''
        else:
            t_id = storageMedium_objs[0].storageMediumID
            
        if t_id:
            #Check if write tape is mounted or need to mount
            tapedev = MountTape(t_id=t_id, IO_obj_id=IO_obj_id)
            if not tapedev:
                # Problem to mount tape
                logger.error('Problem to mount tape: %s' % t_id)
                return 1, 'None', None, 'None'   
        else:
            #########################################
            # Try to mount a new tape from robot
            robot_objs = robot.objects.filter(status='Empty', t_id__startswith=target_obj.target).order_by('t_id')

            if robot_objs: 
                t_id=robot_objs[0].t_id
                logger.info('No writetape found, start to mount new tape: ' + str(t_id))
                ##########################
                # Insert StorageMediumTable
                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                MediumUUID = uuid.uuid4()
                storageMedium_obj = storageMedium()
                storageMedium_obj.id = MediumUUID
                storageMedium_obj.storageMediumUUID=unicode(MediumUUID)
                storageMedium_obj.storageMedium=target_obj.type
                storageMedium_obj.storageMediumID=t_id
                storageMedium_obj.storageMediumDate=timestamp_utc
                storageMedium_obj.storageMediumLocation=MediumLocation
                storageMedium_obj.storageMediumLocationStatus=50
                storageMedium_obj.storageMediumBlockSize=target_obj.blocksize
                storageMedium_obj.storageMediumStatus=20
                storageMedium_obj.storageMediumUsedCapacity=0
                storageMedium_obj.storageMediumFormat=target_obj.format
                storageMedium_obj.storageMediumMounts=1
                storageMedium_obj.linkingAgentIdentifierValue=AgentIdentifierValue
                storageMedium_obj.CreateDate=timestamp_utc
                storageMedium_obj.CreateAgentIdentifierValue=AgentIdentifierValue
                storageMedium_obj.LocalDBdatetime=timestamp_utc
                storageMedium_obj.storagetarget=target_obj
                storageMedium_obj.save()                                                                    
                if ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium', 'INS', ('storageMedium',storageMedium_obj.storageMedium,
                                                                                                    'storageMediumID',storageMedium_obj.storageMediumID,
                                                                                                    'storageMediumDate',storageMedium_obj.storageMediumDate.astimezone(self.tz).replace(tzinfo=None),
                                                                                                    'storageMediumLocation',storageMedium_obj.storageMediumLocation,
                                                                                                    'storageMediumLocationStatus',storageMedium_obj.storageMediumLocationStatus,
                                                                                                    'storageMediumBlockSize',storageMedium_obj.storageMediumBlockSize,
                                                                                                    'storageMediumUsedCapacity',storageMedium_obj.storageMediumUsedCapacity,
                                                                                                    'storageMediumStatus',storageMedium_obj.storageMediumStatus,
                                                                                                    'storageMediumFormat',storageMedium_obj.storageMediumFormat,
                                                                                                    'storageMediumMounts',storageMedium_obj.storageMediumMounts,
                                                                                                    'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue,
                                                                                                    'CreateDate',storageMedium_obj.CreateDate.astimezone(self.tz).replace(tzinfo=None),
                                                                                                    'CreateAgentIdentifierValue',storageMedium_obj.CreateAgentIdentifierValue,
                                                                                                    'StorageMediumGuid',storageMedium_obj.storageMediumUUID))
                    if ext_errno: logger.error('Failed to insert to External DB: ' + str(t_id) + ' (ESSPGM) error: ' + str(ext_why))
                    else:
                        storageMedium_obj.ExtDBdatetime = storageMedium_obj.LocalDBdatetime
                        storageMedium_obj.save(update_fields=['ExtDBdatetime'])   
                ############################
                # Mounting new tape
                tapedev = MountTape(t_id=t_id, IO_obj_id=IO_obj_id)
                if not tapedev:
                    # Problem to mount tape
                    logger.error('Problem to mount tape: %s' % t_id)
                    return 1, 'None', None, 'None'              
                ##########################################
                # Write tapelabel to tape
                xml_labelfilepath = ''
                try:
                    xml_labelfilepath = self._CreateTapeLabel(RootPath='/ESSArch/log/label',storageMedium_obj=storageMedium_obj)
                    tar_obj = tarfile.open(name=tapedev,mode="w|",bufsize=512 * 20)
                    logger.info(t_id + ' succeed to open tapedevice')
                    logger.info(t_id + ' start to add label tape')
                    tarinfo_obj = tar_obj.gettarinfo(xml_labelfilepath, t_id+'_label.xml')
                    tar_obj.addfile(tarinfo_obj, file(xml_labelfilepath))
                    logger.info(t_id + ' succeed to label new media')
                    tar_obj.close()
                    logger.info(t_id + ' close tapedevice succeed')             
                except (ValueError, IOError, OSError, tarfile.TarError) as e:
                    msg = 'Problem to write labelfile: %s to storageMediumID: %s tapedevice: %s (IOuuid: %s) error: %s' % (xml_labelfilepath, t_id, tapedev, IO_obj_id, e)
                    logger.error(msg)
                    
                    timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    storageMedium_obj.storageMediumStatus = 100
                    storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                    storageMedium_obj.LocalDBdatetime = timestamp_utc
                    if ExtDBupdate:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium', 'UPD', ('storageMediumStatus',storageMedium_obj.storageMediumStatus,
                                                                                                        'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue),
                                                                                                        ('storageMediumID',storageMedium_obj.storageMediumID))
                        if ext_errno: logger.error('Failed to update External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                        else:
                            storageMedium_obj.ExtDBdatetime = storageMedium_obj.LocalDBdatetime
                            storageMedium_obj.save(update_fields=['ExtDBdatetime'])                       
            else:    
                logger.error('Problem to find any empty tapes with prefix: %s in robot (IOuuid: %s)' % (target_obj.target, IO_obj_id))
                return 2, 'None', None, 'None'
        try:
            storageMedium_obj = storageMedium.objects.get(storageMediumID=t_id)
        except ObjectDoesNotExist as e:
            logger.error('Storage medium %s not found in database. error: %s' % (t_id,e))
            return 1, 'None', None, 'None'
        except MultipleObjectsReturned as e:
            logger.error('More then one entry for storage medium %s found in database. error: %s' % (t_id,e))
            return 1, 'None', None, 'None'
        if storageMedium_obj.storageMediumStatus == 100:
            logger.error('Storage medium %s has status failed' % t_id)
            return 1, 'None', None, 'None'
        # Check if tape is in write position
        latest_storage_qs = storage.objects.filter(storagemedium__storageMediumID=t_id).extra(
                                                                 select={'contentLocationValue_int': 'CAST(contentLocationValue AS UNSIGNED)'}
                                                                 ).order_by('-contentLocationValue_int')[:1]
        if latest_storage_qs.exists():
            t_pos = int(latest_storage_qs[0].contentLocationValue) + 1
        else:
            t_pos = 1
        logger.info(t_id + ' start to position to writeposition ' + str(t_pos))
        if MTPosition(tapedev, t_pos) == 'OK':
            # Tape is in write position
            logger.info(str(t_id) + ' is in writeposition ' + str(t_pos))
            return 0, t_id, tapedev, t_pos
        else:
            # Problem to position tape
            logger.error(str(t_id) + ' has problem to position to writeposition ' + str(t_pos))
            return 1, t_id, tapedev, t_pos
        
    def _CreateTapeLabel(self, RootPath, storageMedium_obj):
        """Creates a XMLfile containing a description of the tape "tape label"
        
        :param RootPath: Specifies the file directory where to create the XML file
        :param storageMedium_obj: Specify storageMedium_obj
        
        Return:
        filepath where to find tapelabel xmlfile 
        
        """
        ##########################################
        # Create tapelabel xmlfile
        # Create the minidom document
        xml_labeldoc = Document() 
        # Create the <label> base element
        xml_label = xml_labeldoc.createElement("label")
        xml_labeldoc.appendChild(xml_label)
        # Create the <tape> element
        xml_tape = xml_labeldoc.createElement("tape")
        xml_tape.setAttribute("id", storageMedium_obj.storageMediumID)
        xml_tape.setAttribute("date", storageMedium_obj.storageMediumDate.isoformat())
        xml_label.appendChild(xml_tape)
        # Create the <format> element
        xml_format = xml_labeldoc.createElement("format")
        xml_format.setAttribute("format", str(storageMedium_obj.storageMediumFormat))
        xml_format.setAttribute("blocksize", str(storageMedium_obj.storageMediumBlockSize))
        xml_format.setAttribute("drivemanufacture", str(storageMedium_obj.storageMedium))
        xml_label.appendChild(xml_format)
        # Write  tapelabel to file
        xml_labelfilepath = '%s/%s_label.xml' % (RootPath, storageMedium_obj.storageMediumID)
        xml_labelfile = open(xml_labelfilepath, "w")
        xml_labeldoc.writexml(xml_labelfile,addindent="    ",newl="\n")
        xml_labelfile.close()
        xml_labeldoc.unlink()
        return xml_labelfilepath

class ReadStorageMethodTape(Task):
    """Read IP with IO_uuid from tape
    
    Requires the following fields in IOQueue database table:
    archiveobject - Specifies the IP to be read
    storage - Specifies the source of the IP to be read
    ObjectPath - Specifies path where the IP should be written
    ReqType - ReqType shall be set to 20 for read from tape
    Status - Status shall be set to 0    

    :param req_pk: List of primary keys to IOQueue database table to be performed

    Example:
    from StorageMethodTape.tasks import ReadStorageMethodTape
    result = ReadStorageMethodTape().apply_async((['0de502d5-b7aa-493a-8df6-547768a9aac6'],), queue='smtape')
    result.status
    result.result
    
    """
    tz = timezone.get_default_timezone()
    time_limit = 86400
    logger = logging.getLogger('StorageMethodTape')

    def run(self, req_pk_list, *args, **kwargs):
        """The body of the task executed by workers."""
        logger = self.logger
        #IO_objs = IOQueue.objects.filter(pk__in=req_pk_list)
        #NumberOfTasks = IO_objs.count()
        NumberOfTasks = len(req_pk_list)
        logger.debug('Initiate read task, NumberOfTasks: %s' % NumberOfTasks)
        
        for TaskNum, req_pk in enumerate(req_pk_list):
            IO_obj = IOQueue.objects.get(pk=req_pk)
            logger.debug('Prepare to start ReadTapeProc for IOuuid: %s' % IO_obj.id)
            # Let folks know we started
            IO_obj.Status = 5
            IO_obj.save(update_fields=['Status'])
            self.update_state(state='PROGRESS',
                meta={'current': TaskNum, 'total': NumberOfTasks})
    
            try:
                target_obj = IO_obj.storage.storagemedium.storagetarget
                master_server = target_obj.master_server.split(',')
                if len(master_server) == 3:
                    remote_io = True
                else:         
                    remote_io = False
                
                # Read tape
                result = self._ReadTapeProc(IO_obj.id)
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
                ESSPGM.Events().create('1105','',self.__name__,__version__,'0',msg,2,IO_obj.archiveobject.ObjectIdentifierValue) 

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
                exc_type, exc_value, exc_traceback = sys.exc_info()
                IO_obj.refresh_from_db()
                msg = 'Problem to read object %s from tape, error: %s line: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e, exc_traceback.tb_lineno)
                logger.error(msg)
                ESSPGM.Events().create('1105','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
                IO_obj.Status = 100
                IO_obj.save(update_fields=['Status'])
                if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                #raise self.retry(exc=e, countdown=10, max_retries=2)
                raise e
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                IO_obj.refresh_from_db()
                msg = 'Unknown error to read object %s to tape, error: %s trace: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)))
                logger.error(msg)
                ESSPGM.Events().create('1105','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue) 
                IO_obj.Status = 100
                IO_obj.save(update_fields=['Status'])
                if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                raise e
            else:
                IO_obj.refresh_from_db()
                IO_obj.Status = 20
                IO_obj.save(update_fields=['Status'])
                if remote_io: self._update_master_ioqueue(master_server, IO_obj)
                #return result

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
    def remote_read_tape_apply_async(self, remote_server, IOQueue_objs_id_list, ArchiveObject_objs_ObjectUUID_list, queue='smtape'):
        """Remote REST call to appy_async
        
        :param remote_server: example: [https://servername:port, user, password]
        :param IOQueue_objs_id_list: List of primary keys to IOQueue database table to be performed, ex ['id1', 'id2']
        :param ArchiveObject_objs_ObjectUUID_list: List of ObjectUUID keys to ArchiveObject database table to be performed, ex ['id1', 'id2']
        :param queue: celery queue name, ex 'smtape'
        
        """
        logger = logging.getLogger('Storage')
        base_url, ruser, rpass = remote_server
        read_tape_rest_endpoint = urljoin(base_url, '/api/read_storage_method_tape_apply/')
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        data = {'queue': queue, 
                'IOQueue_objs_id_list': IOQueue_objs_id_list, 
                'ArchiveObject_objs_ObjectUUID_list': ArchiveObject_objs_ObjectUUID_list}
        try:
            r = requests_session.post(read_tape_rest_endpoint,
                                  headers={'Content-Type': 'application/json'},
                                  data=JSONRenderer().render(data))
        except requests.ConnectionError as e:
            e = [1, 'ConnectionError', repr(e)]
            msg = 'Problem to connect to remote server and apply read task for object %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_objs_ObjectUUID_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_objs_id_list)
            logger.warning(msg)
            raise ApplyPostRestError(e)
        if not r.status_code == 201:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to apply read task to remote server for ObjectUUID: %s, error: %s (IOuuid: %s)' % (
                                                                                                                                              ArchiveObject_objs_ObjectUUID_list,
                                                                                                                                              e,
                                                                                                                                              IOQueue_objs_id_list)
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
            msg = 'Problem to connect to master server and apply move_to_accesspath task for filename_list: %s, error: %s (IOuuid: %s)' % (
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

    ###############################################
    def _ReadTapeProc(self,IO_obj_uuid):
        """Read IOuuid from tape
        
        :param IO_obj_uuid: Primary key to entry in IOQueue database table
        
        """
        logger = logging.getLogger('StorageMethodTape')
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
        contentLocationValue = storage_obj.contentLocationValue
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        t_id = storageMedium_obj.storageMediumID
        t_pos = contentLocationValue

        logger.debug('ReadTapeProc start with IOuuid: %s, Object: %s, ObjectPath: %s', IO_obj_uuid, ObjectIdentifierValue, target_path)
        logger.info('Start Tape Read Process for object: %s, IOuuid: %s', ObjectIdentifierValue,IO_obj_uuid)
        
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
            
            # Check if tape is mounted or need to mount
            tapedev = MountTape(t_id=t_id, IO_obj_id=IO_obj_uuid)
            if not tapedev:
                logger.error('Problem to mount tape: %s, (IOuuid: %s)' % (t_id,IO_obj_uuid))
                runflag = 0

        if runflag:
            # Position tape
            if not MTPosition(tapedev, t_pos) == 'OK':
                event_info = 'Failed to position the tape: %s to position: %s (IOuuid: %s)' % (t_id, t_pos, IO_obj_uuid)
                logger.error(event_info)
                ###################################################
                # Release lock for tapedrive
                res, errno = ReleaseTapeLock(IO_obj_uuid)
                if errno == 0:
                    logger.info(res)
                else:
                    logger.error(res)
                runflag = 0

        if runflag:
            ######################################################
            # Tar read IP from tape
            ######################################################
            logger.info('Start to read object: %s from tapedevice: %s, storageMediumID: %s, position: %s (IOuuid: %s)' % (ObjectIdentifierValue, tapedev, t_id, t_pos, IO_obj_uuid))
            t_block = storageMedium_obj.storageMediumBlockSize
            if storageMedium_obj.storageMediumFormat in range(100,102):
                tar_proc = subprocess.Popen(["tar","-b",str(t_block),"-C",str(tmp_target_path),"-x","-f",str(tapedev),str(ip_tar_filename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif storageMedium_obj.storageMediumFormat == 102:
                tar_proc = subprocess.Popen(["tar","-b",str(t_block),"-C",str(tmp_target_path),"-x","-f",str(tapedev),str(ip_p_mets_filename),str(ip_tar_filename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif storageMedium_obj.storageMediumFormat == 103:
                tar_proc = subprocess.Popen(["tar","-b",str(t_block),"-C",str(tmp_target_path),"-x","-f",str(tapedev),str(ip_p_mets_filename),str(aic_mets_filename),str(ip_tar_filename)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            tar_proc_res = tar_proc.communicate()
            if tar_proc.returncode == 0:
                event_info = 'Success to read object: %s from tapedevice: %s, storageMediumID: %s, position: %s to tmp_path: %s (IOuuid: %s)' % (ObjectIdentifierValue, tapedev, t_id, t_pos, tmp_target_path, IO_obj_uuid)
                logger.info(event_info)
                ip_tar_path_tmp_target = os.path.join(tmp_target_path, ip_tar_filename)
                ip_p_mets_path_tmp_target = os.path.join(tmp_target_path,ip_p_mets_filename)
                if storageMedium_obj.storageMediumFormat == 103:
                    aic_mets_path_tmp_target = os.path.join(tmp_target_path, aic_mets_filename)
            else:
                event_info = 'Problem to read object: %s from tapedevice: %s, storageMediumID: %s, position: %s to tmp_path: %s (IOuuid: %s), Error: %s' % (ObjectIdentifierValue, tapedev, t_id, t_pos, tmp_target_path, IO_obj_uuid, tar_proc_res)
                logger.error(event_info)
            ###################################################
            # Release lock for tapedrive
            res, errno = ReleaseTapeLock(IO_obj_uuid)
            if errno == 0:
                logger.info(res)
            else:
                logger.error(res)
                        
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

class writer():
    """Class to write file with ptyhon tar or tar command"""
    ###############################################
    def open(self,packagefile,mode,blksize):
        Debug=0
        errno=0
        why=''
        packageobject=''
        try:  #Open packagefile
            packageobject = tarfile.open(name=packagefile,mode=mode,bufsize=512 * int(blksize))
        except (ValueError,OSError,IOError, tarfile.TarError), (errno, why):
            if Debug: print 'Failed to open tarfile',why
        else:
            if Debug: print 'Succeed to open tarfile'
        return errno,why,packageobject

    def addfile(self,packageobject,sourcefile,archfile):
        Debug=0
        errno=0
        why=''
        try:  #Add sourcefile/archfile to packageobject
            tarinfo = packageobject.gettarinfo(sourcefile, archfile)
            packageobject.addfile(tarinfo, file(sourcefile))
        except (ValueError,OSError, tarfile.TarError), (errno, why):
            if Debug: print 'Failed to add files to tarfile'
        else:
            if Debug: print 'Succeed to add files to tarfile'
        return errno,why

    def close(self,packageobject):
        Debug=0
        errno=0
        why=''
        try:  #Close packageobject
            packageobject.close()#Close tapedevice
        except (ValueError,OSError, tarfile.TarError), (errno, why):
            if Debug: print 'Failed to close tarfile'
        else:
            if Debug: print 'Succeed to close tarfile'
        return errno,why

    def hardclose(self,packageobject):
        Debug=0
        errno=0
        why=''
        try:  #HardClose packageobject
            packageobject.hardclose()#Close tapedevice
        except (ValueError,OSError, tarfile.TarError), (errno, why):
            if Debug: print 'Failed to close tarfile'
        else:
            if Debug: print 'Succeed to close tarfile'
        return errno,why

    def subtar(self,packagefile,blksize,workdir,SIPfile,Metafile,AICObjectFILE=None):
        """Write information package with tar command
        
        :param packagefile: SCSI tapedevice or tarfilename
        :param blksize: Block size
        :param workdir: Specifies the directory path to use as the root path of the TAR package
        :param SIPfile: Specifies the filename to the information package tarfile in "workdir"
        :param Metafile: Specifies the filename to the package METS file in "workdir"
        :param AICObjectFILE: Specifies the filename to the AIC METS file in "workdir"
        
        """
        logger = logging.getLogger('StorageMethodTape')
        Debug=0
        # Tar write tape
        if AICObjectFILE == None:
            tar_proc = subprocess.Popen(["tar","-b",str(blksize),"-c","-v","-f",str(packagefile),str(Metafile),str(SIPfile)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir)
        else:
            tar_proc = subprocess.Popen(["tar","-b",str(blksize),"-c","-v","-f",str(packagefile),str(Metafile),str(AICObjectFILE),str(SIPfile)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir)
        tar_proc_result = tar_proc.communicate()
        if tar_proc.returncode == 0:
            if Debug: logger.info('Succeed to write files to tape, stdout: ' + str(tar_proc_result[0]) + ' stderr: ' + str(tar_proc_result[1]) + ' exitcode: ' + str(tar_proc.returncode))
        else:
            if Debug: logger.error('Problem to write files to tape, stdout: ' + str(tar_proc_result[0]) + ' stderr: ' + str(tar_proc_result[1]) + ' exitcode: ' + str(tar_proc.returncode))
        return tar_proc.returncode,tar_proc_result[0],tar_proc_result[1]

def MTFilenum(tapedev):
    """Reads the output from mt command and return the filenum"""
    if ESSConfig.objects.get(Name='OS').Value == 'SUSE':
        mt_proc = subprocess.Popen(["mt -f " + tapedev + " status | grep 'file number'"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        mt_proc = subprocess.Popen(["mt -f " + tapedev + " status | awk {'print $2'} | grep number="], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mt_proc_result = mt_proc.communicate()
    if mt_proc.returncode == 0:
        fileno = ''
        for i in mt_proc_result[0]:       #Reads the output from mt command and return the filenum in fileno
            if i.isdigit():
                fileno = fileno + i
        if len(fileno):
            return int(fileno),0,str(mt_proc_result)
        else:
            return None,1,str(mt_proc_result)
    else:
        return None,2,str(mt_proc_result)

def MTPosition(tapedev, t_num):
    """Position the tape and return OK or Fail"""
    logger = logging.getLogger('StorageMethodTape')
    real_current_t_num,errno,why=MTFilenum(tapedev)
    if errno:
        logger.error('Problem to get current tape position, errno: %s, why: %s',str(errno),why)
        return 'Fail'
    logger.info('Start to position to tapefile: ' + str(t_num) + ' current position is: ' + str(real_current_t_num))
    if int(t_num) == 0:
        logger.info('Start to rewind tape to position: 0')
        mt_proc = subprocess.Popen(["mt","-f",str(tapedev),"rewind"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    elif (int(t_num) - int(real_current_t_num)) < 0:
        fileno = ''
        for i in str(int(t_num) - int(real_current_t_num)):       #Cut away minus sign
            if i.isdigit():
                fileno = fileno + i
        newt_num=int(fileno) + 1
        logger.info('Start to position with: bsfm: ' + str(newt_num))
        mt_proc = subprocess.Popen(["mt","-f",str(tapedev),"bsfm",str(newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    else:
        newt_num=int(t_num) - int(real_current_t_num)
        if newt_num > 0:
            logger.info('Start to position with: fsf: ' + str(newt_num))
            mt_proc = subprocess.Popen(["mt","-f",str(tapedev),"fsf",str(newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif newt_num == 0:
            newt_num = 1
            logger.info('Start to position to beginining of tape file with: bsfm: ' + str(newt_num))
            mt_proc = subprocess.Popen(["mt","-f",str(tapedev),"bsfm",str(newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    mt_proc_result = mt_proc.communicate()
    if mt_proc.returncode == 0:
        real_current_t_num,errno,why=MTFilenum(tapedev)
        if errno:
            logger.error('Problem to get current tape position, errno: %s, why: %s',str(errno),why)
            return 'Fail'
        elif int(t_num) == int(real_current_t_num): 
            logger.info('Success to position to tapefile: ' + str(t_num) + ' cmdout: ' + str(mt_proc_result))
            return 'OK'
    else:
        logger.error('Problem to position to tapefile: ' + str(t_num) + ' cmdout: ' + str(mt_proc_result))
        return 'Fail'

def MountTape(t_id, IO_obj_id):
    """Mount the tape and return tapedevice"""
    logger = logging.getLogger('StorageMethodTape')
    tapedev = None
    #Check if tape is mounted
    try:
        robotdrives_obj = robotdrives.objects.get(t_id=t_id, status='Mounted')
    except ObjectDoesNotExist as e:
        #Tape is not mounted, mounting tape
        logger.info('Start to mount: ' + str(t_id))
        robotQueue_obj, created = robotQueue.objects.update_or_create(
                                                                     ReqUUID=IO_obj_id,
                                                                     ReqType=50,
                                                                     ReqPurpose='MountTapePosition',
                                                                     MediumID=t_id,
                                                                     user='sys',
                                                                     defaults={'Status':0}) 
        #robotQueue_obj = robotQueue()
        #robotQueue_obj.ReqUUID = IO_obj_id
        #robotQueue_obj.ReqType = 50 # Mount
        #robotQueue_obj.ReqPurpose = 'MountTapePosition'
        #robotQueue_obj.Status = 0 # Pending
        #robotQueue_obj.MediumID = t_id
        #robotQueue_obj.user = 'sys'
        #robotQueue_obj.save()
        while 1:
            try:
                robotdrives_obj = robotdrives.objects.get(t_id=t_id, status='Mounted', drive_lock=IO_obj_id)
            except ObjectDoesNotExist as e:
                robotQueue_objs = robotQueue.objects.filter(ReqUUID=IO_obj_id)
                if robotQueue_objs:
                    if robotQueue_objs[0].Status == 100:
                        tapedev = None
                        break
                logger.info('Wait for mounting of: ' + str(t_id))
            else:
                logger.info('Mount succeeded: ' + str(t_id))
                tapedev = robotdrives_obj.drive_dev
                break
            time.sleep(2)
    else:
        while 1:
            robotdrives_obj.refresh_from_db()
            drive_id = robotdrives_obj.drive_id
            current_lock = robotdrives_obj.drive_lock
            tapedev = robotdrives_obj.drive_dev
            ##########################################
            #Tape is mounted, check if locked
            if len(current_lock) > 0:
                ########################################
                # Tape is locked, check if req IO_obj_id = lock
                if str(current_lock) == str(IO_obj_id):
                    ########################################
                    # Tape is already locked with req IO_obj_id
                    logger.info('Already Mounted: ' + str(t_id) + ' and locked by req IO_obj_id: ' + str(IO_obj_id))
                    break
                else:
                    ########################################
                    # Tape is locked with another IO_obj_id
                    logger.info('Tape: ' + str(t_id) + ' is busy and locked by: ' + str(current_lock) + ' and not req IO_obj_id: ' + str(IO_obj_id))
            else:
                ########################################
                # Tape is not locked, lock the drive with req IO_obj_id
                robotdrives_obj.drive_lock=IO_obj_id
                robotdrives_obj.save(update_fields=['drive_lock'])
                logger.info('Tape: ' + str(t_id) + ' is available set lock to req IO_obj_id: ' + str(IO_obj_id))
                break
            time.sleep(5)
    return tapedev

def ReleaseTapeLock(lock_uuid):
    """Release lock for tapedrive"""
    res = 'Missing drivelock for: %s' % lock_uuid
    exitstatus = 1
    robotdrives_objs = robotdrives.objects.filter(drive_lock=lock_uuid)
    for robotdrives_obj in robotdrives_objs:
        robotdrives_obj.drive_lock=''
        robotdrives_obj.save(update_fields=['drive_lock'])
        res = 'Release drivelock for: %s' % lock_uuid
        exitstatus = 0
    return res, exitstatus
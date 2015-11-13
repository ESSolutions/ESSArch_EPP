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

import logging, time, os, datetime, pytz
from celery import Task, shared_task
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from Storage.models import IOQueue
from configuration.models import ESSConfig
from essarch.libs import GetSize, ESSArchSMError, calcsum
from django.utils import timezone
from esscore.rest.uploadchunkedrestclient import UploadChunkedRestClient, UploadChunkedRestException
import requests

@shared_task()
def add(x, y):
    return x + y

class TransferWriteIO(Task):
    """Transfer write IO to remote
    
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
    from Storage.tasks import TransferWriteIO
    result = TransferWriteIO().apply_async(('03a33829bad6494e990fe08bfdfb4f6b',), queue='default')
    result.status
    result.result
    
    """
    tz = timezone.get_default_timezone()
    time_limit = 86400
    logger = logging.getLogger('Storage')

    def run(self, req_pk, *args, **kwargs):
        """The body of the task executed by workers."""
        logger = self.logger
        IO_obj = IOQueue.objects.get(pk=req_pk)

        # Let folks know we started
        IO_obj.remote_status = 5
        IO_obj.save(update_fields=['remote_status'])

        st_obj = IO_obj.storagemethodtarget
        target_obj = st_obj.target
        rhost, rport, ruser, rpass = target_obj.remote_server.split(',')

        try:
            self.upload_rest_client = self._initialize_upload_rest_client(rhost, rport, ruser, rpass)
            result = self._TransferWriteIOProc(req_pk)
        except ESSArchSMError as e:
            IO_obj.refresh_from_db()
            msg = 'Problem to transfer object %s to remote, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            #ESSPGM.Events().create('1102','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.remote_status = 100
            IO_obj.save(update_fields=['remote_status'])
            #raise self.retry(exc=e, countdown=10, max_retries=2)
            raise e
        except Exception as e:
            IO_obj.refresh_from_db()
            msg = 'Unknown error to transfer object %s to remote, error: %s' % (IO_obj.archiveobject.ObjectIdentifierValue, e)
            logger.error(msg)
            #ESSPGM.Events().create('1102','',self.__name__,__version__,'1',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)
            IO_obj.remote_status = 100
            IO_obj.save(update_fields=['remote_status'])
            raise e
        else:
            IO_obj.refresh_from_db()
            ObjectSizeMB = int(result.get('TransferSize'))/1048576
            MBperSEC = ObjectSizeMB/int(result.get('TransferTime').seconds)
            msg = 'Success to transfer IOuuid: %s for object %s to %s, TransferSize: %s, TransferTime: %s (%s MB/Sec)' % (IO_obj.id, 
                                                                                                                                                                       result.get('ObjectIdentifierValue'),
                                                                                                                                                                       result.get('remote_server'),
                                                                                                                                                                       result.get('TransferSize'), 
                                                                                                                                                                       result.get('TransferTime'), 
                                                                                                                                                                       MBperSEC,
                                                                                                                                                                       )
            logger.info(msg)
            #ESSPGM.Events().create('1102','',self.__name__,__version__,'0',msg,2,IO_obj.archiveobject.ObjectIdentifierValue)       
            IO_obj.remote_status = 20
            IO_obj.save(update_fields=['remote_status'])
            return result

    #def on_failure(self, exc, task_id, args, kwargs, einfo):
    #    logger = logging.getLogger('StorageTransfer')
    #    logger.exception("Something happened when trying"
    #                     " to resolve %s" % args[0])

    def _TransferWriteIOProc(self,IO_obj_uuid):
        """Transfer IO_obj to remote host
        
        :param IO_obj_uuid: Primary key to entry in IOQueue database table
        
        """
        logger = self.logger
        runflag = 1
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        error_list = []
        IO_obj = IOQueue.objects.get(id=IO_obj_uuid)
        st_obj = IO_obj.storagemethodtarget
        target_obj = st_obj.target
        remote_server = target_obj.remote_server.split(',')
        target_obj_target = target_obj.target
        
        ArchiveObject_obj = IO_obj.archiveobject
        ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
        source_path = IO_obj.ObjectPath
        WriteSize = IO_obj.WriteSize
        AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value

        logger.info('Start Transfer WriteIO Process for object: %s and target: %s to remote: %s. (IOuuid: %s)' % (
                                                                                                                  ObjectIdentifierValue,
                                                                                                                  target_obj_target,
                                                                                                                  remote_server[0],
                                                                                                                  IO_obj_uuid,
                                                                                                                  ))

        ########################################################
        # Check access to ip_tar_path and verify WriteSize
        ########################################################
        
        aic_obj_uuid = ''
        aic_mets_path_source = ''
        aic_mets_size = 0
        # If storage method format is AIC type (103)
        if target_obj.format == 103:
            try:
                aic_obj_uuid=ArchiveObject_obj.aic_set.get().ObjectUUID
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
        
        '''
        # Check write access to target directory
        if not os.access(target_obj_target, 7):
            msg = 'Problem to access target directory: %s (IOuuid: %s)' % (target_obj_target, IO_obj_uuid)
            error_list.append(msg)    
            logger.error(msg)
            runflag = 0
        '''   
        startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        if runflag:
            ########################################################
            # Transfer AIP package to remote
            ########################################################
            try:
                logger.info('Try to transfer %s to target: %s on remote: %s, IOuuid: %s' % (
                                                                                               ObjectIdentifierValue, 
                                                                                               target_obj_target,
                                                                                               remote_server[0], 
                                                                                               IO_obj_uuid))
                
                self.upload_rest_client.upload(ip_tar_path_source)
                self.upload_rest_client.upload(ip_p_mets_path_source)
                #shutil.copy2(ip_tar_path_source,target_obj_target)
                #shutil.copy2(ip_p_mets_path_source,target_obj_target)
                if target_obj.format == 103:
                    self.upload_rest_client.upload(aic_mets_path_source)
                    #shutil.copy2(aic_mets_path_source,target_obj_target)
            except (UploadChunkedRestException, requests.exceptions.RequestException) as e:
                msg = 'Problem transfer writeIO %s to target %s on remote: %s, IOuuid: %s, error: %s' % (
                                                                                                         ObjectIdentifierValue, 
                                                                                                         target_obj_target,
                                                                                                         remote_server[0], 
                                                                                                         IO_obj_uuid, 
                                                                                                         e)
                logger.error(msg)
                error_list.append(msg)
                runflag = 0
            else:
                pass
            
        if not runflag:
            msg = 'Because of the previous problems it is not possible to transfer the object %s to remote: %s, IOuuid: %s' % (
                                                                                                                               ObjectIdentifierValue, 
                                                                                                                               target_obj_target,
                                                                                                                               remote_server[0],
                                                                                                                               IO_obj_uuid)
            logger.error(msg)
            error_list.append(msg)
        
        stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
        TransferTime = stopTime-startTime
        if TransferTime.seconds < 1: TransferTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.

        res_dict = {
                    'ObjectIdentifierValue': ArchiveObject_obj.ObjectIdentifierValue,
                    'ObjectUUID': ArchiveObject_obj.ObjectUUID,
                    'AgentIdentifierValue': AgentIdentifierValue,
                    'remote_server': remote_server[0],
                    'TransferSize': WriteSize,
                    'TransferTime': TransferTime,
                    'timestamp_utc': timestamp_utc,
                    'error_list': error_list,        
                    'status': runflag,
                    }
        
        IO_obj.result = res_dict
        IO_obj.save(update_fields=['result'])

        if not runflag:
            raise ESSArchSMError(error_list)
        else:
            return res_dict

    def _custom_progress_reporter(self, percent):
            print "\rProgress:{percent:3.0f}%".format(percent=percent)

    def _initialize_upload_rest_client(self, rhost, rport, ruser, rpass, rproto='https'):
        requests_session = requests.Session()
        rest_endpoint = '%s://%s:%s/api/create_tmpworkarea_upload' % (
                                                                         rproto, rhost, rport)
        requests_session.auth = (ruser, rpass)
        return UploadChunkedRestClient(requests_session, rest_endpoint, self._custom_progress_reporter)        
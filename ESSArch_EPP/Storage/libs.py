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

import os, datetime, time, logging, sys, ESSPGM, ESSMD, csv, ESSMSSQL, pytz, traceback, urllib, re

from essarch.models import IngestQueue, ArchiveObject
from configuration.models import ESSConfig, ESSProc, ArchivePolicy, StorageTargets
from Storage.models import IOQueue
from django.db.models import Q
from django import db
from django.utils import timezone
from StorageMethodDisk.tasks import WriteStorageMethodDisk
from StorageMethodTape.tasks import WriteStorageMethodTape
from Storage.tasks import TransferWriteIO
from essarch.libs import ESSArchSMError
from celery.result import AsyncResult
import requests
from rest_framework.renderers import JSONRenderer
from urlparse import urljoin
from api.serializers import ArchiveObjectPlusAICPlusStorageNestedReadSerializer
from retrying import retry

# Disable https insecure warnings
from requests.packages.urllib3.exceptions import InsecureRequestWarning, InsecurePlatformWarning
requests.packages.urllib3.disable_warnings(InsecurePlatformWarning)
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import django
django.setup()

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

class StorageMethodWrite:
    tz = timezone.get_default_timezone()
    def __init__(self):
        # Configuration values
        self.ArchiveObject_objs = []     # ArchiveObjects to write
        self.TempPath = ''                   # Rootpath for IPs
        self.target_list = []                   # Only write to specified targets. If not defined default is to write all targets in archivepolicy
        self.force_write_flag = 0          # Force to write to targets even if the total size of objects is less then minChunkSize in archivepolicy
        self.retry_write_flag = 0           # Flag to retry failed write jobs
        self.retry_transfer_flag = 0       # Flag to retry failed transfer jobs
        self.exitFlag = 0                      # Flag to stop writes

        # Result status flags
        self.all_writes_ok_flag = 0        # If this flag is True, all writes is done for all objects in self.ArchiveObjects_objs
        self.pending_write_flag = 0       # If this flag is True, pending writes exists for current object in self.ArchiveObjects_objs
        self.progress_write_flag = 0      # If this flag is True, progress writes exists for current object in self.ArchiveObjects_objs
        self.fail_write_flag = 0              # If this flag is True, failed writes exists for current object in self.ArchiveObjects_objs
        self.object_writes_ok_flag = 0  # If this flag is True, all writes i done for current object in self.ArchiveObjects_objs

        # Default values 
        self.IOs_to_write = {}
        self.IOs_to_transfer = {}
        self.st_objs_to_check = {}
        self.ActiveTapeIOs = []
        self.logger = logging.getLogger('Storage')
        self.AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
        self.ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)
        if self.ExtDBupdate:
            self.ext_IngestTable = 'IngestObject'
        else:
            self.ext_IngestTable = ''
            
    def add_to_ioqueue(self):
        ArchiveObjects_objs_SizeSum = sum(i[0] for i in self.ArchiveObject_objs.values_list('ObjectSize'))
        self.IOs_to_write = {}
        self.IOs_to_transfer = {}
        self.st_objs_to_check = {}
        for ArchiveObject_obj in self.ArchiveObject_objs:
            
            ArchivePolicy_obj = ArchiveObject_obj.PolicyId #ArchivePolicy.objects.filter(PolicyStat=1)
            if not ArchivePolicy_obj.PolicyStat == 1:
                continue

            if self.TempPath:
                TempPath = self.TempPath
            else:
                TempPath = ArchivePolicy_obj.AIPpath
            
            sm_objs = ArchivePolicy_obj.storagemethod_set.filter(status=1)
            for sm_obj in sm_objs:
                st_objs = sm_obj.storagetarget_set.filter(status=1)
                if st_objs.count() == 1:
                    st_obj = st_objs[0]
                elif st_objs.count() == 0:
                    self.logger.error('The storage method %s has no enabled target configured' % sm_obj.name)
                    continue
                elif st_objs.count() > 1:
                    self.logger.error('The storage method %s has too many targets configured with the status enabled' % sm_obj.name)
                    continue
                if st_obj.target.status == 1:
                    target_obj = st_obj.target
                    remote_server = target_obj.remote_server.split(',')
                    if len(remote_server) == 3:
                        remote_status = 0
                    else:
                        remote_status = 20
                else:
                    self.logger.error('The target %s is disabled' % st_obj.target.name)
                    continue
                
                # if self.target_list is defined, only add write jobs for target in self.target_list
                if self.target_list:                    
                    if not target_obj.target in self.target_list:
                        self.logger.info('Skip to add target: %s to IOQueue therefore target: %s is not defined in target_list: %s' % (target_obj.target, 
                                                                                                                                                                            target_obj.target, 
                                                                                                                                                                            self.target_list))
                        continue
                
                # append st_obj to list per ArchiveObject_obj dict. This dict is used to verify writes status
                if not self.st_objs_to_check.has_key(ArchiveObject_obj):
                    self.st_objs_to_check[ArchiveObject_obj] = []
                self.st_objs_to_check[ArchiveObject_obj].append(st_obj)

                # set sm_minChunkSize_flag if the SizeSum for objects is larger then minChunkSize in archivepolicy
                if target_obj.minChunkSize < ArchiveObjects_objs_SizeSum:
                    sm_minChunkSize_flag = 1
                else:
                    sm_minChunkSize_flag = 0

                self.logger.info('PolicyId: %s, StorageMethod: %s, Flags (min: %s, force: %s, retry: %s), minChunkSize: %s, ObjectsSizeSum: %s' % (ArchivePolicy_obj.PolicyID, 
                                                                                                                                                                                                                sm_obj.name, 
                                                                                                                                                                                                                sm_minChunkSize_flag,
                                                                                                                                                                                                                self.force_write_flag,
                                                                                                                                                                                                                self.retry_write_flag,
                                                                                                                                                                                                                target_obj.minChunkSize, 
                                                                                                                                                                                                                ArchiveObjects_objs_SizeSum))
                
                if target_obj.type in range(300,330): 
                    ReqType = 10
                    ReqPurpose=u'Write package to tape'
                elif target_obj.type in range(200,201):
                    ReqType = 15
                    ReqPurpose=u'Write package to disk'
            
                IOQueue_objs = IOQueue.objects.filter(archiveobject=ArchiveObject_obj, storagemethodtarget=st_obj)
                if not IOQueue_objs.exists():     
                    IOQueue_obj = IOQueue()
                    IOQueue_obj.ReqType=ReqType
                    IOQueue_obj.ReqPurpose=ReqPurpose
                    IOQueue_obj.user=u'sys'
                    IOQueue_obj.ObjectPath=TempPath
                    IOQueue_obj.Status=0
                    IOQueue_obj.archiveobject=ArchiveObject_obj
                    IOQueue_obj.storagemethodtarget=st_obj
                    IOQueue_obj.remote_status=remote_status
                    IOQueue_obj.save()
                    self.logger.info('Add WriteReq with target type: %s for object: %s (IOuuid: %s)' % (target_obj.type, 
                                                                                                        ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                        IOQueue_obj.id))
                    if not self.target_list:
                        ArchiveObject_obj.StatusProcess = 1000
                        ArchiveObject_obj.save(update_fields=['StatusProcess']) 
                elif IOQueue_objs.count() > 1:
                    self.logger.error('More then one WriteReq with target type: %s for object: %s exists (IOuuid: %s)' % (target_obj.type, 
                                                                                                                          ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                          IOQueue_obj.id))
                else:
                    IOQueue_obj = IOQueue_objs[0]
                
                if (IOQueue_obj.Status in [2, 5] and        # if task_id failed and status is set to "OK" in GUI then set task_id='' and Status=100
                         IOQueue_obj.task_id and
                         ArchiveObject_obj.StatusProcess == 1000 and 
                         ArchiveObject_obj.StatusActivity == 0):
                    result = AsyncResult(IOQueue_obj.task_id)
                    self.logger.info('Statusresult=%s for task_id: %s for object: %s (IOuuid: %s)' % (result.status, 
                                                                                                                                         IOQueue_obj.task_id,
                                                                                                                                         ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                                         IOQueue_obj.id ))
                    if result.ready() and result.failed():
                        self.logger.error('task_id: %s failed for object: %s, setting task_id to blank and Status=100 in IOqueue, traceback: %s (IOuuid: %s)' % (IOQueue_obj.task_id,
                                                                                                                                         ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                                         result.traceback,
                                                                                                                                         IOQueue_obj.id))
                        IOQueue_obj.task_id = ''
                        IOQueue_obj.Status = 100
                        IOQueue_obj.save(update_fields=['task_id', 'Status'])
                        
                if (IOQueue_obj.remote_status in [2, 5] and        # if transfer task_id failed and status is set to "OK" in GUI then set task_id='' and Status=100
                         IOQueue_obj.transfer_task_id and
                         ArchiveObject_obj.StatusProcess == 1000 and 
                         ArchiveObject_obj.StatusActivity == 0):
                    result = AsyncResult(IOQueue_obj.transfer_task_id)
                    self.logger.info('Statusresult=%s for transfer task_id: %s for object: %s (IOuuid: %s)' % (result.status, 
                                                                                                                                         IOQueue_obj.transfer_task_id,
                                                                                                                                         ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                                         IOQueue_obj.id ))
                    if result.ready() and result.failed():
                        self.logger.error('transfer task_id: %s failed for object: %s, setting transfer task_id to blank and Status=100 in IOqueue, traceback: %s (IOuuid: %s)' % (IOQueue_obj.transfer_task_id,
                                                                                                                                         ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                                         result.traceback,
                                                                                                                                         IOQueue_obj.id))
                        IOQueue_obj.transfer_task_id = ''
                        IOQueue_obj.remote_status = 100
                        IOQueue_obj.save(update_fields=['transfer_task_id', 'remote_status'])
                
                # append IOQueue_obj to list per remote_target dict and ArchiveObject_obj dict. This dicts is used as a list of objects to transfer to remote.
                if (IOQueue_obj.Status == 0 and           # normal add to IOs_to_transfer list
                        IOQueue_obj.remote_status == 0) or \
                        (IOQueue_obj.Status == 0 and      # add to IOs_to_transfer list if transfer_task_id is blank
                        IOQueue_obj.remote_status == 2 and
                        IOQueue_obj.transfer_task_id == '') or \
                        (IOQueue_obj.Status == 0 and       # if transfer job failed, add to IOs_to_transfer list if retry_transfer_flag
                         IOQueue_obj.Status > 21 and         
                        self.retry_transfer_flag == 1) or \
                        (IOQueue_obj.Status == 0 and       # if transfer job failed, add to IOs_to_transfer list if status is set to "OK" in GUI.
                         IOQueue_obj.remote_status > 21 and
                         ArchiveObject_obj.StatusProcess == 1000 and 
                         ArchiveObject_obj.StatusActivity == 0):
                    IOQueue_obj.remote_tatus=2
                    IOQueue_obj.save(update_fields=['remote_status'])
                    if not self.IOs_to_transfer.has_key(remote_server[0]):
                        self.IOs_to_transfer[remote_server[0]] = {}
                    if not self.IOs_to_transfer[remote_server[0]].has_key(ArchiveObject_obj):
                        self.IOs_to_transfer[remote_server[0]][ArchiveObject_obj] = []
                    self.IOs_to_transfer[remote_server[0]][ArchiveObject_obj].append(IOQueue_obj)                
                
                # append IOQueue_obj to list per st_obj dict. This dict is used as a list of objects to apply for write.
                if (IOQueue_obj.Status == 0 and             # normal add to IOs_to_write list if minChunkSize_flag
                        sm_minChunkSize_flag == 1 and
                        IOQueue_obj.remote_status == 20) or \
                        (IOQueue_obj.Status == 2 and        # add to IOs_to_write list if task_id is blank
                        IOQueue_obj.task_id == '') or \
                        (IOQueue_obj.Status == 0 and        # add  to IOs_to_write list if force_write_flag
                        IOQueue_obj.remote_status == 20 and
                        self.force_write_flag == 1) or \
                        (IOQueue_obj.Status > 21 and        # if IO job failed, add to IOs_to_write list if retry_write_flag 
                        self.retry_write_flag == 1) or \
                        (IOQueue_obj.Status > 21 and        # if IO job failed, add to IOs_to_write list if status is set to "OK" in GUI.
                         ArchiveObject_obj.StatusProcess == 1000 and 
                         ArchiveObject_obj.StatusActivity == 0):
                    IOQueue_obj.Status=2
                    IOQueue_obj.save(update_fields=['Status'])
                    if not self.IOs_to_write.has_key(st_obj):
                        self.IOs_to_write[st_obj] = []
                    self.IOs_to_write[st_obj].append(IOQueue_obj)

    def apply_ios_to_transfer(self):
        '''Apply all IOs to transfer
        
        '''
        for remote_host, ArchiveObject_obj_dict in self.IOs_to_transfer.iteritems():
            for ArchiveObject_obj, IOQueue_obj_list in ArchiveObject_obj_dict.iteritems():
                for IOQueue_obj in IOQueue_obj_list:
                    # transfer IOQueue_obj to remote_host
                    result = TransferWriteIO().apply_async((IOQueue_obj.id,), queue='default')
                    IOQueue_obj.transfer_task_id = result.task_id
                    IOQueue_obj.save(update_fields=['transfer_task_id'])
                    self.logger.info('Apply new transfer writeIO process for IOQueue_obj: %s with transfer_task: %s' % (
                                                                                                                        IOQueue_obj.id, 
                                                                                                                        IOQueue_obj.transfer_task_id))
                    
                    #print 'remote: %s, ip: %s, IOs: %s' % (remote_host, ip_obj, repr(io_list))
            
    def apply_ios_to_write(self):
        '''Apply all IOs to write
        
        '''              
        self.ActiveTapeIOs = [i[0] for i in IOQueue.objects.filter(ReqType=10, Status__lt=100, Status__gt=2).order_by('storagemethodtarget__target__id').values_list('storagemethodtarget__target__id').distinct()]                          
        for st_obj, IOQueue_obj_list in self.IOs_to_write.iteritems():
            target_obj = st_obj.target
            remote_server = target_obj.remote_server.split(',')
            if len(remote_server) == 3:
                remote_io = True
            else:         
                remote_io = False
                
            if target_obj.type in range(300,330): 
                ReqType = 10
                ReqPurpose=u'Write package to tape'
                #ReadTapeIO_flag = IOQueue.objects.filter(ReqType=20, Status__lt=20).exists()
                ArchiveObject_objs_ObjectUUID_list = [i.archiveobject.ObjectUUID for i in IOQueue_obj_list]
                IOQueue_objs_id_list = [i.id for i in IOQueue_obj_list]
                #if not target_obj.id in self.ActiveTapeIOs and not ReadTapeIO_flag:
                if not target_obj.id in self.ActiveTapeIOs:
                    if remote_io:
                        result = WriteStorageMethodTape().remote_write_tape_apply_async(remote_server, 
                                                                               IOQueue_objs_id_list, 
                                                                               ArchiveObject_objs_ObjectUUID_list,
                                                                               queue='smtape')
                    else:
                        result = WriteStorageMethodTape().apply_async((IOQueue_objs_id_list,), queue='smtape')
                    self.ActiveTapeIOs.append(target_obj.id)
                    ActiveTapeIOs_str = ', '.join([i.target for i in StorageTargets.objects.filter(id__in=self.ActiveTapeIOs)])
                    self.logger.info('Apply new write IO process for tape prefix: %s, (ActiveTapeIOs: %s)' % (target_obj.target, ActiveTapeIOs_str))         
                    for  IOQueue_obj in IOQueue_obj_list:
                        IOQueue_obj.task_id = result.task_id
                        IOQueue_obj.save(update_fields=['task_id'])
                else:
                    #if ReadTapeIO_flag:
                    #    self.logger.debug('Read requests from tape exists, skip to add write request for IOuuid: %s' % IOQueue_objs_id_list)
                    if target_obj.id in self.ActiveTapeIOs:
                        self.logger.info('Active write IOs for target name: %s exists, skip to add write request for IOuuid: %s' % (target_obj.name, IOQueue_objs_id_list))                        
            elif target_obj.type in range(200,201):
                ReqType = 15
                ReqPurpose=u'Write package to disk'
                for  IOQueue_obj in IOQueue_obj_list:
                    if remote_io:
                        result = WriteStorageMethodDisk().remote_write_tape_apply_async(remote_server, 
                                                                               IOQueue_obj.id, 
                                                                               IOQueue_obj.archiveobject.ObjectUUID,
                                                                               queue='smdisk')
                    else:
                        result = WriteStorageMethodDisk().apply_async((IOQueue_obj.id,), queue='smdisk')
                    IOQueue_obj.task_id = result.task_id
                    IOQueue_obj.save(update_fields=['task_id'])
    
    def wait_for_all_writes(self):
        '''Wait for all writes is done to all Storage Methods for AIPs
        
        '''
        self.all_writes_ok_flag = 0
        while self.all_writes_ok_flag == 0:
            all_writes_ok_flag = 1        
            all_pending_write_flag = 0 
            for ArchiveObject_obj in self.ArchiveObject_objs:
                try:
                    self.get_write_status(ArchiveObject_obj)
                    if self.target_list:
                        self.handle_migration_write_status(ArchiveObject_obj)
                    else:
                        self.handle_write_status(ArchiveObject_obj)
                    if self.object_writes_ok_flag == 0:
                        all_writes_ok_flag = 0
                    if self.pending_write_flag == 1:
                        all_pending_write_flag = 1
                except ESSArchSMError as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Problem to write object %s to tape, error: %s line: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, exc_traceback.tb_lineno)
                    self.logger.error(msg)
                    all_writes_ok_flag = 0
                    raise e
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Unknown error to write object %s to tape, error: %s trace: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)))
                    self.logger.error(msg)
                    all_writes_ok_flag = 0
                    raise e
            if all_writes_ok_flag == 1:            # if all writes is done flag self.all_writes_ok_flag to 1 and exit loop
                self.all_writes_ok_flag = 1
            else:
                self.logger.debug('sleep 5 sec')
                time.sleep(5)
            if all_pending_write_flag == 1:      # if some of the objects is pending try to add and apply object
                self.add_to_ioqueue()
                self.apply_ios_to_write()                
            if self.exitFlag:
                break
            
    def get_write_status(self, ArchiveObject_obj):        
        error_flag = 0
        error_list = []
        self.pending_write_flag = 0
        self.progress_write_flag = 0
        self.fail_write_flag = 0
        self.object_writes_ok_flag = 0
        object_writes_ok_flag = 1
        if not error_flag:
            IOQueue_objs = ArchiveObject_obj.ioqueue_set.filter(ReqType__in=[10, 15])
            for IOQueue_obj in  IOQueue_objs:
                if not IOQueue_obj.storagemethodtarget in self.st_objs_to_check[ArchiveObject_obj]:                            
                    error_flag = 1
                    msg = 'There are unknown write requests to the storage target: %s for object: %s (IOuuid: %s)' % (
                                                                                                                      IOQueue_obj.storagemethodtarget.name, 
                                                                                                                      ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                      IOQueue_obj.id)
                    self.logger.error(msg)
                    error_list.append(msg)
        if not error_flag:
            st_objs_in_IOQueue = [i.storagemethodtarget for i in IOQueue_objs]
            self.st_names_in_IOQueue = [i.name for i in st_objs_in_IOQueue]
            for st_obj_to_check in self.st_objs_to_check[ArchiveObject_obj]:
                if not st_obj_to_check in st_objs_in_IOQueue:
                    error_flag = 1
                    msg = 'There is no write requests to the storage target: %s for object: %s, storagetarget_list: %s' % (
                                                                                                                                    st_obj_to_check.name, 
                                                                                                                                    ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                                    self.st_names_in_IOQueue)
                    self.logger.error(msg)
                    error_list.append(msg)
        if not error_flag and self.target_list:
            target_list_in_IOQueue = [i.storagemethodtarget.target.target for i in IOQueue_objs]
            for target_item in  self.target_list:
                if not target_item in  target_list_in_IOQueue:
                    error_flag = 1
                    msg = 'There is no write requests to the storage target: %s for object: %s, target_list: %s' % (
                                                                                                                    target_item, 
                                                                                                                    ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                    self.target_list)
                    self.logger.error(msg)
                    error_list.append(msg)
        if not error_flag:
            all_storage_objs = ArchiveObject_obj.Storage_set.all()
            all_storage_target_objs = [i.storagemedium.storagetarget for i in all_storage_objs]
            
            remote_io = False
            for IOQueue_obj in IOQueue_objs:
                if IOQueue_obj.Status == 0:
                    self.pending_write_flag = 1
                    object_writes_ok_flag = 0
                    event_info = 'Pending to write object: %s to storage target: %s (IOuuid: %s)' % (
                                                                                                     ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                     IOQueue_obj.storagemethodtarget.name, 
                                                                                                     IOQueue_obj.id)
                    self.logger.info(event_info)
                elif IOQueue_obj.Status < 20:
                    self.progress_write_flag = 1
                    object_writes_ok_flag = 0
                    event_info = 'Progress to write object: %s to storage target: %s (IOuuid: %s)' % (
                                                                                                      ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                      IOQueue_obj.storagemethodtarget.name, 
                                                                                                      IOQueue_obj.id)
                    self.logger.info(event_info)
                elif IOQueue_obj.Status > 21:
                    self.fail_write_flag = 1
                    object_writes_ok_flag = 0
                    event_info = 'Failed to write object: %s to storage target: %s (IOuuid: %s)' % (
                                                                                                    ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                    IOQueue_obj.storagemethodtarget.name, 
                                                                                                    IOQueue_obj.id)                                
                    self.logger.error(event_info)
                    ESSPGM.Events().create('1100','',self.__name__,__version__,'1',event_info,2,ArchiveObject_obj.ObjectIdentifierValue)
                elif IOQueue_obj.Status == 20:
                    if not IOQueue_obj.storagemethodtarget.target in all_storage_target_objs:
                        self.fail_write_flag = 1
                        object_writes_ok_flag = 0
                        event_info = 'There is no storage entry in the database for the storage target: %s for object: %s (IOuuid: %s)' % (
                                                                                                                                           IOQueue_obj.storagemethodtarget.name, 
                                                                                                                                           ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                                           IOQueue_obj.id)
                        self.logger.error(event_info)
                    elif not IOQueue_obj.storage in all_storage_objs:
                        event_info = 'Storage entry id: %s in the database have no relationship to objects: %s (IOuuid: %s)' % (
                                                                                                                                IOQueue_obj.storage.id, 
                                                                                                                                ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                                IOQueue_obj.id)
                        self.logger.error(event_info)
                    else:
                        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                        storageMedium_obj = IOQueue_obj.storagemedium
                        storageMedium_obj.storageMediumUsedCapacity = storageMedium_obj.storageMediumUsedCapacity + int(IOQueue_obj.result.get('WriteSize'))
                        storageMedium_obj.linkingAgentIdentifierValue = self.AgentIdentifierValue
                        storageMedium_obj.storageMediumDate = timestamp_utc
                        storageMedium_obj.LocalDBdatetime = timestamp_utc
                        storageMedium_obj.save(update_fields=['storageMediumUsedCapacity','storageMediumDate','linkingAgentIdentifierValue','LocalDBdatetime'])
                        if self.ExtDBupdate:
                            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumUsedCapacity',storageMedium_obj.storageMediumUsedCapacity,
                                                                                                            'storageMediumDate',storageMedium_obj.storageMediumDate.astimezone(self.tz).replace(tzinfo=None),
                                                                                                            'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue),
                                                                                                           ('storageMediumID',storageMedium_obj.storageMediumID))
                            if ext_errno: self.logger.error('Failed to update External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                            else:
                                storageMedium_obj.ExtDBdatetime = storageMedium_obj.LocalDBdatetime
                                storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                                
                        # Update remote server
                        target_obj = IOQueue_obj.storagemethodtarget.target
                        remote_server = target_obj.remote_server.split(',')
                        if len(remote_server) == 3:
                            try:
                                self._update_remote_archiveobject(remote_server, ArchiveObject_obj)
                            except DatabasePostRestError as e:
                                self.logger.error('Failed to update remote DB status for AIP: %s, error: %s' % (
                                                                                                                ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                e))

                        event_info = 'Succeeded to write object: %s to storage target: %s (IOuuid: %s)' % (
                                                                                                           ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                           IOQueue_obj.storagemethodtarget.name, 
                                                                                                           IOQueue_obj.id)                            
                        self.logger.info(event_info)
                        ESSPGM.Events().create('1101', '', self.__name__, __version__, '0', event_info, 2, ArchiveObject_obj.ObjectIdentifierValue)
                        if object_writes_ok_flag:
                            IOQueue_obj.Status = 21
                            IOQueue_obj.save(update_fields=['Status'])
                    if len(all_storage_target_objs) < len(self.st_objs_to_check[ArchiveObject_obj]):
                        object_writes_ok_flag = 0
                        event_info = 'There are fewer storage entrys in the database (%s) of object: %s than is configured in the archive policy (%s)' % (
                                                                                                                                                          len(all_storage_target_objs), 
                                                                                                                                                          ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                                                          len(self.st_objs_to_check))
                        self.logger.debug(event_info)

            if error_flag:
                raise ESSArchSMError(error_list)
            elif object_writes_ok_flag == 1:
                self.object_writes_ok_flag = 1
        
    def handle_migration_write_status(self, ArchiveObject_obj):
        if self.fail_write_flag:
            pass
        elif self.pending_write_flag:
            pass
        elif self.progress_write_flag:
            pass
        elif self.object_writes_ok_flag:      
            event_info = 'Succeeded to write object: %s to all Storage targets: %s' % (ArchiveObject_obj.ObjectIdentifierValue, self.st_names_in_IOQueue)
            self.logger.info(event_info)
            ESSPGM.Events().create('1100','',self.__name__,__version__,'0',event_info,2,ArchiveObject_obj.ObjectIdentifierValue)
            IOQueue_objs = ArchiveObject_obj.ioqueue_set.filter(ReqType__in=[10, 15])
            # Delete IOQueue_objs for ArchiveObject
            IOQueue_objs.delete()
                
    def handle_write_status(self, ArchiveObject_obj):
        if self.fail_write_flag:
            errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', self.ext_IngestTable, self.AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 4)
            if errno: self.logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
        elif self.pending_write_flag:
            errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', self.ext_IngestTable, self.AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 6)
            if errno: self.logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
        elif self.progress_write_flag:
            errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', self.ext_IngestTable, self.AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 5)
            if errno: self.logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
        elif self.object_writes_ok_flag:      
            errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', self.ext_IngestTable, self.AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1999, 0)
            if errno: self.logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
            event_info = 'Succeeded to write object: %s to all Storage targets: %s' % (ArchiveObject_obj.ObjectIdentifierValue, self.st_names_in_IOQueue)
            self.logger.info(event_info)
            ESSPGM.Events().create('1100','',self.__name__,__version__,'0',event_info,2,ArchiveObject_obj.ObjectIdentifierValue)
            IOQueue_objs = ArchiveObject_obj.ioqueue_set.filter(ReqType__in=[10, 15])
            #################################
            # Complete Ingest Order
            IngestQueue_objs = IngestQueue.objects.filter( ObjectIdentifierValue=ArchiveObject_obj.ObjectIdentifierValue, Status=5 )[:1]
            if IngestQueue_objs:
                IngestQueue_obj = IngestQueue_objs.get()
                event_info = 'Succeeded to Ingest SIP with ObjectIdentifierValue: %s, ReqUUID: %s' % (IngestQueue_obj.ObjectIdentifierValue,IngestQueue_obj.ReqUUID)
                self.logger.info(event_info)
                ESSPGM.Events().create('1303',IngestQueue_obj.ReqPurpose,self.__name__,__version__,'0',event_info,2,IngestQueue_obj.ObjectIdentifierValue)
                IngestQueue_obj.Status = 20
                IngestQueue_obj.save()
            ##################################################################
            # notify_external_project
            ExtPrjTapedURL = ESSConfig.objects.get(Name='ExtPrjTapedURL').Value
            if len(ExtPrjTapedURL):
                self.notify_external_project(ArchiveObject_obj)          
            ##################################################################
            # notify_user (RECEIPT_EMAIL)      
            if ArchiveObject_obj.PolicyId.IngestMetadata == 1: # METS
                # Get SIP Content METS information
                RECEIPT_EMAIL = self.get_receipt_email(ArchiveObject_obj)
                if RECEIPT_EMAIL:
                    smtp_server = ESSConfig.objects.get(Name='smtp_server').Value
                    if smtp_server:         
                        email_from = ESSConfig.objects.get(Name='email_from').Value
                        self.logger.info('Sending receipt to email address: %s for AIP: %s' % (RECEIPT_EMAIL,ArchiveObject_obj.ObjectIdentifierValue))
                        ESSPGM.mail().send(email_from,RECEIPT_EMAIL,u'ESSArch receipt - object "%s" successfully archived!' % ArchiveObject_obj.ObjectIdentifierValue,u'Object "%s" was successfully archived and can now be accessed from ESSArch.\n\nPlease return to "ESSArch Client" and click on menu "Access" to access archived objects.' % self.ObjectIdentifierValue,smtp_server=smtp_server,smtp_timeout=30)
                    else:
                        self.logger.warning('smtp_server not configured, skip to send email receipt for AIP: %s' % ArchiveObject_obj.ObjectIdentifierValue)
                else:
                    self.logger.error('Missing receipt email address for AIP: %s' % ArchiveObject_obj.ObjectIdentifierValue)
            
            # Delete IOQueue_objs on remote server  
            for IOQueue_obj in IOQueue_objs:
                target_obj = IOQueue_obj.storagemethodtarget.target
                remote_server = target_obj.remote_server.split(',')
                if len(remote_server) == 3:
                    try:
                        self._delete_remote_IOQueue_obj(remote_server, IOQueue_obj)
                    except DatabasePostRestError as e:
                        self.logger.error('Failed to delete IOQueue_obj %s from remote DB for AIP: %s, error: %s' % (
                                                                                                                     IOQueue_obj.id, 
                                                                                                                     ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                     e))
            # Delete IOQueue_objs for ArchiveObject
            IOQueue_objs.delete()
    
    @retry(wait_fixed=60000)
    def _update_remote_archiveobject(self, remote_server, ArchiveObject_obj):
        """ Call REST service on remote to update ArchiveObject with nested storage, storageMedium
        
        :param remote_server: example: [https://servername:port, user, password]
        :param ArchiveObject_obj: ArchiveObject database instance to be performed
        
        """
        base_url, ruser, rpass = remote_server
        ArchiveObject_rest_endpoint_base = urljoin(base_url, '/api/archiveobjectsandstorage/')
        ArchiveObject_rest_endpoint = urljoin(ArchiveObject_rest_endpoint_base, '%s/' % str(ArchiveObject_obj.ObjectUUID))
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        ArchiveObject_obj_data = ArchiveObjectPlusAICPlusStorageNestedReadSerializer(ArchiveObject_obj).data
        # Set StatusProcess and StatusActivity
        ArchiveObject_obj_data['StatusProcess'] = 1999        # 'Write AIP OK'
        ArchiveObject_obj_data['StatusActivity'] = 0              # 'OK'
        # Remove local disk storage type 200 from Storage_set
        exclude_targets = [i.id for i in StorageTargets.objects.filter(type=200, remote_server='')]
        new_Storage_set = []
        for storage_data in ArchiveObject_obj_data['Storage_set']:
            if not storage_data['storagemedium']['storagetarget'] in exclude_targets:
                new_Storage_set.append(storage_data)
        ArchiveObject_obj_data['Storage_set'] = new_Storage_set
        # JSONRenderer
        ArchiveObject_obj_json = JSONRenderer().render(ArchiveObject_obj_data)
        r = requests_session.patch(ArchiveObject_rest_endpoint,
                                        headers={'Content-Type': 'application/json'}, 
                                        data=ArchiveObject_obj_json)
        if not r.status_code == 200:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to update remote server status for AIP, storage, storageMedium for object %s, error: %s' % (
                                                                                                                          ArchiveObject_obj.ObjectIdentifierValue,
                                                                                                                          e)
            self.logger.warning(msg)
            raise DatabasePostRestError(e)

    @retry(stop_max_attempt_number=5, wait_fixed=60000)    
    def _delete_remote_IOQueue_obj(self, remote_server, IO_obj):
        """ Call REST service on remote to remove IOQueue object
        
        :param remote_server: example: [https://servername:port, user, password]
        :param IO_obj: IOQueue database instance to be performed
        
        """
        base_url, ruser, rpass = remote_server
        IOQueue_rest_endpoint_base = urljoin(base_url, '/api/ioqueue/')
        IOQueue_rest_endpoint = urljoin(IOQueue_rest_endpoint_base, '%s/' % str(IO_obj.id))
        requests_session = requests.Session()
        requests_session.verify = False
        requests_session.auth = (ruser, rpass)
        r = requests_session.delete(IOQueue_rest_endpoint)
        if not r.status_code == 204:
            e = [r.status_code, r.reason, r.text]
            msg = 'Problem to delete IOQueue object on remote server for object %s, error: %s (IOuuid: %s)' % (
                                                                                                              IO_obj.archiveobject.ObjectIdentifierValue,
                                                                                                              e,
                                                                                                              IO_obj.id)
            self.logger.warning(msg)
            raise DatabasePostRestError(e)

    def notify_external_project(self, ArchiveObject_obj):
        IOQueue_objs = ArchiveObject_obj.ioqueue_set.filter(ReqType__in=[10])
        storage_objs_in_IOQueue_Type10 = [i.storage for i in IOQueue_objs]
        ObjectIdentifierValue = ArchiveObject_obj.ObjectIdentifierValue
        ExtPrjTapedURL = ESSConfig.objects.get(Name='ExtPrjTapedURL').Value
        url_params = urllib.urlencode({'object': str(ObjectIdentifierValue), 
                                        'tifnum': str(ArchiveObject_obj.DataObjectNumItems), 
                                        'tifsum': str(ArchiveObject_obj.DataObjectSize), 
                                        'date': str(datetime.datetime.today().strftime("%Y-%m-%d")), 
                                        'time': str(datetime.datetime.today().strftime("%H:%M:%S")),
                                        't_id1': str(storage_objs_in_IOQueue_Type10[0].storagemedium.storageMediumID),
                                        't_id2': str(storage_objs_in_IOQueue_Type10[1].storagemedium.storageMediumID),
                                        't_pos1': str(storage_objs_in_IOQueue_Type10[0].contentLocationValue),
                                        't_pos2': str(storage_objs_in_IOQueue_Type10[1].contentLocationValue)})
        #ExtPrjTapedURL = "http://212.181.19.10/web/svarfolder/admin/skanning/update_database.asp?%s"
        self.logger.info('Try to update ExtPrJDB with taped info: ' + str(ObjectIdentifierValue) + ' ExtPrjTapedURL: ' + str(ExtPrjTapedURL) + ' url_params: ' + str(url_params))
        try:
            url_conn_obj = urllib.urlopen('%s?%s %' % (ExtPrjTapedURL, url_params))
        except (IOError), (errno,why):
            self.logger.error('Problem to connect to URL: ' + str(ExtPrjTapedURL) + '?' + str(url_params) + ' Error: ' + str(why) + ' ' + str(errno))
        else:
            url_conn_obj_result = url_conn_obj.read()
            url_conn_obj.close()
            if re.search('OK ',url_conn_obj_result):
                self.logger.info('Success to update ExtPrJDB with taped info: ' + str(ObjectIdentifierValue) + ' cmdout: ' + str(url_conn_obj_result))
            else:
                self.logger.error('Problem to update ExtPrJDB with taped info: ' + str(ObjectIdentifierValue) + ' cmdout: ' + str(url_conn_obj_result))        
    
    def get_receipt_email(self, ArchiveObject_obj):
        # Get SIP Content METS information
        RECEIPT_EMAIL = ''
        Pmets_objpath = os.path.join(ArchiveObject_obj.PolicyId.AIPpath,ArchiveObject_obj.ObjectIdentifierValue + '_Package_METS.xml')
        res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=Pmets_objpath)
        for agent in res_info[2]:
            if agent[0] == 'PRESERVATION' and \
               agent[2] == 'OTHER' and \
               agent[3] == 'SOFTWARE' and \
               agent[4] == 'ESSArch':
                note = csv.reader(agent[5], delimiter='=')
                for i in note:
                    if i[0] == 'RECEIPT_EMAIL':
                        RECEIPT_EMAIL = i[1]
        return RECEIPT_EMAIL

    @property
    def __name__(self):
        return self.__class__.__name__
    
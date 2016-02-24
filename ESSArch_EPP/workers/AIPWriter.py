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

import os, thread, datetime, time, logging, sys, ESSPGM, ESSlogging, ESSMD, csv, ESSMSSQL, pytz, traceback

from essarch.models import IngestQueue, ArchiveObject
from configuration.models import ESSConfig, ESSProc, ArchivePolicy, StorageTargets
from Storage.models import IOQueue
from Storage.libs import StorageMethodWrite
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist
from django import db
from django.utils import timezone
from essarch.libs import ESSArchSMError

import django
django.setup()

#from StorageMethodDisk.tasks import WriteStorageMethodDisk
#from StorageMethodTape.tasks import WriteStorageMethodTape

class WorkingThread:
    tz = timezone.get_default_timezone()
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        ############################################################################
        try:
            PauseIngestWhenActiveWrites_flag = int(ESSConfig.objects.get(Name='PauseIngestWhenActiveWrites').Value)
        except ObjectDoesNotExist:
            PauseIngestWhenActiveWrites_flag = 1
        # Check if any active Write IO exist to set puase flags for ingest of new objects
        if IOQueue.objects.filter(ReqType__in=[10, 15], Status__in = [1,19]).exists() and PauseIngestWhenActiveWrites_flag:
            #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
            ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
        else:
            #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
            ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
        # Get active queue depth for self.TapeIOpool._cache.
        #TapeIOactv = len(self.TapeIOpool._cache)
        #TapeIOactv = 0
        #TapeReadIOtags = 4
        #TapeWriteIOtags = 2
        #ReadTapeIO_flag = 0
        #ActiveTapeIOs = [i[0] for i in IOQueue.objects.filter(ReqType=10).order_by('storagemethodtarget__target__id').values_list('storagemethodtarget__target__id').distinct()]
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            PauseTime, self.Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Run')[0]
            if self.Run == '0':
                logger.info('Stopping ' + ProcName)
                ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()
            if ExtDBupdate:
                ext_IngestTable = ESSConfig.objects.get(Name='IngestTable').Value
            else:
                ext_IngestTable = ''
            ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1)
            for ArchivePolicy_obj in ArchivePolicy_objs:
                if ESSProc.objects.get(Name=ProcName).Run == '0':
                    logger.info('Stopping ' + ProcName)
                    ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                    #thread.interrupt_main()
                    break
                PolicyID = ArchivePolicy_obj.PolicyID
                
                # new start
                ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = PolicyID),
                                                  Q(StatusProcess__range = [69,1000]),
                                                  Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                  )
                try:
                    StorageMethodWrite_obj = StorageMethodWrite()
                    StorageMethodWrite_obj.logger = logger
                    StorageMethodWrite_obj.ArchiveObject_objs = ArchiveObject_objs
                    StorageMethodWrite_obj.add_to_ioqueue()
                    StorageMethodWrite_obj.apply_ios_to_transfer()
                    StorageMethodWrite_obj.apply_ios_to_write()
                except ESSArchSMError as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Problem to write objects for policyID %s, error: %s line: %s' % (PolicyID, e, exc_traceback.tb_lineno)
                    logger.error(msg)
                except Exception as e:
                    exc_type, exc_value, exc_traceback = sys.exc_info()
                    msg = 'Unknown error to write objects for policyID %s, error: %s trace: %s' % (PolicyID, e, repr(traceback.format_tb(exc_traceback)))
                    logger.error(msg)
                for ArchiveObject_obj in ArchiveObject_objs:
                    try:
                        StorageMethodWrite_obj.get_write_status(ArchiveObject_obj)
                        StorageMethodWrite_obj.handle_write_status(ArchiveObject_obj)
                    except ESSArchSMError as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        msg = 'Problem to write object %s, error: %s line: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, exc_traceback.tb_lineno)
                        logger.error(msg)
                    except Exception as e:
                        exc_type, exc_value, exc_traceback = sys.exc_info()
                        msg = 'Unknown error to write object %s, error: %s trace: %s' % (ArchiveObject_obj.ObjectIdentifierValue, e, repr(traceback.format_tb(exc_traceback)))
                        logger.error(msg)
                #new end
                
                '''
                TempPath = ArchivePolicy_obj.AIPpath
                IngestMetadata = ArchivePolicy_obj.IngestMetadata
                self.sm_num = 0
                self.sm_list = []
                logger.debug('Start to list objects to write to storage method for policyid: ' + str(PolicyID))
                sm_objs = ArchivePolicy_obj.storagemethod_set.filter(status=1)
                IOs_to_write = {}
                st_objs_to_check = []
                for sm_obj in sm_objs:
                    st_objs = sm_obj.storagetarget_set.filter(status=1)
                    if st_objs.count() == 1:
                        st_obj = st_objs[0]
                    elif st_objs.count() == 0:
                        logger.error('The storage method %s has no enabled target configured' % sm_obj.name)
                        break
                    elif st_objs.count() > 1:
                        logger.error('The storage method %s has too many targets configured with the status enabled' % sm_obj.name)
                        break
                    if st_obj.target.status == 1:
                        target_obj = st_obj.target
                    else:
                        logger.error('The target %s is disabled' % st_obj.target.name)
                        break
                    st_objs_to_check.append(st_obj)
                    ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = PolicyID),
                                                                      Q(StatusProcess__range = [69,1000]),
                                                                      Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                                      )
                    
                    ArchiveObjects_objs_SizeSum = sum(i[0] for i in ArchiveObject_objs.values_list('ObjectSize'))
                    if target_obj.minChunkSize < ArchiveObjects_objs_SizeSum:
                        sm_minChunkSize_flag = 1
                    else:
                        sm_minChunkSize_flag = 0
                    logging.info('PolicyId: %s, StorageMethod: %s, target_minChunkSize_flag: %s, target_minChunkSize: %s, ObjectsSizeSum: %s' % (PolicyID, sm_obj.name, sm_minChunkSize_flag, target_obj.minChunkSize, ArchiveObjects_objs_SizeSum))
                    self.numobjects = ArchiveObject_objs.count()
                    for ArchiveObject_obj in ArchiveObject_objs:
                        if ESSProc.objects.get(Name=ProcName).Run == '0':
                            logger.info('Stopping ' + ProcName)
                            ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                            #thread.interrupt_main()
                            time.sleep(10)
                            break
                        
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
                            IOQueue_obj.save()
                            logger.info('Add WriteReq with target type: %s for object: %s (IOuuid: %s)' % (target_obj.type, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id))
                            ArchiveObject_obj.StatusProcess = 1000
                            ArchiveObject_obj.save(update_fields=['StatusProcess']) 
                        elif IOQueue_objs.count() > 1:
                            logger.error('More then one WriteReq with target type: %s for object: %s exists (IOuuid: %s)' % (target_obj.type, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id))
                        else:
                            IOQueue_obj = IOQueue_objs[0]
                            
                        if (IOQueue_obj.Status == 0 and 
                                sm_minChunkSize_flag == 1) or \
                                (ArchiveObject_obj.StatusProcess == 1000 and 
                                 ArchiveObject_obj.StatusActivity == 0 and 
                                 IOQueue_obj.Status > 21):
                            IOQueue_obj.Status=2
                            IOQueue_obj.save(update_fields=['Status'])
                            if not IOs_to_write.has_key(st_obj):
                                IOs_to_write[st_obj] = []
                            IOs_to_write[st_obj].append(IOQueue_obj)

                ############################################################
                # Apply all IOs to write                                        
                for st_obj, IOQueue_obj_list in IOs_to_write.iteritems():
                    target_obj = st_obj.target             
                    
                    if target_obj.type in range(300,330): 
                        ReqType = 10
                        ReqPurpose=u'Write package to tape'
                        ReadTapeIO_flag = IOQueue.objects.filter(ReqType=20, Status__lt=20).exists()
                        if not target_obj.id in ActiveTapeIOs and not ReadTapeIO_flag:
                            IOQueue_objs_id_list = [i.id for i in IOQueue_obj_list]
                            result = WriteStorageMethodTape().apply_async((IOQueue_objs_id_list,), queue='smtape')
                            ActiveTapeIOs.append(target_obj.id)
                            ActiveTapeIOs_str = ', '.join([i.target for i in StorageTargets.objects.filter(id__in=ActiveTapeIOs)])
                            logger.info('Apply new write IO process for tape prefix: %s, (ActiveTapeIOs: %s)' % (target_obj.target, ActiveTapeIOs_str))         
                            for  IOQueue_obj in IOQueue_obj_list:
                                IOQueue_obj.task_id = result.task_id
                                IOQueue_obj.save(update_fields=['task_id'])
                        else:
                            if ReadTapeIO_flag:
                                logger.debug('Read requests from tape exists, wait to add write request for IOuuid: %s' % IOQueue_objs_id_list)
                            if target_obj.id in ActiveTapeIOs:
                                logger.debug('Active write IOs for target name: %s exists, skip to add write request for IOuuid: %s' % (target_obj.name, IOQueue_objs_id_list))                        
                    elif target_obj.type in range(200,201):
                        ReqType = 15
                        ReqPurpose=u'Write package to disk'
                        for  IOQueue_obj in IOQueue_obj_list:
                            result = WriteStorageMethodDisk().apply_async((IOQueue_obj.id,), queue='smdisk')
                            IOQueue_obj.task_id = result.task_id
                            IOQueue_obj.save(update_fields=['task_id'])

                ############################################################
                # Check if write is done to all Storage Methods for AIPs
                ArchiveObject_objs = ArchiveObject.objects.filter(Q(PolicyId__PolicyID = PolicyID),
                                                                  Q(StatusProcess = 1000),
                                                                  Q(StatusActivity = 0) | Q(StatusActivity__range = [5,6]),
                                                                  )

                for ArchiveObject_obj in ArchiveObject_objs:
                    if ESSProc.objects.get(Name=ProcName).Run == '0':
                        logger.info('Stopping ' + ProcName)
                        ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                        #thread.interrupt_main()
                        time.sleep(10)
                        break
                    
                    error_flag = 0
                    error_list = []
                    if not error_flag:
                        IOQueue_objs = ArchiveObject_obj.ioqueue_set.filter(ReqType__in=[10, 15])
                        for IOQueue_obj in  IOQueue_objs:
                            if not IOQueue_obj.storagemethodtarget in st_objs_to_check:                            
                                error_flag = 1
                                msg = 'There are unknown write requests to the storage target: %s for object: %s (IOuuid: %s)' % (IOQueue_obj.storagemethodtarget.name, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id)
                                logger.error(msg)
                                error_list.append(msg)
                    if not error_flag:
                        st_objs_in_IOQueue = [i.storagemethodtarget for i in IOQueue_objs]
                        st_names_in_IOQueue = [i.name for i in st_objs_in_IOQueue]
                        for st_obj_to_check in st_objs_to_check:
                            if not st_obj_to_check in st_objs_in_IOQueue:
                                error_flag = 1
                                msg = 'There is no write requests to the storage target: %s for object: %s (IOuuid: %s)' % (st_obj_to_check.name, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id)
                                logger.error(msg)
                                error_list.append(msg)
                    if not error_flag:
                        all_storage_objs = ArchiveObject_obj.Storage_set.all()
                        all_storage_target_objs = [i.storagemedium.storagetarget for i in all_storage_objs]
                        pending_write_flag = 0
                        progress_write_flag = 0
                        fail_write_flag = 0
                        all_writes_ok_flag = 1
                        for IOQueue_obj in IOQueue_objs:
                            if IOQueue_obj.Status == 0:
                                pending_write_flag = 1
                                all_writes_ok_flag = 0
                                event_info = 'Pending to write object: %s to storage target: %s (IOuuid: %s)' % (ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.storagemethodtarget.name, IOQueue_obj.id)
                                logger.info(event_info)
                            elif IOQueue_obj.Status < 20:
                                progress_write_flag = 1
                                all_writes_ok_flag = 0
                                event_info = 'Progress to write object: %s to storage target: %s (IOuuid: %s)' % (ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.storagemethodtarget.name, IOQueue_obj.id)
                                logger.info(event_info)
                            elif IOQueue_obj.Status > 21:
                                fail_write_flag = 1
                                all_writes_ok_flag = 0
                                event_info = 'Failed to write object: %s to storage target: %s (IOuuid: %s)' % (ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.storagemethodtarget.name, IOQueue_obj.id)                                
                                logger.error(event_info)
                                ESSPGM.Events().create('1100','','ESSArch AIPWriter',ProcVersion,'1',event_info,2,ArchiveObject_obj.ObjectIdentifierValue)
                            elif IOQueue_obj.Status == 20:
                                if not IOQueue_obj.storagemethodtarget.target in all_storage_target_objs:
                                    fail_write_flag = 1
                                    all_writes_ok_flag = 0
                                    event_info = 'There is no storage entry in the database for the storage target: %s for object: %s (IOuuid: %s)' % (IOQueue_obj.storagemethodtarget.name, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id)
                                    logger.error(event_info)
                                elif not IOQueue_obj.storage in all_storage_objs:
                                    event_info = 'Storage entry id: %s in the database have no relationship to objects: %s (IOuuid: %s)' % (IOQueue_obj.storage.id, ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.id)
                                    logger.error(event_info)
                                else:
                                    timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                    storageMedium_obj = IOQueue_obj.storagemedium
                                    storageMedium_obj.storageMediumUsedCapacity = storageMedium_obj.storageMediumUsedCapacity + int(IOQueue_obj.result.get('WriteSize'))
                                    storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                                    storageMedium_obj.storageMediumDate =timestamp_utc
                                    storageMedium_obj.LocalDBdatetime = timestamp_utc
                                    storageMedium_obj.save(update_fields=['storageMediumUsedCapacity','storageMediumDate','linkingAgentIdentifierValue','LocalDBdatetime'])
                                    if ExtDBupdate:
                                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumUsedCapacity',storageMedium_obj.storageMediumUsedCapacity,
                                                                                                                        'storageMediumDate',storageMedium_obj.storageMediumDate.astimezone(self.tz).replace(tzinfo=None),
                                                                                                                        'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue),
                                                                                                                       ('storageMediumID',storageMedium_obj.storageMediumID))
                                        if ext_errno: logger.error('Failed to update External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                                        else:
                                            storageMedium_obj.ExtDBdatetime = storageMedium_obj.LocalDBdatetime
                                            storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                                    event_info = 'Succeeded to write object: %s to storage target: %s (IOuuid: %s)' % (ArchiveObject_obj.ObjectIdentifierValue, IOQueue_obj.storagemethodtarget.name, IOQueue_obj.id)                            
                                    logger.info(event_info)
                                    ESSPGM.Events().create('1101', '', 'ESSArch AIPWriter', ProcVersion, '0', event_info, 2, ArchiveObject_obj.ObjectIdentifierValue)
                                    if all_writes_ok_flag:
                                        IOQueue_obj.Status = 21
                                        IOQueue_obj.save(update_fields=['Status'])
                                if not len(all_storage_target_objs) >= len(st_objs_to_check):
                                    all_writes_ok_flag = 0
                                    event_info = 'There are fewer storage entrys in the database (%s) of object: %s than is configured in the archive policy (%s)' % (len(all_storage_target_objs), ArchiveObject_obj.ObjectIdentifierValue, len(st_objs_to_check))
                                    logger.debug(event_info)
                                                                  
                    if not error_flag and fail_write_flag:
                        errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', ext_IngestTable, AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 4)
                        if errno: logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
                    elif not error_flag and pending_write_flag:
                        errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', ext_IngestTable, AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 6)
                        if errno: logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
                    elif not error_flag and progress_write_flag:
                        errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', ext_IngestTable, AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1000, 5)
                        if errno: logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
                    elif not error_flag and all_writes_ok_flag:      
                        errno,why = ESSPGM.DB().SetAIPstatus(u'IngestObject', ext_IngestTable, AgentIdentifierValue, ArchiveObject_obj.ObjectUUID, 1999, 0)
                        if errno == '08S01':
                            logger.warning('Failed to update central DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
                        elif errno:
                            logger.error('Failed to update DB status for AIP: ' + ArchiveObject_obj.ObjectIdentifierValue + ' error: ' + str(why))
                        event_info = 'Succeeded to write object: %s to all Storage targets: %s' % (ArchiveObject_obj.ObjectIdentifierValue, st_names_in_IOQueue)
                        logger.info(event_info)
                        ESSPGM.Events().create('1100','','ESSArch AIPWriter',ProcVersion,'0',event_info,2,ArchiveObject_obj.ObjectIdentifierValue)
                        #################################
                        # Complete Ingest Order
                        IngestQueue_objs = IngestQueue.objects.filter( ObjectIdentifierValue=ArchiveObject_obj.ObjectIdentifierValue, Status=5 )[:1]
                        if IngestQueue_objs:
                            IngestQueue_obj = IngestQueue_objs.get()
                            event_info = 'Succeeded to Ingest SIP with ObjectIdentifierValue: %s, ReqUUID: %s' % (IngestQueue_obj.ObjectIdentifierValue,IngestQueue_obj.ReqUUID)
                            logger.info(event_info)
                            ESSPGM.Events().create('1303',IngestQueue_obj.ReqPurpose,'ESSArch Ingest',ProcVersion,'0',event_info,2,IngestQueue_obj.ObjectIdentifierValue)
                            IngestQueue_obj.Status = 20
                            IngestQueue_obj.save()
                        ##################################################################
                        # Special solution for MKC projectDB feedback
                        UpdateExtPrjDB = 0
                        ExtPrjTapedURL = ESSConfig.objects.get(Name='ExtPrjTapedURL').Value
                        if ExtPrjTapedURL:
                            if len(ExtPrjTapedURL[0][0]):
                                UpdateExtPrjDB = 1
                        if UpdateExtPrjDB:
                            storage_objs_in_IOQueue_Type10 = [i.storage for i in IOQueue_objs.filter(ReqType=10)]
                            # Update ExtPrjDB
                            date_str = datetime.datetime.today().strftime("%Y-%m-%d")
                            time_str = datetime.datetime.today().strftime("%H:%M:%S")
                            if len(storage_objs_in_IOQueue_Type10) >= 2:
                                m1_mediaID = storage_objs_in_IOQueue_Type10[0].storagemedium.storageMediumID
                                m1_location = storage_objs_in_IOQueue_Type10[0].contentLocationValue
                                m2_mediaID = storage_objs_in_IOQueue_Type10[1].storagemedium.storageMediumID
                                m2_location = storage_objs_in_IOQueue_Type10[1].contentLocationValue
                                ESSPGM.ExtPrjDB().taped(ArchiveObject_obj.ObjectIdentifierValue,ArchiveObject_obj.DataObjectNumItems,ArchiveObject_obj.DataObjectSize,date_str,time_str, m1_mediaID, m2_mediaID, m1_location, m2_location)                         
                        if IngestMetadata == 1: # METS
                            # Get SIP Content METS information
                            RECEIPT_EMAIL = ''
                            Pmets_objpath = os.path.join(TempPath,ArchiveObject_obj.ObjectIdentifierValue + '_Package_METS.xml')
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
                            if RECEIPT_EMAIL:
                                smtp_server = ESSConfig.objects.get(Name='smtp_server').Value
                                if smtp_server:         
                                    email_from = ESSConfig.objects.get(Name='email_from').Value
                                    logger.info('Sending receipt to email address: %s for AIP: %s' % (RECEIPT_EMAIL,ArchiveObject_obj.ObjectIdentifierValue))
                                    ESSPGM.mail().send(email_from,RECEIPT_EMAIL,u'ESSArch receipt - object "%s" successfully archived!' % ArchiveObject_obj.ObjectIdentifierValue,u'Object "%s" was successfully archived and can now be accessed from ESSArch.\n\nPlease return to "ESSArch Client" and click on menu "Access" to access archived objects.' % self.ObjectIdentifierValue,smtp_server=smtp_server,smtp_timeout=30)
                                else:
                                    logger.warning('smtp_server not configured, skip to send email receipt for AIP: %s' % ArchiveObject_obj.ObjectIdentifierValue)
                            else:
                                logger.error('Missing receipt email address for AIP: %s' % ArchiveObject_obj.ObjectIdentifierValue)
                        # Delete IOQueue_objs for ArchiveObject
                        IOQueue_objs.delete()
                        logger.info('all writes done!!!')
                            
                ############################################################################
                # If no active Write IO to tape exist remove target reservation from ActiveTapeIOs
                for target_obj_id in ActiveTapeIOs:
                    if not IOQueue.objects.filter(ReqType=10, Status__lt=100, storagemethodtarget__target__id=target_obj_id).exists():
                        ActiveTapeIOs.remove(target_obj_id)
                '''        
            ############################################################################
            try:
                PauseIngestWhenActiveWrites_flag = int(ESSConfig.objects.get(Name='PauseIngestWhenActiveWrites').Value)
            except ObjectDoesNotExist:
                PauseIngestWhenActiveWrites_flag = 1
            # Check if any active Write IO exist to set puase flags for ingest of new objects
            if IOQueue.objects.filter(ReqType__in=[10, 15], Status__in = [1,19]).exists() and PauseIngestWhenActiveWrites_flag:
                #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
                ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=1)
            else:
                #ESSProc.objects.filter(Name__in=['SIPReceiver', 'AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)
                ESSProc.objects.filter(Name__in=['AIPCreator', 'AIPChecksum', 'AIPValidate']).update(Pause=0)

            #db.close_old_connections()
            self.mLock.release()
            time.sleep(int(PauseTime))
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
# Table: ESSProc with Name: AIPWriter, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPWriter'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSProc.objects.filter(Name=ProcName).values_list('LogFile','Time','Status','Run')[0]

    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 0
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
    essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
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
#    if MultiProc:
#        logger = multiprocessing.get_logger()
#        logger.setLevel(LogLevel)
    esslogger = logging.getLogger('')
    esslogger.setLevel(0)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
#    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        esslogger.addHandler(essConsoleHandler)
#        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSConfig.objects.get(Name='AgentIdentifierValue').Value
    ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            break
        time.sleep(5)
    logger.info('test3: ' + str(x.RunFlag))
    del x

# ./AIPWriter.py

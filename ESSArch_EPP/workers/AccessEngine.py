#!/usr/bin/env /ESSArch/pd/python/bin/python
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

import thread, multiprocessing, time, logging, sys, ESSDB, ESSPGM, ESSlogging, os, tarfile, datetime, ESSMD, traceback

from essarch.models import AccessQueue, ArchiveObject
from essarch.libs import calcsum, unicode2str
from django import db
from Storage.models import storage, storageMedium, IOQueue
from StorageMethodDisk.tasks import ReadStorageMethodDisk
from StorageMethodTape.tasks import ReadStorageMethodTape
from celery.result import AsyncResult

import django
django.setup()

class AccessError(Exception):
    def __init__(self, value):
        self.value = value
        super(AccessError, self).__init__(value)

class Access:
    def ProcessAccessRequest(self,ReqUUID):
        """Process access request
        
        :param ReqUUID: ReqUUID in database table AccessQueue
        
        """
        try:
            AccessQueue_obj = AccessQueue.objects.get(ReqUUID = ReqUUID)
            process_name = multiprocessing.current_process().name
            process_pid = multiprocessing.current_process().pid

            AccessQueue_obj.Status = 5
            AccessQueue_obj.save()

            if AccessQueue_obj.ReqType in (1,3,4,5):
                event_info = 'Start Generate DIP Process for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1202',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Start quickverify storageMediumID Process for storageMediumID: %s, ReqUUID: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2202',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)

            if AccessQueue_obj.ReqType == 1:
                storage_objs = self._GetObjectToRead(ReqUUID)
                IOs_to_read = self._AddObjectsToIOQueue(storage_objs, ReqUUID)
                self._ApplyIOsToRead(IOs_to_read, ReqUUID)
                self._WaitForIOsToRead(ReqUUID)
                self._IPunpack(ReqUUID)
                self._IPvalidate(ReqUUID)
            elif AccessQueue_obj.ReqType == 3:
                storage_objs = self._GetObjectToRead(ReqUUID)
                IOs_to_read = self._AddObjectsToIOQueue(storage_objs, ReqUUID)
                self._ApplyIOsToRead(IOs_to_read, ReqUUID)
                self._WaitForIOsToRead(ReqUUID)
            elif AccessQueue_obj.ReqType in [4,5]:
                storage_objs = self._GetObjectToRead(ReqUUID)
                IOs_to_read = self._AddObjectsToIOQueue(storage_objs, ReqUUID)
                self._ApplyIOsToRead(IOs_to_read, ReqUUID)
                self._WaitForIOsToRead(ReqUUID)
                self._IPunpack(ReqUUID)
                self._IPvalidate(ReqUUID)
                self._DeleteAccessedIOs(storage_objs, ReqUUID)
            elif AccessQueue_obj.ReqType == 2:
                storage_objs = self._GetObjectsToVerify(ReqUUID)
                IOs_to_read = self._AddObjectsToIOQueue(storage_objs, ReqUUID)
                self._ApplyIOsToRead(IOs_to_read, ReqUUID)
                self._WaitForIOsToRead(ReqUUID)
                self._DeleteAccessedIOs(storage_objs, ReqUUID)

        except AccessError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()            
            AccessQueue_obj.refresh_from_db()
            if AccessQueue_obj.ReqType in (1,3,4,5):
                event_info = 'Problem to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, error: %s, line: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID, e, exc_traceback.tb_lineno)
                logger.error(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Problem to quickverify storageMediumID: %s, ReqUUID: %s, error: %s line: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID, e, exc_traceback.tb_lineno)
                logger.error(event_info)
                ESSPGM.Events().create('2203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,storageMediumID=AccessQueue_obj.storageMediumID)
            AccessQueue_obj.Status = 100
            AccessQueue_obj.save(update_fields=['Status'])
            #raise e
        except Exception as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()            
            AccessQueue_obj.refresh_from_db()
            msg = 'Unknown error with access ReqUUID: %s, error: %s trace: %s' % (AccessQueue_obj.ReqUUID, e, repr(traceback.format_tb(exc_traceback)))
            logger.error(msg)
            AccessQueue_obj.Status = 100
            AccessQueue_obj.save(update_fields=['Status'])
            #raise e
        except:
            msg = 'Unexpected error: %s %s' % (sys.exc_info()[0], sys.exc_info()[1])
            logger.error(msg)
            print msg
            #raise
        else:
            if AccessQueue_obj.ReqType in (1,3,4):
                event_info = 'Success to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
            elif AccessQueue_obj.ReqType == 5:
                event_info = 'Success to get AIP to ControlArea for ObjectIdentifierValue: %s, ReqUUID: %s' % (AccessQueue_obj.ObjectIdentifierValue,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,AccessQueue_obj.ObjectIdentifierValue)
                # Update IP in ArchiveObject DBtable
                ArchiveObject_upd = ArchiveObject.objects.get(ObjectIdentifierValue = AccessQueue_obj.ObjectIdentifierValue)
                setattr(ArchiveObject_upd, 'StatusActivity', 7)
                # Commit DB updates
                ArchiveObject_upd.save(update_fields=['StatusActivity'])
            elif AccessQueue_obj.ReqType == 2:
                event_info = 'Success to quickverify storageMediumID: %s, ReqUUID: %s' % (AccessQueue_obj.storageMediumID,AccessQueue_obj.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2203',AccessQueue_obj.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,storageMediumID=AccessQueue_obj.storageMediumID)
            AccessQueue_obj.Status = 20
            AccessQueue_obj.save(update_fields=['Status'])
        
    def _GetObjectsToVerify(self, ReqUUID, complete=False):
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        storageMediumID = AccessQueue_obj.storageMediumID

        storageMedium_obj = storageMedium.objects.get(storageMediumID=storageMediumID)
                       
        # get all storage_objs for storageMeduimID
        storage_objs = storage.objects.filter(storagemedium=storageMedium_obj).extra(
                                                                     select={'contentLocationValue_int': 'CAST(contentLocationValue AS UNSIGNED)'}
                                                                     ).order_by('contentLocationValue_int')

        storage_objs_count = storage_objs.count()
        if complete or storage_objs_count<3:
            return storage_objs
        else:
            return [storage_objs[0], storage_objs[storage_objs_count/2], storage_objs[storage_objs_count-1]]

    def _GetObjectToRead(self, ReqUUID):
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        storageMediumID = AccessQueue_obj.storageMediumID
        ObjectIdentifierValue = AccessQueue_obj.ObjectIdentifierValue
        
        storage_objs = storage.objects.filter(archiveobject__ObjectIdentifierValue=ObjectIdentifierValue, storagemedium__storageMediumStatus__in=[20,30], storagemedium__storageMediumLocationStatus=50)
        
        if storageMediumID:
            if storage_objs.filter(storagemedium__storageMediumID=storageMediumID).exists():
                storage_objs = storage_objs.filter(storagemedium__storageMediumID=storageMediumID)
        
        if len(storage_objs) >= 1:
            if storage_objs.filter(storagemedium__storageMedium__in=[200,201]).exists():
                storage_obj = storage_objs.filter(storagemedium__storageMedium__in=[200,201])[0]
            elif storage_objs.filter(storagemedium__storageMedium__in=[300,330]).exists():
                storage_obj = storage_objs.filter(storagemedium__storageMedium__in=[300,330])[0]
            else:
                storage_obj = storage_objs[0]
        else:
            raise AccessError('No storage objects found for object: %s (ReqUUD: %s)' % (ObjectIdentifierValue,ReqUUID) )
        
        return [storage_obj]
        
    def _AddObjectsToIOQueue(self, storage_objs, ReqUUID):
        """Add storage objects to IOQueue
        
        :param storage_objs: List of storage objects
        :param ReqUUID: AccessQueue request UUID
        
        """
        IOs_to_read = {}
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)     
        for storage_obj in storage_objs:
            storageMedium_obj = storage_obj.storagemedium
            if storageMedium_obj.storageMedium in range(300,330): 
                ReqType = 20
                ReqPurpose=u'Read package from tape'
            elif storageMedium_obj.storageMedium in range(200,201):
                ReqType = 25
                ReqPurpose=u'Read package from disk'
            ArchiveObject_obj = storage_obj.archiveobject
            IOQueue_objs = IOQueue.objects.filter(storage=storage_obj)
            if not IOQueue_objs.exists():     
                IOQueue_obj = IOQueue()
                IOQueue_obj.ReqType=ReqType
                IOQueue_obj.ReqPurpose=ReqPurpose
                IOQueue_obj.user=u'sys'
                IOQueue_obj.ObjectPath=AccessQueue_obj.Path
                IOQueue_obj.Status=0
                IOQueue_obj.archiveobject=ArchiveObject_obj
                IOQueue_obj.storage=storage_obj
                IOQueue_obj.accessqueue=AccessQueue_obj
                IOQueue_obj.save()
                logger.info('Add ReadReq from storageMediumID: %s for object: %s (IOuuid: %s)' % (storageMedium_obj.storageMediumID, 
                                                                                                                                             ArchiveObject_obj.ObjectIdentifierValue, 
                                                                                                                                             IOQueue_obj.id))                    
            elif IOQueue_objs.count() > 1:
                logger.error('More then one ReadReq from storageMediumID: %s for object: %s exists' % (storageMedium_obj.storageMediumID, 
                                                                                                                                                    ArchiveObject_obj.ObjectIdentifierValue))
            else:
                IOQueue_obj = IOQueue_objs[0]

            if not IOs_to_read.has_key(storageMedium_obj):
                IOs_to_read[storageMedium_obj] = []
            IOs_to_read[storageMedium_obj].append(IOQueue_obj)        
        
        return IOs_to_read

    def _ApplyIOsToRead(self, IOs_to_read, ReqUUID):
        """Apply all IOs to read
        
        :param IOs_to_read: Dict with {storageMedium_obj=IOQueue_obj_list,...}
        :param ReqUUID: AccessQueue request UUID
        
        """
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)     
        for storageMedium_obj, IOQueue_obj_list in IOs_to_read.iteritems():           
            if storageMedium_obj.storageMedium in range(300,330): 
                # Read from tape (ReqType=20)
                IOQueue_objs_id_list = [i.id for i in IOQueue_obj_list]
                result = ReadStorageMethodTape().apply_async((IOQueue_objs_id_list,), queue='smtape')
                logger.info('Apply new read IO process from tape id: %s (AccessReqUUID: %s)' % (storageMedium_obj.storageMediumID, 
                                                                                                                                           AccessQueue_obj.ReqUUID))         
                for  IOQueue_obj in IOQueue_obj_list:
                    IOQueue_obj.Status=2
                    IOQueue_obj.task_id = result.task_id
                    IOQueue_obj.save(update_fields=['Status', 'task_id'])                        
            elif storageMedium_obj.storageMedium in range(200,201): 
                # Read from disk (ReqType=25)
                for  IOQueue_obj in IOQueue_obj_list:
                    result = ReadStorageMethodDisk().apply_async((IOQueue_obj.id,), queue='smdisk')
                    logger.info('Apply new read IO process for object: %s from disk id: %s (AccessReqUUID: %s, IOuuid: %s)' % (IOQueue_obj.archiveobject.ObjectIdentifierValue, 
                                                                                                                                                                                      storageMedium_obj.storageMediumID, 
                                                                                                                                                                                      AccessQueue_obj.ReqUUID, 
                                                                                                                                                                                      IOQueue_obj.id))
                    IOQueue_obj.Status=2
                    IOQueue_obj.task_id = result.task_id
                    IOQueue_obj.save(update_fields=['Status', 'task_id'])        

    def _WaitForIOsToRead(self, ReqUUID):
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        IOQueue_objs = AccessQueue_obj.ioqueue_set.all()
        while 1:
            ReadOK=1
            for IOQueue_obj in IOQueue_objs:
                result = AsyncResult(IOQueue_obj.task_id)
                if result.failed():
                    ReadOK=0
                    logger.error('Problem to read object: %s, traceback: %s, result: %s (AccessReqUUID: %s, IOuuid: %s)' % (IOQueue_obj.archiveobject.ObjectIdentifierValue, 
                                                                                                                                                                                 result.traceback, 
                                                                                                                                                                                 result.result,
                                                                                                                                                                                 AccessQueue_obj.ReqUUID, 
                                                                                                                                                                                 IOQueue_obj.id))
                    raise AccessError(result.traceback)
                elif result.successful():
                    logger.info('Success to read object: %s (AccessReqUUID: %s, IOuuid: %s)' % (IOQueue_obj.archiveobject.ObjectIdentifierValue,
                                                                                                                                         AccessQueue_obj.ReqUUID, 
                                                                                                                                         IOQueue_obj.id))
                else:
                    ReadOK=0
            if ReadOK==1:
                logger.info('all reads done!!!')
                IOQueue_objs.delete()
                break
            time.sleep(1)

    def _IPunpack(self,ReqUUID):
        """Unpack information package"""
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        ObjectIdentifierValue = AccessQueue_obj.ObjectIdentifierValue
        RootPath = AccessQueue_obj.Path
        RootPath_iso = unicode2str(RootPath)
        try:
            AIPfilename = os.path.join(RootPath,ObjectIdentifierValue + '.tar')
            AIP_tarObject = tarfile.open(name=AIPfilename, mode='r')
            AIP_tarObject.extractall(path=RootPath_iso)
        except (ValueError, IOError, OSError, tarfile.TarError) as e:
            event_info = 'Problem to unpack object: %s, Message: %s' % (ObjectIdentifierValue, str(e))
            logging.error(event_info)
            ESSPGM.Events().create('1210','','IPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
            raise e
        else:
            event_info = 'Success to unpack object: %s' % ObjectIdentifierValue
            logging.info(event_info)
            ESSPGM.Events().create('1210','','IPunpack',ProcVersion,'0',event_info,2,ObjectIdentifierValue)
            
    def _IPvalidate(self,ReqUUID, mets_flag = 1, VerifyChecksum_flag = 0):
        """Validate information package"""
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        ObjectIdentifierValue = AccessQueue_obj.ObjectIdentifierValue
        RootPath = AccessQueue_obj.Path
        ok_flag=1
        if ok_flag and mets_flag:
            ###########################################################
            # find Content_METS file
            #Cmets_obj = Cmets_obj.replace('{uuid}',ObjectIdentifierValue)
            PMetaObjectPath = os.path.join(RootPath,ObjectIdentifierValue + '_Package_METS.xml')
            if not os.path.exists(PMetaObjectPath):
                event_info = 'Problem to find %s for information package: %s' % (PMetaObjectPath,ObjectIdentifierValue)
                logging.error(event_info)
                ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                ok_flag = 0
            if ok_flag:
                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=PMetaObjectPath)
                if not error:
                    for res_file in res_files:
                        if res_file[0] == 'amdSec' and \
                           res_file[2] == 'techMD' and \
                           res_file[13] == 'text/xml' and \
                           res_file[15] == 'OTHER' and \
                           res_file[16] == 'METS':
                            if res_file[8][:5] == 'file:':
                                Cmets_filename = res_file[8][5:]
                else:
                    event_info = 'Problem to read package METS %s for information package: %s, error: %s' % (PMetaObjectPath,ObjectIdentifierValue,str(why))
                    logging.error(event_info)
                    ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                    ok_flag = 0
            #Cmets_obj = Cmets_obj.replace('{uuid}',ObjectIdentifierValue)
            Meta_filepath = os.path.join(RootPath,Cmets_filename)
            if not os.path.exists(Meta_filepath):
                event_info = 'Problem to find %s for information package: %s' % (Meta_filepath,ObjectIdentifierValue)
                logging.error(event_info)
                ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                ok_flag = 0
            if not RootPath == os.path.split(Meta_filepath)[0]:
                RootPath = os.path.split(Meta_filepath)[0]
                logging.info('Setting METSrootpath for IP: %s to %s' % (ObjectIdentifierValue, RootPath))
################################
#            if os.path.exists('%s/%s_Content_METS.xml' % (RootPath,ObjectIdentifierValue)):
#                pass
#            elif os.path.exists('%s/%s/%s_Content_METS.xml' % (RootPath,ObjectIdentifierValue,ObjectIdentifierValue)):
#                RootPath = os.path.join(RootPath,ObjectIdentifierValue)
#            else:
#                event_info = 'Problem to find X_Content_METS.xml file for information package: %s' % ObjectIdentifierValue
#                logging.error(event_info)
#                ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
#                ok_flag = 0
#            Meta_filepath = '%s/%s_Content_METS.xml' % (RootPath,ObjectIdentifierValue)
        if ok_flag and mets_flag:
            ###########################################################
            # get object_list from METS file
            object_list,errno,why = ESSMD.getAIPObjects(FILENAME=Meta_filepath)
            if errno == 0:
                logging.info('Success to get object_list from premis for information package: %s', ObjectIdentifierValue)
                #logging.debug('Meta_filepath: %s , object_list: %s', Meta_filepath,str(object_list))
            else:
                event_info = 'Problem to get object_list from premis for information package: %s, errno: %s, detail: %s' % (ObjectIdentifierValue,errno,str(why))
                logging.error(event_info)
                ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                ok_flag = 0
        if ok_flag and not mets_flag:
            ###########################################################
            # get object_list from RES file
            Meta_filepath = os.path.join(os.path.join(RootPath,ObjectIdentifierValue),'TIFFEdit.RES')
            object_list,errno,why = ESSMD.getRESObjects(FILENAME=Meta_filepath)
            if errno == 0:
                logging.info('Success to get object_list from RES for information package: %s', ObjectIdentifierValue)
            else:
                event_info = 'Problem to get object_list from RES for information package: %s, errno: %s, detail: %s' % (ObjectIdentifierValue,errno,str(why))
                logging.error(event_info)
                ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                ok_flag = 0
        if ok_flag and mets_flag:
            ###########################################################
            # Start to format validate DIP with object list from METS
            logging.info('Format validate object: ' + ObjectIdentifierValue)
            startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            ObjectNumItems = 0
            ObjectSize = 0
            for obj in object_list:
                messageDigestAlgorithm = obj[1]
                filepath = os.path.join(RootPath, obj[0])
                filepath_iso = unicode2str(filepath)
                if ok_flag and os.access(filepath_iso,os.R_OK):
                    pass
                else:
                    event_info = 'Object path: %s do not exist or is not readable!' % filepath
                    logging.error(event_info)
                    ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                    ok_flag = 0
                    break
                if ok_flag and os.access(filepath_iso,os.W_OK):
                    pass
                else:
                    event_info = 'Missing permission, Object path: %s is not writeable!' % filepath
                    logging.error(event_info)
                    ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                    ok_flag = 0
                    break
                if ok_flag:
                    if int(os.stat(filepath_iso)[6]) == int(obj[3]):
                        ObjectSize += int(obj[3])
                    else:
                        event_info = 'Filesize for object path: %s is %s and premis object size is %s. The sizes must match!' % (filepath,str(os.stat(filepath_iso)[6]),str(obj[3]))
                        logging.error(event_info)
                        ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                        ok_flag = 0
                        break
                    if ok_flag and VerifyChecksum_flag:
                        #F_messageDigest,errno,why = Check().checksum(filepath_iso,messageDigestAlgorithm) # Checksum
                        F_messageDigest = calcsum(filepath_iso,messageDigestAlgorithm) # Checksum
                        #if errno:
                        #    event_info = 'Failed to get checksum for: %s, Error: %s' % (filepath,str(why))
                        #    logging.error(event_info)
                        #    ESSPGM.Events().create('1041','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                        #    ok_flag = 0
                        #else:
                        event_info = 'Success to get checksum for: %s, Checksum: %s' % (filepath,F_messageDigest)
                        logging.info(event_info)
                        ESSPGM.Events().create('1041','','ESSPGM_AIPunpack',ProcVersion,'0',event_info,2,ObjectIdentifierValue)
                    else:
                        event_info = 'Skip to verify checksum for: %s' % filepath
                        logging.info(event_info)
                    if ok_flag and VerifyChecksum_flag:
                        if F_messageDigest == obj[2]:
                            event_info = 'Success to verify checksum for object path: %s' % filepath
                            logging.info(event_info)
                            ESSPGM.Events().create('1042','','ESSPGM_AIPunpack',ProcVersion,'0',event_info,2,ObjectIdentifierValue)
                        else:
                            event_info = 'Checksum for object path: %s is %s and premis object checksum is %s. The checksum must match!' % (filepath,F_messageDigest,obj[2])
                            logging.error(event_info)
                            ESSPGM.Events().create('1042','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                            ok_flag = 0
                            break
                ObjectNumItems += 1
        if ok_flag and not mets_flag:
            ###########################################################
            # Start to format validate DIP with object list from RESfile
            logging.info('Format validate object (RES): ' + ObjectIdentifierValue)
            startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            ObjectNumItems = 0
            ObjectSize = 0
            for obj in object_list:
                filepath = os.path.join(RootPath, obj[0])
                if ok_flag and os.access(filepath,os.R_OK):
                    pass
                else:
                    event_info = 'Object path: %s do not exist or is not readable!' % filepath
                    logging.error(event_info)
                    ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                    ok_flag = 0
                    break
                if ok_flag and os.access(filepath,os.W_OK):
                    pass
                else:
                    event_info = 'Missing permission, Object path: %s is not writeable!' % filepath
                    logging.error(event_info)
                    ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                    ok_flag = 0
                    break
                if ok_flag:
                    if int(os.stat(filepath)[6]) == int(obj[1]):
                        ObjectSize += int(obj[1])
                    else:
                        event_info = 'Filesize for object path: %s is %s and RES object size is %s. The sizes must match!' % (filepath,str(os.stat(filepath)[6]),str(obj[1]))
                        logging.error(event_info)
                        ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',event_info,2,ObjectIdentifierValue)
                        ok_flag = 0
                        break
        if ok_flag:
            stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            MeasureTime = stopTime-startTime
            ObjectSizeMB = ObjectSize/1048576
            if MeasureTime.seconds < 1: MeasureTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
            VerMBperSEC = int(ObjectSizeMB)/int(MeasureTime.seconds)
        if ok_flag:
            event_info = 'Success to validate object package: %s, %s MB/Sec and Time: %s' % (ObjectIdentifierValue,str(VerMBperSEC),str(MeasureTime))
            logging.info(event_info)
            ESSPGM.Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'0',event_info,2,ObjectIdentifierValue)
        else:
            msg = 'Problem to validate IP package: ' + ObjectIdentifierValue
            raise AccessError(msg)                  

    def _DeleteAccessedIOs(self, storage_objs, ReqUUID):
        AccessQueue_obj = AccessQueue.objects.get(ReqUUID=ReqUUID)
        RootPath = AccessQueue_obj.Path
        for storage_obj in storage_objs:
            ObjectIdentifierValue = storage_obj.archiveobject.ObjectIdentifierValue
            storageMediumFormat = storage_obj.storagemedium.storageMediumFormat
            PMetaObjectPath = os.path.join(RootPath,ObjectIdentifierValue + '_Package_METS.xml')
            ip_path = os.path.join(RootPath,ObjectIdentifierValue + '.tar')

            if storageMediumFormat in range(100,102):
                logging.info('Try to remove ObjectPath: ' + ip_path)
            else:
                logging.info('Try to remove ObjectPath: ' + ip_path + ' and ' + PMetaObjectPath)
            try:
                os.remove(ip_path)
                if not storageMediumFormat in range(100,102):
                    os.remove(PMetaObjectPath)
            except (IOError, OSError) as e:
                if storageMediumFormat in range(100,102):
                    logging.error('Problem to remove ObjectPath: %s, error: %s' % (ip_path,e))
                else:
                    logging.error('Problem to remove ObjectPath: %s and %s, error: %s' % (ip_path, PMetaObjectPath, e))
                raise e
            else:
                if storageMediumFormat in range(100,102):
                    logging.info('Success to removeObjectPath: ' + ip_path)
                else:
                    logging.info('Success to removeObjectPath: ' + ip_path + ' and ' + PMetaObjectPath)

class Functions:
    def GenerateDIPProc(self,ReqUUID):
        "Generate DIP for request in Accessqueue"
        try:
            DbRow = AccessQueue.objects.filter(ReqUUID = ReqUUID)[:1].get()
            self.run = 1
            self.unpack = 0
            self.delete = 0
            self.process_name = multiprocessing.current_process().name
            self.process_pid = multiprocessing.current_process().pid
            aic_support = False
            DbRow.Status = 5
            DbRow.save()

            if DbRow.ReqType in (1,3,4,5):
                event_info = 'Start Generate DIP Process for ObjectIdentifierValue: %s, ReqUUID: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('1202',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
            elif DbRow.ReqType == 2:
                event_info = 'Start quickverify storageMediumID Process for storageMediumID: %s, ReqUUID: %s' % (DbRow.storageMediumID,DbRow.ReqUUID)
                logger.info(event_info)
                ESSPGM.Events().create('2202',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)

            if DbRow.ReqType == 1:
                self.unpack = 1
                self.delete = 0
            elif DbRow.ReqType == 3:
                self.unpack = 0
                self.delete = 0
            elif DbRow.ReqType == 4:
                self.unpack = 1
                self.delete = 1
            elif DbRow.ReqType == 5:
                self.unpack = 1
                self.delete = 1
                aic_support = True
            elif DbRow.ReqType == 2:
                self.unpack = 0
                self.delete = 1              

            self.cmdres,self.errno,self.why = ESSPGM.Check().AIPextract(storageMediumID=DbRow.storageMediumID, 
                                                                        ObjectIdentifierValue=DbRow.ObjectIdentifierValue,
                                                                        delete=self.delete,
                                                                        prefix=None,
                                                                        target=DbRow.Path,
                                                                        unpack=self.unpack,
                                                                        aic_support=aic_support,
                                                                        )
            if self.errno:
                if DbRow.ReqType in (1,3,4,5):
                    event_info = 'Problem to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, errorcode: %s, errormessage: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.errno),str(self.why))
                    logger.error(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,DbRow.ObjectIdentifierValue)
                elif DbRow.ReqType == 2:
                    event_info = 'Problem to quickverify storageMediumID: %s, ReqUUID: %s, errorcode: %s, errormessage: %s' % (DbRow.storageMediumID,DbRow.ReqUUID,str(self.errno),str(self.why))
                    logger.error(event_info)
                    ESSPGM.Events().create('2203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'1',event_info,2,storageMediumID=DbRow.storageMediumID)
                DbRow.Status = 100
                DbRow.save()
            else:
                if DbRow.ReqType in (1,3,4):
                    event_info = 'Success to Generate DIP for ObjectIdentifierValue: %s, ReqUUID: %s, cmdres: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                elif DbRow.ReqType == 5:
                    event_info = 'Success to get AIP to ControlArea for ObjectIdentifierValue: %s, ReqUUID: %s, cmdres: %s' % (DbRow.ObjectIdentifierValue,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('1203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,DbRow.ObjectIdentifierValue)
                    # Update IP in ArchiveObject DBtable
                    ArchiveObject_upd = ArchiveObject.objects.filter(ObjectIdentifierValue = DbRow.ObjectIdentifierValue)[:1].get()
                    setattr(ArchiveObject_upd, 'StatusActivity', 7)
                    # Commit DB updates
                    ArchiveObject_upd.save()
                elif DbRow.ReqType == 2:
                    event_info = 'Success to quickverify storageMediumID: %s, ReqUUID: %s, cmdres: %s' % (DbRow.storageMediumID,DbRow.ReqUUID,str(self.cmdres))
                    logger.info(event_info)
                    ESSPGM.Events().create('2203',DbRow.ReqPurpose,'ESSArch Access',ProcVersion,'0',event_info,2,storageMediumID=DbRow.storageMediumID)
                DbRow.Status = 20
                DbRow.save()
            db.close_old_connections()
        except:
            logger.error('Unexpected error: %s %s' % (sys.exc_info()[0], sys.exc_info()[1]))
            print "Unexpected error:", sys.exc_info()[0], sys.exc_info()[1]
            raise

def GenerateDIPProc(DbRow):
    #return Functions().GenerateDIPProc(DbRow)
    return Access().ProcessAccessRequest(DbRow)

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        # Start Process pool with 2 process
        self.ReqTags = 2
        self.ProcPool = multiprocessing.Pool(self.ReqTags)
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            self.ProcPoolProblemFlag = 0
            for self.worker in self.ProcPool._pool: 
                if not self.worker.is_alive(): 
                    self.ProcPoolProblemFlag = 1
                    logger.error('Problem with process_name: %s, process_pid: %s, process_exitcode: %s',self.worker.name,self.worker.pid,self.worker.exitcode)
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0' or self.ProcPoolProblemFlag == 1:
                logger.info('Stopping ' + ProcName)
                if self.ProcPoolProblemFlag:
                    self.ProcPool.terminate()
                else:
                    self.ProcPool.close()
                self.ProcPool.join()
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                time.sleep(1)
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item 
            lock=thread.allocate_lock()

            AccessQueue_DbRows = AccessQueue.objects.filter(Status = 0).all()
            for AccessQueue_DbRow in AccessQueue_DbRows:
                ##############################################################################################Y
                # if self.ProcPool._state == 0 then pool is working.
                if self.ProcPool._state == 0:
                    # Get active queue depth for self.ProcPool._cache.
                    self.ActiveProcQueue = len(self.ProcPool._cache)
                    ###########################################################################################
                    # If self.ActiveProcQueue < self.ReqTags start DIPRequest process
                    if self.ActiveProcQueue < self.ReqTags:
                        AccessQueue_DbRow.Status = 2
                        #model.meta.Session.commit()
                        AccessQueue_DbRow.save()
                        self.ProcPool.apply_async(GenerateDIPProc, (AccessQueue_DbRow.ReqUUID,))
            logger.debug('ProcPool_cache: %r',self.ProcPool._cache)
            db.close_old_connections()
            time.sleep(5)
            self.mLock.release()
        time.sleep(10)
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
# Table: ESSProc with Name: IOEngine, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AccessEngine'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]
    LogLevel = logging.INFO
    #LogLevel = logging.DEBUG
    #LogLevel = multiprocessing.SUBDEBUG
    MultiProc = 1
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
    #essLocalFileHandler = logging.handlers.TimedRotatingFileHandler(LogFile, when='W6', backupCount=1040)
    essLocalFileHandler = logging.FileHandler(LogFile)
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
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    #logging = logging.getLogger('')
    esslogger = logging.getLogger('')
    #logging.setLevel(0)
    esslogger.setLevel(0)
    #logging.addHandler(essLocalFileHandler)
    esslogger.addHandler(essLocalFileHandler)
    #esslogger.addHandler(essSocketHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        #logging.addHandler(essConsoleHandler)
        esslogger.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)
    logger = logging.getLogger(ProcName)

    logger.debug('LogFile: ' + str(LogFile))
    logger.debug('Time: ' + str(Time))
    logger.debug('Status: ' + str(Status))
    logger.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])
    
    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            logger.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            logger.info('test2: ' + str(x.RunFlag))
            #x.Die()
            time.sleep(10) 
            break
        time.sleep(1)
    logger.info('test3: ' + str(x.RunFlag))
    del x


# ./AccessEngine.py

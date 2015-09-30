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

import sys, logging, logging.handlers, datetime, time, uuid, ESSMSSQL, ESSsched, types, pytz
from optparse import OptionParser
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from essarch.models import ArchiveObject, ArchiveObjectMetadata, eventIdentifier
from configuration.models import ArchivePolicy, ESSProc, ESSConfig, StorageTargets
from Storage.models import storageMedium, storage
from django import db

class work:
    TimeZone = timezone.get_default_timezone_name()
    tz=pytz.timezone(TimeZone)
    "sync_storageMedium"
    ###############################################
    def sync_storageMedium(self,startDateTime,stopDateTime):
        storageMedium_objs = storageMedium.objects.filter(LocalDBdatetime__range=(startDateTime,stopDateTime))
        for storageMedium_obj in storageMedium_objs:
            if not storageMedium_obj.check_db_sync():
                storageMedium_ext_objs,errno2,why2 = ESSMSSQL.DB().action('storageMedium','GET3',('storageMediumID',),('storageMediumID',storageMedium_obj.storageMediumID))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    storageMediumDate_utc = storageMedium_obj.storageMediumDate.replace(microsecond=0,tzinfo=pytz.utc)
                    storageMediumDate_dst = storageMediumDate_utc.astimezone(self.tz)
                    CreateDate_utc = storageMedium_obj.CreateDate.replace(microsecond=0,tzinfo=pytz.utc)
                    CreateDate_dst = CreateDate_utc.astimezone(self.tz)
                    if storageMedium_ext_objs:
                        logging.info('Found storageMediumID: ' + str(storageMedium_obj.storageMediumID) + ' in AIS, try to update')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','UPD',('StorageMediumGuid',storageMedium_obj.storageMediumUUID,
                                                                                           'storageMedium',storageMedium_obj.storageMedium,
                                                                                           'storageMediumDate',storageMediumDate_dst.replace(tzinfo=None),
                                                                                           'storageMediumLocation',storageMedium_obj.storageMediumLocation,
                                                                                           'storageMediumLocationStatus',storageMedium_obj.storageMediumLocationStatus,
                                                                                           'storageMediumBlockSize',storageMedium_obj.storageMediumBlockSize,
                                                                                           'storageMediumUsedCapacity',storageMedium_obj.storageMediumUsedCapacity,
                                                                                           'storageMediumStatus',storageMedium_obj.storageMediumStatus,
                                                                                           'storageMediumFormat',storageMedium_obj.storageMediumFormat,
                                                                                           'storageMediumMounts',storageMedium_obj.storageMediumMounts,
                                                                                           'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue,
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',storageMedium_obj.CreateAgentIdentifierValue),
                                                                                          ('storageMediumID',storageMedium_obj.storageMediumID))
                        if ext_errno: logging.error('Failed to update External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                        else:
                            storageMedium_obj.ExtDBdatetime=storageMedium_obj.LocalDBdatetime
                            storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                            #if errno: logging.error('Failed to update Local DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(why))
                    else:
                        logging.info('Missing storageMediumID: ' + str(storageMedium_obj.storageMediumID) + ' in AIS, try to insert')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','INS',('StorageMediumGuid',storageMedium_obj.storageMediumUUID,
                                                                                           'storageMedium',storageMedium_obj.storageMedium,
                                                                                           'storageMediumID',storageMedium_obj.storageMediumID,
                                                                                           'storageMediumDate',storageMediumDate_dst.replace(tzinfo=None),
                                                                                           'storageMediumLocation',storageMedium_obj.storageMediumLocation,
                                                                                           'storageMediumLocationStatus',storageMedium_obj.storageMediumLocationStatus,
                                                                                           'storageMediumBlockSize',storageMedium_obj.storageMediumBlockSize,
                                                                                           'storageMediumUsedCapacity',storageMedium_obj.storageMediumUsedCapacity,
                                                                                           'storageMediumStatus',storageMedium_obj.storageMediumStatus,
                                                                                           'storageMediumFormat',storageMedium_obj.storageMediumFormat,
                                                                                           'storageMediumMounts',storageMedium_obj.storageMediumMounts,
                                                                                           'linkingAgentIdentifierValue',storageMedium_obj.linkingAgentIdentifierValue,
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',storageMedium_obj.CreateAgentIdentifierValue))
                        if ext_errno: logging.error('Failed to insert to External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                        else:
                            storageMedium_obj.ExtDBdatetime=storageMedium_obj.LocalDBdatetime
                            storageMedium_obj.save(update_fields=['ExtDBdatetime'])
                            #if errno: logging.error('Failed to update Local DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(why))

    "sync_storage"
    ###############################################
    def sync_storage(self,startDateTime,stopDateTime):
        storage_objs = storage.objects.filter(LocalDBdatetime__range=(startDateTime,stopDateTime))
        for storage_obj in storage_objs:
            if not storage_obj.check_db_sync():
                storage_ext_objs,errno2,why2 = ESSMSSQL.DB().action('storage','GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',storage_obj.archiveobject.ObjectIdentifierValue,'AND',
                                                                                                            'contentLocationType',str(storage_obj.contentLocationType),'AND',
                                                                                                            'contentLocationValue',storage_obj.contentLocationValue,'AND',
                                                                                                            'storageMediumID',storage_obj.storagemedium.storageMediumID))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if storage_ext_objs:
                        logging.info('Found ObjectIdentifierValue: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' contentLocationType: ' + str(storage_obj.contentLocationType) + ' contentLocationValue: ' + str(storage_obj.contentLocationValue) + ' storageMediumID: ' + str(storage_obj.storagemedium.storageMediumID) + ' in AIS, nothing to update')
                        storage_obj.ExtDBdatetime=storage_obj.LocalDBdatetime
                        storage_obj.save(update_fields=['ExtDBdatetime'])
                        #if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' contentLocationType: ' + str(storage_obj.contentLocationType) + ' contentLocationValue: ' + str(storage_obj.contentLocationValue) + ' storageMediumID: ' + str(storage_obj.storagemedium.storageMediumID) + ' error: ' + str(why))
                    else:
                        logging.info('Missing ObjectIdentifierValue: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' contentLocationType: ' + str(storage_obj.contentLocationType) + ' contentLocationValue: ' + str(storage_obj.contentLocationValue) + ' storageMediumID: ' + str(storage_obj.storagemedium.storageMediumID) + ' in AIS, try to insert')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storage','INS',('ObjectIdentifierValue',storage_obj.archiveobject.ObjectIdentifierValue,
                                                                                           'contentLocationType',storage_obj.contentLocationType,
                                                                                           'contentLocationValue',storage_obj.contentLocationValue,
                                                                                           'storageMediumID',storage_obj.storagemedium.storageMediumID))
                        if ext_errno: logging.error('Failed to insert to External DB for ObjectIdentifierValue: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' contentLocationType: ' + str(storage_obj.contentLocationType) + ' contentLocationValue: ' + str(storage_obj.contentLocationValue) + ' storageMediumID: ' + str(storage_obj.storagemedium.storageMediumID) + ' error: ' + str(ext_why))
                        else:
                            storage_obj.ExtDBdatetime=storage_obj.LocalDBdatetime
                            storage_obj.save(update_fields=['ExtDBdatetime'])
                            #if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(storage_obj.archiveobject.ObjectIdentifierValue) + ' contentLocationType: ' + str(storage_obj.contentLocationType) + ' contentLocationValue: ' + str(storage_obj.contentLocationValue) + ' storageMediumID: ' + str(storage_obj.storagemedium.storageMediumID) + ' error: ' + str(why))

    "sync_IngestObject"
    ###############################################
    def sync_IngestObject(self,startDateTime,stopDateTime):
        ArchiveObject_objs = ArchiveObject.objects.filter(LocalDBdatetime__range=(startDateTime,stopDateTime))
        for ArchiveObject_obj in ArchiveObject_objs:
            if not ArchiveObject_obj.check_db_sync():
                rows2,errno2,why2 = ESSMSSQL.DB().action('IngestObject','GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',ArchiveObject_obj.ObjectIdentifierValue))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if rows2:
                        logging.info('Found ObjectIdentifierValue: ' + str(ArchiveObject_obj.ObjectIdentifierValue) + ' in AIS, try to update')                  
                        LastEventDate_utc = ArchiveObject_obj.LastEventDate.replace(microsecond=0,tzinfo=pytz.utc)
                        LastEventDate_dst = LastEventDate_utc.astimezone(self.tz)
                        CreateDate_utc = ArchiveObject_obj.CreateDate.replace(microsecond=0,tzinfo=pytz.utc)
                        CreateDate_dst = CreateDate_utc.astimezone(self.tz)
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('IngestObject','UPD',('PolicyId',ArchiveObject_obj.PolicyId,
                                                                                           'ObjectPackageName',ArchiveObject_obj.ObjectPackageName,
                                                                                           'ObjectSize',ArchiveObject_obj.ObjectSize,
                                                                                           'ObjectNumItems',ArchiveObject_obj.ObjectNumItems,
                                                                                           'ObjectMessageDigestAlgorithm',ArchiveObject_obj.ObjectMessageDigestAlgorithm,
                                                                                           'ObjectMessageDigest',ArchiveObject_obj.ObjectMessageDigest,
                                                                                           'ObjectPath',ArchiveObject_obj.ObjectPath,
                                                                                           'MetaObjectIdentifier',ArchiveObject_obj.MetaObjectIdentifier,
                                                                                           'MetaObjectSize',ArchiveObject_obj.MetaObjectSize,
                                                                                           'CMetaMessageDigestAlgorithm',ArchiveObject_obj.CMetaMessageDigestAlgorithm,
                                                                                           'CMetaMessageDigest',ArchiveObject_obj.CMetaMessageDigest,
                                                                                           'PMetaMessageDigestAlgorithm',ArchiveObject_obj.PMetaMessageDigestAlgorithm,
                                                                                           'PMetaMessageDigest',ArchiveObject_obj.PMetaMessageDigest,
                                                                                           'DataObjectSize',ArchiveObject_obj.DataObjectSize,
                                                                                           'DataObjectNumItems',ArchiveObject_obj.DataObjectNumItems,
                                                                                           #'Status',ArchiveObject_obj.Status,
                                                                                           'StatusActivity',ArchiveObject_obj.StatusActivity,
                                                                                           'StatusProcess',ArchiveObject_obj.StatusProcess,
                                                                                           'LastEventDate',LastEventDate_dst.replace(tzinfo=None),
                                                                                           'linkingAgentIdentifierValue',ArchiveObject_obj.linkingAgentIdentifierValue,
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',ArchiveObject_obj.CreateAgentIdentifierValue,
                                                                                           #'EntryDate',ArchiveObject_obj.EntryDate,
                                                                                           #'EntryAgentIdentifierValue',ArchiveObject_obj.EntryAgentIdentifierValue,
                                                                                           'OAISPackageType',ArchiveObject_obj.OAISPackageType,
                                                                                           'preservationLevelValue',ArchiveObject_obj.preservationLevelValue,
                                                                                           'DELIVERYTYPE',ArchiveObject_obj.DELIVERYTYPE,
                                                                                           'INFORMATIONCLASS',ArchiveObject_obj.INFORMATIONCLASS),
                                                                                          ('ObjectIdentifierValue',ArchiveObject_obj.ObjectIdentifierValue))
                        if ext_errno: logging.error('Failed to update External DB: ' + str(ArchiveObject_obj.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                        else:
                            ArchiveObject_obj.ExtDBdatetime = ArchiveObject_obj.LocalDBdatetime
                            ArchiveObject_obj.save(update_fields=['ExtDBdatetime'])
                    else:
                        logging.error('Missing ObjectIdentifierValue: ' + str(ArchiveObject_obj.ObjectIdentifierValue) + ' in AIS IngestObject, need of manual check!')

    "sync_eventIdentifier"
    ###############################################
    def sync_eventIdentifier(self,startDateTime,stopDateTime):
        eventIdentifier_objs = eventIdentifier.objects.filter(eventDateTime__range=(startDateTime,stopDateTime))
        for eventIdentifier_obj in eventIdentifier_objs:
            if eventIdentifier_obj.eventType <= 40:
                rows2,errno2,why2 = ESSMSSQL.DB().action('eventStorageMedium','GET3',('eventIdentifierValue',),('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue))
            elif eventIdentifier_obj.eventType in range(41,2000):
                rows2,errno2,why2 = ESSMSSQL.DB().action('eventIdentifier','GET3',('eventIdentifierValue',),('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue))
            elif eventIdentifier_obj.eventType >= 2000:
                rows2,errno2,why2 = ESSMSSQL.DB().action('eventStorageMedium','GET3',('eventIdentifierValue',),('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue))
            if errno2:
                logging.error('Problem to access MS-SQL DB ' + str(why2))
            else:
                if rows2:
                    logging.debug('Found eventIdentifierValue: ' + str(eventIdentifier_obj.eventIdentifierValue) + ' in AIS')
                else:
                    logging.info('Missing eventIdentifierValue: ' + str(eventIdentifier_obj.eventIdentifierValue) + ' in AIS try to update')
                    eventDateTime_utc = eventIdentifier_obj.eventDateTime.replace(microsecond=0,tzinfo=pytz.utc)
                    eventDateTime_dst = eventDateTime_utc.astimezone(self.tz)
                    ##########################################################
                    #Update externalDB (AIS) for storagemedium object
                    if eventIdentifier_obj.eventType <= 40:
                        rows3,errno3,why3=ESSMSSQL.DB().action('eventStorageMedium','INS',('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue,
                                                                                                'eventType',eventIdentifier_obj.eventType,
                                                                                                'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                                'eventDetail',eventIdentifier_obj.eventDetail,
                                                                                                'eventApplication',eventIdentifier_obj.eventApplication,
                                                                                                'eventVersion',eventIdentifier_obj.eventVersion,
                                                                                                'eventOutcome',eventIdentifier_obj.eventOutcome,
                                                                                                'eventOutcomeDetailNote',eventIdentifier_obj.eventOutcomeDetailNote,
                                                                                                'linkingAgentIdentifierValue',eventIdentifier_obj.linkingAgentIdentifierValue,
                                                                                                'storageMediumID',eventIdentifier_obj.linkingObjectIdentifierValue))
                        if errno3: logging.error('Failed to insert to External DB: ' + str(eventIdentifier_obj.eventIdentifierValue) + ' error: ' + str(why3))
                    ##########################################################
                    #Update externalDB (AIS) for archive object
                    elif eventIdentifier_obj.eventType in range(41,2000):
                        eventOutcomeDetailNote_MSSQL = ESSMSSQL.escape_string(eventIdentifier_obj.eventOutcomeDetailNote)
                        rows3,errno3,why3=ESSMSSQL.DB().action('eventIdentifier','INS',('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue,
                                                                                             'eventType',eventIdentifier_obj.eventType,
                                                                                             'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                             'eventDetail',eventIdentifier_obj.eventDetail,
                                                                                             'eventApplication',eventIdentifier_obj.eventApplication,
                                                                                             'eventVersion',eventIdentifier_obj.eventVersion,
                                                                                             'eventOutcome',eventIdentifier_obj.eventOutcome,
                                                                                             'eventOutcomeDetailNote',eventOutcomeDetailNote_MSSQL,
                                                                                             'linkingAgentIdentifierValue',eventIdentifier_obj.linkingAgentIdentifierValue,
                                                                                             'linkingObjectIdentifierValue',eventIdentifier_obj.linkingObjectIdentifierValue))
                        if errno3: logging.error('Failed to insert to External DB: ' + str(eventIdentifier_obj.eventIdentifierValue) + ' error: ' + str(why3))
                    ##########################################################
                    #Update externalDB (AIS) for storagemedium object
                    elif eventIdentifier_obj.eventType >= 2000:
                        rows3,errno3,why3=ESSMSSQL.DB().action('eventStorageMedium','INS',('eventIdentifierValue',eventIdentifier_obj.eventIdentifierValue,
                                                                                                'eventType',eventIdentifier_obj.eventType,
                                                                                                'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                                'eventDetail',eventIdentifier_obj.eventDetail,
                                                                                                'eventApplication',eventIdentifier_obj.eventApplication,
                                                                                                'eventVersion',eventIdentifier_obj.eventVersion,
                                                                                                'eventOutcome',eventIdentifier_obj.eventOutcome,
                                                                                                'eventOutcomeDetailNote',eventIdentifier_obj.eventOutcomeDetailNote,
                                                                                                'linkingAgentIdentifierValue',eventIdentifier_obj.linkingAgentIdentifierValue,
                                                                                                'storageMediumID',eventIdentifier_obj.linkingObjectIdentifierValue))
                        if errno3: logging.error('Failed to insert to External DB: ' + str(eventIdentifier_obj.eventIdentifierValue) + ' error: ' + str(why3))

    "sync_IngestObjectMetadata"
    ###############################################
    def sync_IngestObjectMetadata(self,startDateTime,stopDateTime):
        ArchiveObjectMetadata_objs = ArchiveObjectMetadata.objects.filter(LocalDBdatetime__range=(startDateTime,stopDateTime))
        for ArchiveObjectMetadata_obj in ArchiveObjectMetadata_objs:
            if not ArchiveObjectMetadata_obj.check_db_sync():                    
                rows2,errno2,why2 = ESSMSSQL.DB().action('IngestObjectMetadata','GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',ArchiveObjectMetadata_obj.ObjectIdentifierValue,'AND',
                                                                                                            'ObjectMetadataType',str(ArchiveObjectMetadata_obj.ObjectMetadataType)))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if type(ArchiveObjectMetadata_obj.ObjectMetadataBLOB) is not types.NoneType:
                        blob_mssql = ESSMSSQL.escape_string(ArchiveObjectMetadata_obj.ObjectMetadataBLOB)
                    else:
                        blob_mssql = ArchiveObjectMetadata_obj.ObjectMetadataBLOB
                    if rows2:
                        logging.error('Found ObjectIdentifierValue: %s with ObjectMetadataType: %s in AIS, need of manual check!',str(ArchiveObjectMetadata_obj.ObjectIdentifierValue),str(ArchiveObjectMetadata_obj.ObjectMetadataType))
                    else:
                        logging.info('Missing ObjectIdentifierValue: %s with ObjectMetadataType: %s in AIS, try to insert',str(ArchiveObjectMetadata_obj.ObjectIdentifierValue),str(ArchiveObjectMetadata_obj.ObjectMetadataType)) 
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('IngestObjectMetadata','INS',('ObjectIdentifierValue',ArchiveObjectMetadata_obj.ObjectIdentifierValue,
                                                                                           'ObjectMetadataType',ArchiveObjectMetadata_obj.ObjectMetadataType,
                                                                                           'ObjectMetadataBLOB',blob_mssql,
                                                                                           'ObjectMetadataServer',ArchiveObjectMetadata_obj.ObjectMetadataServer,
                                                                                           'ObjectMetadataURL',ArchiveObjectMetadata_obj.ObjectMetadataURL,
                                                                                           'linkingAgentIdentifierValue',ArchiveObjectMetadata_obj.linkingAgentIdentifierValue))
                        if ext_errno: logging.error('Failed to insert to External DB for ObjectIdentifierValue: ' + str(ArchiveObjectMetadata_obj.ObjectIdentifierValue) + ' ObjectMetadataType: ' + str(ArchiveObjectMetadata_obj.ObjectMetadataType) + ' error: ' + str(ext_why))
                        else:
                            ArchiveObjectMetadata_obj.ExtDBdatetime=ArchiveObjectMetadata_obj.LocalDBdatetime
                            ArchiveObjectMetadata_obj.save(update_fields=['ExtDBdatetime'])

    "day_sync_centralDB"
    ###############################################
    def day_sync_centralDB(self,numdays):
        ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)
        #startDateTime = datetime.datetime.replace(datetime.datetime.today()-datetime.timedelta(days=int(numdays)),microsecond=0).isoformat(' ')
        startDateTime = datetime.datetime.replace(datetime.datetime.utcnow()-datetime.timedelta(days=int(numdays)),microsecond=0,tzinfo=pytz.utc).isoformat(' ')
        #stopDateTime = datetime.datetime.replace(datetime.datetime.today(),microsecond=0).isoformat(' ')
        stopDateTime = datetime.datetime.replace(datetime.datetime.utcnow(),microsecond=0,tzinfo=pytz.utc).isoformat(' ')
        logging.info('startDateTime: %s',str(startDateTime))
        logging.info('stopDateTime: %s',stopDateTime)
        if ExtDBupdate:
            work().sync_storageMedium(startDateTime,stopDateTime)
            work().sync_storage(startDateTime,stopDateTime)
            work().sync_IngestObject(startDateTime,stopDateTime)
            work().sync_eventIdentifier(startDateTime,stopDateTime)
            work().sync_IngestObjectMetadata(startDateTime,stopDateTime)
        else:
            logging.info('Skip to update centralDB')

    "sync objects from AIS to ESSArch for mediaid 'XXX001'"
    ###############################################
    def sync_from_centralDB(self,storageMediumID,set_storageMediumLocation='IT_Marieberg',set_storageMediumLocationStatus=''):
        storageMedium_ais_objs,errno,why = ESSMSSQL.DB().action('storageMedium','GET3',('storageMedium',
                                                                               'storageMediumID',
                                                                               'storageMediumDate',
                                                                               'storageMediumLocation',
                                                                               'storageMediumLocationStatus',
                                                                               'storageMediumBlockSize',
                                                                               'storageMediumUsedCapacity',
                                                                               'storageMediumStatus',
                                                                               'storageMediumFormat',
                                                                               'storageMediumMounts',
                                                                               'linkingAgentIdentifierValue',
                                                                               'CreateDate',
                                                                               'CreateAgentIdentifierValue',
                                                                               'StorageMediumGuid'),
                                                                              ('storageMediumID',storageMediumID))
        if errno:
            logging.error('Failed to access central DB ' + str(why))
            return 20
        elif len(storageMedium_ais_objs) == 1:
            storageMedium_ais_obj = storageMedium_ais_objs[0]
            logging.info('Found storageMediumID: %s in central DB',storageMediumID)
            ###################################################
            # Check if storageMediumID exist in local DB
            storageMedium_objs = storageMedium.objects.filter(storageMediumID=storageMediumID)
            #if errno:
            #    logging.error('Failed to access local DB ' + str(why))
            #    return 10
            if len(storageMedium_objs) == 1:
                storageMedium_obj = storageMedium_objs[0]
                if storageMedium_obj.check_db_sync(): # Check if ESSArch and centralDB is in sync
                #if storageMedium_objs[0][1] == 0: # Check if ESSArch and centralDB is in sync
                    ###################################################
                    # storageMediumID exist in local DB try to update

                    ###################################################
                    # Force set storageMediumLocation or storageMediumLocationStatus
                    if set_storageMediumLocation:
                        storageMedium_ais_obj[3] = set_storageMediumLocation
                    if set_storageMediumLocationStatus:
                        storageMedium_ais_obj[4] = set_storageMediumLocationStatus
                        
                    logging.info('Found storageMediumID: %s in local "storageMedium" DB, try to update',storageMediumID)
                    storageMediumDate_dst = storageMedium_ais_obj[2].replace(microsecond=0,tzinfo=self.tz)
                    storageMediumDate_utc = storageMediumDate_dst.astimezone(pytz.utc)
                    CreateDate_dst = storageMedium_ais_obj[11].replace(microsecond=0,tzinfo=self.tz)
                    CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
                    timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    timestamp_dst = timestamp_utc.astimezone(self.tz)
                    #storageMedium_obj.storageMediumUUID = uuid.UUID(bytes_le=storageMedium_ais_obj[13])
                    storageMedium_obj.storageMediumUUID = uuid.UUID(storageMedium_ais_obj[13])
                    storageMedium_obj.storageMedium = storageMedium_ais_obj[0]
                    storageMedium_obj.storageMediumDate = storageMediumDate_utc
                    storageMedium_obj.storageMediumLocation = storageMedium_ais_obj[3]
                    storageMedium_obj.storageMediumLocationStatus = storageMedium_ais_obj[4]
                    storageMedium_obj.storageMediumBlockSize = storageMedium_ais_obj[5]
                    storageMedium_obj.storageMediumUsedCapacity = storageMedium_ais_obj[6]
                    storageMedium_obj.storageMediumStatus = storageMedium_ais_obj[7]
                    storageMedium_obj.storageMediumFormat = storageMedium_ais_obj[8]
                    storageMedium_obj.storageMediumMounts = storageMedium_ais_obj[9]
                    storageMedium_obj.linkingAgentIdentifierValue = storageMedium_ais_obj[10]
                    storageMedium_obj.CreateDate = CreateDate_utc
                    storageMedium_obj.CreateAgentIdentifierValue = storageMedium_ais_obj[12]
                    storageMedium_obj.LocalDBdatetime = timestamp_utc
                    storageMedium_obj.ExtDBdatetime = timestamp_utc
                    storageMedium_obj.save()
                    #if errno: 
                    #    logging.error('Failed to update local DB: %s error: %s', storageMedium_ais_obj[1], str(why))
                    #    return 11
                else:
                    logging.error('Local "storageMedium" DB and Central DB is not in SYNC! for MediaID: %s',storageMediumID)
                    return 14
            elif len(storageMedium_objs) == 0:
                ###################################################
                # storageMediumID not exist in local DB try to insert

                # Force set storageMediumLocation or storageMediumLocationStatus
                if set_storageMediumLocation:
                    storageMedium_ais_obj[3] = set_storageMediumLocation
                if set_storageMediumLocationStatus:
                    storageMedium_ais_obj[4] = set_storageMediumLocationStatus

                logging.info('Missing storageMediumID: %s in local "storageMedium" DB, try to insert',storageMediumID)
                try:
                    if storageMedium_ais_obj[0] in range(300,330):
                        try:
                            target_obj = StorageTargets.objects.get(target=storageMedium_ais_obj[1][:3])
                        except ObjectDoesNotExist:
                            try:
                                target_obj = StorageTargets.objects.get(target=storageMedium_ais_obj[1][:2])
                            except ObjectDoesNotExist:
                                target_obj = StorageTargets.objects.get(target=storageMedium_ais_obj[1][:1])
                    else:
                        target_obj = StorageTargets.objects.get(name=storageMedium_ais_obj[1])
                except (ObjectDoesNotExist, MultipleObjectsReturned) as e:
                    logging.error('Target object not found for storageMediumID: %s, error: %s' % (storageMedium_ais_obj[1], e))
                    return 12
                storageMediumDate_dst = storageMedium_ais_obj[2].replace(microsecond=0,tzinfo=self.tz)
                storageMediumDate_utc = storageMediumDate_dst.astimezone(pytz.utc)
                CreateDate_dst = storageMedium_ais_obj[11].replace(microsecond=0,tzinfo=self.tz)
                CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                timestamp_dst = timestamp_utc.astimezone(self.tz)
                storageMedium_obj = storageMedium()
                storageMedium_obj.id = uuid.UUID(storageMedium_ais_obj[13])
                #storageMedium_obj.storageMediumUUID = uuid.UUID(bytes_le=storageMedium_ais_obj[13])
                storageMedium_obj.storageMediumUUID = uuid.UUID(storageMedium_ais_obj[13])
                storageMedium_obj.storageMedium = storageMedium_ais_obj[0]
                storageMedium_obj.storageMediumID = storageMedium_ais_obj[1]
                storageMedium_obj.storageMediumDate = storageMediumDate_utc
                storageMedium_obj.storageMediumLocation = storageMedium_ais_obj[3]
                storageMedium_obj.storageMediumLocationStatus = storageMedium_ais_obj[4]
                storageMedium_obj.storageMediumBlockSize = storageMedium_ais_obj[5]
                storageMedium_obj.storageMediumUsedCapacity = storageMedium_ais_obj[6]
                storageMedium_obj.storageMediumStatus = storageMedium_ais_obj[7]
                storageMedium_obj.storageMediumFormat = storageMedium_ais_obj[8]
                storageMedium_obj.storageMediumMounts = storageMedium_ais_obj[9]
                storageMedium_obj.linkingAgentIdentifierValue = storageMedium_ais_obj[10]
                storageMedium_obj.CreateDate = CreateDate_utc
                storageMedium_obj.CreateAgentIdentifierValue = storageMedium_ais_obj[12]
                storageMedium_obj.LocalDBdatetime = timestamp_utc
                storageMedium_obj.ExtDBdatetime = timestamp_utc
                storageMedium_obj.storagetarget = target_obj
                storageMedium_obj.save()                                                                  
                #if errno: 
                #    logging.error('Failed to insert to local DB: %s error: %s', storageMedium_ais_obj[1], str(why))
                #    return 12
            else: logging.error('To many storageMediumID found i local "storageMedium" DB for %s', storageMediumID)
            ###################################################
            # Get all archive object for storageMediumID from central DB 
            storage_objs_ext,errno2,why2 = ESSMSSQL.DB().action('storage','GET3',('ObjectIdentifierValue',
                                                                                     'contentLocationType',
                                                                                     'contentLocationValue',
                                                                                     'storageMediumID'),
                                                                                    ('storageMediumID',storageMedium_ais_obj[1]))
            if errno2:
                logging.error('Failed to access central DB ' + str(why2))
                return 20
            elif storage_objs_ext:
                for storage_obj_ext in storage_objs_ext:
                    ###################################################
                    # Get all object for IngestObject from central DB
                    ip_objs_ext,errno3,why3 = ESSMSSQL.DB().action('IngestObject','GET3',('PolicyId',
                                                                                      'ObjectIdentifierValue',
                                                                                      'ObjectPackageName',
                                                                                      'ObjectSize',
                                                                                      'ObjectNumItems',
                                                                                      'ObjectMessageDigestAlgorithm',
                                                                                      'ObjectMessageDigest',
                                                                                      'ObjectPath',
                                                                                      'MetaObjectIdentifier',
                                                                                      'MetaObjectSize',
                                                                                      'CMetaMessageDigestAlgorithm',
                                                                                      'CMetaMessageDigest',
                                                                                      'PMetaMessageDigestAlgorithm',
                                                                                      'PMetaMessageDigest',
                                                                                      'DataObjectSize',
                                                                                      'DataObjectNumItems',
                                                                                      'Status',
                                                                                      'StatusActivity',
                                                                                      'StatusProcess',
                                                                                      'LastEventDate',
                                                                                      'linkingAgentIdentifierValue',
                                                                                      'CreateDate',
                                                                                      'CreateAgentIdentifierValue',
                                                                                      'objectGuid',
                                                                                      'EntryDate',
                                                                                      'EntryAgentIdentifierValue',
                                                                                      'OAISPackageType',
                                                                                      'preservationLevelValue',
                                                                                      'DELIVERYTYPE',
                                                                                      'INFORMATIONCLASS',
                                                                                      'ObjectActive'),
                                                                                     ('ObjectIdentifierValue',storage_obj_ext[0]))
                    if errno3:
                        logging.error('Failed to access central DB ' + str(why3))
                        return 20
                    elif ip_objs_ext:
                        for ip_obj_ext in ip_objs_ext:
                            #logging.debug('storageMediumID: %s ,IngestObjectUUID: %s',storageMediumID,str(uuid.UUID(bytes_le=ip_obj_ext[23])))
                            logging.debug('storageMediumID: %s ,IngestObjectUUID: %s',storageMediumID,str(uuid.UUID(ip_obj_ext[23])))
                            LastEventDate_dst = ip_obj_ext[19].replace(microsecond=0,tzinfo=self.tz)
                            LastEventDate_utc = LastEventDate_dst.astimezone(pytz.utc)
                            CreateDate_dst = ip_obj_ext[21].replace(microsecond=0,tzinfo=self.tz)
                            CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
                            EntryDate_dst = ip_obj_ext[24].replace(microsecond=0,tzinfo=self.tz)
                            EntryDate_utc = EntryDate_dst.astimezone(pytz.utc)
                            ###################################################
                            # Check if archive object exist in local "IngestObject" DB
                            ArchiveObject_objs = ArchiveObject.objects.filter(ObjectIdentifierValue=ip_obj_ext[1])
                            #if errno:
                            #    logging.error('Failed to access local DB ' + str(why))
                            #    return 10
                            if len(ArchiveObject_objs) == 1:
                                ip_obj = ArchiveObject_objs[0]
                                if ip_obj.check_db_sync(): # Check if ESSArch and centralDB is in sync
                                    ###################################################
                                    # archive object exist in local "IngestObject" DB try to update
                                    logging.info('Found archive object: %s in local "IngestObject" DB for storageMediumID: %s, try to update',ip_obj_ext[1],storageMediumID)
                                    timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                    timestamp_dst = timestamp_utc.astimezone(self.tz)
                                    ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = ip_obj_ext[0])
                                    #ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue = ip_obj_ext[1])
                                    ip_obj.PolicyId = ArchivePolicy_obj
                                    ip_obj.ObjectPackageName = ip_obj_ext[2]
                                    ip_obj.ObjectSize = ip_obj_ext[3]
                                    ip_obj.ObjectNumItems = ip_obj_ext[4]
                                    ip_obj.ObjectMessageDigestAlgorithm = ip_obj_ext[5]
                                    ip_obj.ObjectMessageDigest = ip_obj_ext[6]
                                    ip_obj.ObjectPath = ip_obj_ext[7]
                                    ip_obj.MetaObjectIdentifier = ip_obj_ext[8]
                                    ip_obj.MetaObjectSize = ip_obj_ext[9]
                                    ip_obj.CMetaMessageDigestAlgorithm = ip_obj_ext[10]
                                    ip_obj.CMetaMessageDigest = ip_obj_ext[11]
                                    ip_obj.PMetaMessageDigestAlgorithm = ip_obj_ext[12]
                                    ip_obj.PMetaMessageDigest = ip_obj_ext[13]
                                    ip_obj.DataObjectSize = ip_obj_ext[14]
                                    ip_obj.DataObjectNumItems = ip_obj_ext[15]
                                    ip_obj.Status = ip_obj_ext[16]
                                    ip_obj.StatusActivity = ip_obj_ext[17]
                                    ip_obj.StatusProcess = ip_obj_ext[18]
                                    ip_obj.LastEventDate = LastEventDate_utc
                                    ip_obj.linkingAgentIdentifierValue = ip_obj_ext[20]
                                    ip_obj.CreateDate = CreateDate_utc
                                    ip_obj.CreateAgentIdentifierValue = ip_obj_ext[22]
                                    #ip_obj.ObjectUUID = uuid.UUID(bytes_le=ip_obj_ext[23])
                                    ip_obj.ObjectUUID = uuid.UUID(ip_obj_ext[23])
                                    ip_obj.EntryDate = EntryDate_utc
                                    ip_obj.EntryAgentIdentifierValue = ip_obj_ext[25]
                                    ip_obj.OAISPackageType = ip_obj_ext[26]
                                    ip_obj.preservationLevelValue = ip_obj_ext[27]
                                    ip_obj.DELIVERYTYPE = ip_obj_ext[28]
                                    ip_obj.INFORMATIONCLASS = ip_obj_ext[29]
                                    ip_obj.ObjectActive = ip_obj_ext[30]
                                    ip_obj.LocalDBdatetime = timestamp_utc
                                    ip_obj.ExtDBdatetime = timestamp_utc
                                    ip_obj.save()
                                    #if errno: 
                                    #    logging.error('Failed to update local "IngestObject" DB: %s, %s error: %s', ip_obj_ext[1], storageMediumID, str(why))
                                    #    return 11
                                else:
                                    logging.error('Local "IngestObject" DB and Central DB is not in SYNC! for MediaID: %s and Object: %s',storageMediumID,ip_obj_ext[1])
                                    return 14
                            elif len(ArchiveObject_objs) == 0:
                                ###################################################
                                # archive object not exist in local "IngestObject" DB try to insert
                                logging.info('Missing archive object: %s in local "IngestObject" DB for storageMediumID: %s, try to insert',ip_obj_ext[1],storageMediumID)
                                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                timestamp_dst = timestamp_utc.astimezone(self.tz)
                                ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = ip_obj_ext[0])
                                ip_obj = ArchiveObject()
                                ip_obj.PolicyId = ArchivePolicy_obj
                                ip_obj.ObjectIdentifierValue = ip_obj_ext[1]
                                ip_obj.ObjectPackageName = ip_obj_ext[2]
                                ip_obj.ObjectSize = ip_obj_ext[3]
                                ip_obj.ObjectNumItems = ip_obj_ext[4]
                                ip_obj.ObjectMessageDigestAlgorithm = ip_obj_ext[5]
                                ip_obj.ObjectMessageDigest = ip_obj_ext[6]
                                ip_obj.ObjectPath = ip_obj_ext[7]
                                ip_obj.MetaObjectIdentifier = ip_obj_ext[8]
                                ip_obj.MetaObjectSize = ip_obj_ext[9]
                                ip_obj.CMetaMessageDigestAlgorithm = ip_obj_ext[10]
                                ip_obj.CMetaMessageDigest = ip_obj_ext[11]
                                ip_obj.PMetaMessageDigestAlgorithm = ip_obj_ext[12]
                                ip_obj.PMetaMessageDigest = ip_obj_ext[13]
                                ip_obj.DataObjectSize = ip_obj_ext[14]
                                ip_obj.DataObjectNumItems = ip_obj_ext[15]
                                ip_obj.Status = ip_obj_ext[16]
                                ip_obj.StatusActivity = ip_obj_ext[17]
                                ip_obj.StatusProcess = ip_obj_ext[18]
                                ip_obj.LastEventDate = LastEventDate_utc
                                ip_obj.linkingAgentIdentifierValue = ip_obj_ext[20]
                                ip_obj.CreateDate = CreateDate_utc
                                ip_obj.CreateAgentIdentifierValue = ip_obj_ext[22]
                                #ip_obj.ObjectUUID = uuid.UUID(bytes_le=ip_obj_ext[23])
                                ip_obj.ObjectUUID = uuid.UUID(ip_obj_ext[23])
                                ip_obj.EntryDate = EntryDate_utc
                                ip_obj.EntryAgentIdentifierValue = ip_obj_ext[25]
                                ip_obj.OAISPackageType = ip_obj_ext[26]
                                ip_obj.preservationLevelValue = ip_obj_ext[27]
                                ip_obj.DELIVERYTYPE = ip_obj_ext[28]
                                ip_obj.INFORMATIONCLASS = ip_obj_ext[29]
                                ip_obj.ObjectActive = ip_obj_ext[30]
                                ip_obj.LocalDBdatetime = timestamp_utc
                                ip_obj.ExtDBdatetime = timestamp_utc
                                ip_obj.save()
                                #if errno: 
                                #    logging.error('Failed to insert to local "IngestObject" DB: %s, %s error: %s', ip_obj_ext[1], storageMediumID, str(why))
                                #    return 11
                            else: 
                                logging.error('To many objects found in local "IngestObject" DB for %s', ip_obj_ext[1])
                                return 13
                        logging.debug('storageMediumID: %s ,storageObject: %s',storageMediumID,storage_obj_ext[0])
                        ###################################################
                        # Check if archive object exist in local "storage" DB
                        storage_objs = ip_obj.Storage_set.filter(contentLocationType=storage_obj_ext[1],
                                                                          contentLocationValue=storage_obj_ext[2],
                                                                          storagemedium=storageMedium_obj)
                        #if errno:
                        #    logging.error('Failed to access local DB ' + str(why))
                        #    return 10
                        if len(storage_objs) == 1:
                            storage_obj = storage_objs[0]
                            if storage_obj.check_db_sync(): # Check if ESSArch and centralDB is in sync
                                ###################################################
                                # archive object exist in local "storage" DB try to update
                                logging.info('Found archive object: %s in local "storage" DB for storageMediumID: %s, try to update',storage_obj_ext[0],storageMediumID)
                                timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                timestamp_dst = timestamp_utc.astimezone(self.tz)
                                storage_obj.contentLocationType = storage_obj_ext[1]
                                storage_obj.contentLocationValue = storage_obj_ext[2]
                                storage_obj.LocalDBdatetime = timestamp_utc
                                storage_obj.ExtDBdatetime = timestamp_utc
                                storage_obj.save()                           
                                #if errno: 
                                #    logging.error('Failed to update local "storage" DB: %s, %s error: %s', storage_obj_ext[0], storage_obj_ext[3], str(why))
                                #    return 11
                            else:
                                logging.error('Local "storage" DB and Central DB is not in SYNC! for MediaID: %s and Object: %s',storageMediumID,storage_obj_ext[0])
                                return 14
                        elif len(storage_objs) == 0:
                            ###################################################
                            # archive object not exist in local "storage" DB try to insert
                            logging.info('Missing archive object: %s in local "storage" DB for storageMediumID: %s, try to insert',storage_obj_ext[0],storageMediumID)
                            timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                            timestamp_dst = timestamp_utc.astimezone(self.tz)
                            storage_obj = storage()
                            storage_obj.contentLocationType = storage_obj_ext[1]
                            storage_obj.contentLocationValue = storage_obj_ext[2]
                            storage_obj.storagemedium = storageMedium_obj
                            storage_obj.archiveobject = ip_obj
                            storage_obj.LocalDBdatetime = timestamp_utc
                            storage_obj.ExtDBdatetime = timestamp_utc
                            storage_obj.save()   
                            #if errno: 
                            #    logging.error('Failed to insert to local "storage" DB: %s, %s error: %s', storage_obj_ext[0], storage_obj_ext[3], str(why))
                            #    return 12
                        else: 
                            logging.error('To many objects found i local "storage" DB for %s', storage_obj_ext[0])
                            return 13
                    else:
                        logging.info('No archive objects found for storageMedia %s in central "IngestObject" DB', storageMediumID)
                        return 3
            else: 
                logging.info('No archive objects found for storageMedia %s in central "storage" DB', storageMediumID)
                return 2
        elif len(storageMedium_ais_objs) > 1:
            logging.error('To many storagemedias found in central "storageMedium" DB for %s', storageMediumID)
            return 23
        else:
            logging.info('storageMedia %s not found in central "storageMedium" DB', storageMediumID)
            return 1
        logging.info('Succeed to update local DB for storageMedia %s', storageMediumID)
        return 0

#######################################################################################################
# Dep:
#######################################################################################################
if __name__ == '__main__':
    ProcName = 'db_sync_ais'
    ProcVersion = __version__

    op = OptionParser(prog=ProcName,usage="usage: %prog [options] arg", version="%prog Version " + str(ProcVersion))
    op.add_option("-d", "--days", help="Days back in time (DAYS: 1)", dest="days", metavar="DAYS")
    op.add_option("--StartDateTime", help="StartDateTime (TIMESTAMP: '2009-01-01 00:00:00')", dest="startDateTime", metavar="TIMESTAMP")
    op.add_option("--stopDateTime", help="stopDateTime (TIMESTAMP: '2009-01-01 00:00:00')", dest="stopDateTime", metavar="TIMESTAMP")
    op.add_option("-t", "--table", help="Only one table (TABLE: storageMedium, storage, IngestObject, eventIdentifier, IngestObjectMetadata) (Default all)", dest="table", metavar="TABLE")
    op.add_option("-g", "--GetStorageMediaID", help="Get Storage Medium ID from Central DB (MediaID exmaple: 'TSA001')", dest="GetStorageMediaID", metavar="MediaID")
    op.add_option("-x", "--LogLevel", help="Set LogLevel (LEVEL: CRITICAL, ERROR, WARNING, INFO, DEBUG) (Default INFO)", dest="LogLevel", metavar="LEVEL")
    op.add_option("-p", "--process", help="ESSArch process", action="store_true", dest="process")
    op.add_option("-q", "--quiet", help="No information to console", action="store_true", dest="quiet")
    options, args = op.parse_args()

    optionflag = 1
    if options.process:
        optionflag = 0
        options.quiet = 1
    if options.days:
        optionflag = 0
        #startDateTime = datetime.datetime.replace(datetime.datetime.today()-datetime.timedelta(days=int(options.days)),microsecond=0).isoformat(' ')
        startDateTime = datetime.datetime.replace(datetime.datetime.utcnow()-datetime.timedelta(days=int(options.days)),microsecond=0,tzinfo=pytz.utc).isoformat(' ')
    elif options.startDateTime:
        optionflag = 0
        try: startDateTime = datetime.datetime.replace(datetime.datetime.strptime(options.startDateTime,"%Y-%m-%d %H:%M:%S"),microsecond=0,tzinfo=pytz.utc).isoformat(' ')
        except: op.error("Invalid startDateTime")
    elif options.GetStorageMediaID:
        optionflag = 0
        if not len(options.GetStorageMediaID) == 6: op.error("Invalid MediaID")

    if optionflag: op.error("incorrect options")

    if options.stopDateTime:
        try: stopDateTime = datetime.datetime.replace(datetime.datetime.strptime(options.stopDateTime,"%Y-%m-%d %H:%M:%S"),microsecond=0,tzinfo=pytz.utc).isoformat(' ')
        except: op.error("Invalid stopDateTime")
    else:
        stopDateTime = datetime.datetime.replace(datetime.datetime.utcnow(),microsecond=0,tzinfo=pytz.utc).isoformat(' ')

    if options.LogLevel: 
        if options.LogLevel == 'CRITICAL': LogLevel = 50
        elif options.LogLevel == 'ERROR': LogLevel = 40
        elif options.LogLevel == 'WARNING': LogLevel = 30
        elif options.LogLevel == 'INFO': LogLevel = 20
        elif options.LogLevel == 'DEBUG': LogLevel = 10
        else: op.error("Invalid LogLevel")
        if LogLevel == 10: Debug = 1
        else: Debug = 0
    else: 
        LogLevel = 20
        Debug = 0
    if options.quiet: Console = 0
    else: Console = 1

    if options.process:
        LogFile,Time,Status,Run = ESSProc.objects.filter(Name=ProcName).values_list('LogFile','Time','Status','Run')[0]
    else:
        LogFile = '/ESSArch/log/db_sync/ais.log'
    ##########################
    # Log format
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
    ##########################
    # Add handlers to default logger
    logging.getLogger('').setLevel(0)
    logging.getLogger('').addHandler(essLocalFileHandler)
    if Console: logging.getLogger('').addHandler(essConsoleHandler)

    if options.table:
        logging.debug('table: %s',str(options.table))
        logging.info('startDateTime: %s',startDateTime)
        logging.info('stopDateTime: %s',stopDateTime)
        if options.table == 'storageMedium': work().sync_storageMedium(startDateTime,stopDateTime)
        elif options.table == 'storage': work().sync_storage(startDateTime,stopDateTime)
        elif options.table == 'IngestObject': work().sync_IngestObject(startDateTime,stopDateTime)
        elif options.table == 'eventIdentifier': work().sync_eventIdentifier(startDateTime,stopDateTime)
        elif options.table == 'IngestObjectMetadata': work().sync_IngestObjectMetadata(startDateTime,stopDateTime)
        else: op.error("incorrect table option")
    elif not options.GetStorageMediaID and not options.process:
        logging.info('startDateTime: %s',str(startDateTime))
        logging.info('stopDateTime: %s',stopDateTime)
        work().sync_storageMedium(startDateTime,stopDateTime)
        work().sync_storage(startDateTime,stopDateTime)
        work().sync_IngestObject(startDateTime,stopDateTime)
        work().sync_eventIdentifier(startDateTime,stopDateTime)
        work().sync_IngestObjectMetadata(startDateTime,stopDateTime)
    elif options.process:
        s = ESSsched.ThreadedScheduler()
        logging.info('Add sync to schedule daily')
        s.add_daytime_task( work().day_sync_centralDB, "day_sync_centralDB action", (1,2,3,4,5,6,7), 0, (07,00),  ESSsched.method.threaded, [Time], None ) 
        s.start()
        while 1:
            Time,Status,Run = ESSProc.objects.filter(Name=ProcName).values_list('Time','Status','Run')[0]
            if Run == '0':
                logging.info('Stopping ' + ProcName)
                ESSProc.objects.filter(Name=ProcName).update(Status='0', Run='0', PID=0)
                s.stop()
                break
            time.sleep(10)
            
    elif options.GetStorageMediaID:
        logging.info('MediaID: %s',str(options.GetStorageMediaID))
        work().sync_from_centralDB(options.GetStorageMediaID)
    
    #startDateTime = datetime.datetime.today()-datetime.timedelta(days=1)
    #stopDateTime = datetime.datetime.today()
    #print 'startDateTime', startDateTime
    #print 'stopDateTime', stopDateTime
#    work().sync_storageMedium('2009-01-01 00:00:00','2019-01-15 23:59:59')
#    work().sync_storage('2009-01-01 00:00:00','2019-01-15 23:59:59')
#    work().sync_IngestObject('2009-01-01 00:00:00','2019-01-15 23:59:59')
#    wora().sync_eventIdentifier('2009-01-01 00:00:00','2019-01-15 23:59:59')

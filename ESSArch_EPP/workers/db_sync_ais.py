#!/usr/bin/env /ESSArch/pd/python/bin/python
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB, Henrik Ek

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
import sys, logging, logging.handlers, datetime, time, uuid, ESSDB, ESSMSSQL, ESSsched, types, pytz
from optparse import OptionParser
from django.utils import timezone
from essarch.models import storageMedium, storage, ArchiveObject
from configuration.models import ESSArchPolicy
from django import db

class work:
    TimeZone = timezone.get_default_timezone_name()
    tz=pytz.timezone(TimeZone)
    "sync_storageMedium"
    ###############################################
    def sync_storageMedium(self,startDateTime,stopDateTime):
        self.table = 'storageMedium'
        self.rows,errno,why = ESSDB.DB().action(self.table,'GET4',('id',
                                                                   'storageMediumUUID',
                                                                   'storageMedium',
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
                                                                   'LocalDBdatetime',
                                                                   'ExtDBdatetime'),
                                                                  ('LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'ExtDBdatetime','IS','NULL','AND',
                                                                   'LocalDBdatetime','IS NOT','NULL',
                                                                   'OR',
                                                                   'LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)','<', '0'))

        if errno:
            logging.error('Problem to access MySQL DB ' + str(why))
        else:
            for self.i in self.rows:
                self.rows2,errno2,why2 = ESSMSSQL.DB().action(self.table,'GET3',('storageMediumID',),('storageMediumID',self.i[3]))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    storageMediumDate_utc = self.i[4].replace(microsecond=0,tzinfo=pytz.utc)
                    storageMediumDate_dst = storageMediumDate_utc.astimezone(self.tz)
                    CreateDate_utc = self.i[13].replace(microsecond=0,tzinfo=pytz.utc)
                    CreateDate_dst = CreateDate_utc.astimezone(self.tz)
                    if self.rows2:
                        logging.info('Found storageMediumID: ' + str(self.i[3]) + ' in AIS, try to update')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.table,'UPD',('StorageMediumGuid',self.i[1],
                                                                                           'storageMedium',self.i[2],
                                                                                           'storageMediumDate',storageMediumDate_dst.replace(tzinfo=None),
                                                                                           'storageMediumLocation',self.i[5],
                                                                                           'storageMediumLocationStatus',self.i[6],
                                                                                           'storageMediumBlockSize',self.i[7],
                                                                                           'storageMediumUsedCapacity',self.i[8],
                                                                                           'storageMediumStatus',self.i[9],
                                                                                           'storageMediumFormat',self.i[10],
                                                                                           'storageMediumMounts',self.i[11],
                                                                                           'linkingAgentIdentifierValue',self.i[12],
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',self.i[14]),
                                                                                          ('storageMediumID',self.i[3]))
                        if ext_errno: logging.error('Failed to update External DB: ' + str(self.i[3]) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[15]),('id',self.i[0]))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.i[3]) + ' error: ' + str(why))
                    else:
                        logging.info('Missing storageMediumID: ' + str(self.i[3]) + ' in AIS, try to insert')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.table,'INS',('StorageMediumGuid',self.i[1],
                                                                                           'storageMedium',self.i[2],
                                                                                           'storageMediumID',self.i[3],
                                                                                           'storageMediumDate',storageMediumDate_dst.replace(tzinfo=None),
                                                                                           'storageMediumLocation',self.i[5],
                                                                                           'storageMediumLocationStatus',self.i[6],
                                                                                           'storageMediumBlockSize',self.i[7],
                                                                                           'storageMediumUsedCapacity',self.i[8],
                                                                                           'storageMediumStatus',self.i[9],
                                                                                           'storageMediumFormat',self.i[10],
                                                                                           'storageMediumMounts',self.i[11],
                                                                                           'linkingAgentIdentifierValue',self.i[12],
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',self.i[14]))
                        if ext_errno: logging.error('Failed to insert to External DB: ' + str(self.i[3]) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[15]),('id',self.i[0]))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.i[3]) + ' error: ' + str(why))

    "sync_storage"
    ###############################################
    def sync_storage(self,startDateTime,stopDateTime):
        self.table = 'storage'
        self.rows,errno,why = ESSDB.DB().action(self.table,'GET4',('id',
                                                                   'ObjectIdentifierValue',
                                                                   'contentLocationType',
                                                                   'contentLocationValue',
                                                                   'storageMediumID',
                                                                   'LocalDBdatetime',
                                                                   'ExtDBdatetime'),
                                                                  ('LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'ExtDBdatetime','IS','NULL','AND',
                                                                   'LocalDBdatetime','IS NOT','NULL',
                                                                   'OR',
                                                                   'LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)','<', '0'))
        if errno:
            logging.error('Problem to access MySQL DB ' + str(why))
        else:
            for self.i in self.rows:
                self.rows2,errno2,why2 = ESSMSSQL.DB().action(self.table,'GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',self.i[1],'AND',
                                                                                                            'contentLocationType',str(self.i[2]),'AND',
                                                                                                            'contentLocationValue',self.i[3],'AND',
                                                                                                            'storageMediumID',self.i[4]))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if self.rows2:
                        logging.info('Found ObjectIdentifierValue: ' + str(self.i[1]) + ' contentLocationType: ' + str(self.i[2]) + ' contentLocationValue: ' + str(self.i[3]) + ' storageMediumID: ' + str(self.i[4]) + ' in AIS, nothing to update')
                        res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[5]),('id',self.i[0]))
                        if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(self.i[1]) + ' contentLocationType: ' + str(self.i[2]) + ' contentLocationValue: ' + str(self.i[3]) + ' storageMediumID: ' + str(self.i[4]) + ' error: ' + str(why))
                    else:
                        logging.info('Missing ObjectIdentifierValue: ' + str(self.i[1]) + ' contentLocationType: ' + str(self.i[2]) + ' contentLocationValue: ' + str(self.i[3]) + ' storageMediumID: ' + str(self.i[4]) + ' in AIS, try to insert')
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.table,'INS',('ObjectIdentifierValue',self.i[1],
                                                                                           'contentLocationType',self.i[2],
                                                                                           'contentLocationValue',self.i[3],
                                                                                           'storageMediumID',self.i[4]))
                        if ext_errno: logging.error('Failed to insert to External DB for ObjectIdentifierValue: ' + str(self.i[1]) + ' contentLocationType: ' + str(self.i[2]) + ' contentLocationValue: ' + str(self.i[3]) + ' storageMediumID: ' + str(self.i[4]) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[5]),('id',self.i[0]))
                            if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(self.i[1]) + ' contentLocationType: ' + str(self.i[2]) + ' contentLocationValue: ' + str(self.i[3]) + ' storageMediumID: ' + str(self.i[4]) + ' error: ' + str(why))

    "sync_IngestObject"
    ###############################################
    def sync_IngestObject(self,startDateTime,stopDateTime):
        self.table = 'IngestObject'
        self.rows,errno,why = ESSDB.DB().action(self.table,'GET4',('id',
                                                                   'ObjectUUID',
                                                                   'PolicyId',
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
                                                                   'EntryDate',
                                                                   'EntryAgentIdentifierValue',
                                                                   'OAISPackageType',
                                                                   'preservationLevelValue',
                                                                   'DELIVERYTYPE',
                                                                   'INFORMATIONCLASS',
                                                                   'LocalDBdatetime',
                                                                   'ExtDBdatetime'),
                                                                  ('LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'ExtDBdatetime','IS','NULL','AND',
                                                                   'LocalDBdatetime','IS NOT','NULL',
                                                                   'OR',
                                                                   'LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)','<', '0'))
        if errno:
            logging.error('Problem to access MySQL DB ' + str(why))
        else:
            for self.i in self.rows:
                self.rows2,errno2,why2 = ESSMSSQL.DB().action(self.table,'GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',self.i[3]))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if self.rows2:
                        logging.info('Found ObjectIdentifierValue: ' + str(self.i[3]) + ' in AIS, try to update')
                        LastEventDate_utc = self.i[21].replace(microsecond=0,tzinfo=pytz.utc)
                        LastEventDate_dst = LastEventDate_utc.astimezone(self.tz)
                        CreateDate_utc = self.i[23].replace(microsecond=0,tzinfo=pytz.utc)
                        CreateDate_dst = CreateDate_utc.astimezone(self.tz)
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.table,'UPD',('PolicyId',self.i[2],
                                                                                           'ObjectPackageName',self.i[4],
                                                                                           'ObjectSize',self.i[5],
                                                                                           'ObjectNumItems',self.i[6],
                                                                                           'ObjectMessageDigestAlgorithm',self.i[7],
                                                                                           'ObjectMessageDigest',self.i[8],
                                                                                           'ObjectPath',self.i[9],
                                                                                           'MetaObjectIdentifier',self.i[10],
                                                                                           'MetaObjectSize',self.i[11],
                                                                                           'CMetaMessageDigestAlgorithm',self.i[12],
                                                                                           'CMetaMessageDigest',self.i[13],
                                                                                           'PMetaMessageDigestAlgorithm',self.i[14],
                                                                                           'PMetaMessageDigest',self.i[15],
                                                                                           'DataObjectSize',self.i[16],
                                                                                           'DataObjectNumItems',self.i[17],
                                                                                           #'Status',self.i[18],
                                                                                           'StatusActivity',self.i[19],
                                                                                           'StatusProcess',self.i[20],
                                                                                           'LastEventDate',LastEventDate_dst.replace(tzinfo=None),
                                                                                           'linkingAgentIdentifierValue',self.i[22],
                                                                                           'CreateDate',CreateDate_dst.replace(tzinfo=None),
                                                                                           'CreateAgentIdentifierValue',self.i[24],
                                                                                           #'EntryDate',self.i[25],
                                                                                           #'EntryAgentIdentifierValue',self.i[26],
                                                                                           'OAISPackageType',self.i[27],
                                                                                           'preservationLevelValue',self.i[28],
                                                                                           'DELIVERYTYPE',self.i[29],
                                                                                           'INFORMATIONCLASS',self.i[30]),
                                                                                          ('ObjectIdentifierValue',self.i[3]))
                        if ext_errno: logging.error('Failed to update External DB: ' + str(self.i[3]) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[31]),('id',self.i[0]))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.i[3]) + ' error: ' + str(why))
                    else:
                        logging.error('Missing ObjectIdentifierValue: ' + str(self.i[3]) + ' in AIS IngestObject, need of manual check!')

    "sync_eventIdentifier"
    ###############################################
    def sync_eventIdentifier(self,startDateTime,stopDateTime):
        self.table = 'eventIdentifier'
        self.rows,errno,why = ESSDB.DB().action(self.table,'GET4',('id',
                                                                   'eventIdentifierValue',
                                                                   'eventType',
                                                                   'eventDateTime',
                                                                   'eventDetail',
                                                                   'eventApplication',
                                                                   'eventVersion',
                                                                   'eventOutcome',
                                                                   'eventOutcomeDetailNote',
                                                                   'linkingAgentIdentifierValue',
                                                                   'linkingObjectIdentifierValue'),
                                                                  ('eventDateTime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'"))
        if errno:
            logging.error('Problem to access MySQL DB ' + str(why))
        else:
            for self.i in self.rows:
                if int(self.i[2]) <= 40:
                    self.rows2,errno2,why2 = ESSMSSQL.DB().action('eventStorageMedium','GET3',('eventIdentifierValue',),('eventIdentifierValue',self.i[1]))
                elif int(self.i[2]) in range(41,2000):
                    self.rows2,errno2,why2 = ESSMSSQL.DB().action('eventIdentifier','GET3',('eventIdentifierValue',),('eventIdentifierValue',self.i[1]))
                elif int(self.i[2]) >= 2000:
                    self.rows2,errno2,why2 = ESSMSSQL.DB().action('eventStorageMedium','GET3',('eventIdentifierValue',),('eventIdentifierValue',self.i[1]))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if self.rows2:
                        logging.debug('Found eventIdentifierValue: ' + str(self.i[1]) + ' in AIS')
                    else:
                        logging.info('Missing eventIdentifierValue: ' + str(self.i[1]) + ' in AIS try to update')
                        eventDateTime_utc = self.i[3].replace(microsecond=0,tzinfo=pytz.utc)
                        eventDateTime_dst = eventDateTime_utc.astimezone(self.tz)
                        ##########################################################
                        #Update externalDB (AIS) for storagemedium object
                        if int(self.i[2]) <= 40:
                            self.rows3,errno3,why3=ESSMSSQL.DB().action('eventStorageMedium','INS',('eventIdentifierValue',self.i[1],
                                                                                                    'eventType',self.i[2],
                                                                                                    'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                                    'eventDetail',self.i[4],
                                                                                                    'eventApplication',self.i[5],
                                                                                                    'eventVersion',self.i[6],
                                                                                                    'eventOutcome',self.i[7],
                                                                                                    'eventOutcomeDetailNote',self.i[8],
                                                                                                    'linkingAgentIdentifierValue',self.i[9],
                                                                                                    'storageMediumID',self.i[10]))
                            if errno3: logging.error('Failed to insert to External DB: ' + str(self.i[1]) + ' error: ' + str(why3))
                        ##########################################################
                        #Update externalDB (AIS) for archive object
                        elif int(self.i[2]) in range(41,2000):
                            eventOutcomeDetailNote_MSSQL = ESSMSSQL.escape_string(self.i[8])
                            self.rows3,errno3,why3=ESSMSSQL.DB().action('eventIdentifier','INS',('eventIdentifierValue',self.i[1],
                                                                                                 'eventType',self.i[2],
                                                                                                 'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                                 'eventDetail',self.i[4],
                                                                                                 'eventApplication',self.i[5],
                                                                                                 'eventVersion',self.i[6],
                                                                                                 'eventOutcome',self.i[7],
                                                                                                 'eventOutcomeDetailNote',eventOutcomeDetailNote_MSSQL,
                                                                                                 'linkingAgentIdentifierValue',self.i[9],
                                                                                                 'linkingObjectIdentifierValue',self.i[10]))
                            if errno3: logging.error('Failed to insert to External DB: ' + str(self.i[1]) + ' error: ' + str(why3))
                        ##########################################################
                        #Update externalDB (AIS) for storagemedium object
                        elif int(self.i[2]) >= 2000:
                            self.rows3,errno3,why3=ESSMSSQL.DB().action('eventStorageMedium','INS',('eventIdentifierValue',self.i[1],
                                                                                                    'eventType',self.i[2],
                                                                                                    'eventDateTime',eventDateTime_dst.replace(tzinfo=None),
                                                                                                    'eventDetail',self.i[4],
                                                                                                    'eventApplication',self.i[5],
                                                                                                    'eventVersion',self.i[6],
                                                                                                    'eventOutcome',self.i[7],
                                                                                                    'eventOutcomeDetailNote',self.i[8],
                                                                                                    'linkingAgentIdentifierValue',self.i[9],
                                                                                                    'storageMediumID',self.i[10]))
                            if errno3: logging.error('Failed to insert to External DB: ' + str(self.i[1]) + ' error: ' + str(why3))

    "sync_IngestObjectMetadata"
    ###############################################
    def sync_IngestObjectMetadata(self,startDateTime,stopDateTime):
        self.table = 'IngestObjectMetadata'
        self.rows,errno,why = ESSDB.DB().action(self.table,'GET4',('id',
                                                                   'ObjectUUID',
                                                                   'ObjectIdentifierValue',
                                                                   'ObjectMetadataType',
                                                                   'ObjectMetadataBLOB',
                                                                   'ObjectMetadataServer',
                                                                   'ObjectMetadataURL',
                                                                   'linkingAgentIdentifierValue',
                                                                   'LocalDBdatetime',
                                                                   'ExtDBdatetime'),
                                                                  ('LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'ExtDBdatetime','IS','NULL','AND',
                                                                   'LocalDBdatetime','IS NOT','NULL',
                                                                   'OR',
                                                                   'LocalDBdatetime','BETWEEN',"'" + startDateTime + "'",'AND',"'" + stopDateTime + "'",'AND',
                                                                   'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)','<', '0'))
        if errno:
            logging.error('Problem to access MySQL DB ' + str(why))
        else:
            for self.i in self.rows:
                self.rows2,errno2,why2 = ESSMSSQL.DB().action(self.table,'GET3',('ObjectIdentifierValue',),('ObjectIdentifierValue',self.i[2],'AND',
                                                                                                            'ObjectMetadataType',str(self.i[3])))
                if errno2:
                    logging.error('Problem to access MS-SQL DB ' + str(why2))
                else:
                    if type(self.i[4]) is not types.NoneType:
                        self.blob_mssql = ESSMSSQL.escape_string(self.i[4])
                    else:
                        self.blob_mssql = self.i[4]
                    if self.rows2:
                        logging.error('Found ObjectIdentifierValue: %s with ObjectMetadataType: %s in AIS, need of manual check!',str(self.i[2]),str(self.i[3]))
                        #res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[5]),('id',self.i[0]))
                        #if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(self.i[2]) + ' ObjectMetadataType: ' + str(self.i[3]) + ' error: ' + str(why))
                    else:
                        logging.info('Missing ObjectIdentifierValue: %s with ObjectMetadataType: %s in AIS, try to insert',str(self.i[2]),str(self.i[3])) 
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.table,'INS',('ObjectIdentifierValue',self.i[2],
                                                                                           'ObjectMetadataType',self.i[3],
                                                                                           'ObjectMetadataBLOB',self.blob_mssql,
                                                                                           'ObjectMetadataServer',self.i[5],
                                                                                           'ObjectMetadataURL',self.i[6],
                                                                                           'linkingAgentIdentifierValue',self.i[7]))
                        if ext_errno: logging.error('Failed to insert to External DB for ObjectIdentifierValue: ' + str(self.i[2]) + ' ObjectMetadataType: ' + str(self.i[3]) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.table,'UPD',('ExtDBdatetime',self.i[8]),('id',self.i[0]))
                            if errno: logging.error('Failed to update Local DB for ObjectIdentifierValue: ' + str(self.i[2]) + ' ObjectMetadataType: ' + str(self.i[3]) + ' error: ' + str(why))

    "day_sync_centralDB"
    ###############################################
    def day_sync_centralDB(self,numdays):
        ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])
        startDateTime = datetime.datetime.replace(datetime.datetime.today()-datetime.timedelta(days=int(numdays)),microsecond=0).isoformat(' ')
        stopDateTime = datetime.datetime.replace(datetime.datetime.today(),microsecond=0).isoformat(' ')
        logging.info('startDateTime: %s',str(startDateTime))
        logging.info('stopDateTime: %s',stopDateTime)
        if ExtDBupdate:
            work().sync_storageMedium(startDateTime,stopDateTime)
            work().sync_storage(startDateTime,stopDateTime)
            work().sync_IngestObject(startDateTime,stopDateTime)
            work().sync_eventIdentifier(startDateTime,stopDateTime)
            work().sync_IngestObjectMetadata(startDateTime,stopDateTime)
            db.close_old_connections()
        else:
            logging.info('Skip to update centralDB')

    "sync objects from AIS to ESSArch for mediaid 'XXX001'"
    ###############################################
    def sync_from_centralDB(self,storageMediumID,set_storageMediumLocation='IT_Marieberg',set_storageMediumLocationStatus=''):
        #self.table = 'storageMedium'
        self.storageMedium,errno,why = ESSMSSQL.DB().action('storageMedium','GET3',('storageMedium',
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
        elif len(self.storageMedium) == 1:
            self.storageMedium = self.storageMedium[0]
            logging.info('Found storageMediumID: %s in central DB',storageMediumID)
            ###################################################
            # Check if storageMediumID exist in local DB
            self.local_storageMedium,errno,why = ESSDB.DB().action('storageMedium','GET3',('storageMediumID',
                                                                                      'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)'),
                                                                                     ('storageMediumID',storageMediumID))
            if errno:
                logging.error('Failed to access local DB ' + str(why))
                return 10

            elif len(self.local_storageMedium) == 1:
                if self.local_storageMedium[0][1] == 0: # Check if ESSArch and centralDB is in sync
                    ###################################################
                    # storageMediumID exist in local DB try to update

                    ###################################################
                    # Force set storageMediumLocation or storageMediumLocationStatus
                    if set_storageMediumLocation:
                        self.storageMedium[3] = set_storageMediumLocation
                    if set_storageMediumLocationStatus:
                        self.storageMedium[4] = set_storageMediumLocationStatus

                    logging.info('Found storageMediumID: %s in local "storageMedium" DB, try to update',storageMediumID)
                    storageMediumDate_dst = self.storageMedium[2].replace(microsecond=0,tzinfo=self.tz)
                    storageMediumDate_utc = storageMediumDate_dst.astimezone(pytz.utc)
                    CreateDate_dst = self.storageMedium[11].replace(microsecond=0,tzinfo=self.tz)
                    CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    storageMedium_obj = storageMedium.objects.get(storageMediumID=self.storageMedium[1])
                    storageMedium_obj.storageMedium = self.storageMedium[0]
                    storageMedium_obj.storageMediumDate = storageMediumDate_utc.replace(tzinfo=None)
                    storageMedium_obj.storageMediumLocation = self.storageMedium[3]
                    storageMedium_obj.storageMediumLocationStatus = self.storageMedium[4]
                    storageMedium_obj.storageMediumBlockSize = self.storageMedium[5]
                    storageMedium_obj.storageMediumUsedCapacity = self.storageMedium[6]
                    storageMedium_obj.storageMediumStatus = self.storageMedium[7]
                    storageMedium_obj.storageMediumFormat = self.storageMedium[8]
                    storageMedium_obj.storageMediumMounts = self.storageMedium[9]
                    storageMedium_obj.linkingAgentIdentifierValue = self.storageMedium[10]
                    storageMedium_obj.CreateDate = CreateDate_utc.replace(tzinfo=None)
                    storageMedium_obj.CreateAgentIdentifierValue = self.storageMedium[12]
                    #storageMedium_obj.storageMediumUUID = uuid.UUID(bytes_le=self.storageMedium[13])
                    storageMedium_obj.storageMediumUUID = uuid.UUID(self.storageMedium[13])
                    storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                    storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                    storageMedium_obj.save()
                                                                        
#                    res,errno,why = ESSDB.DB().action('storageMedium','UPD',('storageMedium',self.storageMedium[0],
#                                                                        'storageMediumDate',storageMediumDate_utc.replace(tzinfo=None),
#                                                                        'storageMediumLocation',self.storageMedium[3],
#                                                                        'storageMediumLocationStatus',self.storageMedium[4],
#                                                                        'storageMediumBlockSize',self.storageMedium[5],
#                                                                        'storageMediumUsedCapacity',self.storageMedium[6],
#                                                                        'storageMediumStatus',self.storageMedium[7],
#                                                                        'storageMediumFormat',self.storageMedium[8],
#                                                                        'storageMediumMounts',self.storageMedium[9],
#                                                                        'linkingAgentIdentifierValue',self.storageMedium[10],
#                                                                        'CreateDate',CreateDate_utc.replace(tzinfo=None),
#                                                                        'CreateAgentIdentifierValue',self.storageMedium[12],
#                                                                        #'storageMediumUUID',uuid.UUID(bytes_le=self.storageMedium[13]),
#                                                                        'storageMediumUUID',uuid.UUID(self.storageMedium[13]),
#                                                                        'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                        'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                       ('storageMediumID',self.storageMedium[1]))
#                    if errno: 
#                        logging.error('Failed to update local DB: %s error: %s', self.storageMedium[1], str(why))
#                        return 11
                else:
                    logging.error('Local "storageMedium" DB and Central DB is not in SYNC! for MediaID: %s',storageMediumID)
                    return 14
            elif len(self.local_storageMedium) == 0:
                ###################################################
                # storageMediumID not exist in local DB try to insert

                ###################################################
                # Force set storageMediumLocation or storageMediumLocationStatus
                if set_storageMediumLocation:
                    self.storageMedium[3] = set_storageMediumLocation
                if set_storageMediumLocationStatus:
                    self.storageMedium[4] = set_storageMediumLocationStatus

                logging.info('Missing storageMediumID: %s in local "storageMedium" DB, try to insert',storageMediumID)
                storageMediumDate_dst = self.storageMedium[2].replace(microsecond=0,tzinfo=self.tz)
                storageMediumDate_utc = storageMediumDate_dst.astimezone(pytz.utc)
                CreateDate_dst = self.storageMedium[11].replace(microsecond=0,tzinfo=self.tz)
                CreateDate_utc = CreateDate_dst.astimezone(pytz.utc)
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                storageMedium_obj = storageMedium()
                storageMedium_obj.storageMedium = self.storageMedium[0]
                storageMedium_obj.storageMediumID = self.storageMedium[1]
                storageMedium_obj.storageMediumDate = storageMediumDate_utc.replace(tzinfo=None)
                storageMedium_obj.storageMediumLocation = self.storageMedium[3]
                storageMedium_obj.storageMediumLocationStatus = self.storageMedium[4]
                storageMedium_obj.storageMediumBlockSize = self.storageMedium[5]
                storageMedium_obj.storageMediumUsedCapacity = self.storageMedium[6]
                storageMedium_obj.storageMediumStatus = self.storageMedium[7]
                storageMedium_obj.storageMediumFormat = self.storageMedium[8]
                storageMedium_obj.storageMediumMounts = self.storageMedium[9]
                storageMedium_obj.linkingAgentIdentifierValue = self.storageMedium[10]
                storageMedium_obj.CreateDate = CreateDate_utc.replace(tzinfo=None)
                storageMedium_obj.CreateAgentIdentifierValue = self.storageMedium[12]
                #storageMedium_obj.storageMediumUUID = uuid.UUID(bytes_le=self.storageMedium[13])
                storageMedium_obj.storageMediumUUID = uuid.UUID(self.storageMedium[13])
                storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.save()                                                                  
#                res,errno,why = ESSDB.DB().action('storageMedium','INS',('storageMedium',self.storageMedium[0],
#                                                                    'storageMediumID',self.storageMedium[1],
#                                                                    'storageMediumDate',storageMediumDate_utc.replace(tzinfo=None),
#                                                                    'storageMediumLocation',self.storageMedium[3],
#                                                                    'storageMediumLocationStatus',self.storageMedium[4],
#                                                                    'storageMediumBlockSize',self.storageMedium[5],
#                                                                    'storageMediumUsedCapacity',self.storageMedium[6],
#                                                                    'storageMediumStatus',self.storageMedium[7],
#                                                                    'storageMediumFormat',self.storageMedium[8],
#                                                                    'storageMediumMounts',self.storageMedium[9],
#                                                                    'linkingAgentIdentifierValue',self.storageMedium[10],
#                                                                    'CreateDate',CreateDate_utc.replace(tzinfo=None),
#                                                                    'CreateAgentIdentifierValue',self.storageMedium[12],
#                                                                    #'storageMediumUUID',uuid.UUID(bytes_le=self.storageMedium[13]),
#                                                                    'storageMediumUUID',uuid.UUID(self.storageMedium[13]),
#                                                                    'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                    'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                if errno: 
#                    logging.error('Failed to insert to local DB: %s error: %s', self.storageMedium[1], str(why))
#                    return 12
            else: logging.error('To many storageMediumID found i local "storageMedium" DB for %s', storageMediumID)
            ###################################################
            # Get all archive object for storageMediumID from central DB 
            #self.table = 'storage'
            storage_objs_ext,errno2,why2 = ESSMSSQL.DB().action('storage','GET3',('ObjectIdentifierValue',
                                                                                     'contentLocationType',
                                                                                     'contentLocationValue',
                                                                                     'storageMediumID'),
                                                                                    ('storageMediumID',self.storageMedium[1]))
            if errno2:
                logging.error('Failed to access central DB ' + str(why2))
                return 20
            elif storage_objs_ext:
                for storage_obj_ext in storage_objs_ext:
############################
                    ###################################################
                    # Get all object for IngestObject from central DB
                    #self.table = 'IngestObject'
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
                            self.local_object,errno,why = ESSDB.DB().action('IngestObject','GET3',('id',
                                                                                               'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)'),
                                                                                              ('ObjectIdentifierValue',ip_obj_ext[1]))
                            if errno:
                                logging.error('Failed to access local DB ' + str(why))
                                return 10
                            elif len(self.local_object) == 1:
                                if self.local_object[0][1] == 0: # Check if ESSArch and centralDB is in sync
                                    ###################################################
                                    # archive object exist in local "IngestObject" DB try to update
                                    logging.info('Found archive object: %s in local "IngestObject" DB for storageMediumID: %s, try to update',ip_obj_ext[1],storageMediumID)
                                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                    ESSArchPolicy_obj = ESSArchPolicy.objects.get(PolicyID = ip_obj_ext[0])
                                    ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue = ip_obj_ext[1])
                                    ip_obj.PolicyId = ESSArchPolicy_obj
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
                                    ip_obj.LastEventDate = LastEventDate_utc.replace(tzinfo=None)
                                    ip_obj.linkingAgentIdentifierValue = ip_obj_ext[20]
                                    ip_obj.CreateDate = CreateDate_utc.replace(tzinfo=None)
                                    ip_obj.CreateAgentIdentifierValue = ip_obj_ext[22]
                                    #ip_obj.ObjectUUID = uuid.UUID(bytes_le=ip_obj_ext[23])
                                    ip_obj.ObjectUUID = uuid.UUID(ip_obj_ext[23])
                                    ip_obj.EntryDate = EntryDate_utc.replace(tzinfo=None)
                                    ip_obj.EntryAgentIdentifierValue = ip_obj_ext[25]
                                    ip_obj.OAISPackageType = ip_obj_ext[26]
                                    ip_obj.preservationLevelValue = ip_obj_ext[27]
                                    ip_obj.DELIVERYTYPE = ip_obj_ext[28]
                                    ip_obj.INFORMATIONCLASS = ip_obj_ext[29]
                                    ip_obj.ObjectActive = ip_obj_ext[30]
                                    ip_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                    ip_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                    ip_obj.save()
                                                                                        
#                                    res,errno,why = ESSDB.DB().action('IngestObject','UPD',('PolicyId',ip_obj_ext[0],
#                                                                                        'ObjectPackageName',ip_obj_ext[2],
#                                                                                        'ObjectSize',ip_obj_ext[3],
#                                                                                        'ObjectNumItems',ip_obj_ext[4],
#                                                                                        'ObjectMessageDigestAlgorithm',ip_obj_ext[5],
#                                                                                        'ObjectMessageDigest',ip_obj_ext[6],
#                                                                                        'ObjectPath',ip_obj_ext[7],
#                                                                                        'MetaObjectIdentifier',ip_obj_ext[8],
#                                                                                        'MetaObjectSize',ip_obj_ext[9],
#                                                                                        'CMetaMessageDigestAlgorithm',ip_obj_ext[10],
#                                                                                        'CMetaMessageDigest',ip_obj_ext[11],
#                                                                                        'PMetaMessageDigestAlgorithm',ip_obj_ext[12],
#                                                                                        'PMetaMessageDigest',ip_obj_ext[13],
#                                                                                        'DataObjectSize',ip_obj_ext[14],
#                                                                                        'DataObjectNumItems',ip_obj_ext[15],
#                                                                                        'Status',ip_obj_ext[16],
#                                                                                        'StatusActivity',ip_obj_ext[17],
#                                                                                        'StatusProcess',ip_obj_ext[18],
#                                                                                        'LastEventDate',LastEventDate_utc.replace(tzinfo=None),
#                                                                                        'linkingAgentIdentifierValue',ip_obj_ext[20],
#                                                                                        'CreateDate',CreateDate_utc.replace(tzinfo=None),
#                                                                                        'CreateAgentIdentifierValue',ip_obj_ext[22],
#                                                                                        #'ObjectUUID',uuid.UUID(bytes_le=ip_obj_ext[23]),
#                                                                                        'ObjectUUID',uuid.UUID(ip_obj_ext[23]),
#                                                                                        'EntryDate',EntryDate_utc.replace(tzinfo=None),
#                                                                                        'EntryAgentIdentifierValue',ip_obj_ext[25],
#                                                                                        'OAISPackageType',ip_obj_ext[26],
#                                                                                        'preservationLevelValue',ip_obj_ext[27],
#                                                                                        'DELIVERYTYPE',ip_obj_ext[28],
#                                                                                        'INFORMATIONCLASS',ip_obj_ext[29],
#                                                                                        'ObjectActive',ip_obj_ext[30],
#                                                                                        'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                                        'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                                       ('ObjectIdentifierValue',ip_obj_ext[1]))
#                                    if errno: 
#                                        logging.error('Failed to update local "IngestObject" DB: %s, %s error: %s', ip_obj_ext[1], storageMediumID, str(why))
#                                        return 11
                                else:
                                    logging.error('Local "IngestObject" DB and Central DB is not in SYNC! for MediaID: %s and Object: %s',storageMediumID,ip_obj_ext[1])
                                    return 14
                            elif len(self.local_object) == 0:
                                ###################################################
                                # archive object not exist in local "IngestObject" DB try to insert
                                logging.info('Missing archive object: %s in local "IngestObject" DB for storageMediumID: %s, try to insert',ip_obj_ext[1],storageMediumID)
                                self.timestamp = datetime.datetime.replace(datetime.datetime.today(),microsecond=0).isoformat(' ')
                                ESSArchPolicy_obj = ESSArchPolicy.objects.get(PolicyID = ip_obj_ext[0])
                                ip_obj = ArchiveObject()
                                ip_obj.PolicyId = ESSArchPolicy_obj
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
                                ip_obj.LastEventDate = LastEventDate_utc.replace(tzinfo=None)
                                ip_obj.linkingAgentIdentifierValue = ip_obj_ext[20]
                                ip_obj.CreateDate = CreateDate_utc.replace(tzinfo=None)
                                ip_obj.CreateAgentIdentifierValue = ip_obj_ext[22]
                                #ip_obj.ObjectUUID = uuid.UUID(bytes_le=ip_obj_ext[23])
                                ip_obj.ObjectUUID = uuid.UUID(ip_obj_ext[23])
                                ip_obj.EntryDate = EntryDate_utc.replace(tzinfo=None)
                                ip_obj.EntryAgentIdentifierValue = ip_obj_ext[25]
                                ip_obj.OAISPackageType = ip_obj_ext[26]
                                ip_obj.preservationLevelValue = ip_obj_ext[27]
                                ip_obj.DELIVERYTYPE = ip_obj_ext[28]
                                ip_obj.INFORMATIONCLASS = ip_obj_ext[29]
                                ip_obj.ObjectActive = ip_obj_ext[30]
                                ip_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                ip_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                                ip_obj.save()

#                                res,errno,why = ESSDB.DB().action('IngestObject','INS',('PolicyId',ip_obj_ext[0],
#                                                                                    'ObjectIdentifierValue',ip_obj_ext[1],
#                                                                                    'ObjectPackageName',ip_obj_ext[2],
#                                                                                    'ObjectSize',ip_obj_ext[3],
#                                                                                    'ObjectNumItems',ip_obj_ext[4],
#                                                                                    'ObjectMessageDigestAlgorithm',ip_obj_ext[5],
#                                                                                    'ObjectMessageDigest',ip_obj_ext[6],
#                                                                                    'ObjectPath',ip_obj_ext[7],
#                                                                                    'MetaObjectIdentifier',ip_obj_ext[8],
#                                                                                    'MetaObjectSize',ip_obj_ext[9],
#                                                                                    'CMetaMessageDigestAlgorithm',ip_obj_ext[10],
#                                                                                    'CMetaMessageDigest',ip_obj_ext[11],
#                                                                                    'PMetaMessageDigestAlgorithm',ip_obj_ext[12],
#                                                                                    'PMetaMessageDigest',ip_obj_ext[13],
#                                                                                    'DataObjectSize',ip_obj_ext[14],
#                                                                                    'DataObjectNumItems',ip_obj_ext[15],
#                                                                                    'Status',ip_obj_ext[16],
#                                                                                    'StatusActivity',ip_obj_ext[17],
#                                                                                    'StatusProcess',ip_obj_ext[18],
#                                                                                    'LastEventDate',LastEventDate_utc.replace(tzinfo=None),
#                                                                                    'linkingAgentIdentifierValue',ip_obj_ext[20],
#                                                                                    'CreateDate',CreateDate_utc.replace(tzinfo=None),
#                                                                                    'CreateAgentIdentifierValue',ip_obj_ext[22],
#                                                                                    #'ObjectUUID',uuid.UUID(bytes_le=ip_obj_ext[23]),
#                                                                                    'ObjectUUID',uuid.UUID(ip_obj_ext[23]),
#                                                                                    'EntryDate',EntryDate_utc.replace(tzinfo=None),
#                                                                                    'EntryAgentIdentifierValue',ip_obj_ext[25],
#                                                                                    'OAISPackageType',ip_obj_ext[26],
#                                                                                    'preservationLevelValue',ip_obj_ext[27],
#                                                                                    'DELIVERYTYPE',ip_obj_ext[28],
#                                                                                    'INFORMATIONCLASS',ip_obj_ext[29],
#                                                                                    'ObjectActive',ip_obj_ext[30],
#                                                                                    'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                                    'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                                if errno: 
#                                    logging.error('Failed to insert to local "IngestObject" DB: %s, %s error: %s', ip_obj_ext[1], storageMediumID, str(why))
#                                    return 11
                            else: 
                                logging.error('To many objects found in local "IngestObject" DB for %s', ip_obj_ext[1])
                                return 13
                    else:
                        logging.info('No archive objects found for storageMedia %s in central "IngestObject" DB', storageMediumID)
                        return 3

############################
                    logging.debug('storageMediumID: %s ,storageObject: %s',storageMediumID,storage_obj_ext[0])
                    ###################################################
                    # Check if archive object exist in local "storage" DB
                    self.table = 'storage'
                    self.local_storage,errno,why = ESSDB.DB().action('storage','GET3',('id',
                                                                                        'TIMESTAMPDIFF(SECOND,LocalDBdatetime,ExtDBdatetime)'),
                                                                                       ('ObjectIdentifierValue',storage_obj_ext[0],'AND',
                                                                                        'contentLocationType',storage_obj_ext[1],'AND',
                                                                                        'contentLocationValue',storage_obj_ext[2],'AND',
                                                                                        'storageMediumID',storage_obj_ext[3]))
                    if errno:
                        logging.error('Failed to access local DB ' + str(why))
                        return 10
                    elif len(self.local_storage) == 1:
                        if self.local_storage[0][1] == 0: # Check if ESSArch and centralDB is in sync
                            ###################################################
                            # archive object exist in local "storage" DB try to update
                            logging.info('Found archive object: %s in local "storage" DB for storageMediumID: %s, try to update',storage_obj_ext[0],storageMediumID)
                            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                            storage_obj = storage.objects.get(id = self.local_storage[0][0])
                            storage_obj.ObjectIdentifierValue = storage_obj_ext[0]
                            storage_obj.contentLocationType = storage_obj_ext[1]
                            storage_obj.contentLocationValue = storage_obj_ext[2]
                            storage_obj.storageMediumID = storage_obj_ext[3]
                            storage_obj.storageMediumUUID = storageMedium_obj
                            storage_obj.ObjectUUID = ip_obj
                            storage_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                            storage_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                            storage_obj.save()                           
                                                      
#                            res,errno,why = ESSDB.DB().action('storage','UPD',('ObjectIdentifierValue',storage_obj_ext[0],
#                                                                                'contentLocationType',storage_obj_ext[1],
#                                                                                'contentLocationValue',storage_obj_ext[2],
#                                                                                'storageMediumID',storage_obj_ext[3],
#                                                                                'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                                'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                               ('id',self.local_storage[0][0]))
#                            if errno: 
#                                logging.error('Failed to update local "storage" DB: %s, %s error: %s', storage_obj_ext[0], storage_obj_ext[3], str(why))
#                                return 11
                        else:
                            logging.error('Local "storage" DB and Central DB is not in SYNC! for MediaID: %s and Object: %s',storageMediumID,storage_obj_ext[0])
                            return 14
                    elif len(self.local_storage) == 0:
                        ###################################################
                        # archive object not exist in local "storage" DB try to insert
                        logging.info('Missing archive object: %s in local "storage" DB for storageMediumID: %s, try to insert',storage_obj_ext[0],storageMediumID)
                        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                        storage_obj = storage()
                        storage_obj.ObjectIdentifierValue = storage_obj_ext[0]
                        storage_obj.contentLocationType = storage_obj_ext[1]
                        storage_obj.contentLocationValue = storage_obj_ext[2]
                        storage_obj.storageMediumID = storage_obj_ext[3]
                        storage_obj.storageMediumUUID = storageMedium_obj
                        storage_obj.ObjectUUID = ip_obj
                        storage_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                        storage_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                        storage_obj.save()   
#                        res,errno,why = ESSDB.DB().action('storage','INS',('ObjectIdentifierValue',storage_obj_ext[0],
#                                                                            'contentLocationType',storage_obj_ext[1],
#                                                                            'contentLocationValue',storage_obj_ext[2],
#                                                                            'storageMediumID',storage_obj_ext[3],
#                                                                            'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None),
#                                                                            'ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                        if errno: 
#                            logging.error('Failed to insert to local "storage" DB: %s, %s error: %s', storage_obj_ext[0], storage_obj_ext[3], str(why))
#                            return 12
                    else: 
                        logging.error('To many objects found i local "storage" DB for %s', storage_obj_ext[0])
                        return 13
            else: 
                logging.info('No archive objects found for storageMedia %s in central "storage" DB', storageMediumID)
                return 2
        elif len(self.storageMedium) > 1:
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
        startDateTime = datetime.datetime.replace(datetime.datetime.today()-datetime.timedelta(days=int(options.days)),microsecond=0).isoformat(' ')
    elif options.startDateTime:
        optionflag = 0
        try: startDateTime = datetime.datetime.replace(datetime.datetime.strptime(options.startDateTime,"%Y-%m-%d %H:%M:%S"),microsecond=0).isoformat(' ')
        except: op.error("Invalid startDateTime")
    elif options.GetStorageMediaID:
        optionflag = 0
        if not len(options.GetStorageMediaID) == 6: op.error("Invalid MediaID")

    if optionflag: op.error("incorrect options")

    if options.stopDateTime:
        try: stopDateTime = datetime.datetime.replace(datetime.datetime.strptime(options.stopDateTime,"%Y-%m-%d %H:%M:%S"),microsecond=0).isoformat(' ')
        except: op.error("Invalid stopDateTime")
    else:
        stopDateTime = datetime.datetime.replace(datetime.datetime.today(),microsecond=0).isoformat(' ')

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
        LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]
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
            Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('Time','Status','Run'),('Name',ProcName))[0]
            if Run == '0':
                logging.info('Stopping ' + ProcName)
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
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

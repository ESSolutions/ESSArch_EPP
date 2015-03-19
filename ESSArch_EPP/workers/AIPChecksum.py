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
import os, thread, multiprocessing, datetime, time, pytz, logging, sys, ESSDB, ESSMSSQL, ESSPGM, ESSMD, uuid

from configuration.models import SchemaProfile, ChecksumAlgorithm_CHOICES, Parameter
from essarch.models import ArchiveObject
from django.db.models import Q
from django import db
from django.utils import timezone

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logging.info('Starting ' + ProcName)
        TimeZone = timezone.get_default_timezone_name()
        self.tz=pytz.timezone(TimeZone)
        METS_NAMESPACE = SchemaProfile.objects.get(entity = 'mets_namespace').value
        METS_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'mets_schemalocation').value
        METS_PROFILE = SchemaProfile.objects.get(entity = 'mets_profile').value
        XLINK_NAMESPACE = SchemaProfile.objects.get(entity = 'xlink_namespace').value
        XSI_NAMESPACE = SchemaProfile.objects.get(entity = 'xsi_namespace').value
        while 1:
                if self.mDieFlag==1: break      # Request for death
                self.mLock.acquire()
                self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
                if self.Run == '0':
                    logging.info('Stopping ' + ProcName)
                    ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                    self.RunFlag=0
                    self.mLock.release()
                    if Debug: logging.info('RunFlag: 0')
                    time.sleep(2)
                    continue
                # Process Item 
                lock=thread.allocate_lock()
                Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
                self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
                self.PolicyTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','PolicyTable'))[0][0]
                if ExtDBupdate:
                    self.ext_IngestTable = self.IngestTable
                else:
                    self.ext_IngestTable = ''
                self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue',
                                                                                  'ObjectUUID',
                                                                                  'PolicyId',
                                                                                  'ObjectSize'),
                                                                                 ('StatusProcess','BETWEEN',39,'AND',40,'AND',
                                                                                  'StatusActivity','=','0'))
                if errno: logging.error('Failed to access Local DB, error: ' + str(why))
                for self.obj in self.dbget:
                    self.ok = 1
                    self.ProcDB = ESSDB.DB().action('ESSProc','GET',('Run','Pause'),('Name',ProcName))[0]
                    if self.ProcDB[0]=='0':
                        logging.info('Stopping ' + ProcName)
                        ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                        thread.interrupt_main()
                        time.sleep(5)
                        break
                    elif self.ProcDB[1]==1:
                        while 1:
                            time.sleep(60)
                            self.ProcDB = ESSDB.DB().action('ESSProc','GET',('Run','Pause'),('Name',ProcName))[0]
                            if self.ProcDB[1]==1:
                                logging.info('Process is in pause state')
                            else:
                                break
                    self.ObjectIdentifierValue = self.obj[0]
                    self.ObjectUUID = self.obj[1]
                    self.PolicyId = self.obj[2]
                    self.ObjectSize = self.obj[3]
                    self.PolicyDB,errno,why = ESSDB.DB().action(self.PolicyTable,'GET3',('AIPpath','IngestMetadata','ChecksumAlgorithm','IngestPath'),('PolicyID',self.PolicyId))
                    if errno:
                        logging.error('Failed to access Local DB, error: ' + str(why))
                        self.ok = 0
                    if self.ok:
                        ###########################################################
                        # set variables
                        self.AIPpath = self.PolicyDB[0][0]
                        self.metatype = self.PolicyDB[0][1]
                        self.ChecksumAlgorithm = self.PolicyDB[0][2]
                        self.CA = dict(ChecksumAlgorithm_CHOICES)[self.ChecksumAlgorithm]
                        self.SIPpath = self.PolicyDB[0][3]
                        self.p_obj = self.ObjectIdentifierValue + '.tar'
                        self.ObjectPath = os.path.join(self.AIPpath,self.p_obj)
                        self.SIProotpath = os.path.join(self.SIPpath,self.ObjectIdentifierValue)
                        if self.metatype in [4]:
                            #self.Cmets_obj = '%s/%s_Content_METS.xml' % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                            #self.Cmets_objpath = os.path.join(self.SIPpath,self.Cmets_obj)
                            #self.Cmets_obj = Cmets_obj.replace('{uuid}',self.ObjectIdentifierValue)
                            self.Cmets_obj = Cmets_obj.replace('{objid}',self.ObjectIdentifierValue)
                            self.Cmets_objpath = os.path.join(self.SIProotpath,self.Cmets_obj)
                        elif self.metatype in [1,2,3]:
                            self.Cmets_obj = '%s_Content_METS.xml' % (self.ObjectIdentifierValue)
                            self.Cmets_objpath = os.path.join(self.AIPpath,self.Cmets_obj)
                        self.Pmets_obj = '%s_Package_METS.xml' % (self.ObjectIdentifierValue)
                        self.Pmets_objpath = os.path.join(self.AIPpath,self.Pmets_obj)
                        self.AIC_UUID = None
                        self.AIC_UUID_rel_ObjectUUIDs = []
                    if self.ok:
                        METS_agent_list = []
                        METS_altRecordID_list = []
                        if self.metatype == 1:
                            ############################################
                            # Object have metatype 1 (METS)
                            self.METS_LABEL = 'ESSArch AIP'
                            # Get SIP Content METS information
                            self.METSfilepath = os.path.join(self.SIPpath,self.ObjectIdentifierValue + '/metadata/SIP/' + self.ObjectIdentifierValue + '_Content_METS.xml')
                            res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=self.METSfilepath)
                            for agent in res_info[2]:
                                if not (agent[0] == 'CREATOR' and agent[3] == 'SOFTWARE'):
                                    METS_agent_list.append(agent)
                            METS_agent_list.append(['CREATOR','INDIVIDUAL','',AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                        elif self.metatype == 2:
                            ############################################
                            # Object have metatype 2 (RES)
                            self.METS_LABEL = 'Imaging AIP RA'
                            METS_agent_list.append(['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','INDIVIDUAL','',AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                        elif self.metatype == 3:
                            ############################################
                            # Object have metatype 3 (ADDML)
                            self.METS_LABEL = 'Born Digital AIP RA'
                            METS_agent_list.append(['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','INDIVIDUAL','',AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                        elif self.metatype in [4]:
                            ############################################
                            # Object have metatype 4 (eARD METS)
                            res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=self.Cmets_objpath)
                            for agent in res_info[2]:
                                #if not (agent[0] == 'CREATOR' and agent[3] == 'SOFTWARE'):
                                    METS_agent_list.append(agent)
                            self.METS_LABEL = res_info[0][0]
                            METS_agent_list.append(['CREATOR',None, 'INDIVIDUAL',None,AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR',None, 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                            for altRecordID in res_info[3]:
                                METS_altRecordID_list.append(altRecordID)
                    logging.debug('self.obj: '+str(self.obj))
                    if self.ChecksumAlgorithm > 0: #self.ChecksumAlgorithm 1 = MD5, 2 = SHA-256
                        self.startCalTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 40, 5)
                        if errno: logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Start create Package METS for: ' + self.ObjectIdentifierValue)
                        if self.ok:
                            ###########################################################
                            # Create PMETS for AIP package
                            self.M_CHECKSUM, errno, why = ESSPGM.Check().checksum(self.Cmets_objpath,self.CA)
                            if errno:
                                self.event_info = 'Problem to get checksum for METS object for AIP package: ' + str(self.Cmets_objpath)
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            self.M_statinfo = os.stat(self.Cmets_objpath)
                            self.M_SIZE = self.M_statinfo.st_size
                            self.M_utc_mtime = datetime.datetime.utcfromtimestamp(self.M_statinfo.st_mtime).replace(tzinfo=pytz.utc)
                            self.M_lociso_mtime = self.M_utc_mtime.astimezone(self.tz).isoformat()
                            self.P_CHECKSUM, errno, why = ESSPGM.Check().checksum(self.ObjectPath,self.CA)
                            if errno:
                                self.event_info = 'Problem to get checksum for AIP package: ' + str(self.ObjectPath)
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1040','','ESSArch AIPChecksum',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            self.P_statinfo = os.stat(self.ObjectPath)
                            self.P_SIZE = self.P_statinfo.st_size
                            self.P_utc_mtime = datetime.datetime.utcfromtimestamp(self.P_statinfo.st_mtime).replace(tzinfo=pytz.utc)
                            self.P_lociso_mtime = self.P_utc_mtime.astimezone(self.tz).isoformat()
        
                            if self.metatype in [1,2,3]:
                                self.PMETSdoc = ESSMD.createPMets(
                                    ID=self.ObjectIdentifierValue,
                                    LABEL=self.METS_LABEL,
                                    AGENT=METS_agent_list,
                                    P_SIZE=self.P_SIZE,
                                    P_CREATED=self.P_lociso_mtime,
                                    P_CHECKSUM=self.P_CHECKSUM,
                                    P_CHECKSUMTYPE=self.CA,
                                    M_SIZE=self.M_SIZE,
                                    M_CREATED=self.M_lociso_mtime,
                                    M_CHECKSUM=self.M_CHECKSUM,
                                    M_CHECKSUMTYPE=self.CA,
                                )
                                errno,why = ESSMD.writeToFile(self.PMETSdoc,self.Pmets_objpath)
                                if errno:
                                    self.event_info = 'Problem to write PMETS to file for AIP package: ' + str(self.Pmets_objpath)
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1040','','ESSArch AIPChecksum',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    time.sleep(2)
                                    self.ok = 0
                            elif self.metatype in [4]:
                                ms_files = []
                                ms_files.append(['amdSec', None, 'techMD', 'techMD001', None,
                                                 None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s/%s' % (self.ObjectIdentifierValue,self.Cmets_obj), 'simple',
                                                 self.M_CHECKSUM, self.CA, self.M_SIZE, 'text/xml', self.M_lociso_mtime,
                                                 'OTHER', 'METS', None])

                                ms_files.append(['fileSec', None, None, None, None,
                                                 None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % self.p_obj, 'simple',
                                                 self.P_CHECKSUM, self.CA, self.P_SIZE, 'application/x-tar', self.P_lociso_mtime,
                                                 'tar', 'techMD001', None])                          
                                # define namespaces
                                self.namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
                                self.namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
                                self.namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
                                self.namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
                                                            
                                errno,info_list = ESSMD.Create_IP_mets(ObjectIdentifierValue = self.ObjectIdentifierValue, 
                                                                       METS_ObjectPath = self.Pmets_objpath,
                                                                       agent_list = METS_agent_list, 
                                                                       altRecordID_list = METS_altRecordID_list, 
                                                                       file_list = ms_files, 
                                                                       namespacedef = self.namespacedef, 
                                                                       METS_LABEL = self.METS_LABEL, 
                                                                       METS_PROFILE = METS_PROFILE, 
                                                                       METS_TYPE = 'AIP',  
                                                                       METS_DocumentID = self.Pmets_obj,
                                                                       TimeZone = TimeZone)
                                if errno:
                                    logging.error('Problem to create Package METS file, why: %s' % str(info_list))   

                        self.ObjectMessageDigest = self.P_CHECKSUM
                        self.stopCalTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        self.CalTime = self.stopCalTime-self.startCalTime
                        self.ObjectSizeMB = self.ObjectSize/1048576
                        if self.CalTime.seconds < 1: self.CalTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                        self.CalMBperSEC = int(self.ObjectSizeMB)/int(self.CalTime.seconds)
                        logging.info('Finished calculate checksum: ' + self.ObjectIdentifierValue + ' , ' + str(self.CalMBperSEC) + ' MB/Sec and Time: ' + str(self.CalTime))

                        if self.ok:
                            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                            res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ObjectMessageDigestAlgorithm',self.ChecksumAlgorithm,
                                                                                      'ObjectMessageDigest',self.ObjectMessageDigest,
                                                                                      'MetaObjectSize',self.M_SIZE,
                                                                                      'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                                      'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                      'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                     ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            if errno == 0 and ExtDBupdate:
                                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('ObjectMessageDigestAlgorithm',self.ChecksumAlgorithm,
                                                                                                         'ObjectMessageDigest',self.ObjectMessageDigest,
                                                                                                         'MetaObjectSize',self.M_SIZE,
                                                                                                         'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                         'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                        ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                if ext_errno: logging.error('Failed to update External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                                else:
                                    res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                    if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))

                        if self.ok and self.metatype == 4:
                            ####################################################
                            # Create AIC METS File:
                            aic_obj = ArchiveObject.objects.filter(relaic_set__UUID=self.ObjectUUID)[:1]
                            if aic_obj:
                                self.AIC_UUID = aic_obj.get().ObjectUUID
                                logging.info('Succeeded to get AIC_UUID: %s from DB' % self.AIC_UUID)
                            else:
                                logging.warning('AIC not found for IP object: %s, skip to create AIC METS file' % self.ObjectUUID)
                        if self.ok and self.AIC_UUID:
                            ip_obj_list = ArchiveObject.objects.filter(Q(StatusProcess=3000) | Q(ObjectUUID=self.ObjectUUID), reluuid_set__AIC_UUID=self.AIC_UUID).order_by('Generation')
                            if ip_obj_list:
                                logging.info('Start create AIC METS: ' + self.AIC_UUID)
                                self.AICmets_objpath = os.path.join(self.AIPpath,self.AIC_UUID + '_AIC_METS.xml')
                                ms_files = []
                                for ip_obj in ip_obj_list:
                                    logging.info('Add IP: %s to AIC METS: %s' % (ip_obj.ObjectUUID,self.AIC_UUID))
                                    ms_files.append(['fileSec', None, None, None, None,
                                          None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % ip_obj.ObjectUUID, 'simple',
                                          ip_obj.ObjectMessageDigest, dict(ChecksumAlgorithm_CHOICES)[ip_obj.ObjectMessageDigestAlgorithm], ip_obj.ObjectSize, 'application/x-tar', ip_obj.CreateDate,
                                          'IP Package', None, None])

                                # define namespaces
                                self.namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
                                self.namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
                                self.namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
                                self.namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)

                                errno,info_list = ESSMD.Create_IP_mets(ObjectIdentifierValue = self.AIC_UUID, 
                                                                       METS_ObjectPath = self.AICmets_objpath,
                                                                       agent_list = [], 
                                                                       altRecordID_list = [], 
                                                                       file_list = ms_files, 
                                                                       namespacedef = self.namespacedef, 
                                                                       METS_LABEL = 'AIC relation to IP', 
                                                                       METS_PROFILE = METS_PROFILE, 
                                                                       METS_TYPE = 'AIC',  
                                                                       METS_DocumentID = self.AIC_UUID + '_AIC_METS.xml',
                                                                       TimeZone = TimeZone)
                                if errno:
                                    logging.error('Problem to create AIC METS file, why: %s' % str(info_list))                                
                            else:
                                logging.error('Problem to get objects related to AIC_UUID: %s from DB' % (self.AIC_UUID))
                                self.ok = 0

                        if self.ok:                            
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 49, 0)
                            if errno: 
                                logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else:
                                self.event_info = 'Succeeded to create checksum for Object: %s' % self.ObjectIdentifierValue
                                logging.info(self.event_info)
                                ESSPGM.Events().create('1040','','ESSArch AIPChecksum',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)                            
                        else:
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 40, 100)
                            if errno: 
                                logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else:
                                self.event_info = 'Failed to create checksum for Object: %s' % self.ObjectIdentifierValue
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1040','','ESSArch AIPChecksum',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    elif self.ChecksumAlgorithm == 0: #self.ChecksumAlgorithm 0 = No checksum
                        logging.info('Skip creation of checksum: ' + self.ObjectIdentifierValue)
                        self.ObjectMessageDigest = ''
                        self.MetaObjectSize = os.stat(self.Cmets_objpath)[6] 
                        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                        res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ObjectMessageDigestAlgorithm',self.ChecksumAlgorithm,
                                                                                  'ObjectMessageDigest',self.ObjectMessageDigest,
                                                                                  'StatusProcess','49',
                                                                                  'StatusActivity','0',
                                                                                  'MetaObjectSize',self.MetaObjectSize,
                                                                                  'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                                  'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                  'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                 ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else: ESSPGM.Events().create('1040','','ESSArch AIPChecksum',ProcVersion,'0','Skip creation of checksum',2,self.ObjectIdentifierValue)
                        if errno == 0 and ExtDBupdate:
                            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('ObjectMessageDigestAlgorithm',self.ChecksumAlgorithm,
                                                                                                     'ObjectMessageDigest',self.ObjectMessageDigest,
                                                                                                     'StatusProcess','49',
                                                                                                     'StatusActivity','0',
                                                                                                     'MetaObjectSize',self.MetaObjectSize,
                                                                                                     'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                     'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                    ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                            if ext_errno: logging.error('Failed to update External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                            else:
                                res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                db.close_old_connections()
                self.mLock.release()
                time.sleep(int(self.Time))
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
# Table: ESSProc with Name: AIPChecksum, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Table: ESSConfig with Name: PolicyTable Value: archpolicy
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPChecksum'
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
    ##########################
    # Add handlers to default logger
    if MultiProc:
        logger = multiprocessing.get_logger()
        logger.setLevel(LogLevel)
    logging = logging.getLogger('')
    logging.setLevel(0)
    logging.addHandler(essLocalFileHandler)
    if MultiProc: logger.addHandler(essLocalFileHandler)
    if Console:
        logging.addHandler(essConsoleHandler)
        if MultiProc: logger.addHandler(essConsoleHandler)

    logging.debug('LogFile: ' + str(LogFile))
    logging.debug('Time: ' + str(Time))
    logging.debug('Status: ' + str(Status))
    logging.debug('Run: ' + str(Run))

    AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
    ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

    x=WorkingThread(ProcName)
    while 1:
        if x.RunFlag==99:
            if Debug: logging.info('test1: ' + str(x.RunFlag))
            sys.exit(10)
        elif x.RunFlag==0:
            if Debug: logging.info('test2: ' + str(x.RunFlag))
            x.Die()
            break
        time.sleep(5)
    if Debug: logging.info('test3: ' + str(x.RunFlag))
    del x

# ./AIPChecksum.py

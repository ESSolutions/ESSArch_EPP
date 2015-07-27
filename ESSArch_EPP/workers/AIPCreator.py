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
import os, thread, datetime, time, pytz, logging, sys, ESSDB, ESSMSSQL, ESSPGM, tarfile, ESSMD
from django.utils import timezone
from django import db
from configuration.models import Parameter, ArchivePolicy

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logging.info('Starting ' + ProcName)
        self.tz=timezone.get_default_timezone()
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0':
                logging.info('Stopping ' + ProcName)
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                self.RunFlag=0
                self.mLock.release()
                #if Debug: print 'RunFlag: 0'
                time.sleep(2)
                continue
            # Process Item 
            lock=thread.allocate_lock()
            self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
            Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
            if ExtDBupdate:
                self.ext_IngestTable = self.IngestTable
            else:
                self.ext_IngestTable = ''
            self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue','ObjectUUID','PolicyId'),('StatusProcess','BETWEEN',29,'AND',31,'AND',
                                                                                                                   'StatusActivity','=','0'))
            if errno: logging.error('Failed to access Local DB, error: ' + str(why))
            for self.obj in self.dbget:
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
                self.ok = 1
                ###########################################################
                # get policy info
                self.ObjectIdentifierValue = self.obj[0]
                self.ObjectUUID = self.obj[1]
                self.PolicyId = self.obj[2]
                logging.info('Start to create AIP for: %s', self.ObjectIdentifierValue)
                ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyStat=1, PolicyID=self.PolicyId)
                if self.ok:
                    ###########################################################
                    # set variables
                    self.AIPpath = ArchivePolicy_obj.AIPpath
                    self.metatype = ArchivePolicy_obj.IngestMetadata
                    self.SIPpath = ArchivePolicy_obj.IngestPath
                    self.p_obj = self.ObjectIdentifierValue + '.tar'
                    self.p_objpath = os.path.join(self.AIPpath,self.p_obj)
                    #self.Cmets_obj = self.ObjectIdentifierValue + '_Content_METS.xml'
                    #self.Cmets_obj = Cmets_obj.replace('{uuid}',self.ObjectIdentifierValue)
                    self.Cmets_obj = Cmets_obj.replace('{objid}',self.ObjectIdentifierValue)
                    self.SIProotpath = os.path.join(self.SIPpath,self.ObjectIdentifierValue)
                    if self.metatype in [4]:
                        self.Cmets_objpath = os.path.join(self.SIProotpath,self.Cmets_obj)
                        if os.path.exists(os.path.join(self.SIProotpath,'sip.xml')):
                            mets_file = 'sip.xml'
                            self.SIPmets_objpath = os.path.join(self.SIProotpath,mets_file)
                        elif os.path.exists(os.path.join(self.SIProotpath,'mets.xml')):
                            mets_file = 'mets.xml'
                            self.SIPmets_objpath = os.path.join(self.SIProotpath,mets_file)
                        #elif os.path.exists(os.path.join(self.SIProotpath,'%s_Content_METS.xml' % self.ObjectIdentifierValue)):
                        #    mets_file = '%s_Content_METS.xml' % self.ObjectIdentifierValue
                        #    self.SIPmets_objpath = os.path.join(self.SIProotpath,mets_file)
                        else:
                            self.SIPmets_objpath = ''
                    elif self.metatype in [1,2,3]:
                        self.Cmets_objpath = os.path.join(self.AIPpath,self.Cmets_obj)
                    Debug = 1
                    logging.debug('self.obj: %s', str(self.obj))
                    logging.debug('self.ObjectIdentifierValue: %s', self.ObjectIdentifierValue)
                    logging.debug('Len self.ObjectIdentifierValue: %s', len(self.ObjectIdentifierValue))
                    logging.debug('self.SIPpath: %s', self.SIPpath)
                    logging.debug('self.AIPpath: %s', self.AIPpath)
                if self.metatype in [1,2,3]:
                    if self.ok:
                        ###########################################################
                        # get object_list from PREMIS file 
                        self.Premis_filepath = '%s/%s/%s_PREMIS.xml' % (self.SIPpath,self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list,errno,why = ESSMD.getPremisObjects(FILENAME=self.Premis_filepath)
                        # list [objectIdentifierValue,messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,formatName,formatVersion]
                        if errno == 0:
                            logging.info('Succeeded to get object_list from premis for information package: %s', self.ObjectIdentifierValue)
                        else:
                            self.event_info = 'Problem to get object_list from premis for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                    if self.ok:
                        ###########################################################
                        # create AIP content METS file
                        #self.firstPremisObjectFlag = 1
                        METS_agent_list = []
                        if self.metatype == 1:
                            ############################################
                            # Object have metatype 1 (METS)
                            self.METS_LABEL = 'ESSArch AIP'
                            self.tmp_object_id = ('%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                            self.tmp_object_size = os.stat(os.path.join(self.SIPpath,self.tmp_object_id))[6]
                            self.object_list.append([self.tmp_object_id,'', '', '', self.tmp_object_size, 'ARCHMETAxmlWrap', 'PREMIS'])
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
                            self.tmp_object_id = ('%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                            self.tmp_object_size = os.stat(os.path.join(self.SIPpath,self.tmp_object_id))[6]
                            self.object_list.append([self.tmp_object_id,'', '', '', self.tmp_object_size, 'ARCHMETAxmlWrap', 'PREMIS'])
                            METS_agent_list.append(['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','INDIVIDUAL','',AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                        elif self.metatype == 3:
                            ############################################
                            # Object have metatype 3 (ADDML)
                            self.METS_LABEL = 'Born Digital AIP RA'
                            self.tmp_object_id = ('%s/%s_ADDML.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                            self.tmp_object_size = os.stat(os.path.join(self.SIPpath,self.tmp_object_id))[6]
                            self.object_list.append([self.tmp_object_id,'', '', '', self.tmp_object_size, 'ARCHMETAxmlWrap', 'ADDML'])
                            self.tmp_object_id = ('%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                            self.tmp_object_size = os.stat(os.path.join(self.SIPpath,self.tmp_object_id))[6]
                            self.object_list.append([self.tmp_object_id,'', '', '', self.tmp_object_size, 'ARCHMETAxmlWrap', 'PREMIS'])
                            METS_agent_list.append(['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','ORGANIZATION','','Riksarkivet',[]])
                            METS_agent_list.append(['CREATOR','INDIVIDUAL','',AgentIdentifierValue,[]])
                            METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                        self.firstPremisObjectFlag = 1
                        self.DataObjectNumItems = 0
                        self.DataObjectSize = 0
                        self.MetaObjectSize = 0
                        self.MetaObjectIdentifier = 'None'
                        for self.object in self.object_list:
                            self.filepath = os.path.join(self.SIPpath, self.object[0])
                            self.filepath_iso = ESSPGM.Check().unicode2str(self.filepath)
                            self.a_filepath = self.object[0]
                            if self.firstPremisObjectFlag:
                                if self.object[0] == self.ObjectIdentifierValue:
                                    logging.info('First premis object match information package: %s', self.ObjectIdentifierValue)
                                    if self.metatype == 1:
                                        self.METSdoc = ESSMD.createMets(self.ObjectIdentifierValue,self.METS_LABEL,METS_agent_list,['premis'])
                                    elif self.metatype == 2:
                                        self.METSdoc = ESSMD.createMets(self.ObjectIdentifierValue,self.METS_LABEL,METS_agent_list,['premis','mix'])
                                    elif self.metatype == 3:
                                        self.METSdoc = ESSMD.createMets(self.ObjectIdentifierValue,self.METS_LABEL,METS_agent_list,['premis','addml','xhtml'])
                                    self.firstPremisObjectFlag = 0
                                    continue
                                else:
                                    self.event_info = 'First premis object do not match information package: %s, premis_object: %s' % (self.ObjectIdentifierValue,self.object[0])
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                            elif os.access(self.filepath_iso,os.R_OK):
                                self.file_statinfo = os.stat(self.filepath_iso)
                                if self.metatype == 2 and self.object[5] == 'ARCHMETA':
                                    ############################################
                                    # Object have metatype 2 and RES file
                                    #self.file_ID = string.replace(self.object[0],'/','%')
                                    self.file_ID = self.object[0]
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'Content description'
                                    self.file_MIMETYPE = 'text/csv'
                                    self.file_MDTYPE = 'OTHER'
                                    self.file_OTHERMDTYPE = 'RES'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                                elif self.object[5] == 'ARCHMETAxmlWrap' and self.object[6] == 'PREMIS':
                                    ############################################
                                    # Object is a PREMIS XML file
                                    self.file_MDTYPE = 'PREMIS'
                                    self.file_OTHERMDTYPE = ''
                                elif self.object[5] == 'ARCHMETAxmlWrap':
                                    ############################################
                                    # Object is a OTHER XML file
                                    self.file_MDTYPE = 'OTHER'
                                    self.file_OTHERMDTYPE = self.object[6]
                                elif self.metatype == 1:
                                    ############################################
                                    # Object have metatype 1, convert PREMIS formatName to MIME-type, datafile
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'Datafiles'
                                    self.file_MIMETYPE = ESSPGM.Check().PREMISformat2MIMEtype(self.object[5])
                                    self.file_USE = 'Datafile'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                                    if self.file_MIMETYPE == 'unknown':
                                        self.event_info = 'Problem to idetify MIMETYPE from PREMIS for: %s' % self.filepath
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                elif self.metatype == 2 and self.object[0][-12:] == 'TIFFEdit.RES':
                                    ############################################
                                    # Object have metatype 2 and RES file
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'RA Information'
                                    self.file_MIMETYPE = 'text/csv'
                                    self.file_USE = 'RA Information'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                                elif self.metatype == 2:
                                    ############################################
                                    # Object have metatype 2 and datafile is an tiff image
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'RA Datafiles'
                                    self.file_MIMETYPE = 'image/tiff'
                                    self.file_USE = 'RA Datafile'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                                elif self.metatype == 3:
                                    ############################################
                                    # Object have metatype 3, convert PREMIS formatName to MIME-type, datafile 
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'Datafiles'
                                    self.file_MIMETYPE = ESSPGM.Check().PREMISformat2MIMEtype(self.object[5])
                                    self.file_USE = 'Datafile'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                                    if self.file_MIMETYPE == 'unknown':
                                        self.event_info = 'Problem to idetify MIMETYPE from PREMIS for: %s' % self.filepath
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                else:
                                    ############################################
                                    # Object is a datafile
                                    self.file_ID = self.object[0]
                                    self.file_SIZE = self.file_statinfo.st_size
                                    self.file_LABEL = 'Datafiles'
                                    self.file_MIMETYPE = 'xxxxx'                # Maste fixas
                                    self.file_USE = 'Datafile'
                                    self.file_CHECKSUMTYPE = self.object[1]
                                    self.file_CHECKSUM = self.object[2]
                                    self.file_LOCTYPE = 'URL'
                                    self.file_xlink_type = 'simple'
                            else:
                                self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            if self.ok:
                                ###########################################################
                                # add files to METS file
                                if not (self.object[5] == 'ARCHMETA' or self.object[5] == 'ARCHMETAxmlWrap'):
                                    self.DataObjectNumItems += 1
                                    self.DataObjectSize += self.file_SIZE
                                    self.fil_utc_mtime = datetime.datetime.utcfromtimestamp(self.file_statinfo.st_mtime).replace(tzinfo=pytz.utc)
                                    self.fil_lociso_mtime = self.fil_utc_mtime.astimezone(self.tz).isoformat()
                                    self.METSdoc = ESSMD.AddDataFiles(self.METSdoc,self.file_LABEL,'FILES','',[(self.file_ID,self.file_SIZE,self.fil_lociso_mtime,self.file_MIMETYPE,'',self.file_USE,self.file_CHECKSUMTYPE,self.file_CHECKSUM,self.file_LOCTYPE,self.file_xlink_type)])
                                elif self.object[5] == 'ARCHMETA':
                                    self.MetaObjectSize += self.file_SIZE
                                    self.fil_utc_mtime = datetime.datetime.utcfromtimestamp(self.file_statinfo.st_mtime).replace(tzinfo=pytz.utc)
                                    self.fil_lociso_mtime = self.fil_utc_mtime.astimezone(self.tz).isoformat()
                                    self.METSdoc = ESSMD.AddContentFiles(self.METSdoc,self.file_LABEL,'',[(self.file_ID,self.file_SIZE,self.fil_lociso_mtime,self.file_MIMETYPE,self.file_MDTYPE,self.file_OTHERMDTYPE,self.file_CHECKSUMTYPE,self.file_CHECKSUM,self.file_LOCTYPE,self.file_xlink_type)])
                                elif self.object[5] == 'ARCHMETAxmlWrap':
                                    logging.info('Wrap XML file: ' + self.a_filepath + ' to METS file')
                                    self.file_xml,errno,why = ESSMD.parseFromFile(self.filepath)
                                    if errno:
                                        self.event_info = 'Failed to parse XML file: ' + str(self.filepath) + ' error: ' + str(why)
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                    self.METSdoc = ESSMD.AddContentEtree(self.METSdoc,[(self.file_xml,self.file_MDTYPE,self.file_OTHERMDTYPE)])
                    if self.ok:
                        ########################
                        # Update root schemalocation and remove all other schemalocation
                        self.METSdoc,errno,why = ESSMD.updateSchemaLocation(self.METSdoc)
                        ########################
                        # Update all ADMID in DOC
                        res,errno,why = ESSMD.updateFilesADMID(self.METSdoc)
                        ########################
                        # Set xml_METS to self.METSdoc
                        xml_METS = self.METSdoc
                if self.metatype in [4]:
                    dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    loc_dt_isoformat = dt.astimezone(self.tz).isoformat()
                    xml_METS = ESSMD.updatePackage(FILENAME=self.SIPmets_objpath,TYPE='AIP',CREATED=loc_dt_isoformat,metsDocumentID=self.Cmets_obj)
                if self.ok:
                    ########################
                    # Write METS file
                    errno,why = ESSMD.writeToFile(xml_METS,self.Cmets_objpath)
                    if errno:
                        self.event_info = 'Problem to write METS to file for AIP package: ' + str(self.p_objpath)
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        time.sleep(2)
                        self.ok = 0
                    self.MetaObjectIdentifier = self.Cmets_obj
                    self.MetaObjectSize = 0
                if self.ok:
                    ###########################################################
                    # get object_list from METS 
                    self.object_list,errno,why = ESSMD.getAIPObjects(FILENAME=self.Cmets_objpath)
                    if errno == 0:
                        logging.info('Succeeded to get object_list from METS for information package: %s', self.ObjectIdentifierValue)
                    else:
                        self.event_info = 'Problem to get object_list from METS for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        self.ok = 0
                if self.ok:
                    ###########################################################
                    # Insert METS file as first object in AIP package
                    self.tmp_object_size = os.stat(self.Cmets_objpath)[6]
                    self.object_list.insert(0,[self.Cmets_obj,'','',self.tmp_object_size,''])
                if self.ok:
                    ###########################################################
                    # create AIP package file
                    try:
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 30, 5)
                        if errno: logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Create AIP Package: ' + self.p_objpath)
                        self.tarfile = tarfile.open(self.p_objpath, "w",)
                    except tarfile.TarError:
                        self.event_info = 'Problem to create AIP Package: ' + str(self.p_objpath)
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        self.ok = 0
                if self.ok:
                    ###########################################################
                    # add files to AIP package file
                    self.startTarTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    self.firstPremisObjectFlag = 1
                    self.ObjectNumItems = 0
                    self.ObjectSize = 0
                    for self.object in self.object_list: 
                        if self.metatype in [1,2,3]:
                            self.a_filepath = self.object[0]
                        elif self.metatype in [4]:
                            self.a_filepath = '%s/%s' % (self.ObjectIdentifierValue,self.object[0])
                        self.a_filepath_iso = ESSPGM.Check().unicode2str(self.a_filepath)
                        self.object_size = int(self.object[3])
                        if self.a_filepath == self.Cmets_obj or self.a_filepath == '%s/%s' % (self.ObjectIdentifierValue,self.Cmets_obj):
                            self.filepath = self.Cmets_objpath
                            if self.metatype in [4]:
                                self.MetaObjectSize = self.object_size
                                self.DataObjectSize = 0
                                self.DataObjectNumItems = 0
                        else:
                            self.filepath = os.path.join(self.SIPpath, self.a_filepath)
                            if self.metatype in [4]:
                                self.DataObjectSize += self.object_size
                                self.DataObjectNumItems += 1
                        self.filepath_iso = ESSPGM.Check().unicode2str(self.filepath)
                        if os.access(self.filepath_iso,os.R_OK):
                            if int(os.stat(self.filepath_iso)[6]) == self.object_size:
                                try:
                                    self.ObjectNumItems += 1
                                    self.tarinfo = self.tarfile.gettarinfo(self.filepath_iso, self.a_filepath_iso)
                                    self.tarfile.addfile(self.tarinfo, file(self.filepath_iso))
                                    logging.info('Add: ' + self.a_filepath + ' to AIP Package: ' + self.p_obj)
                                except tarfile.TarError:
                                    self.event_info = 'Problem to add: ' + str(self.a_filepath) + ' to AIP Package: ' + str(self.p_objpath)
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                            else:
                                self.event_info = 'Filesize for object path: %s is %s and METS object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath_iso)[6]),str(self.object_size))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                        else:
                            self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                if self.ok:
                    ###########################################################
                    # Close AIP package
                    try: 
                        self.tarfile.close()
                    except tarfile.TarError: 
                        self.event_info = 'Problem to close AIP package: ' + str(self.p_objpath)
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        self.ok = 0
                if self.ok:
                    ###########################################################
                    # Check if StatusActivity is OK
                    self.ObjectSize = os.stat(self.p_objpath)[6]
                    self.stopTarTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    self.TarTime = self.stopTarTime-self.startTarTime
                    self.WriteSize = int(self.ObjectSize)/1048576 
                    if self.TarTime.seconds < 1: self.TarTime = datetime.timedelta(seconds=1)	#Fix min time to 1 second if it is zero.
                    self.TarMBperSEC = int(self.WriteSize)/int(self.TarTime.seconds)
                    logging.info('Close AIP package: ' + self.p_obj)
                    logging.info('Succeeded to create AIP for: ' + self.ObjectIdentifierValue + ' , ' + str(self.TarMBperSEC) + ' MB/Sec and Time: ' + str(self.TarTime))
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ObjectPackageName',self.p_obj,
                                                                              'ObjectSize',self.ObjectSize,
                                                                              'ObjectNumItems',self.ObjectNumItems,
                                                                              'ObjectMessageDigest','',
                                                                              'ObjectPath','',
                                                                              'MetaObjectIdentifier',self.MetaObjectIdentifier,
                                                                              'MetaObjectSize',self.MetaObjectSize,
                                                                              'DataObjectSize',self.DataObjectSize,
                                                                              'DataObjectNumItems',self.DataObjectNumItems,
                                                                              'CreateDate',self.timestamp_utc.replace(tzinfo=None),
                                                                              'CreateAgentIdentifierValue',AgentIdentifierValue,
                                                                              'StatusProcess','39',
                                                                              'StatusActivity','0',
                                                                              'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                              'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                              'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                             ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    else: ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                    if errno == 0 and self.ext_IngestTable:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.ext_IngestTable,'UPD',('ObjectPackageName',self.p_obj,
                                                                                                 'ObjectSize',self.ObjectSize,
                                                                                                 'ObjectNumItems',self.ObjectNumItems,
                                                                                                 'ObjectMessageDigest','',
                                                                                                 'ObjectPath','',
                                                                                                 'MetaObjectIdentifier',self.MetaObjectIdentifier,
                                                                                                 'MetaObjectSize',self.MetaObjectSize,
                                                                                                 'DataObjectSize',self.DataObjectSize,
                                                                                                 'DataObjectNumItems',self.DataObjectNumItems,
                                                                                                 'CreateDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                 'CreateAgentIdentifierValue',AgentIdentifierValue,
                                                                                                 'StatusProcess','39',
                                                                                                 'StatusActivity','0',
                                                                                                 'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if ext_errno: logging.error('Failed to update External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                        else:
                            res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                else:
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 31, 4)
                    if errno: 
                        logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    else:
                        self.event_info = 'Failed to create AIP package: ' + self.p_obj
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1030','','ESSArch AIPCreator',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
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
# Table: ESSProc with Name: ESSObjectValidate, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPCreator'
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

# ./AIPCreator.py

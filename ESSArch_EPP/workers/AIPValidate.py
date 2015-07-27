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
import os, thread, datetime, time, pytz, logging, sys, ESSDB, ESSMSSQL, ESSPGM, ESSMD, ESSmetablob, string
from configuration.models import ChecksumAlgorithm_CHOICES, ArchivePolicy
from django.utils import timezone
from django import db

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logging.info('Starting ' + ProcName)
        self.tz=timezone.get_default_timezone()
        self.ChecksumAlgorithm_CHOICES_dict = dict(ChecksumAlgorithm_CHOICES)
        self.ChecksumAlgorithm_CHOICES_invdict = ESSPGM.Check().invert_dict(self.ChecksumAlgorithm_CHOICES_dict)
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
                self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
                if ExtDBupdate:
                    self.ext_IngestTable = self.IngestTable
                else:
                    self.ext_IngestTable = ''
                #if Debug: logging.info('Start to list worklist (self.dbget)')
                self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue','ObjectPackageName',
                                                                                  'PolicyId','MetaObjectIdentifier',
                                                                                  'MetaObjectSize','DataObjectSize',
                                                                                  'ObjectSize',
                                                                                  'ObjectUUID'),
                                                                                 ('StatusActivity','=','0','AND',
                                                                                  'StatusProcess','BETWEEN',49,'AND',51))
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
                    self.ObjectIdentifierValue = self.obj[0]
                    self.ObjectPackageName = self.obj[1]
                    self.PolicyId = self.obj[2]
                    #self.MetaObjectIdentifier = self.obj[3] 	#METS filename
                    #self.MetaObjectSize = self.obj[4]		#METS size (bytes)
                    #self.DataObjectSize = self.obj[5]
                    self.ObjectSize = self.obj[6]
                    self.ObjectUUID = self.obj[7]
                    logging.debug('self.obj: '+str(self.obj))

                    self.ok = 1

                    ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyStat=1, PolicyID=self.PolicyId)
                    if self.ok:
                        ###########################################################
                        # set variables
                        self.AIPpath = ArchivePolicy_obj.AIPpath
                        self.metatype = ArchivePolicy_obj.IngestMetadata
                        self.ChecksumAlgorithm = ArchivePolicy_obj.ChecksumAlgorithm
                        self.SIPpath = ArchivePolicy_obj.IngestPath
                        self.ValidateChecksum = ArchivePolicy_obj.ValidateChecksum
                        self.ValidateXML = ArchivePolicy_obj.ValidateXML
                        self.ObjectPath = os.path.join(self.AIPpath,self.ObjectPackageName)
                        self.Pmets_objpath = os.path.join(self.AIPpath,self.ObjectIdentifierValue + '_Package_METS.xml')

                    if self.metatype > 0:
                        self.startVerTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 50, 5)
                        if errno: logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        logging.info('Start validate AIP package: ' + self.ObjectIdentifierValue)
                        self.Cmets_obj = None 
                        self.Cmets_objpath = None 
                        self.premis_obj = None 
                        self.premis_objpath = None
                        self.addml_obj = None
                        self.addml_objpath = None
                        ##########################################
                        # Get PMETS info
                        if self.ok:
                            [self.Package_info,self.CMets_info],errno,why = ESSMD.getPMETSInfo(FILENAME=self.Pmets_objpath)
                            if errno:
                                self.event_info = 'Failed to get PMETS info for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Object: %s, Package_info: %s, CMets_info: %s',self.ObjectIdentifierValue,str(self.Package_info),str(self.CMets_info))
                                # CMets_info and Package_info: ['A0007600_Content_METS.xml', 'MD5', 'b0270cb4d196b72b87fe27ce6242df18', 64058, 'text/xml']
                                #if self.Package_info[1] == 'MD5': self.PackageMessageDigestAlgorithm = 1
                                self.PackageMessageDigestAlgorithm = self.ChecksumAlgorithm_CHOICES_invdict[self.Package_info[1]]
                                if self.Package_info[2]: self.PackageMessageDigest = self.Package_info[2]
                                if self.Package_info[3]: self.PackageSize = int(self.Package_info[3])
                                self.Cmets_obj = self.CMets_info[0]
                                if self.metatype in [1,2,3]:
                                    self.Cmets_objpath = os.path.join(self.AIPpath,self.Cmets_obj)
                                elif self.metatype in [4]:
                                    self.Cmets_objpath = os.path.join(self.SIPpath,self.Cmets_obj)
                                #if self.CMets_info[1] == 'MD5': self.CMetsMessageDigestAlgorithm = 1
                                self.CMetsMessageDigestAlgorithm = self.ChecksumAlgorithm_CHOICES_invdict[self.CMets_info[1]]
                                if self.CMets_info[2]: self.CMetsMessageDigest = self.CMets_info[2]
                                if self.CMets_info[3]: self.CMetsSize = int(self.CMets_info[3])
                        ##########################################################
                        # Check if ObjectPath and Cmets_objpath exist
                        if os.path.exists(self.ObjectPath) and os.path.exists(self.Cmets_objpath):
                            self.ok = 1
                        else:
                            self.event_info = 'The path to Object: %s or METS_Metaobject: %s is not accessible!' % (self.ObjectPath,self.Cmets_objpath)
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                        ##########################################
                        # Get MetsFgrp001TotalSize from METSfile 
                        if self.ok:
                            self.MetsFgrp001TotalSize,errno,why = ESSMD.getFileSizeFgrp001(FILENAME=self.Cmets_objpath)
                            if errno:
                                self.event_info = 'Failed to get MetsFgrp001TotalSize for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Object: %s, MetsFgrp001TotalSize: %s',self.ObjectIdentifierValue,str(self.MetsFgrp001TotalSize))
                        ##########################################
                        # Get PremisObjectTotalSize from METSfile
                        if self.ok:
                            if self.metatype in [1,2,3]:
                                self.premis_objpath = self.Cmets_objpath
                            elif self.metatype in [4]:
                                # Get metadata from METS file
                                res_info, res_files, res_struct, errno, why = ESSMD.getMETSFileList(FILENAME=self.Cmets_objpath)
                                if errno:
                                    self.event_info = 'Failed to get metadata from content METS for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                                else:
                                    for res_file in res_files:
                                        if res_file[0] == 'amdSec' and res_file[2] == 'digiprovMD':
                                            self.premis_obj = res_file[8][5:]
                                            self.premis_objpath = '%s/%s/%s' % (self.SIPpath,self.ObjectIdentifierValue,self.premis_obj)
                                        elif res_file[0] == 'amdSec' and res_file[2] == 'techMD' and res_file[16] == 'ADDML': 
                                            self.addml_obj = res_file[8][5:]
                                            self.addml_objpath = '%s/%s/%s' % (self.SIPpath,self.ObjectIdentifierValue,self.addml_obj)
                            self.PremisObjectTotalSize,errno,why = ESSMD.getFileSizePremis(FILENAME=self.premis_objpath)
                            if errno:
                                self.event_info = 'Failed to get PREMISobjects total size in METSfile for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Object: %s, PremisObjectTotalSize: %s',self.ObjectIdentifierValue,str(self.PremisObjectTotalSize))
                        ###################################################
                        # Check if MetsFgrp001TotalSize is equal to PremisObjectTotalSize
                        if self.ok:
                            if self.MetsFgrp001TotalSize == self.PremisObjectTotalSize:
                                logging.info('Succeeded to verify METS Fgrp001 and PREMIS for object: %s, MetsFgrp001TotalSize: %s is equal to PremisObjectTotalSize: %s',self.ObjectIdentifierValue,str(self.MetsFgrp001TotalSize),str(self.PremisObjectTotalSize))
                            else:
                                self.event_info = 'Failed to verify METS Fgrp001 and PREMIS for object: %s, MetsFgrp001TotalSize: %s is not equal to PremisObjectTotalSize: %s' % (self.ObjectIdentifierValue,str(self.MetsFgrp001TotalSize),str(self.PremisObjectTotalSize))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                        ##########################################
                        # Get CMetsTotalSize
                        if self.ok:
                            self.CMetsTotalSize,errno,why = ESSMD.getTotalSize(FILENAME=self.Cmets_objpath)
                            if errno:
                                self.event_info = 'Failed to get CMetsTotalSize for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Object: %s, raw CMetsTotalSize: %s',self.ObjectIdentifierValue,str(self.CMetsTotalSize))
                                if self.CMetsSize:
                                    # Add Content Mets filesize
                                    self.CMetsTotalSize[0] += 1
                                    self.CMetsTotalSize[1] += self.CMetsSize
                                logging.debug('Object: %s, CMetsTotalSize: %s',self.ObjectIdentifierValue,str(self.CMetsTotalSize))
                        ##########################################
                        # Get TarFileSize
                        if self.ok:
                            self.TarFileSize,errno,why = ESSPGM.Check().getFileSizeTAR(self.ObjectPath)
                            if errno:
                                self.event_info = 'Failed to get TarFileSize for object: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Object: %s, TarFileSize: %s',self.ObjectIdentifierValue,str(self.TarFileSize))
                        ###################################################
                        # Check if CMetsTotalSize is equal to TarFileSize
                        if self.ok:
                            if self.CMetsTotalSize == self.TarFileSize:
                                logging.info('Succeeded to verify total package size for object: %s, CMetsTotalSize: %s is equal to TarFileSize: %s',self.ObjectIdentifierValue,str(self.CMetsTotalSize),str(self.TarFileSize))
                            else:
                                self.event_info = 'Failed to verify total package size for object: %s, CMetsTotalSize: %s is not equal to TarFileSize: %s' % (self.ObjectIdentifierValue,str(self.CMetsTotalSize),str(self.TarFileSize))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                        ########################
                        # get checksum for PMETS file
                        if self.ok:
                            self.PMetsMessageDigestAlgorithm = self.ChecksumAlgorithm
                            self.PMetsMessageDigest = ''
                            self.Pmets_obj_checksum,errno,why = ESSPGM.Check().checksum(self.Pmets_objpath, self.PMetsMessageDigestAlgorithm) # Checksum
                            if errno:
                                self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.Cmets_objpath,str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Checksum for PMETS file: %s',self.Pmets_obj_checksum)
                                self.PMetsMessageDigestAlgorithm = 1
                                self.PMetsMessageDigest = self.Pmets_obj_checksum
                        ########################
                        # get checksum for CMETS file
                        if self.ok:
                            self.Cmets_obj_checksum,errno,why = ESSPGM.Check().checksum(self.Cmets_objpath, self.CMetsMessageDigestAlgorithm) # Checksum
                            if errno:
                                self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.Cmets_objpath,str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                            else:
                                logging.debug('Checksum for CMETS file: %s',self.Cmets_obj_checksum)
                        ###################################################
                        # Check CMetsMessageDigest 
                        if self.ok:
                            if self.ValidateChecksum:
                                if self.CMetsMessageDigest == self.Cmets_obj_checksum:
                                    logging.info('Succeeded to verify Content Mets MessageDigest for object: %s',self.ObjectIdentifierValue)
                                else:
                                    self.event_info = 'Failed to verify Content Mets MessageDigest for object: %s, CMetsMessageDigest: %s is equal to FileMessageDigest: %s' % (self.ObjectIdentifierValue,str(self.CMetsMessageDigest),str(self.Cmets_obj_checksum))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                            else:
                                logging.warning('Checksum validate is disabled for object: %s',self.ObjectIdentifierValue)
                        if self.ValidateXML:
                            ########################
                            # XML Schema Validate CMETS file
                            if self.ok:
                                errno,why = ESSMD.validate(FILENAME=self.Cmets_objpath)
                                if errno:
                                    self.event_info = 'Failed to schema validate Content METS file for object: %s, why: %s' % (self.ObjectIdentifierValue, str(why))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                                else:
                                    logging.info('Succeeded to schema validate Content METS file for object: %s',self.ObjectIdentifierValue)
                            ########################
                            # XML Schema Validate PMETS file
                            if self.ok:
                                errno,why = ESSMD.validate(FILENAME=self.Pmets_objpath)
                                if errno:
                                    self.event_info = 'Failed to schema validate Package METS file for object: %s, why: %s' % (self.ObjectIdentifierValue, str(why))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                                else:
                                    logging.info('Succeeded to schema validate Package METS file for object: %s',self.ObjectIdentifierValue)
                            ########################
                            # XML Schema Validate PREMIS file
                            if self.ok and self.premis_obj:
                                errno,why = ESSMD.validate(FILENAME=self.premis_objpath)
                                if errno:
                                    self.event_info = 'Failed to schema validate PREMIS file for object: %s, why: %s' % (self.ObjectIdentifierValue, str(why))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                                else:
                                    logging.info('Succeeded to schema validate PREMIS file for object: %s',self.ObjectIdentifierValue)
                            ########################
                            # XML Schema Validate ADDML file
                            if self.ok and self.addml_obj:
                                errno,why = ESSMD.validate(FILENAME=self.addml_objpath)
                                if errno:
                                    self.event_info = 'Failed to schema validate ADDML file for object: %s, why: %s' % (self.ObjectIdentifierValue, str(why))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                    self.ok = 0
                                else:
                                    logging.info('Succeeded to schema validate ADDML file for object: %s',self.ObjectIdentifierValue)
                        else:
                            logging.warning('Schema validate XML is disabled for object: %s',self.ObjectIdentifierValue)
                        self.stopVerTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                        self.VerTime = self.stopVerTime-self.startVerTime
                        if self.VerTime.seconds < 1: self.VerTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
                        self.ObjectSizeMB = int(self.ObjectSize)/1048576
                        self.VerMBperSEC = int(self.ObjectSizeMB)/int(self.VerTime.seconds)
                        ##################################
                        # Write metadatafiles to DB-blob or FTP
                        if self.ok:
                            if ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_HOST'))[0][0]:
                                if self.Cmets_obj:
                                    ##################################
                                    # Write CMETS metadatafile to DB-blob
                                    res,errno,why = ESSmetablob.prod().StoreMetadataBlob(ObjectUUID=self.ObjectUUID,
                                                                                         ObjectIdentifierValue=self.ObjectIdentifierValue,
                                                                                         ObjectMetadataType=26,
                                                                                         FILENAME=self.Cmets_objpath,
                                                                                         FTPFileName=string.replace(self.Cmets_obj,self.ObjectIdentifierValue+'/',''),
                                                                                         FTPflag=1,
                                                                                         DBflag=0,
                                                                                         AgentIdentifierValue=AgentIdentifierValue)
                                    if errno:
                                        self.event_info = 'Failed to store Content METS file to FTP server or DB-blob: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue, str(errno), str(why))
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                    else:
                                        logging.info('Succeeded to store Content METS file to FTP server or DB-blob for object: %s',self.ObjectIdentifierValue)
                                if self.premis_obj:
                                    ##################################
                                    # Write PREMIS metadatafile to DB-blob
                                    res,errno,why = ESSmetablob.prod().StoreMetadataBlob(ObjectUUID=self.ObjectUUID,
                                                                                         ObjectIdentifierValue=self.ObjectIdentifierValue,
                                                                                         ObjectMetadataType=27,
                                                                                         FILENAME=self.premis_objpath,
                                                                                         FTPFileName=self.premis_obj,
                                                                                         FTPflag=1,
                                                                                         DBflag=0,
                                                                                         AgentIdentifierValue=AgentIdentifierValue)
                                    if errno:
                                        self.event_info = 'Failed to store PREMIS file to FTP server or DB-blob: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue, str(errno), str(why))
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                    else:
                                        logging.info('Succeeded to store PREMIS file to FTP server or DB-blob for object: %s',self.ObjectIdentifierValue)
                                if self.addml_obj:
                                    ##################################
                                    # Write ADDML metadatafile to DB-blob
                                    res,errno,why = ESSmetablob.prod().StoreMetadataBlob(ObjectUUID=self.ObjectUUID,
                                                                                         ObjectIdentifierValue=self.ObjectIdentifierValue,
                                                                                         ObjectMetadataType=25,
                                                                                         FILENAME=self.addml_objpath,
                                                                                         FTPFileName=self.addml_obj,
                                                                                         FTPflag=1,
                                                                                         DBflag=0,
                                                                                         AgentIdentifierValue=AgentIdentifierValue)
                                    if errno:
                                        self.event_info = 'Failed to store ADDML file to FTP server or DB-blob: %s, errno: %s, why: %s' % (self.ObjectIdentifierValue, str(errno), str(why))
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                        self.ok = 0
                                    else:
                                        logging.info('Succeeded to store ADDML file to FTP server or DB-blob for object: %s',self.ObjectIdentifierValue)
                            else:
                                logging.info('Skip to store metadata to FTP server or DB-blob for object: %s',self.ObjectIdentifierValue)
                        if not self.ok:
                            errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 51, 4)
                            if errno: 
                                logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else:
                                self.event_info = 'Failed to validate AIP package: ' + self.ObjectIdentifierValue
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        else:
                            logging.info('Succeeded to validate AIP package: ' + self.ObjectIdentifierValue + ' , ' + str(self.VerMBperSEC) + ' MB/Sec and Time: ' + str(self.VerTime))
                            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                            res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('StatusProcess','59',
                                                                                      'StatusActivity','0',
                                                                                      'CMetaMessageDigestAlgorithm',self.CMetsMessageDigestAlgorithm,
                                                                                      'CMetaMessageDigest',self.CMetsMessageDigest,
                                                                                      'PMetaMessageDigestAlgorithm',self.PMetsMessageDigestAlgorithm,
                                                                                      'PMetaMessageDigest',self.PMetsMessageDigest,
                                                                                      'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                                      'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                      'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                     ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                            else: ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'0','',2,self.ObjectIdentifierValue)
                            if errno == 0 and ExtDBupdate:
                                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('StatusProcess','59',
                                                                                                         'StatusActivity','0',
                                                                                                         'CMetaMessageDigestAlgorithm',self.CMetsMessageDigestAlgorithm,
                                                                                                         'CMetaMessageDigest',self.CMetsMessageDigest,
                                                                                                         'PMetaMessageDigestAlgorithm',self.PMetsMessageDigestAlgorithm,
                                                                                                         'PMetaMessageDigest',self.PMetsMessageDigest,
                                                                                                         'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                         'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                        ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                if ext_errno: logging.error('Failed to update External DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(ext_why))
                                else:
                                    res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                                    if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))

                    elif self.metatype == 0: #self.metatype 0 = No metadata
                        logging.info('Skip to validate AIP package: ' + self.ObjectIdentifierValue)
                        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                        res,errno,why = ESSDB.DB().action(self.IngestTable,'UPD',('StatusProcess','59',
                                                                                  'StatusActivity','0',
                                                                                  'CMetaMessageDigestAlgorithm','0',
                                                                                  'PMetaMessageDigestAlgorithm','0',
                                                                                  'LastEventDate',self.timestamp_utc.replace(tzinfo=None),
                                                                                  'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                  'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                 ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if errno: logging.error('Failed to update Local DB: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                        else: ESSPGM.Events().create('1050','','ESSArch AIPValidate',ProcVersion,'0','Skip to validate AIP package',2,self.ObjectIdentifierValue)
                        if errno == 0 and ExtDBupdate:
                            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('StatusProcess','59',
                                                                                                     'StatusActivity','0',
                                                                                                     'CMetaMessageDigestAlgorithm','0',
                                                                                                     'PMetaMessageDigestAlgorithm','0',
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
# Table: ESSProc with Name: AIPValidate, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'AIPValidate'
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

# ./AIPValidate.py

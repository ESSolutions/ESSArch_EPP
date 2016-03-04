#!/usr/bin/env /ESSArch/pd/python/bin/python
# -*- coding: UTF-8 -*-

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

import os, thread, datetime, time, logging, sys, ESSDB, ESSPGM, ESSMD
from configuration.models import ChecksumAlgorithm_CHOICES, ArchivePolicy
from django import db

class WorkingThread:
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logging.info('Starting ' + ProcName)
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
            if ExtDBupdate:
                self.ext_IngestTable = self.IngestTable
            else:
                self.ext_IngestTable = ''
            #if Debug: logging.info('Start to list worklist (self.dbget)')

            self.dbget,errno,why = ESSDB.DB().action(self.IngestTable,'GET4',('ObjectIdentifierValue','ObjectUUID','PolicyId','INFORMATIONCLASS'),
                                                                             ('StatusActivity','=','0','AND',
                                                                              'StatusProcess','BETWEEN',24,'AND',26))
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
                self.ObjectIdentifierValue = ESSPGM.Check().str2unicode(self.obj[0])
                self.ObjectUUID = self.obj[1]
                self.PolicyId = self.obj[2]
                self.INFORMATIONCLASS = self.obj[3]
                logging.info('Start to validate format for SIP: %s', self.ObjectIdentifierValue)
                self.ChecksumAlgorithm_CHOICES_dict = dict(ChecksumAlgorithm_CHOICES)
                self.ChecksumAlgorithm_CHOICES_invdict = ESSPGM.Check().invert_dict(self.ChecksumAlgorithm_CHOICES_dict)
                ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyStat=1, PolicyID=self.PolicyId)
                if self.ok:
                    ###########################################################
                    # set variables
                    self.AIPpath = ESSPGM.Check().str2unicode(ArchivePolicy_obj.AIPpath)
                    self.metatype = ArchivePolicy_obj.IngestMetadata
                    self.Policy_INFORMATIONCLASS = ArchivePolicy_obj.INFORMATIONCLASS
                    self.ChecksumAlgorithm = ArchivePolicy_obj.ChecksumAlgorithm
                    self.ChecksumAlgorithm_name = self.ChecksumAlgorithm_CHOICES_dict[self.ChecksumAlgorithm]
                    self.SIPpath = ESSPGM.Check().str2unicode(ArchivePolicy_obj.IngestPath)
                    self.DBmode = ArchivePolicy_obj.Mode
                    logging.debug('self.obj: %s', str(self.obj))
                    logging.debug('self.ObjectIdentifierValue: %s', self.ObjectIdentifierValue)
                    logging.debug('Len self.ObjectIdentifierValue: %s', len(self.ObjectIdentifierValue))
                    logging.debug('self.SIPpath: %s', self.SIPpath)
                    logging.debug('self.AIPpath: %s', self.AIPpath)
                if self.metatype == 2:
                    ############################################
                    # Create PREMISfile from TIFFEdit.RES if metatype is 2
                    logging.info('Start to convert RESfile to PREMISfile for object: ' + self.ObjectIdentifierValue)
                    self.xml_PREMIS,self.errno,self.why = ESSMD.RES2PREMIS(os.path.join(self.SIPpath,self.ObjectIdentifierValue),AgentIdentifierValue[8:])
                    if self.errno == 10:
                        self.event_info = 'Failed to parse RESfile, error.num: %s error.det: %s' % (str(self.errno),str(self.why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                    elif self.errno == 20:
                        self.event_info = 'I/O error to access RESfile, error.num: %s error.det: %s' % (str(self.errno),str(self.why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                    elif self.errno == 30:
                        self.event_info = 'Validation errors for PREMIS file, error.num: %s error.det: %s' % (str(self.errno),str(self.why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                    elif self.errno == 40:
                        self.event_info = 'Problem to write PREMIS file, error.num: %s error.det: %s' % (str(self.errno),str(self.why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                    if self.errno > 1:
                        self.event_info = 'Problem to convert RES to PREMIS for SIP package: %s, error.num: %s  error.desc: %s' % (self.ObjectIdentifierValue,str(self.errno),str(self.why))
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                        self.ok = 0
                    elif self.errno == 1:
                        self.event_info = 'Warning in convert RES to PREMIS for SIP package: %s, error.num: %s  warning.desc: %s' % (self.ObjectIdentifierValue,str(self.errno),str(self.why))
                        logging.warning(self.event_info)
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'0',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                    else:
                        ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPValidateFormat',ProcVersion,'0','',self.DBmode,self.ObjectIdentifierValue)
                    if self.ok:
                        ############################################
                        # Clean RES SIP from "junk" files 
                        self.errno,self.why = ESSPGM.Check().CleanRES_SIP(os.path.join(self.SIPpath,self.ObjectIdentifierValue))
                        if self.errno:
                            self.event_info = 'Problem to clean RES SIP from "junk files" for SIP package: %s, error.num: %s  error.desc: %s' % (self.ObjectIdentifierValue,str(self.errno),str(self.why))
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1022','CleanRES_SIP','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                            self.ok = 0
                        else:
                            ESSPGM.Events().create('1022','CleanRES_SIP','ESSArch SIPValidateFormat',ProcVersion,'0','',self.DBmode,self.ObjectIdentifierValue)
                elif self.metatype == 1:
                    ###########################################################
                    # Create PREMISfile from Content_METS if metatype is 1
                    res,errno,why = ESSMD.METS2PREMIS(self.SIPpath,self.ObjectIdentifierValue)
                    if not errno:
                        logging.info('Succeeded to convert Content_METS to PREMISfile for information package: %s', self.ObjectIdentifierValue)
                    else:
                        self.event_info = 'Problem to convert Content_METS to PREMISfile for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                        logging.error(self.event_info)
                        #ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                        self.ok = 0
                elif self.metatype in [4]:
                    self.SIPpath = os.path.join(self.SIPpath,self.ObjectIdentifierValue)
                if self.ok:
                    if self.metatype in [1,2,3]:
                        ###########################################################
                        # get object_list from PREMIS file
                        self.Premis_filepath = u'%s/%s/%s_PREMIS.xml' % (self.SIPpath,self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list,errno,why = ESSMD.getPremisObjects(FILENAME=self.Premis_filepath)
                        if errno == 0:
                            logging.info('Succeeded to get object_list from premis for information package: %s', self.ObjectIdentifierValue)
                        else:
                            self.event_info = 'Problem to get object_list from premis for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                            self.ok = 0
                    elif self.metatype in [4]:
                        ###########################################################
                        # get object_list from METS
                        if os.path.exists(os.path.join(self.SIPpath,'sip.xml')):
                            mets_file = 'sip.xml'
                            self.SIPmets_objpath = os.path.join(self.SIPpath,mets_file)
                        elif os.path.exists(os.path.join(self.SIPpath,'mets.xml')):
                            mets_file = 'mets.xml'
                            self.SIPmets_objpath = os.path.join(self.SIPpath,mets_file)
                        #elif os.path.exists(os.path.join(self.SIPpath,'%s_Content_METS.xml' % self.ObjectIdentifierValue)):
                        #    mets_file = '%s_Content_METS.xml' % self.ObjectIdentifierValue
                        #    self.SIPmets_objpath = os.path.join(self.SIPpath,mets_file)
                        else:
                            self.SIPmets_objpath = ''
                            self.event_info = 'Problem to find METS file for information package: %s in path: %s' % (self.ObjectIdentifierValue,self.SIPpath)
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                        if self.SIPmets_objpath:                    
                            self.object_list,errno,why = ESSMD.getAIPObjects(FILENAME=self.SIPmets_objpath)
                            if errno == 0:
                                logging.info('Succeeded to get object_list from METS for information package: %s', self.ObjectIdentifierValue)
                                self.F_Checksum,errno,why = ESSPGM.Check().checksum(self.SIPmets_objpath, self.ChecksumAlgorithm) # Checksum
                                self.F_SIZE = os.stat(self.SIPmets_objpath)[6]
                                self.object_list.append([mets_file,self.ChecksumAlgorithm_name,self.F_Checksum,self.F_SIZE,''])
                            else:
                                self.event_info = 'Problem to get object_list from METS for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                                self.ok = 0
                if self.ok:
                    ###########################################################
                    # update ObjectIdentifierValue to StatusProcess: 25 and StatusActivity: 5
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 25, 5)
                    if errno:
                        logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    logging.info('Format validate object: ' + self.ObjectIdentifierValue)
                if self.ok:
                    ###########################################################
                    # Start to format validate SIP
                    self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    self.ObjectNumItems = 0
                    self.ObjectSize = 0
                    if self.metatype == 1:
                        ############################################
                        # Object have metatype 1 (METS)
                        self.tmp_object_id = (u'%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list.append([self.tmp_object_id,'', '', '', '', 'ARCHMETAxmlWrap', 'PREMIS'])
                    elif self.metatype == 2:
                        ############################################
                        # Object have metatype 2 (RES)
                        #self.tmp_object_id = ('%s/TIFFEdit.RES') % self.ObjectIdentifierValue
                        #self.object_list.append([self.tmp_object_id,'', '', '', '', 'ARCHMETA', ''])
                        self.tmp_object_id = (u'%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list.append([self.tmp_object_id,'', '', '', '', 'ARCHMETAxmlWrap', 'PREMIS'])
                    elif self.metatype == 3:
                        ############################################
                        # Object have metatype 3 (ADDML)
                        self.tmp_object_id = (u'%s/%s_ADDML.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list.append([self.tmp_object_id,'', '', '', '', 'ARCHMETAxmlWrap', 'ADDML'])
                        self.tmp_object_id = (u'%s/%s_PREMIS.xml') % (self.ObjectIdentifierValue,self.ObjectIdentifierValue)
                        self.object_list.append([self.tmp_object_id,'', '', '', '', 'ARCHMETAxmlWrap', 'PREMIS'])
                    for self.object in self.object_list:
                        logging.debug('variable self.SIPpath: %s, type: %s' % (self.SIPpath,type(self.SIPpath)))
                        logging.debug('variable self.object[0]: %s, type: %s' % (self.object[0],type(self.object[0])))
                        self.filepath = os.path.join(self.SIPpath, self.object[0])
                        logging.debug('variable self.filepath: %s, type: %s' % (self.filepath,type(self.filepath)))
                        #self.filepath = ESSPGM.Check().Unicode2isoStr(self.filepath.encode('utf-8'))
                        #self.filepath_iso = ESSPGM.Check().unicode2str(self.filepath)
                        #logging.debug('variable self.filepath_iso: %s, type: %s' % (self.filepath_iso,type(self.filepath_iso)))
                        if self.metatype in [1,2,3] and self.ObjectNumItems == 0:
                            if self.object[0] == self.ObjectIdentifierValue:
                                logging.info('First premis object match information package: %s', self.ObjectIdentifierValue)
                            else:
                                self.event_info = 'First premis object do not match information package: %s, premis_object: %s' % (self.ObjectIdentifierValue,self.object[0])
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                self.ok = 0
                                break
                            if self.ok and os.access(self.filepath,os.X_OK):
                                pass
                            else:
                                self.event_info = 'Object path: %s do not exist or is not executable!' % self.filepath
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                self.ok = 0
                                break
                        if self.ok and os.access(self.filepath,os.R_OK):
                            pass
                        else:
                            self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                            self.ok = 0
                            break
                        if self.ok and os.access(self.filepath,os.W_OK):
                            pass
                        else:
                            self.event_info = 'Missing permission, Object path: %s is not writeable!' % self.filepath
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                            self.ok = 0
                            break
                        if self.metatype in [1,2,3]:
                            if self.ok and not (self.ObjectNumItems == 0 or self.object[5] == 'ARCHMETA' or self.object[5] == 'ARCHMETAxmlWrap'):
                                if int(os.stat(self.filepath)[6]) == int(self.object[4]):
                                    self.ObjectSize += int(self.object[4])
                                else:
                                    self.event_info = 'Filesize for object path: %s is %s and premis object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath)[6]),str(self.object[4]))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                    self.ok = 0
                                    break
                                if self.ok:
                                    self.F_Checksum,errno,why = ESSPGM.Check().checksum(self.filepath,self.object[1]) # Checksum
                                    if errno:
                                        self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.filepath,str(why))
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                        self.ok = 0
                                if self.ok:
                                    if self.F_Checksum == self.object[2]:
                                        pass
                                    else:
                                        self.event_info = 'Checksum for object path: %s is %s and premis object checksum is %s. The checksum must match!' % (self.filepath,self.F_Checksum,self.object[2])
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                        self.ok = 0
                                        break
                            elif self.ok and not self.ObjectNumItems == 0 and (self.object[5] == 'ARCHMETA' or self.object[5] == 'ARCHMETAxmlWrap'):
                                if int(os.stat(self.filepath)[6]) > 0:
                                    pass
                                else:
                                    self.event_info = 'Filesize for object path: %s is 0 bytes. The size should be more then 0 bytes!' % self.filepath
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                    self.ok = 0
                                    break
                        elif self.metatype in [4]:
                            if self.ok:
                                #[objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE]
                                if int(os.stat(self.filepath)[6]) == int(self.object[3]):
                                    self.ObjectSize += int(self.object[3])
                                else:
                                    self.event_info = 'Filesize for object path: %s is %s and METS object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath)[6]),str(self.object[3]))
                                    logging.error(self.event_info)
                                    ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                    self.ok = 0
                                    break
                                if self.ok:
                                    self.F_Checksum,errno,why = ESSPGM.Check().checksum(self.filepath,self.object[1]) # Checksum
                                    if errno:
                                        self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.filepath,str(why))
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                        self.ok = 0
                                if self.ok:
                                    if self.F_Checksum == self.object[2]:
                                        pass
                                    else:
                                        self.event_info = 'Checksum for object path: %s is %s and METS object checksum is %s. The checksum must match!' % (self.filepath,self.F_Checksum,self.object[2])
                                        logging.error(self.event_info)
                                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                        self.ok = 0
                                        break
                        self.ObjectNumItems += 1
                if self.ok:
                    if self.metatype in [1,2,3]:
                        ###############################################################################
                        # Check if SIP filesystem path contain files that not exist in metadatafile
                        for self.filesystem_object in ESSPGM.Check().GetFiletree(os.path.join(self.SIPpath,self.ObjectIdentifierValue)):
                            self.missmatch_flag = 0
                            for self.object in self.object_list:
                                #if os.path.join(self.ObjectIdentifierValue,self.filesystem_object) == self.object[0].encode('utf-8'):
                                if os.path.join(self.ObjectIdentifierValue,self.filesystem_object) == self.object[0]:
                                    self.missmatch_flag = 0
                                    break
                                else:
                                    self.missmatch_flag = 1
                            if self.missmatch_flag:
                                self.filesystempath = u'%s/%s/%s' % (self.SIPpath,self.ObjectIdentifierValue,self.filesystem_object)
                                self.event_info = 'Filesystem file: %s do not exist in metadatafile for object: %s' % (self.filesystempath,os.path.join(self.SIPpath,self.ObjectIdentifierValue))
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                self.ok = 0
                    if self.metatype in [4]:
                        ###############################################################################
                        # Check if SIP filesystem path contain files that not exist in metadatafile
                        for self.filesystem_object in ESSPGM.Check().GetFiletree(self.SIPpath):
                            self.missmatch_flag = 0
                            for self.object in self.object_list:
                                if self.filesystem_object == self.object[0]:
                                    self.missmatch_flag = 0
                                    break
                                else:
                                    self.missmatch_flag = 1
                            if self.missmatch_flag:
                                self.filesystempath = u'%s/%s' % (self.SIPpath,self.filesystem_object)
                                self.event_info = 'Filesystem file: %s do not exist in metadatafile for object: %s' % (self.filesystempath,self.SIPpath)
                                logging.error(self.event_info)
                                ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                                self.ok = 0
                if self.ok:
                    if self.metatype in [4]:
                        ###############################################################################
                        # Check if SIP INFORMATIONCLASS match Policy
                        if self.INFORMATIONCLASS == self.Policy_INFORMATIONCLASS:
                            self.event_info = 'Object: %s InformationClass: %s match defined InformaionClass: %s in PolicyID: %s' % (self.ObjectIdentifierValue,self.INFORMATIONCLASS,self.Policy_INFORMATIONCLASS,self.PolicyId)
                            logging.info(self.event_info)
                        else:
                            self.event_info = 'Object: %s InformationClass: %s do not match defined InformationClass: %s in PolicyID: %s' % (self.ObjectIdentifierValue,self.INFORMATIONCLASS,self.Policy_INFORMATIONCLASS,self.PolicyId)
                            logging.error(self.event_info)
                            ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
                            self.ok = 0
                if self.ok:
                    self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
                    self.MeasureTime = self.stopTime-self.startTime
                    self.ObjectSizeMB = self.ObjectSize/1048576 
                    if self.MeasureTime.seconds < 1: self.MeasureTime = datetime.timedelta(seconds=1)	#Fix min time to 1 second if it is zero.
                    self.VerMBperSEC = int(self.ObjectSizeMB)/int(self.MeasureTime.seconds)
                if self.ok:
                    logging.info('Succeeded to validate SIP package: ' + self.ObjectIdentifierValue + ' , ' + str(self.VerMBperSEC) + ' MB/Sec and Time: ' + str(self.MeasureTime))
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 29, 0)
                    if errno:
                        logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    else: 
                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'0','',self.DBmode,self.ObjectIdentifierValue)
                else:
                    errno,why = ESSPGM.DB().SetAIPstatus(self.IngestTable, self.ext_IngestTable, AgentIdentifierValue, self.ObjectUUID, 26, 4)
                    if errno:
                        logging.error('Failed to update DB status for AIP: ' + str(self.ObjectIdentifierValue) + ' error: ' + str(why))
                    else:
                        self.event_info = 'Failed to validate SIP package: ' + self.ObjectIdentifierValue
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1025','','ESSArch SIPValidateFormat',ProcVersion,'1',self.event_info,self.DBmode,self.ObjectIdentifierValue)
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
# Table: ESSProc with Name: SIPValidateFormat, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    Debug=1
    ProcName = 'SIPValidateFormat'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    LogFile,Time,Status,Run = ESSDB.DB().action('ESSProc','GET',('LogFile','Time','Status','Run'),('Name',ProcName))[0]

    #LogLevel = logging.INFO
    LogLevel = logging.DEBUG
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

# ./SIPValidateFormat.py

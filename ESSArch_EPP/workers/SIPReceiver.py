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

import os, shutil, thread, datetime, time, logging, sys, csv, tarfile, stat, ESSDB, ESSMSSQL, ESSPGM, ESSlogging, ESSMD, pytz
import uuid

from essarch.models import IngestQueue, ArchiveObject
from configuration.models import ArchivePolicy
from django.utils import timezone
from django import db

class WorkingThread:
    tz=timezone.get_default_timezone()
    "Thread is working in the background"
    ###############################################
    def ThreadMain(self,ProcName):
        logger.info('Starting ' + ProcName)
        while 1:
            if self.mDieFlag==1: break      # Request for death
            self.mLock.acquire()
            self.Time,self.Run = ESSDB.DB().action('ESSProc','GET',('Time','Run'),('Name',ProcName))[0]
            if self.Run == '0':
                logger.info('Stopping ' + ProcName)
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('Name',ProcName))
                self.mLock.release()
                logger.info('RunFlag: 0')
                time.sleep(1)
                break
            # Process Item
            lock=thread.allocate_lock()
            self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
            if ExtDBupdate:
                self.ext_IngestTable = self.IngestTable
            else:
                self.ext_IngestTable = ''

            try:
                IngestPath_dict = {}
                
                ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat = 1).all()
                for ArchivePolicy_obj in ArchivePolicy_objs:
                    if not ArchivePolicy_obj.IngestPath in IngestPath_dict.keys():
                        IngestPath_dict[ArchivePolicy_obj.IngestPath] = [ArchivePolicy_obj]
                    else:
                        IngestPath_dict[ArchivePolicy_obj.IngestPath].append(ArchivePolicy_obj)
                
                for IngestPath in IngestPath_dict.keys():
                    try:
                        dir_list = os.listdir(IngestPath)
                    except OSError:
                        logging.error('Problem to list dir: %s, error: %s' % (IngestPath, str(sys.exc_info())))
                        dir_list = []
                    for ArchivePolicy_obj in IngestPath_dict[IngestPath]:
                        #########################################################
                        # PreIngestMetadata 1 = RES SIP
                        if ArchivePolicy_obj.PreIngestMetadata == 1:
                            self.Convert_RES_to_METS_SIP(dir_list, ArchivePolicy_obj)
                        
                        #########################################################
                        # IngestMetadata 1 or 4 = METS SIP
                        if ArchivePolicy_obj.IngestMetadata == 1 or ArchivePolicy_obj.IngestMetadata == 4:
                            self.Check_IngestPath_for_updates(dir_list, ArchivePolicy_obj)

                        #########################################################
                        # IngestMetadata 3 = PREMIS/ADDML SIP
                        elif ArchivePolicy_obj.IngestMetadata == 3:
                            self.Check_IngestPath_for_updates_PREMIS(dir_list, ArchivePolicy_obj)

                        time.sleep(int(self.Time))
            except:
                logger.error('Unexpected error: %s' % (str(sys.exc_info())))
                raise
            db.close_old_connections()
            self.mLock.release()
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

    def Convert_RES_to_METS_SIP(self, dir_list, ArchivePolicy_obj):
        #########################################################
        # PreIngestMetadata 1 = RES SIP
        for self.ObjectIdentifierValue in dir_list:
            self.objectstatus = 0
            self.DataObjectSize = 0
            self.numfiles = 0
            self.dbget = None
            # Fix to filter out eveyrything except dirs with lengt of 8 or 9
            if len(self.ObjectIdentifierValue) in range(8,10):
                SIPpath = ArchivePolicy_obj.IngestPath
                SIProotpath = os.path.join(SIPpath,self.ObjectIdentifierValue)
                if os.path.exists(os.path.join(SIProotpath,'sip.xml')):
                    logging.debug('The SIPtype for object %s is eARD METS' % self.ObjectIdentifierValue)
                    self.objectstatus = 0
                    self.newobject = 0
                    continue
                elif os.path.exists(os.path.join(SIProotpath,'TIFFEdit.RES')):
                    ###############################################################
                    # Try to access ingestpath
                    ###############################################################
                    self.DataObjectSize, self.numfiles, self.file_list, self.filetree_errno, self.filetree_why = Functions().GetFiletreeSum(SIProotpath)

                    self.dbget = ESSDB.DB().action(self.IngestTable,'GET',('DataObjectSize','StatusActivity','StatusProcess'),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    self.newobject = 1
                    if self.dbget:
                        if int(self.dbget[0][2]) == 5:
                            #logging.info('The object %s is ready to remodel.' % self.ObjectIdentifierValue)
                            logging.info('The object %s is ready to ingest.' % self.ObjectIdentifierValue)
                            self.objectstatus = 0
                            self.newobject = 0
                        elif int(self.dbget[0][2]) > 9:
                            ###############################################################
                            # The object %s is already archived
                            ###############################################################
                            self.objectstatus = 100
                            self.newobject = 0

                    if not self.filetree_errno:
                        if self.newobject and self.dbget and int(self.dbget[0][2]) in range(0,5) and int(self.dbget[0][1]) in range(0,3):
                            ###############################################################
                            # An already discovered directory found, checking if stable
                            ###############################################################
                            if self.dbget[0][0] == self.DataObjectSize:
                                ###############################################################
                                # directory is stable
                                ###############################################################
                                self.objectstatus = 3
                            else:
                                ###############################################################
                                # directory is still growing
                                ###############################################################
                                self.objectstatus = 2
                        elif self.newobject and not self.dbget:
                            ###############################################################
                            # A new directory discovered
                            ###############################################################
                            self.objectstatus = 1
                    elif self.filetree_errno and not self.objectstatus == 100:
                        ###############################################################
                        # Problem to access object
                        ###############################################################
                        self.objectstatus = 99

                if self.objectstatus == 0:
                    pass
                elif self.objectstatus == 1:
                    #maste kolla mot arkiv tabellen om objektet redan ar skrivit till band
                    self.StatusProcess = 0
                    self.StatusActivity = 1
                    logging.info('Object %s do not exist in DB or receive, Insert object to DB' % self.ObjectIdentifierValue)
                elif self.objectstatus == 2:
                    self.StatusProcess = 0
                    self.StatusActivity = 2
                    logging.info('Object %s, %s is receive, update DB with new size.' % (self.ObjectIdentifierValue,self.DataObjectSize))
                elif self.objectstatus == 3:
                    logging.info('Object %s, %s is stable start to convert to METS SIP.' % (self.ObjectIdentifierValue,self.DataObjectSize))
                    self.ok = 1
                    SIPcontentpath = os.path.join(SIProotpath,'c')
                    SIPmetapath = os.path.join(SIProotpath,'m')
                    Premis_filepath = os.path.join(SIPmetapath,'%s_PREMIS.xml' % self.ObjectIdentifierValue)
                    Mets_filepath = os.path.join(SIProotpath,'sip.xml')
                    altRecordID_dict = {}
                    
                    if ArchivePolicy_obj.Mode == 2:
                        ############################################
                        # Get PolicyId / ProjectGroupCode from AIS
                        self.extOBJdbget,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'GET3',('ProjectGroupCode',
                                                                                                           'ObjectPackageName',
                                                                                                           'ObjectGuid',
                                                                                                           'ObjectActive',
                                                                                                           'EntryDate',
                                                                                                           'EntryAgentIdentifierValue',
                                                                                                           'OAISPackageType',
                                                                                                           'preservationLevelValue',
                                                                                                           'ProjectName'),
                                                                                                          ('ObjectIdentifierValue',self.ObjectIdentifierValue))

                        if self.extOBJdbget and ext_errno == 0:
                            altRecordID_dict['POLICYID'] = self.extOBJdbget[0][0]
                            try:
                                altRecordID_dict['PROJECTNAME'] = self.extOBJdbget[0][8].decode('utf-8')
                            except UnicodeDecodeError:
                                altRecordID_dict['PROJECTNAME'] = self.extOBJdbget[0][8].decode('unicode-escape')
                        else:
                            logging.error('Problem to get ProjectGroupCode from AIS, ObjectIdentifierValue: %s, why: %s' % (self.ObjectIdentifierValue, ext_why))
                            self.ok = 0
                    else:
                        altRecordID_dict['POLICYID'] = 10
                        altRecordID_dict['PROJECTNAME'] = 'xyz12345'
                        logging.info('ESSArch is not in AIS mode setting PolicyId = 10.')

                    ############################################
                    # Convert SIP filestructur to eARD
                    if not os.path.isdir(SIPcontentpath):
                        os.mkdir(SIPcontentpath)
                    if not os.path.isdir(SIPmetapath):
                        os.mkdir(SIPmetapath)
                    res,errno,why = ESSMD.getRESObjects(os.path.join(SIProotpath,'TIFFEdit.RES'))
                    if not errno:
                        for f in res:
                            src_f = os.path.join(SIPpath,f[0])
                            if not os.path.exists(src_f):
                                logging.error('missing file: %s' % src_f)
                                self.ok = 0
                    else:
                        logging.warning('missing RESfile: %s' % os.path.join(SIProotpath,'TIFFEdit.RES'))

                    if self.ok:
                        for f in res:
                            src_f = os.path.join(SIPpath,f[0])
                            try:
                                shutil.move(src_f,SIPcontentpath)
                            except (IOError,os.error,shutil.Error), why:
                                logging.error('Problem to move %s to %s, ObjectIdentifierValue: %s, why: %s' % (src_f,SIPcontentpath,self.ObjectIdentifierValue, why))
                                self.ok = 0
                     
                    if self.ok:
                        try:
                            shutil.move(os.path.join(SIProotpath,'TIFFEdit.RES'),SIPcontentpath)
                        except (IOError,os.error,shutil.Error), why:
                            logging.error('Problem to move %s to %s, ObjectIdentifierValue: %s, why: %s' % (os.path.join(SIProotpath,'TIFFEdit.RES'),SIPcontentpath,self.ObjectIdentifierValue, why))
                            self.ok = 0

                    if self.ok:
                        ############################################
                        # Create PREMIS/mix from RESfile
                        res,errno,why = ESSMD.RES2PREMIS(SIProotpath,AgentIdentifierValue,Premis_filepath, eARD=True)
                        if errno == 10:
                            event_info = 'Failed to parse RESfile, error.num: %s error.det: %s' % (str(errno),str(why))
                            logging.error(event_info)
                        elif errno == 20:
                            event_info = 'I/O error to access RESfile, error.num: %s error.det: %s' % (str(errno),str(why))
                            logging.error(event_info)
                        elif errno == 30:
                            event_info = 'Validation errors for PREMIS file, error.num: %s error.det: %s' % (str(errno),str(why))
                            logging.error(event_info)
                        elif errno == 40:
                            event_info = 'Problem to write PREMIS file, error.num: %s error.det: %s' % (str(errno),str(why))
                            logging.error(event_info)
                        if errno > 1:
                            event_info = 'Problem to create PREMIS/mix for ObjectIdentifierValue: %s, error.num: %s  error.desc: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                            logging.error(event_info)
                            ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPReceiver',ProcVersion,'1',event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                            self.ok = 0
                        elif errno == 1:
                            event_info = 'Warning in convert RES to PREMIS for objectIdentifierValue: %s, error.num: %s  warning.desc: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                            logging.warning(event_info)
                            ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPReceiver',ProcVersion,'0',event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                        else:
                            ESSPGM.Events().create('1022','RES2PREMIS','ESSArch SIPReceiver',ProcVersion,'0','',ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                            errno,why = ESSMD.validate(FILENAME=Premis_filepath)
                            if errno:
                                logging.error('Problem to validate PREMIS/mix for ObjectIdentifierValue: %s, why: %s' % (self.ObjectIdentifierValue, why))
                                self.ok = 0
                    if self.ok:
                        ############################################
                        # Create eARD METS sip.xml from PREMISfile
                        errno,why = ESSMD.PREMIS2METS(SIProotpath,self.ObjectIdentifierValue,AgentIdentifierValue,altRecordID_dict,Mets_filepath)
                        if errno:
                            logging.error('Problem to convert PREMIS to METS for ObjectIdentifierValue: %s, why: %s, errno: %s' % (self.ObjectIdentifierValue, why, errno))
                            self.ok = 0
                        errno,why = ESSMD.validate(FILENAME=Mets_filepath)
                        if errno:
                            logging.error('Problem to validate METS for ObjectIdentifierValue: %s, why: %s' % (self.ObjectIdentifierValue, why))
                            self.ok = 0

                    if self.ok:
                        ############################################
                        # Clean SIP from "junk" files
                        errno,why = ESSPGM.Check().CleanRES_SIP(SIProotpath)
                        if errno:
                            event_info = 'Problem to clean RES SIP from "junk files" for SIP package: %s, error.num: %s  error.desc: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                            logging.error(event_info)
                            self.ok = 0
                    
                    if self.ok:
                        ############################################
                        self.StatusProcess = 5
                        self.StatusActivity = 0
                        logging.info('Success to convert object %s to METS SIP and is now ready to ingest.' % self.ObjectIdentifierValue)
                    else:
                        ############################################
                        self.StatusProcess = 0
                        self.StatusActivity = 4
                        self.event_info = 'Problem to create METS SIP for object: %s' % self.ObjectIdentifierValue
                        logging.error(self.event_info)
                        ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                elif self.objectstatus == 100:
                    logging.info('The object %s is already archived.' % self.ObjectIdentifierValue)
                elif self.objectstatus == 99:
                    self.StatusProcess = 0
                    self.StatusActivity = 4
                    self.event_info = 'Problem to access object: %s, errorcode: %s, error: %s' % (SIProotpath,str(self.filetree_errno),self.filetree_why)
                    logging.error(self.event_info)
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)

                if self.objectstatus in range(1,100):
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    if self.dbget:
                        ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue = self.ObjectIdentifierValue)
                        ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()
                    else:
                        ArchiveObject_obj = ArchiveObject()
                        ArchiveObject_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                        ArchiveObject_obj.ObjectUUID = 'ffff%s' % uuid.uuid4().hex
                        ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.OAISPackageType = 0
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()
                    if self.ext_IngestTable:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('DataObjectSize',self.DataObjectSize,
                                                                                                 'StatusProcess',self.StatusProcess,
                                                                                                 'StatusActivity',self.StatusActivity,
                                                                                                 'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if ext_errno: logging.error('Failed to update External DB: %s error: %s' % (self.ObjectIdentifierValue,str(ext_why)))
                        else:
                            ArchiveObject_obj.ExtDBdatetime = self.timestamp_utc
                            ArchiveObject_obj.save()

    def Check_IngestPath_for_updates(self, dir_list, ArchivePolicy_obj):
        #########################################################
        # ArchivePolicy_obj.IngestMetadata == 1 or ArchivePolicy_obj.IngestMetadata == 4: # METS SIP
        for self.fileitem in dir_list:
            self.objectstatus = 0
            self.SIPsize = 0
            self.POLICYID = 0
            self.DELIVERYTYPE = None
            self.DELIVERYSPECIFICATION = None
            self.SUBMISSIONAGREEMENT = None
            self.INFORMATIONCLASS = 0
            self.DataObjectSize = 0
            self.dbget = None

            self.path = os.path.join(ArchivePolicy_obj.IngestPath,self.fileitem)
            try:
                if os.path.exists(self.path):
                    self.mode = os.stat(self.path)
                else:
                    logging.warning('Filepath: %s do not exists, continue with next' % self.path)
                    continue
            except OSError:
                exitstatus = sys.exc_info()[1][0]
                why = sys.exc_info()[1][1]
                logging.warning('Problem to get stat for filepath: %s, exitstatus: %s, error: %s, continue with next' % (self.path,exitstatus,why))
                continue
            #self.mode = os.stat(self.path)
            if stat.S_ISREG(self.mode[0]):
                #############################################################################
                # It's a file
                #############################################################################
                if self.fileitem[-17:] == '_Package_METS.xml':
                    ###############################################################
                    # Try to access ingestpath
                    ###############################################################
                    self.ObjectIdentifierValue = self.fileitem[:-17]
                    self.SIPinfo,errno,error_list = Functions().GetSIPinfo_container(ArchivePolicy_obj.IngestPath,self.fileitem)

                    self.dbget = ESSDB.DB().action(self.IngestTable,'GET',('DataObjectSize','StatusActivity','StatusProcess'),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    self.newobject = 1
                    if self.dbget:
                        if int(self.dbget[0][2]) > 9:
                            ###############################################################
                            # The object %s is already archived
                            ###############################################################
                            self.objectstatus = 100
                            self.newobject = 0
                            logging.debug('The object %s is already archived.' % self.ObjectIdentifierValue)
                            continue

                    if not errno and not self.objectstatus == 100:
                        self.ObjectIdentifierValue = self.SIPinfo[3][0][1]
                        if self.SIPinfo[0][1] is not None:
                            self.SIPsize += int(self.SIPinfo[0][1])
                        if self.SIPinfo[1][1] is not None:
                            self.SIPsize += int(self.SIPinfo[1][1])
                        if self.newobject and self.dbget and int(self.dbget[0][2]) in range(0,9) and int(self.dbget[0][1]) in range(0,3):
                            ###############################################################
                            # An already discovered object found, checking if stable
                            ###############################################################
                            if self.dbget[0][0] == self.SIPsize:
                                ###############################################################
                                # object is stable
                                ###############################################################
                                self.SIP_OK = 1
                                #######################################
                                # Verify package checksum and size
                                if self.SIP_OK:
                                    errno,error_list = Functions().VerifySIPchecksum(ArchivePolicy_obj.IngestPath,self.SIPinfo[1])
                                    if not errno:
                                        logging.info('Success to verify package checksum and size for object: %s' % self.ObjectIdentifierValue)
                                    else:
                                        logging.error('Problem to verify package checksum and size for object: %s, Errno: %s, error_list: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list)))
                                        self.SIP_OK = 0
                                #######################################
                                # Extract package
                                if self.SIP_OK:
                                    errno,error_list = Functions().ExtractSIP(ArchivePolicy_obj.IngestPath,self.SIPinfo[1])
                                    if not errno:
                                        logging.info('Success to extract object: %s' % self.ObjectIdentifierValue)
                                    else:
                                        logging.error('Problem to extract object: %s, Errno: %s, error_list: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list)))
                                        self.SIP_OK = 0
                                #######################################
                                # Get SIP information after Extract
                                if self.SIP_OK:
                                    self.SIPinfo,errno,error_list = Functions().GetSIPinfo_container(ArchivePolicy_obj.IngestPath,self.fileitem)
                                    if not errno:
                                        logging.info('Success to get SIP information after extract for object: %s' % self.ObjectIdentifierValue)
                                        self.POLICYID = self.SIPinfo[2]['POLICYID']
                                        try:
                                            ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = self.POLICYID)
                                        except ArchivePolicy.DoesNotExist, why:
                                            logging.error('Problem to get ArchivePolicy for object: %s, error: %s' % (self.ObjectIdentifierValue, why)) 
                                            ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = 0) 
                                            self.objectstatus = 99  
                                        if 'DELIVERYTYPE' in self.SIPinfo[2].keys():
                                            self.DELIVERYTYPE = self.SIPinfo[2]['DELIVERYTYPE']
                                        if 'DELIVERYSPECIFICATION' in self.SIPinfo[2].keys():
                                            self.DELIVERYSPECIFICATION = self.SIPinfo[2]['DELIVERYSPECIFICATION']
                                        if 'SUBMISSIONAGREEMENT' in self.SIPinfo[2].keys():
                                            self.SUBMISSIONAGREEMENT = self.SIPinfo[2]['SUBMISSIONAGREEMENT']
                                        if 'INFORMATIONCLASS' in self.SIPinfo[2].keys():
                                            self.INFORMATIONCLASS = self.SIPinfo[2]['INFORMATIONCLASS']
                                    else:
                                        logging.error('Problem to get SIP information after extract for object: %s, Errno: %s, error_list: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list)))
                                        self.SIP_OK = 0
                                #######################################
                                # Verify Content_METS checksum and size
                                if self.SIP_OK:
                                    errno,error_list = Functions().VerifySIPchecksum(ArchivePolicy_obj.IngestPath,self.SIPinfo[0])
                                    if not errno:
                                        logging.info('Success to verify Content_METS checksum and size for object: %s' % self.ObjectIdentifierValue)
                                        self.objectstatus = 3
                                    else:
                                        logging.error('Problem to verify Content_METS checksum and size for object: %s, Errno: %s, error_list: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list)))
                                        self.objectstatus = 99
                            else:
                                ###############################################################
                                # directory is still growing
                                ###############################################################
                                self.objectstatus = 2
                        elif self.newobject and not self.dbget:
                            ###############################################################
                            # A new directory discovered
                            ###############################################################
                            self.objectstatus = 1
                    elif errno and not self.objectstatus == 100:
                        ###############################################################
                        # Problem to access object
                        ###############################################################
                        self.objectstatus = 99
                if self.objectstatus == 0:
                    pass
                elif self.objectstatus == 1:
                    #maste kolla mot arkiv tabellen om objektet redan ar skrivit till band
                    self.StatusProcess = 0
                    self.StatusActivity = 1
                    logging.info('Object %s do not exist in DB or receive, Insert object to DB' % self.ObjectIdentifierValue)
                elif self.objectstatus == 2:
                    self.StatusProcess = 0
                    self.StatusActivity = 2
                    logging.info('Object %s, %s is receive, update DB with new size.' % (self.ObjectIdentifierValue,self.SIPsize))
                elif self.objectstatus == 3:
                    self.StatusProcess = 9
                    self.StatusActivity = 0
                    logging.info('Object %s, %s is stable, moving to next step.' % (self.ObjectIdentifierValue,self.SIPsize))
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'0','',ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                elif self.objectstatus == 100:
                    logging.info('The object %s is already archived.' % self.ObjectIdentifierValue)
                elif self.objectstatus == 99:
                    self.StatusProcess = 0
                    self.StatusActivity = 4
                    self.event_info = 'Problem to access object: %s, errorcode: %s, error: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list))
                    logging.error(self.event_info)
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)

                if self.objectstatus in range(1,100):
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    if self.dbget:
                        ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue = self.ObjectIdentifierValue)
                        ArchiveObject_obj.PolicyId = ArchivePolicy_obj
                        ArchiveObject_obj.DELIVERYTYPE = self.DELIVERYTYPE
                        ArchiveObject_obj.INFORMATIONCLASS = self.INFORMATIONCLASS
                        ArchiveObject_obj.DataObjectSize = self.SIPsize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()

                    else:
                        ArchiveObject_obj = ArchiveObject()
                        ArchiveObject_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                        ArchiveObject_obj.ObjectUUID = 'ffff%s' % uuid.uuid4().hex
                        ArchiveObject_obj.PolicyId = ArchivePolicy_obj
                        ArchiveObject_obj.DELIVERYTYPE = self.DELIVERYTYPE
                        ArchiveObject_obj.INFORMATIONCLASS = self.INFORMATIONCLASS
                        ArchiveObject_obj.DataObjectSize = self.SIPsize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()

                    if self.ext_IngestTable: 
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('PolicyID',self.POLICYID,
                                                                                                 'DELIVERYTYPE',self.DELIVERYTYPE,
                                                                                                 'INFORMATIONCLASS',self.INFORMATIONCLASS,
                                                                                                 'DataObjectSize',self.SIPsize,
                                                                                                 'StatusProcess',self.StatusProcess,
                                                                                                 'StatusActivity',self.StatusActivity,
                                                                                                 'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if ext_errno: logging.error('Failed to update External DB: %s error: %s' % (self.ObjectIdentifierValue,str(ext_why)))
                        else:
                            ArchiveObject_obj.ExtDBdatetime = self.timestamp_utc
                            ArchiveObject_obj.save()
            
            elif stat.S_ISDIR(self.mode[0]): 
                #############################################################################
                # It's a directory
                #############################################################################
                self.sipmetspath = None
                logging.debug('self.path:%s' % self.path)
                if os.path.exists(os.path.join(self.path,'sip.xml')):
                    self.sipmetspath = os.path.join(self.path,'sip.xml')
                elif os.path.exists(os.path.join(self.path,'mets.xml')):
                    self.sipmetspath = os.path.join(self.path,'mets.xml')
                #elif os.path.exists(os.path.join(self.path,'%s_Content_METS.xml' % self.fileitem)):
                #    self.sipmetspath = os.path.join(self.path,'%s_Content_METS.xml' % self.fileitem)
                
                if self.sipmetspath:
                    logging.debug('self.sipmetspath:%s' % self.sipmetspath)
                    ###############################################################
                    # Try to access ingestpath
                    ###############################################################
                    self.ObjectIdentifierValue = self.fileitem

                    self.dbget = ESSDB.DB().action(self.IngestTable,'GET',('DataObjectSize','StatusActivity','StatusProcess'),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    logging.debug('self.dbget:%s' % str(self.dbget))
                    errno = 0
                    self.newobject = 1
                    if self.dbget:
                        if int(self.dbget[0][2]) > 9:
                            ###############################################################
                            # The object %s is already archived
                            ###############################################################
                            self.objectstatus = 100
                            self.newobject = 0
                            logging.debug('The object %s is already archived.' % self.ObjectIdentifierValue)
                            continue
                        elif int(self.dbget[0][1]) in [4]:
                            ###############################################################
                            # The object %s need manual assistance, continue with next object
                            ###############################################################
                            logging.warning('The object %s need manual assistance, continue with next object.' % self.ObjectIdentifierValue)
                            continue
                    
                    if not errno and not self.objectstatus == 100:
                        self.SIPinfo,errno,error_list = Functions().GetSIPinfo(self.path,os.path.split(self.sipmetspath)[1])
                        if errno and not self.objectstatus == 100:
                            ###############################################################
                            # Problem to access object
                            logging.error('Problem to get information from sip.xml, self.SIPinfo:%s' % (str(self.SIPinfo)))
                            self.objectstatus = 99
                    if not errno and not self.objectstatus == 100:
                        self.DataObjectSize, self.numfiles, self.file_list, errno, error_list = Functions().GetFiletreeSum(self.path)
                        if errno and not self.objectstatus == 100:
                            ###############################################################
                            # Problem to access object
                            logging.error('Problem to get SIPinformation from filesystem, self.DataObjectSize:%s,self.numfiles:%s,self.file_list:%s' % (self.DataObjectSize, self.numfiles, str(self.file_list)))
                            self.objectstatus = 99
                    if not errno and not self.objectstatus == 100:
                        if self.SIPinfo[3][0][1][:5] == 'UUID:' or self.SIPinfo[3][0][1][:5] == 'RAID:':
                            mets_ObjectIdentifierValue = self.SIPinfo[3][0][1][5:]
                        else:
                            mets_ObjectIdentifierValue = self.SIPinfo[3][0][1]
                            
                        # Check if self.ObjectIdentifierValue and mets_ObjectIdentifierValue match
                        if not self.ObjectIdentifierValue ==  mets_ObjectIdentifierValue:
                            event_info = 'Directory name "ObjectIdentifierValue" %s does not match METS "ObjectIdentifierValue" %s' % (self.ObjectIdentifierValue, mets_ObjectIdentifierValue)
                            error_list.append(event_info)
                            logger.error(event_info)
                            self.objectstatus = 99
                            
                        logging.debug('self.ObjectIdentifierValue:%s' % self.ObjectIdentifierValue)
                        self.SIPsize = self.SIPinfo[2]
                        logging.debug('self.SIPsize:%s' % self.SIPsize)
                        self.POLICYID = self.SIPinfo[1]['POLICYID']
                        try:
                            ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = self.POLICYID)
                        except ArchivePolicy.DoesNotExist, why:
                            logging.error('Problem to get ArchivePolicy for object: %s, error: %s' % (self.ObjectIdentifierValue, why))
                            ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = 0) 
                            self.objectstatus = 99  
                        logging.debug('self.POLICYID:%s' % self.POLICYID)
                        if 'DELIVERYTYPE' in self.SIPinfo[1].keys():
                            self.DELIVERYTYPE = self.SIPinfo[1]['DELIVERYTYPE']
                        if 'DELIVERYSPECIFICATION' in self.SIPinfo[1].keys():
                            self.DELIVERYSPECIFICATION = self.SIPinfo[1]['DELIVERYSPECIFICATION']
                        if 'SUBMISSIONAGREEMENT' in self.SIPinfo[1].keys():
                            self.SUBMISSIONAGREEMENT = self.SIPinfo[1]['SUBMISSIONAGREEMENT']
                        if 'INFORMATIONCLASS' in self.SIPinfo[1].keys():
                            self.INFORMATIONCLASS = self.SIPinfo[1]['INFORMATIONCLASS']

                        if self.newobject and self.dbget and int(self.dbget[0][2]) in range(0,9) and int(self.dbget[0][1]) in range(0,3):
                            ###############################################################
                            # An already discovered object found, checking if stable
                            ###############################################################
                            if self.dbget[0][0] == self.DataObjectSize:
                                ###############################################################
                                # object is stable
                                ###############################################################
                                if self.SIPsize == self.DataObjectSize:
                                    ###############################################################
                                    # Check if totalsize for files in filelist in METS == actual size in filesystem
                                    ###############################################################
                                    self.objectstatus = 3
                                else:
                                    self.objectstatus = 98
                            else:
                                ###############################################################
                                # directory is still growing
                                ###############################################################
                                self.objectstatus = 2
                        elif self.newobject and not self.dbget:
                            ###############################################################
                            # A new directory discovered
                            ###############################################################
                            self.objectstatus = 1
                    elif errno and not self.objectstatus == 100:
                        ###############################################################
                        # Problem to access object
                        ###############################################################
                        self.objectstatus = 99
                elif os.path.split(self.path)[1] == 'user':
                    IngestQueue_objs = IngestQueue.objects.filter( Status=0 ).all()
                    if IngestQueue_objs:
                        for IngestQueue_obj in IngestQueue_objs:
                            user_Req = IngestQueue_obj.user
                            ObjectIdentifierValue_Req = IngestQueue_obj.ObjectIdentifierValue
                            src_name = '%s/%s/%s' % (self.path,user_Req,ObjectIdentifierValue_Req)
                            trg_name = os.path.split(self.path)[0]
                            try:
                                shutil.move(src_name,trg_name)
                            except (IOError,os.error,shutil.Error), why:
                                logging.error('Problem to move %s to %s, ObjectIdentifierValue: %s, why: %s' % (src_name,trg_name,ObjectIdentifierValue_Req, why))
                            else:
                                logging.info('Success to move %s to %s, ObjectIdentifierValue: %s' % (src_name,trg_name,ObjectIdentifierValue_Req))
                                IngestQueue_obj.Status = 2
                                #model.meta.Session.commit()
                                IngestQueue_obj.save()
                if self.objectstatus == 0:
                    pass
                elif self.objectstatus == 1:
                    #maste kolla mot arkiv tabellen om objektet redan ar skrivit till band
                    self.StatusProcess = 0
                    self.StatusActivity = 1
                    logging.info('Object %s do not exist in DB or receive, Insert object to DB' % self.ObjectIdentifierValue)
                elif self.objectstatus == 2:
                    self.StatusProcess = 0
                    self.StatusActivity = 2
                    logging.info('Object %s, %s is receive, update DB with new size.' % (self.ObjectIdentifierValue,self.SIPsize))
                elif self.objectstatus == 3:
                    self.StatusProcess = 9
                    self.StatusActivity = 0
                    logging.info('Object %s, %s is stable, moving to next step.' % (self.ObjectIdentifierValue,self.SIPsize))
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'0','',ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                elif self.objectstatus == 100:
                    logging.warning('The object %s is already archived.' % self.ObjectIdentifierValue)
                elif self.objectstatus == 98:
                    self.StatusProcess = 0
                    self.StatusActivity = 4
                    self.event_info = 'Filesize in METS is not equal to tha actual filesize. Totalsize in METS:%s, filesystem:%s' % (str(self.SIPsize),str(self.DataObjectSize))
                    logging.error(self.event_info)
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
                elif self.objectstatus == 99:
                    self.StatusProcess = 0
                    self.StatusActivity = 4
                    self.event_info = 'Problem to access object: %s, errorcode: %s, error: %s' % (self.ObjectIdentifierValue,str(errno),str(error_list))
                    logging.error(self.event_info)
                    ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)

                if self.objectstatus in range(1,100):
                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                    if self.dbget:
                        ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue = self.ObjectIdentifierValue)
                        ArchiveObject_obj.PolicyId = ArchivePolicy_obj
                        ArchiveObject_obj.DELIVERYTYPE = self.DELIVERYTYPE
                        ArchiveObject_obj.INFORMATIONCLASS = self.INFORMATIONCLASS
                        ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()

                    else:
                        ArchiveObject_obj = ArchiveObject()
                        ArchiveObject_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                        ArchiveObject_obj.ObjectUUID = 'ffff%s' % uuid.uuid4().hex
                        ArchiveObject_obj.PolicyId = ArchivePolicy_obj
                        ArchiveObject_obj.DELIVERYTYPE = self.DELIVERYTYPE
                        ArchiveObject_obj.INFORMATIONCLASS = self.INFORMATIONCLASS
                        ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                        ArchiveObject_obj.StatusProcess = self.StatusProcess
                        ArchiveObject_obj.StatusActivity = self.StatusActivity
                        ArchiveObject_obj.LastEventDate = self.timestamp_utc
                        ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                        ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save()

                    if self.ext_IngestTable:
                        ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('PolicyID',self.POLICYID,
                                                                                                 'DELIVERYTYPE',self.DELIVERYTYPE,
                                                                                                 'INFORMATIONCLASS',self.INFORMATIONCLASS,
                                                                                                 'DataObjectSize',self.DataObjectSize,
                                                                                                 'StatusProcess',self.StatusProcess,
                                                                                                 'StatusActivity',self.StatusActivity,
                                                                                                 'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                        if ext_errno: logging.error('Failed to update External DB: %s error: %s' % (self.ObjectIdentifierValue,str(ext_why)))
                        else:
                            ArchiveObject_obj.ExtDBdatetime = self.timestamp_utc
                            ArchiveObject_obj.save()

    def Check_IngestPath_for_updates_PREMIS(self, dir_list, ArchivePolicy_obj):
        #########################################################
        # IngestMetadata 3 = PREMIS/ADDML SIP        
        for self.ObjectIdentifierValue in dir_list:
            self.objectstatus = 0
            self.DataObjectSize = 0
            self.numfiles = 0
            self.dbget = None
            # Fix to filter out eveyrything except dirs with lengt of 8 or 9
            if len(self.ObjectIdentifierValue) in range(8,10):
                self.path = os.path.join(ArchivePolicy_obj.IngestPath,self.ObjectIdentifierValue)
                ###############################################################
                # Try to access ingestpath
                ###############################################################
                self.DataObjectSize, self.numfiles, self.file_list, self.filetree_errno, self.filetree_why = Functions().GetFiletreeSum(self.path) 

                self.dbget = ESSDB.DB().action(self.IngestTable,'GET',('DataObjectSize','StatusActivity','StatusProcess'),('ObjectIdentifierValue',self.ObjectIdentifierValue))
                self.newobject = 1
                if self.dbget:
                    if int(self.dbget[0][2]) == 5:
                        logging.info('The object %s is ready to remodel.' % self.ObjectIdentifierValue)
                    elif int(self.dbget[0][2]) > 9:
                        ###############################################################
                        # The object %s is already archived
                        ###############################################################
                        self.objectstatus = 100
                        self.newobject = 0

                if not self.filetree_errno:
                    if self.newobject and self.dbget and int(self.dbget[0][2]) in range(0,9) and int(self.dbget[0][1]) in range(0,3):
                        ###############################################################
                        # An already discovered directory found, checking if stable
                        ###############################################################
                        if self.dbget[0][0] == self.DataObjectSize:
                            ###############################################################
                            # directory is stable
                            ###############################################################
                            self.objectstatus = 3
                        else:
                            ###############################################################
                            # directory is still growing
                            ###############################################################
                            self.objectstatus = 2
                    elif self.newobject and not self.dbget:
                        ###############################################################
                        # A new directory discovered
                        ###############################################################
                        self.objectstatus = 1
                elif self.filetree_errno and not self.objectstatus == 100:
                    ###############################################################
                    # Problem to access object
                    ###############################################################
                    self.objectstatus = 99

            if self.objectstatus == 0:
                pass
            elif self.objectstatus == 1:
                #maste kolla mot arkiv tabellen om objektet redan ar skrivit till band
                self.StatusProcess = 0
                self.StatusActivity = 1
                logging.info('Object %s do not exist in DB or receive, Insert object to DB' % self.ObjectIdentifierValue)
            elif self.objectstatus == 2:
                self.StatusProcess = 0
                self.StatusActivity = 2
                logging.info('Object %s, %s is receive, update DB with new size.' % (self.ObjectIdentifierValue,self.DataObjectSize))
            elif self.objectstatus == 3:
                self.StatusProcess = 9
                self.StatusActivity = 0
                logging.info('Object %s, %s is stable, moving to next step.' % (self.ObjectIdentifierValue,self.DataObjectSize))
                ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'0','',ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)
            elif self.objectstatus == 100:
                logging.info('The object %s is already archived.' % self.ObjectIdentifierValue)
            elif self.objectstatus == 99:
                self.StatusProcess = 0
                self.StatusActivity = 4
                self.event_info = 'Problem to access object: %s, errorcode: %s, error: %s' % (self.path,str(self.filetree_errno),self.filetree_why)
                logging.error(self.event_info)
                ESSPGM.Events().create('1000','','ESSArch SIPReceiver',ProcVersion,'1',self.event_info,ArchivePolicy_obj.Mode,self.ObjectIdentifierValue)

            if self.objectstatus in range(1,100):
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                if self.dbget:
                    ArchiveObject_obj = ArchiveObject.objects.get(ObjectIdentifierValue = self.ObjectIdentifierValue)
                    ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                    ArchiveObject_obj.StatusProcess = self.StatusProcess
                    ArchiveObject_obj.StatusActivity = self.StatusActivity
                    ArchiveObject_obj.LastEventDate = self.timestamp_utc
                    ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                    ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                    ArchiveObject_obj.save()

                else:
                    ArchiveObject_obj = ArchiveObject()
                    ArchiveObject_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
                    ArchiveObject_obj.ObjectUUID = 'ffff%s' % uuid.uuid4().hex
                    ArchiveObject_obj.DataObjectSize = self.DataObjectSize
                    ArchiveObject_obj.StatusProcess = self.StatusProcess
                    ArchiveObject_obj.StatusActivity = self.StatusActivity
                    ArchiveObject_obj.LastEventDate = self.timestamp_utc
                    ArchiveObject_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                    ArchiveObject_obj.LocalDBdatetime = self.timestamp_utc
                    ArchiveObject_obj.save()

                if self.ext_IngestTable:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.IngestTable,'UPD',('DataObjectSize',self.DataObjectSize,
                                                                                             'StatusProcess',self.StatusProcess,
                                                                                             'StatusActivity',self.StatusActivity,
                                                                                             'LastEventDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                             'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                            ('ObjectIdentifierValue',self.ObjectIdentifierValue))
                    if ext_errno: logging.error('Failed to update External DB: %s error: %s' % (self.ObjectIdentifierValue,str(ext_why)))
                    else:
                        ArchiveObject_obj.ExtDBdatetime = self.timestamp_utc
                        ArchiveObject_obj.save() 

class Functions:
    "Get filetree"
    ###############################################
    def GetFiletree(self,path):
        self.file_list = []
        self.exitstatus = 0
        self.why = None
        try:
            if os.path.exists(path):
                if os.access(path, os.R_OK) and os.access(path, os.W_OK) and os.access(path, os.X_OK):
                    for self.f in os.listdir(path):
                        self.path = os.path.join(path,self.f)
                        if os.access(self.path, os.R_OK):
                            self.mode = os.stat(self.path)
                            if stat.S_ISREG(self.mode[0]):                   # It's a file
                                self.file_list.append([self.f, os.stat(self.path)])
                            elif stat.S_ISDIR(self.mode[0]):                 # It's a directory
                                self.dir_file_list, errno, why = Functions().GetFiletree(self.path)
                                if not errno:
                                    for self.df in self.dir_file_list:
                                        self.file_list.append([self.f + '/' + self.df[0], self.df[1]])
                                else:
                                    return self.file_list, errno, why
                        else:
                            self.exitstatus = 12
                            self.why = 'Permision problem for path: %s' % self.path
                else:
                    self.exitstatus = 11
                    self.why = 'Permision problem for path: %s' % path
            else:
                self.exitstatus = 13
                self.why = 'No such file or directory: %s' % path
        except OSError:
            self.exitstatus = sys.exc_info()[1][0]
            self.why = sys.exc_info()[1][1] + ': ' + path
        return self.file_list, self.exitstatus, self.why

    "Get FiletreeSum"
    ###############################################
    def GetFiletreeSum(self,path):
        self.file_list, errno, why = Functions().GetFiletree(path)
        if not errno:
            tot_size = 0
            tot_number = 0
            for f in self.file_list:
                tot_size += f[1].st_size
                tot_number += 1
            return tot_size, tot_number, self.file_list , 0 , None
        else:
            return 0, 0, [], errno, why

    "Get SIP Information (container type)"
    ###############################################
    def GetSIPinfo_container(self,path,METSfile):
        error_list = []
        METSfilepath = os.path.join(path,METSfile)
        res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=METSfilepath)
        if not error:
            self.SIP_OK = 1
            self.PackageFile = None
            self.ContentFile = None
            self.altRecordID_dict = {}

            if not res_info[0][3] == 'SIP':
                error_list.append('METS TYPE is not "SIP"')
                self.SIP_OK = 0
            
            if not len(res_files) == 2:
                error_list.append('METS file must contain two files ("xxx_Content_METS.xml" and "xxx.tar")')
                self.SIP_OK = 0

            if self.SIP_OK:
                self.altRecordID_dict = dict(res_info[3])
                ################################################
                # Check for POLICYID
                if 'POLICYID' in self.altRecordID_dict.keys():
                    try:
                        self.altRecordID_dict['POLICYID'] = int(self.altRecordID_dict['POLICYID'])
                    except:
                        self.altRecordID_dict['POLICYID'] = None
                else:
                    self.altRecordID_dict['POLICYID'] = None

            if self.SIP_OK:
                if 'POLICYID' in self.altRecordID_dict.keys():
                    if self.altRecordID_dict['POLICYID'] is None:
                        for agent in res_info[2]:
                            if agent[0] == 'PRESERVATION' and \
                               agent[2] == 'OTHER' and \
                               agent[3] == 'SOFTWARE' and \
                               agent[4] == 'ESSArch':
                                note = csv.reader(agent[5], delimiter='=')
                                for i in note:
                                    if i[0] == 'POLICYID':
                                        try:
                                            self.altRecordID_dict['POLICYID'] = int(i[1])
                                        except:
                                            self.altRecordID_dict['POLICYID'] = None
                        if self.altRecordID_dict['POLICYID'] is None:
                            error_list.append('METS ESSArch agent with POLICYID is missing')
                            self.SIP_OK = 0

            if self.SIP_OK:
                if 'POLICYID' in self.altRecordID_dict.keys():
                    if self.altRecordID_dict['POLICYID'] is None:
                        error_list.append('POLICYID is missing in METS')
                        self.SIP_OK = 0
                else:
                    error_list.append('POLICYID is missing in METS')
                    self.SIP_OK = 0

            if self.SIP_OK:
                for self.file in res_files:
                    if self.file[0] == 'amdSec' and \
                       self.file[2] == 'techMD' and \
                       self.file[13] == 'text/xml' and \
                       self.file[15] == 'OTHER' and \
                       self.file[16] == 'METS':
                        if self.file[8][:5] == 'file:':
                            try:
                                self.C_size = os.stat(os.path.join(path,self.file[8][5:])).st_size
                            except:
                                self.C_size = None
                            self.ContentFile = [self.file[8][5:],self.C_size,self.file]
                    elif self.file[0] == 'fileSec' and \
                       self.file[2] == 'fileGrp' and \
                       self.file[13] == 'application/x-tar' and \
                       self.file[15] == 'PACKAGE':
                        if self.file[8][:5] == 'file:':
                            try:
                                self.P_size = os.stat(os.path.join(path,self.file[8][5:])).st_size
                            except:
                                self.P_size = None
                            self.PackageFile = [self.file[8][5:],self.P_size,self.file]
                if not self.PackageFile:
                    error_list.append('PackageFile not found in METS')
                    self.SIP_OK = 0
                if not self.ContentFile:
                    error_list.append('ContentFile not found in METS')
                    self.SIP_OK = 0

            if self.SIP_OK:
                return [self.ContentFile,self.PackageFile,self.altRecordID_dict,res_info],0,error_list
            else:
                return [self.ContentFile,self.PackageFile,self.altRecordID_dict,res_info],1,error_list
        else:
            error_list.append(why)
            return None,2,error_list

    "Get SIP Information"
    ###############################################
    def GetSIPinfo(self,path,METSfile):
        error_list = []
        METSfilepath = os.path.join(path,METSfile)
        res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=METSfilepath)
        if not error:
            self.SIP_OK = 1
            self.ContentFile = None
            self.altRecordID_dict = {}
            self.SIPsize = 0 
            if not res_info[0][3] == 'SIP':
                error_list.append('METS TYPE is not "SIP"')
                self.SIP_OK = 0
            if self.SIP_OK:
                self.altRecordID_dict = dict(res_info[3])
                ################################################
                # Check for POLICYID
                #if 'POLICYID' in self.altRecordID_dict.keys():
                    #self.altRecordID_dict['POLICYID'] = self.altRecordID_dict['POLICYID']
                    #try:
                    #    self.altRecordID_dict['POLICYID'] = int(self.altRecordID_dict['POLICYID']) 
                    #except:
                    #    error_list.append('altRecordID POLICYID is not an int, POLICYID in METS is: %s' % self.altRecordID_dict['POLICYID'])
                    #   self.altRecordID_dict['POLICYID'] = None
                    #    self.SIP_OK = 0
                #else:
                if not 'POLICYID' in self.altRecordID_dict.keys():
                    error_list.append('Missing altRecordID POLICYID in METS')
                    self.altRecordID_dict['POLICYID'] = None
                    self.SIP_OK = 0
                ################################################
                # Check for INFORMATIONCLASS
                if 'INFORMATIONCLASS' in self.altRecordID_dict.keys():
                    try:
                        self.altRecordID_dict['INFORMATIONCLASS'] = int(self.altRecordID_dict['INFORMATIONCLASS'])
                    except:
                        error_list.append('altRecordID INFORMATIONCLASS is not an int, INFORMATIONCLASS in METS is: %s' % self.altRecordID_dict['INFORMATIONCLASS'])
                        self.altRecordID_dict['INFORMATIONCLASS'] = None
                        self.SIP_OK = 0
                else:
                    error_list.append('Missing altRecordID INFORMATIONCLASS in METS')
                    self.altRecordID_dict['INFORMATIONCLASS'] = None
                    self.SIP_OK = 0
                ################################################
                # Check for DELIVERYTYPE
                if not 'DELIVERYTYPE' in self.altRecordID_dict.keys():
                    error_list.append('Missing altRecordID DELIVERYTYPE in METS')
                    self.altRecordID_dict['DELIVERYTYPE'] = None
                    self.SIP_OK = 0
                ################################################
                # Check for DELIVERYSPECIFICATION
                if not 'DELIVERYSPECIFICATION' in self.altRecordID_dict.keys():
                    error_list.append('Missing altRecordID DELIVERYSPECIFICATION in METS')
                    self.altRecordID_dict['DELIVERYSPECIFICATION'] = None
                    self.SIP_OK = 0
                ################################################
                # Check for SUBMISSIONAGREEMENT
                if not 'SUBMISSIONAGREEMENT' in self.altRecordID_dict.keys():
                    error_list.append('Missing altRecordID SUBMISSIONAGREEMENT in METS')
                    self.altRecordID_dict['SUBMISSIONAGREEMENT'] = None
                    self.SIP_OK = 0
            if self.SIP_OK:
                self.C_size = os.stat(METSfilepath).st_size
                self.ContentFile = [self.C_size,None]
                self.SIPsize += self.C_size
            if self.SIP_OK:
                for res_file in res_files: 
                    self.SIPsize += int(res_file[12]) 

            if self.SIP_OK:
                return [self.ContentFile,self.altRecordID_dict,self.SIPsize,res_info],0,error_list
            else:
                return [self.ContentFile,self.altRecordID_dict,self.SIPsize,res_info],1,error_list
        else:
            error_list.append(why)
            return None,2,error_list

    "Verify SIP Checksum"
    ###############################################
    def VerifySIPchecksum(self,path,PackageFile):
        self.PackageFile = PackageFile[0]
        self.PackageFile_path = os.path.join(path,self.PackageFile)
        self.PackageFile_size = PackageFile[1]
        self.PackageFile_m_size = PackageFile[2][12]
        self.PackageFile_m_checksum = PackageFile[2][10]
        self.PackageFile_m_checksumtype = PackageFile[2][11]
        self.SIP_OK = 1
        error_list = []
        ####################################
        # Check PackageFile_size
        if self.PackageFile_size is None:
            error_list.append('Problem to get filesize for %s' % self.PackageFile_path)
            self.SIP_OK = 0
        elif not self.PackageFile_m_size == self.PackageFile_size:
            error_list.append('Filesize mismatch for %s' % self.PackageFile_path)
            self.SIP_OK = 0
        ####################################
        # Check PackageFile_checksum
        if self.SIP_OK:
            self.PackageFile_checksum, errno, why = ESSPGM.Check().checksum(self.PackageFile_path, self.PackageFile_m_checksumtype)
            if not errno:
                if not self.PackageFile_m_checksum == self.PackageFile_checksum:
                    error_list.append('Checksum mismatch for %s' % self.PackageFile_path)
                    self.SIP_OK = 0
            else:
                error_list.append('Problem to get checksum for %s, error: %s, why: %s' % (self.PackageFile_path,str(errno),str(why)))
                self.SIP_OK = 0
        if self.SIP_OK:
            return 0, error_list
        else:
            return 1, error_list

    "Extract SIP"
    ###############################################
    def ExtractSIP(self,path,PackageFile):
        self.PackageFile = PackageFile[0]
        self.PackageFile_path = os.path.join(path,self.PackageFile)
        self.path_iso = ESSPGM.Check().unicode2str(path)
        self.SIP_OK = 1
        error_list = []
        #################################################
        # Extract SIP
        try:
            self.SIP_tarObject = tarfile.open(name=self.PackageFile_path, mode='r')
            self.SIP_tarObject.extractall(path=self.path_iso)
        except (ValueError, OSError, IOError, tarfile.TarError),why:
            error_list.append('Problem to extract %s, why: %s' % (self.PackageFile_path,str(why)))
            self.SIP_OK = 0
        if self.SIP_OK:
            return 0, error_list
        else:
            return 1, error_list

#######################################################################################################
# Dep:
# Table: ESSProc with Name: SIPReceiver, LogFile: /log/xxx.log, Time: 5, Status: 0/1, Run: 0/1
# Table: ESSConfig with Name: IngestPath Value: /tmp/Ingest
# Table: ESSConfig with Name: IngestTable Value: IngestObject
# Arg: -d = Debug on
#######################################################################################################
if __name__ == '__main__':
    ProcName = 'SIPReceiver'
    ProcVersion = __version__
    Debug=0
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
            break
        time.sleep(5)
    logger.info('test3: ' + str(x.RunFlag))
    del x

# ./SIPReceiver.py 

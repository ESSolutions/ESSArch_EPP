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

import hashlib, subprocess, ESSDB,  ESSMSSQL, ESSMD, logging, time, datetime, os, stat, re, tarfile, urllib, uuid, db_sync_ais, csv, smtplib, email.charset, pytz, mimetypes, sys, _mysql_exceptions, MySQLdb
from xml.dom.minidom import Document
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.utils import timezone
#from essarch.models import ArchiveObject, robotQueue, IOqueue, eventIdentifier, storageMedium
from essarch.models import ArchiveObject, eventIdentifier
from configuration.models import Path
from Storage.models import storageMedium
from django import db

Debug = 0

class PROC:
    def action(self,action,Name=None,id=None):
        if not id:
            self.dbget = ESSDB.DB().action('ESSProc','GET',('id',),('Name',Name))
            if self.dbget:
                id = self.dbget[0][0]
        ############### Start ################
        if action == 'Start':
            procrow = ESSDB.DB().action('ESSProc','GET',('Name','Path'),('id',id))[0]
            ESSDB.DB().action('ESSProc','UPD',('alarm',1),('id',id))
            self.ProcName = procrow[0]
            self.ProcPath = procrow[1]
            self.ProcStdOut = open('/ESSArch/log/proc/' + self.ProcName + '.log','a')
            if self.ProcName == 'db_sync_ais' or self.ProcName == 'storageLogistics' or self.ProcName == 'ESSlogging':
                self.cmd = subprocess.Popen(["/ESSArch/pd/python/bin/python",self.ProcPath,"-p","&"], stdout=self.ProcStdOut, stderr=self.ProcStdOut)
            else:
                self.cmd = subprocess.Popen(["/ESSArch/pd/python/bin/python",self.ProcPath,"&"], stdout=self.ProcStdOut, stderr=self.ProcStdOut)
            ESSDB.DB().action('ESSProc','UPD',('Status','1','Run','1','PID',self.cmd.pid),('id',id))
        ############### Stop #################
        if action == 'Stop':
            ESSDB.DB().action('ESSProc','UPD',('Status','2','Run','0','alarm',1),('id',id))
        ############### Kill #################
        if action == 'Kill':
            procrow = ESSDB.DB().action('ESSProc','GET',('PID',),('id',id))[0]
            ESSDB.DB().action('ESSProc','UPD',('alarm',1),('id',id))
            self.ProcPID = procrow[0]
            if (subprocess.call(["ps","-p", str(self.ProcPID)])) == 0:
                self.retcode = subprocess.call(["kill", str(self.ProcPID)])
                if self.retcode == 0:
                    ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('id',id))
            else:
                ESSDB.DB().action('ESSProc','UPD',('Status','0','Run','0','PID','0'),('id',id))

class DB:
    TimeZone = timezone.get_default_timezone_name()
    tz=timezone.get_default_timezone()
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #                format='%(asctime)s %(levelname)-8s %(message)s',
        #                datefmt='%d %b %Y %H:%M:%S',
        #                filename='/tmp/ESSPGM_DB.log')
        pass

    "Update AIP Status"
    ###############################################
    def SetAIPstatus(self, local_table, ext_table, AgentIdentifierValue, ObjectUUID, StatusProcess, StatusActivity):
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        timestamp_dst = timestamp_utc.astimezone(self.tz)
        ArchiveObject_obj = ArchiveObject.objects.get(ObjectUUID=ObjectUUID)
        ArchiveObject_obj.StatusProcess=StatusProcess
        ArchiveObject_obj.StatusActivity=StatusActivity
        ArchiveObject_obj.LastEventDate=timestamp_utc
        ArchiveObject_obj.linkingAgentIdentifierValue=AgentIdentifierValue
        ArchiveObject_obj.LocalDBdatetime=timestamp_utc
        ArchiveObject_obj.save(update_fields=['StatusProcess',
                                              'StatusActivity',
                                              'LastEventDate',
                                              'linkingAgentIdentifierValue',
                                              'LocalDBdatetime',
                                              ])
        if ext_table:
            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(ext_table,'UPD',('StatusProcess',StatusProcess,
                                                                              'StatusActivity',StatusActivity,
                                                                              'LastEventDate',timestamp_dst.replace(tzinfo=None),
                                                                              'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                             ('ObjectGuid',ObjectUUID))
            if ext_errno: return ext_errno,ext_why
            else:
                ArchiveObject_obj.ExtDBdatetime=timestamp_utc
                ArchiveObject_obj.save(update_fields=['ExtDBdatetime'])
        return 0,''

    "Update storageMediumLocation and storageMediumLocationStatus"
    ###############################################
    def SetStorageMediumLocation(self, local_table, ext_table, AgentIdentifierValue, storageMediumID, storageMediumLocation, storageMediumLocationStatus, storageMediumDate):
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        timestamp_dst = timestamp_utc.astimezone(self.tz)
        storageMedium_obj = storageMedium.objects.get(storageMediumID=storageMediumID)
        storageMedium_obj.storageMediumLocationStatus=storageMediumLocationStatus
        storageMedium_obj.storageMediumLocation=storageMediumLocation
        storageMedium_obj.storageMediumDate=storageMediumDate
        storageMedium_obj.linkingAgentIdentifierValue=AgentIdentifierValue
        storageMedium_obj.LocalDBdatetime=timestamp_utc
        storageMedium_obj.save(update_fields=['storageMediumLocationStatus',
                                              'storageMediumLocation',
                                              'storageMediumDate',
                                              'linkingAgentIdentifierValue',
                                              'LocalDBdatetime',
                                              ])        
        if ext_table:
            ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(ext_table,'UPD',('storageMediumLocationStatus',storageMediumLocationStatus,
                                                                              'storageMediumLocation',storageMediumLocation,
                                                                              'storageMediumDate',storageMediumDate.astimezone(self.tz).replace(tzinfo=None),
                                                                              'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                             ('storageMediumID',storageMediumID))

            if ext_errno: return ext_errno,ext_why
            else:
                storageMedium_obj.ExtDBdatetime=timestamp_utc
                storageMedium_obj.save(update_fields=['ExtDBdatetime'])
        return 0,''

    """
    "Update AIP Status"
    ###############################################
    def CreateWriteReq(self, AIPpath, ObjectUUID, ObjectIdentifierValue, ObjectSize, MetaObjectSize, sm_list):
        #sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location]
        if sm_list[0] in range(300,330): 
            self.cmd = 10
            self.t_prefix = sm_list[6]
        elif sm_list[0] in range(200,201):
            self.cmd = 15
            self.t_prefix = ''
        self.cmdprio = 0
        self.work_uuid = uuid.uuid1()
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.ObjectMessageDigest = ''
        self.ObjectPath = os.path.join(AIPpath,self.ObjectIdentifierValue + '.tar')
        self.storageMedium = sm_list[0]
        self.storageMediumID = ''
        #self.storageMediumBlockSize = sm_list[2]
        #self.storageMediumFormat = sm_list[1]
        #self.contentLocationValue = 0
        #self.storageMediumLocation = ''
        self.WriteSize = int(ObjectSize) + int(MetaObjectSize)
        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
        self.Status = 0
        ###########################################################
        # Update table WriteJobs with new writejob
        ###########################################################
        IOqueue_obj = IOqueue()
        IOqueue_obj.cmd = self.cmd
        IOqueue_obj.cmdprio = self.cmdprio
        IOqueue_obj.work_uuid = self.work_uuid
        IOqueue_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
        IOqueue_obj.ObjectMessageDigest = self.ObjectMessageDigest
        IOqueue_obj.ObjectPath = self.ObjectPath
        IOqueue_obj.storageMedium = self.storageMedium
        IOqueue_obj.storageMediumID = self.storageMediumID
        IOqueue_obj.sm_list = sm_list
        IOqueue_obj.t_prefix = self.t_prefix
        IOqueue_obj.WriteSize = self.WriteSize
        #IOqueue_obj.date_created = self.timestamp_utc.replace(tzinfo=None)
        IOqueue_obj.date_created = self.timestamp_utc
        IOqueue_obj.Status = self.Status
        IOqueue_obj.save() 
#        self.res,self.errno,self.why=ESSDB.DB().action('IOqueue','INS',('cmd',self.cmd,
#                                                       'cmdprio',self.cmdprio,
#                                                       'work_uuid',self.work_uuid,
#                                                       'ObjectIdentifierValue',self.ObjectIdentifierValue,
#                                                       'ObjectMessageDigest',self.ObjectMessageDigest,
#                                                       'ObjectPath',self.ObjectPath,
#                                                       'storageMedium',self.storageMedium,
#                                                       'storageMediumID',self.storageMediumID,
#                                                       'sm_list',sm_list,
#                                                       #'storageMediumBlockSize',self.storageMediumBlockSize,
#                                                       #'storageMediumFormat',self.storageMediumFormat,
#                                                       #'contentLocationValue',self.contentLocationValue,
#                                                       #'storageMediumLocation',self.storageMediumLocation,
#                                                       't_prefix',self.t_prefix,
#                                                       'WriteSize',self.WriteSize,
#                                                       'date_created',self.timestamp_utc.replace(tzinfo=None),
#                                                       'Status',self.Status))
#        if self.errno: return self.work_uuid, self.errno, self.why
        return self.work_uuid, 0, ''

    "Update AIP Status"
    ###############################################
    def CreateReadReq(self, DIPpath, ObjectUUID, ObjectIdentifierValue, ObjectMessageDigest, sm_list):
        #sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location,self.contentLocationValue]
        if sm_list[0] in range(300,330):
            self.cmd = 20
            self.storageMediumID = sm_list[6]
        elif sm_list[0] in range(200,201):
            self.cmd = 25
            self.storageMediumID = ''
        self.cmdprio = 0
        self.work_uuid = uuid.uuid1()
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.ObjectMessageDigest = ObjectMessageDigest
        self.ObjectPath = DIPpath
        self.storageMedium = sm_list[0]
        #self.storageMediumBlockSize = sm_list[2]
        #self.storageMediumFormat = sm_list[1]
        self.contentLocationValue = 0
        self.storageMediumLocation = ''
        self.t_prefix = ''
        self.WriteSize = 0
        self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
        self.Status = 0
        ###########################################################
        # Update table WriteJobs with new writejob
        ###########################################################
        IOqueue_obj = IOqueue()
        IOqueue_obj.cmd = self.cmd
        IOqueue_obj.cmdprio = self.cmdprio
        IOqueue_obj.work_uuid = self.work_uuid
        IOqueue_obj.ObjectIdentifierValue = self.ObjectIdentifierValue
        IOqueue_obj.ObjectMessageDigest = self.ObjectMessageDigest
        IOqueue_obj.ObjectPath = self.ObjectPath
        IOqueue_obj.storageMedium = self.storageMedium
        IOqueue_obj.storageMediumID = self.storageMediumID
        IOqueue_obj.sm_list = sm_list
        IOqueue_obj.contentLocationValue = self.contentLocationValue
        IOqueue_obj.storageMediumLocation = self.storageMediumLocation
        IOqueue_obj.t_prefix = self.t_prefix
        IOqueue_obj.WriteSize = self.WriteSize
        #IOqueue_obj.date_created = self.timestamp_utc.replace(tzinfo=None)
        IOqueue_obj.date_created = self.timestamp_utc
        IOqueue_obj.Status = self.Status
        IOqueue_obj.save()

#        self.res,self.errno,self.why=ESSDB.DB().action('IOqueue','INS',('cmd',self.cmd,
#                                                       'cmdprio',self.cmdprio,
#                                                       'work_uuid',self.work_uuid,
#                                                       'ObjectIdentifierValue',self.ObjectIdentifierValue,
#                                                       'ObjectMessageDigest',self.ObjectMessageDigest,
#                                                       'ObjectPath',self.ObjectPath,
#                                                       'storageMedium',self.storageMedium,
#                                                       'storageMediumID',self.storageMediumID,
#                                                       'sm_list',sm_list,
#                                                       #'storageMediumBlockSize',self.storageMediumBlockSize,
#                                                       #'storageMediumFormat',self.storageMediumFormat,
#                                                       'contentLocationValue',self.contentLocationValue,
#                                                       'storageMediumLocation',self.storageMediumLocation,
#                                                       't_prefix',self.t_prefix,
#                                                       'WriteSize',self.WriteSize,
#                                                       'date_created',self.timestamp_utc.replace(tzinfo=None),
#                                                       'Status',self.Status))
#        if self.errno: return self.work_uuid, self.errno, self.why
        return self.work_uuid, 0, ''
    """

    "Get AIC relation to AIPs"
    ###############################################
    def GetAIC(self, ObjectUUID):
        status_code = 0
        status_list = []
        error_list = []
        AIC_UUID = ''

        if status_code == 0:
            self.Object_rel_dbget,errno,why = ESSDB.DB().action('Object_rel','GET3',('AIC_UUID',),('UUID',ObjectUUID))
            if errno:
                status_code = 1
                error_list.append('Failed to access Local DB, error: ' + str(why))
            elif len(self.Object_rel_dbget) == 0:
                status_code = 2
                error_list.append('ObjectUUID: %s not found in Object_rel DB.' %  str(ObjectUUID))
            elif len(self.Object_rel_dbget) > 1:
                status_code = 3
                error_list.append('ObjectUUID: %s have to many entrys in Object_rel DB.' %  str(ObjectUUID))
            else:
                AIC_UUID = self.Object_rel_dbget[0][0]
        if status_code == 0:
            return status_code,[status_list,error_list],AIC_UUID
        else:
            return status_code,[status_list,error_list],AIC_UUID

    "Get all AIPs related to AIC"
    ###############################################
    def GetIPs(self, AIC_UUID):
        status_code = 0
        status_list = []
        error_list = []
        self.AIC_UUID_rel_ObjectUUIDs = []

        if status_code == 0:
            self.Object_rel_dbget,errno,why = ESSDB.DB().action('Object_rel','GET3',('UUID',),('AIC_UUID',AIC_UUID))
            if errno:
                status_code = 1
                error_list.append('Failed to access Local DB, error: ' + str(why))
            elif len(self.Object_rel_dbget) == 0:
                status_code = 2
                error_list.append('AIC_UUID: %s not found in Object_rel DB.' %  str(AIC_UUID))
            else:
                for self.AIC_UUID_rel_ObjectUUID in self.Object_rel_dbget:
                    self.dbget,errno,why = ESSDB.DB().action('IngestObject','GET3',('PolicyId',
                                                                                    'ObjectIdentifierValue',
                                                                                    'ObjectSize',
                                                                                    'ObjectMessageDigestAlgorithm',
                                                                                    'MetaObjectSize',
                                                                                    'ObjectMessageDigest',
                                                                                    'CMetaMessageDigestAlgorithm',
                                                                                    'CMetaMessageDigest',
                                                                                    'CreateDate'),
                                                                                   ('ObjectUUID',self.AIC_UUID_rel_ObjectUUID[0]))
                    if errno:
                        status_code = 3
                        error_list.append('Failed to access Local DB, error: ' + str(why))
                    elif len(self.dbget):
                        PolicyId = self.dbget[0][0] 
                        ObjectIdentifierValue = self.dbget[0][1] 
                        ObjectSize = self.dbget[0][2] 
                        ObjectMessageDigestAlgorithm = self.dbget[0][3] 
                        MetaObjectSize = self.dbget[0][4] 
                        ObjectMessageDigest = self.dbget[0][5] 
                        CMetaMessageDigestAlgorithm = self.dbget[0][6] 
                        CMetaMessageDigest = self.dbget[0][7] 
                        CreateDate = self.dbget[0][8].replace(microsecond=0,tzinfo=pytz.utc)
                        self.AIC_UUID_rel_ObjectUUIDs.append([self.AIC_UUID_rel_ObjectUUID[0],ObjectSize,CMetaMessageDigestAlgorithm,ObjectMessageDigest,CreateDate])
        if status_code == 0:
            return status_code,[status_list,error_list],self.AIC_UUID_rel_ObjectUUIDs
        else:
            return status_code,[status_list,error_list],self.AIC_UUID_rel_ObjectUUIDs

class Check:
    TimeZone = timezone.get_default_timezone_name()
    tz=timezone.get_default_timezone()
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #                format='%(asctime)s %(levelname)-8s %(message)s',
        #                datefmt='%d %b %Y %H:%M:%S',
        #                filename='/tmp/ESSPGM_Check.log')
        pass

    "Clean RES_SIP from junk files"
    ###############################################
    def CleanRES_SIP(self,path='/ESSArch/testdata/A0007601'):
        for root, dirs, files in os.walk(path, topdown=False):
            for name in files:
                if name[-4:].lower() == '.tif':
                    pass
                elif name[-5:].lower() == '.tiff':
                    pass
                elif name.lower() == 'tiffedit.res':
                    pass
                elif name[-11:] == '_PREMIS.xml':
                    pass
                elif name.lower() == 'sip.xml':
                    pass
                else:
                    # Try to remove "junk" file
                    try:
                        os.remove(os.path.join(root, name))
                    except OSError, why:
                        return 1,str(why)
            for name in dirs:
                if name.lower() == 'c':
                    pass
                elif name.lower() == 'm':
                    pass
                else:
                    # Try to remove dir/dir...
                    try:
                        os.rmdir(os.path.join(root, name))
                    except OSError, why:
                        return 2,str(why)
        return 0,'OK'

    "Get filetree"
    ###############################################
    def GetFiletree(self,path='/ESSArch/testdata/A0007601'):
        self.file_list = []
        for self.f in os.listdir(path):
            self.path = os.path.join(path,self.f) 
            self.mode = os.stat(self.path)
            if stat.S_ISREG(self.mode[0]):                   # It's a file
                self.file_list.append(self.f)
            elif stat.S_ISDIR(self.mode[0]):                 # It's a directory
                for self.df in Check().GetFiletree(self.path):
                    self.file_list.append(self.f + '/' + self.df)
        return self.file_list

    "Get filetree"
    ###############################################
    def GetFiletree2(self,path,checksum=None,allow_unknown_filetypes=False):
        try:
            mimefilepath = Path.objects.get(entity='path_mimetypes_definitionfile').value
        except Path.DoesNotExist as e:
            if os.path.exists('/ESSArch/config/mime.types'):
                mimefilepath = '/ESSArch/config/mime.types'
            else:
                mimefilepath = '/ESSArch/config/data/mime.types'
            
        if os.path.exists(mimefilepath):
            mimetypes.suffix_map={}
            mimetypes.encodings_map={}
            mimetypes.types_map={}
            mimetypes.common_types={}
            mimetypes.init([mimefilepath])
        file_list = []
        status_code = 0
        status_list = []
        error_list = []
        try:
            if os.path.exists(path):
                if os.access(path, os.R_OK) and os.access(path, os.W_OK) and os.access(path, os.X_OK):
                    for f in os.listdir(path):
                        path_object = os.path.join(path,f)
                        if os.access(path_object, os.R_OK):
                            mode = os.stat(path_object)
                            if stat.S_ISREG(mode[0]):                   # It's a file
                                if checksum:
                                    f_checksum, errno, why = Check().checksum(path_object,checksum)
                                    if errno:
                                        error_list.append(why)
                                        return file_list, errno, [status_list,error_list]
                                    f_mimetype = mimetypes.guess_type(path_object,True)[0]
                                    if f_mimetype is None:
                                        if allow_unknown_filetypes:
                                            status_list.append('Warning filetype %s is not recognized, setting mimetype to application/octet-stream' % f)
                                            f_mimetype = 'application/octet-stream'
                                        else:
                                            error_list.append('Filetype %s is not supported' % f)
                                            return file_list, 2, [status_list,error_list]
                                else:
                                    f_checksum = None
                                    f_mimetype = None
                                file_list.append([Check().str2unicode(f), os.stat(path_object), f_checksum, f_mimetype])
                            elif stat.S_ISDIR(mode[0]):                 # It's a directory
                                dir_file_list, errno, [status_list2,error_list2] = Check().GetFiletree2(path_object,checksum,allow_unknown_filetypes)
                                if not errno:
                                    for df in dir_file_list:
                                        file_list.append([f + '/' + df[0], df[1], df[2], df[3]])
                                    for ss in status_list2:
                                        status_list.append(ss)
                                    for ee in error_list2:
                                        error_list.append(ee)
                                else:
                                    for ss in status_list2:
                                        status_list.append(ss)
                                    for ee in error_list2:
                                        error_list.append(ee)
                                    return file_list, errno, [status_list,error_list]
                        else:
                            status_code = 12
                            error_list.append('Permission problem for path: %s' % path_object)
                else:
                    status_code = 11
                    error_list.append('Permission problem for path: %s' % path)
            else:
                status_code = 13
                error_list.append('No such file or directory: %s' % path)
        except OSError:
            status_code = sys.exc_info()[1][0]
            error_list.append(sys.exc_info()[1][1] + ': ' + path)
        file_list = sorted(file_list) 
        return file_list, status_code, [status_list,error_list]

    "Get FiletreeSum"
    ###############################################
    def GetFiletreeSum(self,path,checksum=None):
        self.file_list, errno, why = Check().GetFiletree2(path,checksum)
        if not errno:
            tot_size = 0
            tot_number = 0
            for f in self.file_list:
                tot_size += f[1].st_size
                tot_number += 1
            return tot_size, tot_number, self.file_list , 0 , None
        else:
            return None, None, None, errno, why


    "Checks if the sum och TIFs in REFfile match the sum of TIFs in TARfile"
    ###############################################
    def rescheck(self, resfile, ressize, tarfile):
        #logging.info('Start to check tifsize and restifsize for: ' + tarfile)
        # List the RESfile and sum the tifs size
        f=open(resfile, 'r')
        self.a = 0
        self.s = ''
        self.restifsize = []
        for line in f:
            for i in line:
                if i == ',':
                    self.a = self.a + 1
                elif self.a == 2:
                    self.s = self.s + i
                elif self.a == 3:
                    self.restifsize.append(self.s)
                    break
            self.s = ''
            self.a = 0
        f.close()
        self.restarsize = 0
        for i in self.restifsize:
            self.restarsize = self.restarsize + int(i)
        # Read the first line i RESfile and grep the SEpath
        f=open(resfile, 'r')
        self.sepath = ''
        self.a = 0
        self.ab = 0
        for i in f.readline():
            if i == ',':
                self.a = self.a + 1
            elif self.a == 22:
                if i == '/':
                    self.ab = self.ab + 1
                if not i == '"' and self.ab < 5:
                    self.sepath = self.sepath + i
            elif self.a == 23:
                break
        f.close()
        # List the tarfile and sum the tifs size
        errortarout = open('/ESSArch/log/tarcheckerror.log','a')
        self.tar = subprocess.Popen(["tar tvf " + tarfile + " | awk {'print $3'}"], shell=True, stdout=subprocess.PIPE, stderr=errortarout)
        self.tarout = self.tar.communicate()
        errortarout.close()
        self.ss = ''
        self.tartifsize = []
        for i in self.tarout[0]:
            if not i == '\n':
                self.ss = self.ss + i
            else:
                self.tartifsize.append(self.ss)
                self.ss = ''
        self.tartarsize = 0
        for i in self.tartifsize:
            self.tartarsize = self.tartarsize + int(i)
        return self.restarsize, self.tartarsize - int(ressize), self.sepath

    "Get the FileNumber and FileSizeSum from RESfile"
    ###############################################
    def getFileSizeRES(self, resfile):
        self.TotalSize = 0
        self.TotalNum = 0
        try:
            self.reader = csv.reader(open(resfile, "rb"))
            for self.row in self.reader:
                self.TotalSize += int(self.row[2]) 
                self.TotalNum += 1
        except csv.Error, self.e:
            return [0,0],10,'file %s, line %d: %s' % (resfile, self.reader.line_num, self.e)
        except IOError, self.detail:
            return [0,0],20,str(self.detail)
        else:
            return [self.TotalNum,self.TotalSize],0,''

    "Get the SEPATH from RESfile"
    ###############################################
    def getSEPathRES(self, resfile):
        self.sepath = ''
        self.TotalNum = 0
        try:
            self.reader = csv.reader(open(resfile, "rb"))
            for self.row in self.reader:
                self.TotalNum += 1
                if self.TotalNum == 2:
                    #self.sepath = self.row[22]
                    self.ab = 0
                    for self.i in self.row[22]:
                        if self.i == '/':
                            self.ab = self.ab + 1
                        if self.ab < 5:
                            self.sepath += self.i
                    break
        except csv.Error, self.e:
            return self.sepath,10,'file %s, line %d: %s' % (resfile, self.reader.line_num, self.e)
        except IOError, self.detail:
            return self.sepath,20,str(self.detail)
        else:
            if len(self.sepath) > 1:
                return self.sepath,0,''
            else:
                return self.sepath,1,'Missing SEPATH?'

    "Get the FileNumber and FileSizeSum from TARfile"
    ###############################################
    def getFileSizeTAR(self, tarfile):
        self.TotalSize = 0
        self.TotalNum = 0
        try:
            errortarout = open('/ESSArch/log/tarcheckerror.log','a')
            self.cmd = subprocess.Popen(['tar', 'tvf', tarfile], stdout=subprocess.PIPE, stderr=errortarout)
            self.tarout = self.cmd.communicate()
            errortarout.close()
            if self.cmd.returncode == 0:
                for self.i in self.tarout[0].split('\n'):
                    if self.i:
                        self.TotalSize += int(self.i.split()[2])
                        self.TotalNum += 1
            else:
                return [0,0],10,'For more information check /ESSArch/log/tarcheckerror.log'
        except IOError, self.detail:
            return [0,0],20,str(self.detail)
        else:
            return [self.TotalNum,self.TotalSize],0,''

    def Unicode2isoStr(self,x):
        try:
            res = str(x)
        except UnicodeEncodeError:
            res = str(x.encode('iso-8859-1'))
        return res

    "Convert unicode to string"
    ###############################################
    def unicode2str(self,x):
        if type(x).__name__ == 'unicode':
            try:
                res = x.encode('utf-8')
            except UnicodeDecodeError:
                res = x.decode('iso-8859-1').encode('utf-8')
            except UnicodeEncodeError:
                res = str(x.encode('iso-8859-1'))
        else:
            res = x
        return res

    def unicode2isostr(self,x):
        if type(x).__name__ == 'unicode':
            res = x.encode('iso-8859-1')
        else:
            res = x
        return res

    "Convert string to unicode"
    ###############################################
    def str2unicode(self,x,y=None):
        if type(x).__name__ == 'str':
            try:
                res = x.decode('utf-8')
            except UnicodeDecodeError:
                res = x.decode('iso-8859-1')
        elif type(x).__name__ == 'list':
            num = 0
            for i in x:
                x[num] = Check().str2unicode(i)
                num += 1
            res = x
        elif type(x).__name__ == 'int' or type(x).__name__ == 'long':
            res = Check().str2unicode(str(x))
        elif type(x).__name__ == 'NoneType' and not type(y).__name__ == 'NoneType':
            res = Check().str2unicode(y)
        else:
            res = x
        return res

    "Convert list to string string newline for every item"
    ###############################################
    def list2strn(self,x):
        if type(x).__name__ == 'list':
            res = u''
            num = len(x)
            for i in x:
                if num > 1:
                    res += '%s\n' % i
                else:
                    res += '%s' % i
                num -= 1
        return res

    "Return checksum for file fname"
    def checksum(self,fname,ChecksumAlgorithm = 1):
        logging.info('Start to create %s checksum for: %s' % (ChecksumAlgorithm, fname))
        if type(ChecksumAlgorithm) in [str,unicode]:
            ChecksumAlgorithm = ChecksumAlgorithm.lower()
        if ChecksumAlgorithm in ['md5',1]:
            h = hashlib.md5()
        elif ChecksumAlgorithm in ['sha256','sha-256',2]:
            h = hashlib.sha256()
        else:
            h = hashlib.md5()
        chunk = 1048576
        try:
            f = open(fname, 'rb')
            s = f.read(chunk)
            while s != "":
                h.update(s)
                s = f.read(chunk)
            f.close()
        except IOError, why:
            return '',1,str(why)
        else:
            return h.hexdigest(),0,''

    def calcsum(self,filepath,checksumtype='MD5'):
        """Return checksum for a file."""
        if type(checksumtype) in [str,unicode]:
            checksumtype = checksumtype.lower()
        if checksumtype in ['md5',1]:
            h = hashlib.md5()
        elif checksumtype in ['sha256','sha-256',2]:
            h = hashlib.sha256()
        else:
            h = hashlib.md5()
        chunk = 1048576
        f = open(filepath, "rb")
        s = f.read(chunk)
        while s != "":
            h.update(s)
            s = f.read(chunk)
        f.close()
        return h.hexdigest()
    
    def invert_dict(self, d):
        return dict([(v,k) for k, v in d.iteritems()])
    
    ###############################################
    def DiffCheck_IP(self,ObjectIdentifierValue,ObjectPath,METS_ObjectPath=None,TimeZone=timezone.get_default_timezone_name(),checksumtype_default='MD5'):  
        status_code = 0
        status_list = []
        error_list = []
        res_list = []
        errno = 0 

        self.ObjectPath = ObjectPath
        if METS_ObjectPath is None:
            self.Cmets_obj = 'sip.xml'
            self.Cmets_objpath = os.path.join(self.ObjectPath,self.Cmets_obj)
        else:
            self.Cmets_objpath = METS_ObjectPath
            self.Cmets_obj = os.path.split(self.Cmets_objpath)[1]
        self.ObjectIdentifierValue = ObjectIdentifierValue
        
        if status_code == 0:
            ###########################################################
            # get object_list from METS 
            self.res_info, self.res_files, self.res_struct, errno, why = ESSMD.getMETSFileList(FILENAME=self.Cmets_objpath)
            if not errno == 0:
                self.event_info = 'Problem to get object_list from METS for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                error_list.append(self.event_info)
                status_code = 1
        if status_code == 0:
            ###########################################################
            # Insert METS file as first object in IP package
            self.M_CHECKSUM = self.calcsum(self.Cmets_objpath,checksumtype_default)
            self.M_statinfo = os.stat(self.Cmets_objpath)
            self.M_SIZE = self.M_statinfo.st_size
            self.M_utc_mtime = datetime.datetime.utcfromtimestamp(self.M_statinfo.st_mtime).replace(tzinfo=pytz.utc)
            self.M_lociso_mtime = self.M_utc_mtime.astimezone(pytz.timezone(TimeZone)).isoformat()
            self.res_files.insert(0,['amdSec', None, 'techMD', 'techMD001', None,
                                     None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % self.Cmets_obj, 'simple',
                                     self.M_CHECKSUM, checksumtype_default, self.M_SIZE, 'text/xml', self.M_lociso_mtime,
                                     'OTHER', 'METS', None])
        if status_code == 0:
            # present is used to detect case changed files on Windows
            checksums = {} # Map fname->checksum
            checksums_algo = {} # Map fname->checksumtype
            present = {}   # Map checksum->fname for present files 
            deleted = {}   # Map checksum->fname for deleted files
        
            changed = []   # Changed files
            added = []     # Added files
            confirmed = [] # Confirmed files
            renamed = []   # Renamed files as (old,new) pairs
            permission = [] # Permission problem
         
            result = ''           
            
            for self.object in self.res_files:
                self.ok = 1
                self.filepath = os.path.join(self.ObjectPath, self.object[8][5:])
                fname = self.object[8][5:]
                checksum = self.object[10]
                hash_algo = self.object[11].lower()
                #print 'filepath: %s, object: %s' % (self.filepath, str(self.object[11].lower()))
                if os.access(self.filepath,os.R_OK):
                    checksums[fname] = checksum
                    present[checksum] = fname
                    if not os.access(self.filepath,os.W_OK):
                        permission.append(fname)
                else:
                    deleted[checksum] = fname
                checksums_algo[fname] = hash_algo

            for fname in Check().GetFiletree(self.ObjectPath):
                if fname not in checksums:
                    if fname in checksums_algo:
                        checksumtype = checksums_algo[fname]
                    else:
                        checksumtype = checksumtype_default
                    newhash = self.calcsum(os.path.join(self.ObjectPath,fname),checksumtype)
                    checksums[fname] = newhash
                    if newhash in deleted:
                        renamed.append((deleted[newhash], fname))
                        del deleted[newhash]
                    elif newhash in present:
                        oldname = present[newhash]
                        if oldname.lower() == fname.lower():
                            renamed.append((oldname, fname))
                            del checksums[oldname]
                            checksums[fname] = newhash
                    else:
                        added.append(fname)
                else:
                    checksumtype = checksums_algo[fname]
                    newhash = self.calcsum(os.path.join(self.ObjectPath,fname),checksumtype)
                    if checksums[fname] == newhash:
                        if not newhash in permission:
                            confirmed.append(fname)
                    else:
                        changed.append(fname)

        if status_code == 0:
            # Log all changes
            #for fname in confirmed:
            #    result+="%s\n" % "CONFIRMED %s" % os.path.join(self.ObjectPath,fname) 
            for old, new in renamed:
                result+="%s\n" % "RENAMED %s: %s --> %s" % (self.ObjectPath,old,new)
                status_list.append("RENAMED %s: %s --> %s" % (self.ObjectPath,old,new)) 
            for fname in added:
                result+="%s\n" % "ADDED %s" % os.path.join(self.ObjectPath,fname)
                status_list.append("ADDED %s" % os.path.join(self.ObjectPath,fname))
            for fname in sorted(deleted.itervalues()):
                result+="%s\n" % "DELETED %s" % os.path.join(self.ObjectPath,fname)
                status_list.append("DELETED %s" % os.path.join(self.ObjectPath,fname))
            for fname in changed:
                result+="%s\n" % "CHANGED %s" % os.path.join(self.ObjectPath,fname)
                status_list.append("CHANGED %s" % os.path.join(self.ObjectPath,fname))
            for fname in permission:
                result+="%s\n" % "PERMISSION_ERROR %s" % os.path.join(self.ObjectPath,fname)
                status_list.append("PERMISSION_ERROR %s" % os.path.join(self.ObjectPath,fname))
            result+="%s\n" % "STATUS %s" % "confirmed %d renamed %d added %d deleted %d changed %d permission_error %d" % (
                len(confirmed), len(renamed), len(added), len(deleted), len(changed), len(permission))
            status_list.append("STATUS - %s" % "confirmed:%d renamed:%d added:%d deleted:%d changed:%d permission_error:%d" % (
                len(confirmed), len(renamed), len(added), len(deleted), len(changed), len(permission)))
            res_list.append(confirmed)
            res_list.append(renamed)
            res_list.append(added)
            res_list.append(changed)
            res_list.append(permission)
#            # Write list of changed files, removed on update
#            if changed:
#                logfile = open(changelog, "a")
#                try:
#                    for fname in changed:
#                        logfile.write(op.join(root, fname)+"\n")
#                finally:
#                    logfile.close()
             
        return status_code, [status_list,error_list], res_list    

    "Create TARpackage IP"
    ###############################################
    def Create_IP_package(self,ObjectIdentifierValue,ObjectPath,Package_ObjectPath,METS_ObjectPath=None,aic_object=None,TimeZone=timezone.get_default_timezone_name(),checksumtype_default='MD5'):   
        self.ok = 1
        error_list = []
        self.ObjectPath = ObjectPath
        if METS_ObjectPath is None:
            self.Cmets_obj = 'sip.xml'
            self.Cmets_objpath = os.path.join(self.ObjectPath,self.Cmets_obj)
        else:
            self.Cmets_objpath = METS_ObjectPath
            self.Cmets_obj = os.path.split(self.Cmets_objpath)[1]
        self.p_objpath = Package_ObjectPath
        self.p_obj = os.path.split(self.p_objpath)[1]
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.aic_object = aic_object
        
        if self.ok:
            ###########################################################
            # get object_list from METS 
            self.res_info, self.res_files, self.res_struct, errno, why = ESSMD.getMETSFileList(FILENAME=self.Cmets_objpath)
            if errno == 0:
                logging.info('Succeeded to get object_list from METS for information package: %s', self.ObjectIdentifierValue)
            else:
                self.event_info = 'Problem to get object_list from METS for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,str(errno),str(why))
                logging.error(self.event_info)
                self.ok = 0
        if self.ok:
            ###########################################################
            # Insert METS file as first object in IP package
            self.M_CHECKSUM, errno, why = Check().checksum(self.Cmets_objpath,checksumtype_default)
            if errno:
                self.event_info = 'Problem to get checksum for metsfile for IP package: ' + str(self.Cmets_fileobj)
                logging.error(self.event_info)
                self.ok = 0
            self.M_statinfo = os.stat(self.Cmets_objpath)
            self.M_SIZE = self.M_statinfo.st_size
            self.M_utc_mtime = datetime.datetime.utcfromtimestamp(self.M_statinfo.st_mtime).replace(tzinfo=pytz.utc)
            self.M_lociso_mtime = self.M_utc_mtime.astimezone(pytz.timezone(TimeZone)).isoformat()
            self.res_files.insert(0,['amdSec', None, 'techMD', 'techMD001', None,
                                     None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % self.Cmets_obj, 'simple',
                                     self.M_CHECKSUM, checksumtype_default, self.M_SIZE, 'text/xml', self.M_lociso_mtime,
                                     'OTHER', 'METS', None])
        if self.ok:
            ###########################################################
            # create IP package file
            try:
                logging.info('Create IP Package: ' + self.p_objpath)
                self.tarfile = tarfile.open(self.p_objpath, "w",)
            except tarfile.TarError:
                self.event_info = 'Problem to create IP Package: ' + str(self.p_objpath)
                logging.error(self.event_info)
                self.ok = 0
        if self.ok:
            ###########################################################
            # add files to AIP package file
            self.startTarTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            self.firstPremisObjectFlag = 1
            self.ObjectNumItems = 0
            self.ObjectSize = 0
            for self.object in self.res_files: 
                self.a_filepath = '%s/%s' % (self.ObjectIdentifierValue,self.object[8][5:])
                self.a_filepath_iso = Check().unicode2str(self.a_filepath)
                self.object_size = int(self.object[12])
                if self.a_filepath == self.Cmets_obj or self.a_filepath == '%s/%s' % (self.ObjectIdentifierValue,self.Cmets_obj):
                    self.filepath = self.Cmets_objpath
                else:
                    self.filepath = os.path.join(self.ObjectPath, self.object[8][5:])
                self.filepath_iso = Check().unicode2str(self.filepath)
                if os.access(self.filepath_iso,os.R_OK):
                    if int(os.stat(self.filepath_iso)[6]) == self.object_size:
                        try:
                            self.ObjectNumItems += 1
                            self.tarinfo = self.tarfile.gettarinfo(self.filepath_iso, self.a_filepath_iso)
                            self.tarfile.addfile(self.tarinfo, file(self.filepath_iso))
                            logging.info('Add: ' + self.a_filepath + ' to IP Package: ' + self.p_obj)
                        except tarfile.TarError:
                            self.event_info = 'Problem to add: ' + str(self.a_filepath) + ' to IP Package: ' + str(self.p_objpath)
                            logging.error(self.event_info)
                            self.ok = 0
                    else:
                        self.event_info = 'Filesize for object path: %s is %s and METS object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath_iso)[6]),str(self.object_size))
                        logging.error(self.event_info)
                        self.ok = 0
                else:
                    self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                    logging.error(self.event_info)
                    self.ok = 0
        if self.ok:
            ###########################################################
            # Close IP package
            try: 
                self.tarfile.close()
            except tarfile.TarError: 
                self.event_info = 'Problem to close IP package: ' + str(self.p_objpath)
                logging.error(self.event_info)
                self.ok = 0

        if self.ok:
            ###########################################################
            # Create PMETS for IP package
            self.METS_agent_list = []
            for agent in self.res_info[2]:
                #if not (agent[0] == 'CREATOR' and agent[3] == 'SOFTWARE'):
                self.METS_agent_list.append(agent)
                #self.METS_agent_list.append(['CREATOR',None,'INDIVIDUAL',None,AgentIdentifierValue,[]])
                #self.METS_agent_list.append(['CREATOR',None,'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
                
            self.METS_LABEL = self.res_info[0][0]
                        
            self.METS_altRecordID_list = []
            for altRecordID in self.res_info[3]:
                self.METS_altRecordID_list.append(altRecordID)
            
            self.ms_files = []
            self.res_files[0][8] = 'file:%s/%s' % (self.ObjectIdentifierValue,self.res_files[0][8][5:]) # Add ObjectIdentifierValue to Cmets filepath
            self.ms_files.append(self.res_files[0]) # Append Cmets
            self.P_CHECKSUM, errno, why = Check().checksum(self.p_objpath,checksumtype_default)
            if errno:
                self.event_info = 'Problem to get checksum for IP package: ' + str(self.p_objpath)
                logging.error(self.event_info)
                self.ok = 0
            self.P_statinfo = os.stat(self.p_objpath)
            self.P_SIZE = self.P_statinfo.st_size
            self.P_utc_mtime = datetime.datetime.utcfromtimestamp(self.P_statinfo.st_mtime).replace(tzinfo=pytz.utc)
            self.P_lociso_mtime = self.P_utc_mtime.astimezone(pytz.timezone(TimeZone)).isoformat()
            self.ms_files.append(['fileSec', None, None, None, None,
                                  None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % self.p_obj, 'simple',
                                  self.P_CHECKSUM, checksumtype_default, self.P_SIZE, 'application/x-tar', self.P_lociso_mtime,
                                  'tar', 'techMD001', None]) # Append Packagefile

            ESSMD.Create_IP_mets(ObjectIdentifierValue=self.ObjectIdentifierValue, 
                                 METS_ObjectPath='%s_Package_METS.xml' % self.p_objpath[:-4], 
                                 METS_TYPE='AIP', 
                                 agent_list=self.METS_agent_list, 
                                 altRecordID_list=self.METS_altRecordID_list, 
                                 file_list=self.ms_files,
                                 METS_LABEL=self.METS_LABEL
                                 )

    "Return MIME-type for PREMIS formatName"
    def PREMISformat2MIMEtype(self,formatName):
        if formatName[:4] == 'TIFF': formatName = 'tiff'
        MIMEtype = ''
        formatName_dict = dict({'fixed':'text/plain',
                                'separated':'text/plain',
                                'sgml':'text/sgml',
                                'html':'text/html',
                                'xml':'application/xml',
                                'xhtml':'application/xhtml+xml',
                                'text':'text/plain',
                                'pdf/a':'application/pdf',
                                'pdf':'application/pdf',
                                'jpeg':'image/jpeg',
                                'tiff':'image/tiff',
                                'png':'image/png',
                                'gml':'application/xml',
                                'pdf/e':'application/pdf',
                                'cals rasterfil':'image/x-cals',
                                'css':'text/css',
                                'mpeg (video)':'video/mpeg',
                                'mpeg (audio)':'audio/mpeg',
                                'mp3 (audio)':'audio/mpeg',
                                'jpeg2000':'image/jp2',
                                'dtd':'application/xml-dtd',
                                'xsl':'application/xslt+xml',
                                'xsd':'application/xml',
                                'warc':'application/warc',
                                'gif':'image/gif',
                                'javascript':'application/javascript',
                                'odf':'application.cnd.oasis.opendocument.formula',
                                'bmf':'image/x-xbitmap',
                                'wave':'audio/wav',
                                'wma':'audio/x-ms-wma',
                                'oggvorbis':'audio/ogg',
                                'midi':'audio/midi',
                                'wmv':'video/x-ms-wmv',
                                'qt':'video/quicktime',
                                'flv':'video/x-flv',
                                'divx':'video/x-divx',
                                'xvid':'video/x-xvid',
                                'res':'text/csv',
                                'unknownwebfileformat':'application/octet-stream',
                                'xml-register':'application/xml',
        })
        try:
            MIMEtype = formatName_dict[formatName]
        except KeyError:
            MIMEtype = 'unknown'
        if len(MIMEtype) == 0: 
            MIMEtype = 'unknown'
        return MIMEtype

    "Return PREMIS formatName for MIME-type"
    def MIMEtype2PREMISformat(self,formatName):
        if formatName[:4] == 'TIFF': formatName = 'TIFF'
        MIMEtype = ''
        formatName_dict = dict({'text/plain':'text',
                                'text/sgml':'sgml',
                                'text/html':'html',
                                'application/xml':'xml',
                                'application/xhtml+xml':'xhtml',
                                'application/pdf':'pdf',
                                'image/jpeg':'jpeg',
                                'image/tiff':'tiff',
                                'image/png':'png',
                                'image/x-cals':'cals rasterfil',
                                'text/css':'css',
                                'video/mpeg':'mpeg (video)',
                                'audio/mpeg':'mpeg (audio)',
                                'image/jp2':'jpeg2000',
                                'application/xml-dtd':'dtd',
                                'application/xslt+xml':'xsl',
                                'application/warc':'warc',
                                'image/gif':'gif',
                                'application/javascript':'javascript',
                                'application.cnd.oasis.opendocument.formula':'odf',
                                'image/x-xbitmap':'bmf',
                                'audio/wav':'wave',
                                'audio/x-ms-wma':'wma',
                                'audio/ogg':'oggvorbis',
                                'audio/midi':'midi',
                                'video/x-ms-wmv':'wmv',
                                'video/quicktime':'qt',
                                'video/x-flv':'flv',
                                'video/x-divx':'divx',
                                'video/x-xvid':'xvid',
                                'text/csv':'text',
                                'application/x-tar':'tar',
                                'application/octet-stream':'unknownwebfileformat',
        })
        try:
            MIMEtype = formatName_dict[formatName]
        except KeyError:
            MIMEtype = 'unknown'
        if len(MIMEtype) == 0:
            MIMEtype = 'unknown'
        return MIMEtype

    """
    "Extract and Verify AIPs in Storage Method and return OK or Fail"
    ##############################################
    # storageMediumID = storageMediumID (FB0001,disk) (always specified)
    # ObjectIdentifierValue = object id  (00063220) (default not set)
    # complete = None (1:complete check of tape None:quick check of tape) (default None)
    # delete = 1 (0: Don't delete verified object, 1: Delete object after verify) (default 1)
    # prefix = XX or XXX (Tape prefix only used to seperate verify files) (default None)
    # target = Target extract path ('/tmp/extract' or None(get verifydir from ESSConfig)) (default None)
    # unpack = 0 (0: Don't unpack AIP package, 1: Unpack AIP package) (default 0)
    ##############################################
    def AIPextract(self,storageMediumID=None,ObjectIdentifierValue=None,complete=None,delete=1,prefix=None,target=None,unpack=0,aic_support=False):
        self.storageMediumID=storageMediumID
        self.IngestTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','IngestTable'))[0][0]
        self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        self.storageMediumLocation = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','storageMediumLocation'))[0][0]
        if target:
            self.verifydir = target
        else:
            self.verifydir = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','verifydir'))[0][0]
        if prefix:
            self.verifydir = os.path.join(self.verifydir,prefix)
            if not os.path.exists(self.verifydir):
                os.mkdir(self.verifydir)
        self.numOK = 0
        if complete:
            logging.info('Start complete verify storageMediumID: ' + str(self.storageMediumID))
        elif ObjectIdentifierValue:
            logging.info('Start verify ObjectIdentifierValue: ' + str(ObjectIdentifierValue) + ' from storageMediumID: ' + str(self.storageMediumID))
        else: 
            logging.info('Start quick verify storageMediumID: ' + str(self.storageMediumID))
        if ObjectIdentifierValue and not storageMediumID:
            self.sql = "SELECT a.id,a.ObjectIdentifierValue,a.ObjectMessageDigest,b.contentLocationValue,b.storageMediumID,b.contentLocationType,c.storageMediumUUID,c.storageMedium,c.storageMediumLocation,c.storageMediumLocationStatus,c.storageMediumBlockSize,c.storageMediumStatus,c.storageMediumFormat FROM %s a, %s b, %s c WHERE a.ObjectIdentifierValue = b.ObjectIdentifierValue AND b.storageMediumID = c.storageMediumID AND c.storageMediumLocation = '%s' AND c.storageMediumLocationStatus = 50 AND NOT c.storageMediumStatus = 0 AND NOT c.storageMediumStatus = 200 AND a.ObjectIdentifierValue = '%s' ORDER BY ABS(b.contentLocationValue);" % (self.IngestTable,self.StorageTable,self.StorageMediumTable,self.storageMediumLocation,ObjectIdentifierValue)
        elif ObjectIdentifierValue and storageMediumID:
            self.sql = "SELECT a.id,a.ObjectIdentifierValue,a.ObjectMessageDigest,b.contentLocationValue,b.storageMediumID,b.contentLocationType,c.storageMediumUUID,c.storageMedium,c.storageMediumLocation,c.storageMediumLocationStatus,c.storageMediumBlockSize,c.storageMediumStatus,c.storageMediumFormat FROM %s a, %s b, %s c WHERE a.ObjectIdentifierValue = b.ObjectIdentifierValue AND b.storageMediumID = c.storageMediumID AND c.storageMediumLocation = '%s' AND c.storageMediumLocationStatus = 50 AND NOT c.storageMediumStatus = 200 AND a.ObjectIdentifierValue = '%s' AND b.storageMediumID = '%s' ORDER BY ABS(b.contentLocationValue);" % (self.IngestTable,self.StorageTable,self.StorageMediumTable,self.storageMediumLocation,ObjectIdentifierValue,storageMediumID)
        elif storageMediumID:
            self.sql = "SELECT a.id,a.ObjectIdentifierValue,a.ObjectMessageDigest,b.contentLocationValue,b.storageMediumID,b.contentLocationType,c.storageMediumUUID,c.storageMedium,c.storageMediumLocation,c.storageMediumLocationStatus,c.storageMediumBlockSize,c.storageMediumStatus,c.storageMediumFormat FROM %s a, %s b, %s c WHERE a.ObjectIdentifierValue = b.ObjectIdentifierValue AND b.storageMediumID = c.storageMediumID AND c.storageMediumLocation = '%s' AND c.storageMediumLocationStatus = 50 AND NOT c.storageMediumStatus = 200 AND b.storageMediumID = '%s' ORDER BY ABS(b.contentLocationValue);" % (self.IngestTable,self.StorageTable,self.StorageMediumTable,self.storageMediumLocation,storageMediumID)
        #logging.info('self.sql: ' + str(self.sql))
        self.rows,errno,why = ESSDB.DB().CursorExecute(self.sql)
        if errno == 5:
            self.event_info = 'Problem to access MySQL DB for verify' + str(self.storageMediumID) + ', ' + str(why)
            logging.warning(self.event_info)
        elif errno:
            self.event_info = 'Problem to access MySQL DB for verify' + str(self.storageMediumID) + ', ' + str(why)
            logging.error(self.event_info)
            return [[None],self.storageMediumID,self.verifydir],1,self.event_info
        self.NumOfRows = len(self.rows)
        self.contentLocationType200_list = []
        self.contentLocationType300_list = []
        self.checks = []
        if complete:
            self.checks = range(0,self.NumOfRows)
        elif ObjectIdentifierValue and not storageMediumID:
            self.RowNum = 0
            for self.row in self.rows:
                self.IngestObject_id = self.row[0]
                self.ObjectIdentifierValue = self.row[1] 
                self.ObjectMessageDigest = self.row[2]
                self.contentLocationValue = self.row[3]
                self.storageMediumID = self.row[4]
                self.contentLocationType = int(self.row[5])
                self.storageMediumUUID = self.row[6]
                self.storageMedium = self.row[7]
                self.storageMediumLocation = self.row[8]
                self.storageMediumLocationStatus = self.row[9]
                self.storageMediumBlockSize = self.row[10]
                self.storageMediumStatus = self.row[11]
                self.storageMediumFormat = self.row[12]
                if self.contentLocationType == 200:
                    self.contentLocationType200_list.append(self.RowNum)
                elif self.contentLocationType == 300: 
                    self.contentLocationType300_list.append(self.RowNum)
                self.RowNum += 1
            if len(self.contentLocationType200_list):
                self.checks.append(self.contentLocationType200_list[0])
            elif len(self.contentLocationType300_list):
                self.checks.append(self.contentLocationType300_list[0])
            else:
                self.event_info = 'No Storage Method is available for ObjectIdentifierValue %s' % ObjectIdentifierValue
                logging.error(self.event_info)
                return [[ObjectIdentifierValue],self.storageMediumID,self.verifydir],2,self.event_info
        elif ObjectIdentifierValue and storageMediumID:
            if self.NumOfRows > 0:
                self.checks.append(0)  
            else:
                self.event_info = 'No Storage Method is available for ObjectIdentifierValue %s on storageMediumID: %s' % (ObjectIdentifierValue,storageMediumID)
                logging.error(self.event_info)
                return [[ObjectIdentifierValue],self.storageMediumID,self.verifydir],5,self.event_info
        elif storageMediumID and self.NumOfRows > 2:
            self.checks.append(0)			#First ObjectIdentifierValue on SM
            self.checks.append(self.NumOfRows/2)	#Midel ObjectIdentifierValue on SM
            self.checks.append(self.NumOfRows-1)	#Last ObjectIdentifierValue on SM
        else:
            self.event_info = 'Less then 3 objects on Storage Method'
            logging.error(self.event_info)
            return [[None],self.storageMediumID,self.verifydir],3,self.event_info

        logging.debug('self.NumOfRows: %s, len(self.checks): %s, self.checks: %s',str(self.NumOfRows),str(len(self.checks)),str(self.checks))

        for self.check in self.checks:
            logging.debug('self.numOK: %s',str(self.numOK))
            self.ObjectIdentifierValue = self.rows[self.check][1]
            self.ObjectMessageDigest = self.rows[self.check][2]
            self.contentLocationValue = self.rows[self.check][3]
            self.storageMediumID = self.rows[self.check][4]
            self.storageMedium = self.rows[self.check][7]
            self.storageMediumLocation = self.rows[self.check][8]
            self.storageMediumBlockSize = self.rows[self.check][10]
            self.storageMediumFormat = None
            if not self.rows[self.check][12] is None:
                try:
                    self.storageMediumFormat = int(self.rows[self.check][12])
                except ValueError:
                    self.storageMediumFormat = self.rows[self.check][12]
            if aic_support:
                ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue=self.ObjectIdentifierValue)
                aic_obj = ip_obj.reluuid_set.get().AIC_UUID
                access_path = os.path.join(self.verifydir,aic_obj.ObjectUUID)
            else:
                access_path = self.verifydir
            self.ObjectPath = os.path.join(access_path,self.ObjectIdentifierValue + '.tar')
            try:
                Check().ensure_dir(self.ObjectPath)
            except (IOError,os.error), why:
                self.event_info = 'Problem to create path: %s, detail: %s' % (self.ObjectPath,why)
                logging.error(self.event_info)
                return [[None],self.storageMediumID,self.verifydir],5,self.event_info
            #sm_list = [self.sm_type,self.sm_format,self.sm_blocksize,self.sm_maxCapacity,self.sm_minChunkSize,self.sm_minContainerSize,self.sm_target,self.sm_location,self.sm_contentLocationValue]
            self.sm_list = [self.storageMedium,self.storageMediumFormat,self.storageMediumBlockSize,0,0,0,self.storageMediumID,self.storageMediumLocation,self.contentLocationValue]

            self.work_uuid, errno, why = DB().CreateReadReq(DIPpath = self.ObjectPath, ObjectUUID = '', ObjectIdentifierValue = self.ObjectIdentifierValue, ObjectMessageDigest = self.ObjectMessageDigest, sm_list = self.sm_list)
            if errno:
                print 'Problem to update local IOqueueDB for Object: ' + str(self.ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + str(why)
            while 1:
                self.res_ioqueue=ESSDB.DB().action('IOqueue','GET',('Status',),('work_uuid',self.work_uuid))
                if len(self.res_ioqueue):
                    if int(self.res_ioqueue[0][0]) == 20:
                        self.numOK += 1
                        self.VerifyChecksum = 0
                        logging.info('Checksum verify OK for storageMediumID: ' + str(self.storageMediumID) + ' ObjectIdentifierValue: ' + str(self.ObjectIdentifierValue))
                        break
                    elif int(self.res_ioqueue[0][0]) > 20:
                        self.VerifyChecksum = 1
                        logging.error('Checksum verify failed!! for storageMediumID: ' + str(self.storageMediumID) + ' ObjectIdentifierValue: ' + str(self.ObjectIdentifierValue))
                        break
                time.sleep(1)
            if unpack:
                logging.info('Start to unpack %s', self.ObjectIdentifierValue)
                if self.storageMediumFormat in range(100,102):
                    self.res,errno,why = Check().AIPunpack(self.ObjectIdentifierValue,access_path,0,self.VerifyChecksum)
                else:
                    self.res,errno,why = Check().AIPunpack(self.ObjectIdentifierValue,access_path,1,self.VerifyChecksum)
                if errno:
                    self.numOK -= 1
                    logging.error(self.res)
                else: 
                    logging.info(self.res)
            if delete == 1:
                self.PMetaObjectPath = self.ObjectPath[:-4] + '_Package_METS.xml'
                if self.storageMediumFormat in range(100,102):
                    logging.info('Try to remove ObjectPath: ' + self.ObjectPath)
                else:
                    logging.info('Try to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.PMetaObjectPath)
                try:
                    os.remove(self.ObjectPath)
                    if not self.storageMediumFormat in range(100,102):
                        os.remove(self.PMetaObjectPath)
                except (IOError,os.error), why:
                    if self.storageMediumFormat in range(100,102):
                        logging.error('Problem to remove ObjectPath: ' + self.ObjectPath)
                    else:
                        logging.error('Problem to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.PMetaObjectPath)
                else:
                    if self.storageMediumFormat in range(100,102):
                        logging.info('Success to removeObjectPath: ' + self.ObjectPath)
                    else:
                        logging.info('Success to removeObjectPath: ' + self.ObjectPath + ' and ' + self.PMetaObjectPath)
            elif delete == 2:
                self.CMetaObjectPath = self.ObjectPath[:-4] + '_Content_METS.xml'
                self.PMetaObjectPath = self.ObjectPath[:-4] + '_Package_METS.xml'
                if self.storageMediumFormat in range(100,102):
                    logging.info('Try to remove ObjectPath: ' + self.ObjectPath)
                else:
                    logging.info('Try to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.CMetaObjectPath + ' and ' + self.PMetaObjectPath)
                try:
                    os.remove(self.ObjectPath)
                    if not self.storageMediumFormat in range(100,102):
                        os.remove(self.CMetaObjectPath)
                        os.remove(self.PMetaObjectPath)
                except (IOError,os.error), why:
                    if self.storageMediumFormat in range(100,102):
                        logging.error('Problem to remove ObjectPath: ' + self.ObjectPath)
                    else:
                        logging.error('Problem to remove ObjectPath: ' + self.ObjectPath + ' and ' + self.CMetaObjectPath + ' and ' + self.PMetaObjectPath)
                else:
                    if self.storageMediumFormat in range(100,102):
                        logging.info('Success to removeObjectPath: ' + self.ObjectPath)
                    else:
                        logging.info('Success to removeObjectPath: ' + self.ObjectPath + ' and ' + self.CMetaObjectPath + ' and ' + self.PMetaObjectPath)
        logging.debug('last self.numOK: %s',str(self.numOK))
        if complete and self.numOK == self.NumOfRows:
            self.event_info = 'Finished complete verify storageMediumID: ' + str(self.storageMediumID) + ' OK'
            logging.info(self.event_info)
            return [[None],self.storageMediumID,self.verifydir],0,self.event_info
        elif ObjectIdentifierValue and self.numOK == 1:
            self.event_info = 'Success to generate DIP for ObjectIdentifierValue: %s from storageMediumID: %s to target directory: %s' % (self.ObjectIdentifierValue,self.storageMediumID,self.verifydir)
            logging.info(self.event_info)
            return [[self.ObjectIdentifierValue],self.storageMediumID,self.verifydir],0,self.event_info
        elif self.numOK == 3:
            self.event_info = 'Finished quick verify storageMediumID: ' + str(self.storageMediumID)
            logging.info(self.event_info)
            return [[None],self.storageMediumID,self.verifydir],0,self.event_info
        else:
            self.event_info = 'Failed to verify storageMediumID: ' + str(self.storageMediumID)
            logging.error(self.event_info)
            return [[None],self.storageMediumID,self.verifydir],4,self.event_info
    
    ###############################################
    def AIPunpack(self,ObjectIdentifierValue,target,mets = 1,VerifyChecksum = 1):
        ProcVersion = __version__
        self.ok = 1
        self.ObjectIdentifierValue = ObjectIdentifierValue
        self.DIPpath = target
        self.DIPpath_iso = Check().unicode2str(self.DIPpath)
        self.mets_flag = mets
        self.VerifyChecksum_flag = VerifyChecksum
        #Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
        #################################################
        # Unpack AIP
        try:
            self.AIPfilename = os.path.join(self.DIPpath,self.ObjectIdentifierValue + '.tar')
            self.AIP_tarObject = tarfile.open(name=self.AIPfilename, mode='r')
            self.AIP_tarObject.extractall(path=self.DIPpath_iso)
        except (ValueError, OSError, tarfile.TarError),why:
            self.event_info = 'Problem to unpack object: %s, Message: %s' % (self.ObjectIdentifierValue, str(why))
            logging.error(self.event_info)
            Events().create('1210','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
            self.ok = 0
        else:
            self.event_info = 'Success to unpack object: %s' % self.ObjectIdentifierValue
            logging.info(self.event_info)
            Events().create('1210','','ESSPGM_AIPunpack',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
        if self.ok and self.mets_flag:
            ###########################################################
            # find Content_METS file
            #self.Cmets_obj = Cmets_obj.replace('{uuid}',self.ObjectIdentifierValue)
            self.PMetaObjectPath = self.AIPfilename[:-4] + '_Package_METS.xml'
            if not os.path.exists(self.PMetaObjectPath):
                self.event_info = 'Problem to find %s for information package: %s' % (self.PMetaObjectPath,self.ObjectIdentifierValue)
                logging.error(self.event_info)
                Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.ok = 0
            if self.ok:
                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=self.PMetaObjectPath)
                if not error:
                    for self.file in res_files:
                        if self.file[0] == 'amdSec' and \
                           self.file[2] == 'techMD' and \
                           self.file[13] == 'text/xml' and \
                           self.file[15] == 'OTHER' and \
                           self.file[16] == 'METS':
                            if self.file[8][:5] == 'file:':
                                self.ContentFile = self.file[8][5:]
                else:
                    self.event_info = 'Problem to read package METS %s for information package: %s, error: %s' % (self.PMetaObjectPath,self.ObjectIdentifierValue,str(why))
                    logging.error(self.event_info)
                    Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    self.ok = 0
            #self.Cmets_obj = Cmets_obj.replace('{uuid}',self.ObjectIdentifierValue)
            self.Meta_filepath = os.path.join(self.DIPpath,self.ContentFile)
            if not os.path.exists(self.Meta_filepath):
                self.event_info = 'Problem to find %s for information package: %s' % (self.Meta_filepath,self.ObjectIdentifierValue)
                logging.error(self.event_info)
                Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.ok = 0
            if not self.DIPpath == os.path.split(self.Meta_filepath)[0]:
                self.DIPpath = os.path.split(self.Meta_filepath)[0]
                logging.info('Setting METSrootpath for IP: %s to %s' % (self.ObjectIdentifierValue, self.DIPpath))
################################
#            if os.path.exists('%s/%s_Content_METS.xml' % (self.DIPpath,self.ObjectIdentifierValue)):
#                pass
#            elif os.path.exists('%s/%s/%s_Content_METS.xml' % (self.DIPpath,self.ObjectIdentifierValue,self.ObjectIdentifierValue)):
#                self.DIPpath = os.path.join(self.DIPpath,self.ObjectIdentifierValue)
#            else:
#                self.event_info = 'Problem to find X_Content_METS.xml file for information package: %s' % self.ObjectIdentifierValue
#                logging.error(self.event_info)
#                Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
#                self.ok = 0
#            self.Meta_filepath = '%s/%s_Content_METS.xml' % (self.DIPpath,self.ObjectIdentifierValue)
        if self.ok and self.mets_flag:
            ###########################################################
            # get object_list from METS file
            self.object_list,errno,why = ESSMD.getAIPObjects(FILENAME=self.Meta_filepath)
            if errno == 0:
                logging.info('Success to get object_list from premis for information package: %s', self.ObjectIdentifierValue)
                #logging.debug('Meta_filepath: %s , object_list: %s', self.Meta_filepath,str(self.object_list))
            else:
                self.event_info = 'Problem to get object_list from premis for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,errno,str(why))
                logging.error(self.event_info)
                Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.ok = 0
        if self.ok and not self.mets_flag:
            ###########################################################
            # get object_list from RES file
            self.Meta_filepath = os.path.join(os.path.join(self.DIPpath,self.ObjectIdentifierValue),'TIFFEdit.RES')
            self.object_list,errno,why = ESSMD.getRESObjects(FILENAME=self.Meta_filepath)
            if errno == 0:
                logging.info('Success to get object_list from RES for information package: %s', self.ObjectIdentifierValue)
            else:
                self.event_info = 'Problem to get object_list from RES for information package: %s, errno: %s, detail: %s' % (self.ObjectIdentifierValue,errno,str(why))
                logging.error(self.event_info)
                Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                self.ok = 0
        if self.ok and self.mets_flag:
            ###########################################################
            # Start to format validate DIP with object list from METS
            logging.info('Format validate object: ' + self.ObjectIdentifierValue)
            self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            self.ObjectNumItems = 0
            self.ObjectSize = 0
            for self.object in self.object_list:
                self.messageDigestAlgorithm = self.object[1]
                self.filepath = os.path.join(self.DIPpath, self.object[0])
                self.filepath_iso = Check().unicode2str(self.filepath)
                if self.ok and os.access(self.filepath_iso,os.R_OK):
                    pass
                else:
                    self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                    logging.error(self.event_info)
                    Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    self.ok = 0
                    break
                if self.ok and os.access(self.filepath_iso,os.W_OK):
                    pass
                else:
                    self.event_info = 'Missing permission, Object path: %s is not writeable!' % self.filepath
                    logging.error(self.event_info)
                    Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    self.ok = 0
                    break
                if self.ok:
                    if int(os.stat(self.filepath_iso)[6]) == int(self.object[3]):
                        self.ObjectSize += int(self.object[3])
                    else:
                        self.event_info = 'Filesize for object path: %s is %s and premis object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath_iso)[6]),str(self.object[3]))
                        logging.error(self.event_info)
                        Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        self.ok = 0
                        break
                    if self.ok and self.VerifyChecksum_flag:
                        self.F_messageDigest,errno,why = Check().checksum(self.filepath_iso,self.messageDigestAlgorithm) # Checksum
                        if errno:
                            self.event_info = 'Failed to get checksum for: %s, Error: %s' % (self.filepath,str(why))
                            logging.error(self.event_info)
                            Events().create('1041','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                        else:
                            self.event_info = 'Success to get checksum for: %s, Checksum: %s' % (self.filepath,self.F_messageDigest)
                            logging.info(self.event_info)
                            Events().create('1041','','ESSPGM_AIPunpack',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                    else:
                        self.event_info = 'Skip to verify checksum for: %s' % self.filepath
                        logging.info(self.event_info)
                    if self.ok and self.VerifyChecksum_flag:
                        if self.F_messageDigest == self.object[2]:
                            self.event_info = 'Success to verify checksum for object path: %s' % self.filepath
                            logging.info(self.event_info)
                            Events().create('1042','','ESSPGM_AIPunpack',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
                        else:
                            self.event_info = 'Checksum for object path: %s is %s and premis object checksum is %s. The checksum must match!' % (self.filepath,self.F_messageDigest,self.object[2])
                            logging.error(self.event_info)
                            Events().create('1042','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                            self.ok = 0
                            break
                self.ObjectNumItems += 1
        if self.ok and not self.mets_flag:
            ###########################################################
            # Start to format validate DIP with object list from RESfile
            logging.info('Format validate object (RES): ' + self.ObjectIdentifierValue)
            self.startTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            self.ObjectNumItems = 0
            self.ObjectSize = 0
            for self.object in self.object_list:
                self.filepath = os.path.join(self.DIPpath, self.object[0])
                if self.ok and os.access(self.filepath,os.R_OK):
                    pass
                else:
                    self.event_info = 'Object path: %s do not exist or is not readable!' % self.filepath
                    logging.error(self.event_info)
                    Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    self.ok = 0
                    break
                if self.ok and os.access(self.filepath,os.W_OK):
                    pass
                else:
                    self.event_info = 'Missing permission, Object path: %s is not writeable!' % self.filepath
                    logging.error(self.event_info)
                    Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                    self.ok = 0
                    break
                if self.ok:
                    if int(os.stat(self.filepath)[6]) == int(self.object[1]):
                        self.ObjectSize += int(self.object[1])
                    else:
                        self.event_info = 'Filesize for object path: %s is %s and RES object size is %s. The sizes must match!' % (self.filepath,str(os.stat(self.filepath)[6]),str(self.object[1]))
                        logging.error(self.event_info)
                        Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'1',self.event_info,2,self.ObjectIdentifierValue)
                        self.ok = 0
                        break
        if self.ok:
            self.stopTime = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            self.MeasureTime = self.stopTime-self.startTime
            self.ObjectSizeMB = self.ObjectSize/1048576
            if self.MeasureTime.seconds < 1: self.MeasureTime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
            self.VerMBperSEC = int(self.ObjectSizeMB)/int(self.MeasureTime.seconds)
        if self.ok:
            self.event_info = 'Success to validate object package: %s, %s MB/Sec and Time: %s' % (self.ObjectIdentifierValue,str(self.VerMBperSEC),str(self.MeasureTime))
            logging.info(self.event_info)
            Events().create('1043','','ESSPGM_AIPunpack',ProcVersion,'0',self.event_info,2,self.ObjectIdentifierValue)
            self.res = 'Success to validate DIP package: ' + self.ObjectIdentifierValue + ' , ' + str(self.VerMBperSEC) + ' MB/Sec and Time: ' + str(self.MeasureTime)
            return self.res,0,'' 
        else:
            self.res = 'Problem to validate DIP package: ' + self.ObjectIdentifierValue
            return self.res,1,''


    "Return StartTime or [start,stop,writetime,MPperSEC]"
    def MBperSEC(self,action,start=0,size=0):
        if action == 'start':
            return datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3]) 
        elif action == 'stop':
            self.result = []
            self.stop = datetime.timedelta(seconds=time.localtime()[5],minutes=time.localtime()[4],hours=time.localtime()[3])
            self.writetime = self.stop-start
            if self.writetime.seconds < 1: self.writetime = datetime.timedelta(seconds=1)   #Fix min time to 1 second if it is zero.
            self.mbsec = int(size)/int(self.writetime.seconds)
            self.result.append(start)
            self.result.append(self.stop)
            self.result.append(self.writetime)
            self.result.append(self.mbsec)
            return self.result 

    def ensure_dir(self,f):
        d = os.path.dirname(f)
        if not os.path.exists(d):
            os.makedirs(d)
    """

"""
class Robot:
    TimeZone = timezone.get_default_timezone_name()
    tz=timezone.get_default_timezone()
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #            format='%(asctime)s %(levelname)-8s %(message)s',
        #            datefmt='%d %b %Y %H:%M:%S',
        #            filename='/tmp/ESSPGM_Robot.log')
        pass
    "Inventory robot"
    ###############################################
    def Inventory_old(self):
        logging.info('Start to inventory robot')
        robotdev = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','Robotdev'))[0][0]
        self.inv = subprocess.Popen(["mtx -f " + robotdev + " inventory"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.invout = self.inv.communicate()
        if self.inv.returncode:
            logging.error('Faild to inventory robot, error: %s',str(self.invout))
            return 1
        else:
            logging.debug('Robot inventory output: %s',str(self.invout))
            return 0

    "Update localDB whith volserDB from robot"
    ###############################################
    def GetVolserDB_old(self,CentralDB=1,set_storageMediumLocation='',set_storageMediumLocationStatus=''):
        logging.info('Start to GetVolserDB')
        AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
        self.MediumLocation = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','storageMediumLocation'))[0][0]
        ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        if ExtDBupdate:
            self.ext_StorageMediumTable = self.StorageMediumTable
        else:
            self.ext_StorageMediumTable = ''
        robotdev = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','Robotdev'))[0][0]
        self.RobotStat = subprocess.Popen(["mtx -f " + str(robotdev) + " status"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.RobotStatout = self.RobotStat.communicate()
        if self.RobotStat.returncode:
            logging.error('Faild to get status from robot, error: %s',str(self.RobotStatout))
            return 1
        else:
            logging.debug('Robot status output: %s',str(self.RobotStatout))
        self.line = ''
        self.word = re.compile(r'\W+')
        for self.i in self.RobotStatout[0]:
            if self.i == '\n':
                if re.match('  Storage Changer',self.line):     #Grep Storage Changer information (Not used)
                    self.info = self.word.split(self.line)
                    if Debug: print 'Info:', self.info
                    #######################
                    # Prepare robot table
                    res,errno,why = ESSDB.DB().action('robot','GET3',('status','t_id','drive_id','slot_id'))
                    if not errno: 
                        if not len(res) == int(self.info[7]):
                            ESSDB.DB().action('robot','DEL',('ALL'))
                            for slot_id in range(1,int(self.info[7])+1):
                                res,errno,why = ESSDB.DB().action('robot','INS',('status','None',       # old function GetVolserDB is moved to administration.tasks
                                                                                 't_id','',
                                                                                 'drive_id','99',
                                                                                 'slot_id',slot_id))
                if re.match('Data Transfer Element',self.line):         #Grep Robot drive status
                    self.d_elements = self.word.split(self.line)
                    if Debug: print 'Data Transfer Element:', self.d_elements
                    if self.d_elements[4] == 'Full':
                        ESSDB.DB().action('robotdrives','UPD',('status','Mounted',
                                                               't_id',self.d_elements[10],
                                                               'slot_id',self.d_elements[7]),
                                                              ('drive_id',self.d_elements[3]))
                    elif self.d_elements[4] == 'Empty':
                        ESSDB.DB().action('robotdrives','UPD',('status','Ready',
                                                               't_id','',
                                                               'slot_id','0'),
                                                              ('drive_id',self.d_elements[3]))
                if re.match('      Storage Element',self.line):         #Grep Robot slot status
                    if not re.search('EXPORT',self.line):
                        self.s_elements = self.word.split(self.line)
                        if Debug:
                            print 'Storage Element:', self.line
                            print 'slot_id:', self.s_elements[3]
                            print 'status:', self.s_elements[4]
                            if self.s_elements[4] == 'Full':
                                print 't_id:', self.s_elements[6][:6]
                                print 't_id_ver:', self.s_elements[6][6:]
                            else:
                                print 't_id:', 'None'
                        if self.s_elements[4] == 'Full':
                            print 's_elements',self.s_elements
                            if len(self.s_elements) >= 7:
                                self.TapeExistFlag = 0
                                #######################################################
                                # Slot is occupied
                                if CentralDB:
                                    logging.info('Try to sync local DB from central DB for mediaID: %s',self.s_elements[6][:6])
                                    errno = db_sync_ais.work().sync_from_centralDB(storageMediumID=self.s_elements[6][:6],set_storageMediumLocation=set_storageMediumLocation,set_storageMediumLocationStatus=set_storageMediumLocationStatus)
                                    if errno == 1:
                                        ######################################################
                                        # storageMediaID not found in central "storageMedium" DB 
                                        logging.info('Check if mediaID: %s exist in local DB',self.s_elements[6][:6])
                                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'GET3',('storageMediumID',),
                                                                                                         ('storageMediumID',self.s_elements[6][:6]))
                                        if errno:
                                            logging.error('Failed to access local DB: %s',str(why))
                                            return 10
                                        elif len(res) > 1:
                                            logging.error('To many storagemedias found in local "storageMedium" DB for %s',self.s_elements[6][:6])
                                            self.TapeExistFlag = 1
                                        elif len(res) == 1:
                                            logging.info('Found storageMedia %s in local DB', self.s_elements[6][:6])
                                            self.TapeExistFlag = 1
                                    elif errno == 2 or errno == 3:
                                        logging.info('No archive objects to sync for mediaID: %s from central DB, exit code: %s',self.s_elements[6][:6],str(errno))
                                        self.TapeExistFlag = 1
                                    elif errno > 3:
                                        logging.error('Failed to sync mediaID: %s from central DB, errno: %s',self.s_elements[6][:6],str(errno))
                                        return 30
                                    else:
                                        ######################################################
                                        # Succeed to update local DB for storageMediaID 
                                        self.TapeExistFlag = 1
                                else:
                                    res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'GET3',('storageMediumID',),
                                                                                                     ('storageMediumID',self.s_elements[6][:6]))
                                    if errno:
                                        logging.error('Failed to access local DB: %s',str(why))
                                        return 10 
                                    elif len(res) > 1:
                                        logging.error('To many storagemedias found in local "storageMedium" DB for %s',self.s_elements[6][:6])
                                        self.TapeExistFlag = 1
                                    elif len(res) == 1:
                                        logging.info('Found storageMedia %s in local DB', self.s_elements[6][:6])
                                        self.TapeExistFlag = 1
                                if Debug: 
                                    logging.debug('self.s_elements[6][:6]: ' + str(self.s_elements[6][:6]))
                                    logging.debug('self.TapeExistFlag: ' + str(self.TapeExistFlag))
                                if self.TapeExistFlag:                        #Check if t_id exist in archtape
                                    res,errno,why = ESSDB.DB().action('robot','UPD',('status','Full',
                                                                                     't_id',self.s_elements[6][:6],
                                                                                     'drive_id','99'),
                                                                                    ('slot_id',self.s_elements[3]))
                                    self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                    errno,why = DB().SetStorageMediumLocation(local_table=self.StorageMediumTable,
                                                                              ext_table=self.ext_StorageMediumTable,
                                                                              AgentIdentifierValue=AgentIdentifierValue,
                                                                              storageMediumID=self.s_elements[6][:6],
                                                                              storageMediumLocation=self.MediumLocation,
                                                                              storageMediumLocationStatus=50,
                                                                              storageMediumDate=self.timestamp_utc)
                                    if errno:
                                        logging.error('Failed to update location for MediumID: %s , error: %s',self.s_elements[6][:6],str(why))
                                else:
                                    res,errno,why = ESSDB.DB().action('robot','UPD',('status','Empty',
                                                                                     't_id',self.s_elements[6][:6],
                                                                                     'drive_id','99'),
                                                                                    ('slot_id',self.s_elements[3]))
                                if errno:
                                    logging.error('Failed to update local "robot" DB: %s, %s error: %s', str(self.s_elements[3]), self.s_elements[6][:6], str(why))
                                    return 11
                            else:
                                #######################################################
                                # Slot is empty
                                res,errno,why = ESSDB.DB().action('robot','UPD',('status','None',
                                                                                 't_id','',
                                                                                 'drive_id','99'),
                                                                                ('slot_id',self.s_elements[3]))
                                if errno:
                                    logging.error('Failed to update local "robot" DB: %s, none, error: %s', str(self.s_elements[3]), str(why))
                                    return 11
                        elif self.s_elements[4] == 'Empty':
                            self.mounted_slot_id = ESSDB.DB().action('robotdrives','GET',('drive_id','t_id'),('slot_id',self.s_elements[3]))
                            if self.mounted_slot_id:
                                res,errno,why = ESSDB.DB().action('robot','UPD',('status','Mounted',
                                                                                 't_id',self.mounted_slot_id[0][1],
                                                                                 'drive_id',self.mounted_slot_id[0][0]),
                                                                                ('slot_id',self.s_elements[3]))
                                if errno:
                                    logging.error('Failed to update local "robot" DB: %s, %s error: %s', str(self.s_elements[3]), self.mounted_slot_id[0][1], str(why))
                                    return 11
                            else:
                                res,errno,why = ESSDB.DB().action('robot','UPD',('status','None','t_id','','drive_id','99'),('slot_id',self.s_elements[3]))
                                if errno:
                                    logging.error('Failed to update local "robot" DB: %s, None, error: %s', str(self.s_elements[3]), str(why))
                                    return 11
                    else:                       #If robot slot is Import/Export slot (Not used)
                        self.e_elements = self.word.split(self.line)
                        if Debug: print 'Export/Import Element:', self.e_elements
                        if self.e_elements[6] == 'Full':
                            self.TapeExistFlag = ESSDB.DB().action('Full','GET',('status',),('t_id',self.e_elements[8]))
                            if self.TapeExistFlag:                        #Check if t_id exist in archtape (full tape)
                                ESSDB.DB().action('robotie','UPD',('status','Full','t_id',self.e_elements[8],'drive_id','99'),('slot_id',self.e_elements[3]))
                            else:
                                ESSDB.DB().action('robotie','UPD',('status','Ready','t_id',self.e_elements[8],'drive_id','99'),('slot_id',self.e_elements[3]))
                        elif self.e_elements[6] == 'Empty':
                            self.mounted_slot_id = ESSDB.DB().action('robotdrives','GET',('drive_id','t_id'),('slot_id',self.e_elements[3]))
                            if self.mounted_slot_id:
                                ESSDB.DB().action('robotie','UPD',('status','Mounted','t_id',self.mounted_slot_id[0][1],'drive_id',self.mounted_slot_id[0][0]),('slot_id',self.e_elements[3]))
                            else:
                                ESSDB.DB().action('robotie','UPD',('status','None','t_id','','drive_id','99'),('slot_id',self.e_elements[3]))
                self.line = ''
                continue
            self.line = self.line + self.i
        return 0

    "Reads the output from mt command and return the filenum"
    ###############################################
    def MTFilenum(self, tapedev):
        if ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','OS'))[0][0] == 'SUSE':
            self.mt = subprocess.Popen(["mt -f " + tapedev + " status | grep 'file number'"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            self.mt = subprocess.Popen(["mt -f " + tapedev + " status | awk {'print $2'} | grep number="], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.mtout = self.mt.communicate()
        if self.mt.returncode == 0:
            self.fileno = ''
            for i in self.mtout[0]:       #Reads the output from mt command and return the filenum in self.fileno
                if i.isdigit():
                    self.fileno = self.fileno + i
            if len(self.fileno):
                return int(self.fileno),0,str(self.mtout)
            else:
                return None,1,str(self.mtout)
        else:
            return None,2,str(self.mtout)

    "Position the tape and return OK or Fail"
    ###############################################
    def MTPosition(self, tapedev, t_num):
        self.real_current_t_num,errno,why=Robot().MTFilenum(tapedev)
        if errno:
            logging.error('Problem to get current tape position, errno: %s, why: %s',str(errno),why)
            return 'Fail'
        logging.info('Start to position to tapefile: ' + str(t_num) + ' current position is: ' + str(self.real_current_t_num))
        if int(t_num) == 0:
            logging.info('Start to rewind tape to position: 0')
            self.cmd = subprocess.Popen(["mt","-f",str(tapedev),"rewind"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        elif (int(t_num) - int(self.real_current_t_num)) < 0:
            self.fileno = ''
            for i in str(int(t_num) - int(self.real_current_t_num)):       #Cut away minus sign
                if i.isdigit():
                    self.fileno = self.fileno + i
            self.newt_num=int(self.fileno) + 1
            logging.info('Start to position with: bsfm: ' + str(self.newt_num))
            self.cmd = subprocess.Popen(["mt","-f",str(tapedev),"bsfm",str(self.newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        else:
            self.newt_num=int(t_num) - int(self.real_current_t_num)
            if self.newt_num > 0:
                logging.info('Start to position with: fsf: ' + str(self.newt_num))
                self.cmd = subprocess.Popen(["mt","-f",str(tapedev),"fsf",str(self.newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            elif self.newt_num == 0:
                self.newt_num = 1
                logging.info('Start to position to beginining of tape file with: bsfm: ' + str(self.newt_num))
                self.cmd = subprocess.Popen(["mt","-f",str(tapedev),"bsfm",str(self.newt_num)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        self.mtout = self.cmd.communicate()
        if self.cmd.returncode == 0:
            self.real_current_t_num,errno,why=Robot().MTFilenum(tapedev)
            if errno:
                logging.error('Problem to get current tape position, errno: %s, why: %s',str(errno),why)
                return 'Fail'
            elif int(t_num) == int(self.real_current_t_num): 
                logging.info('Success to position to tapefile: ' + str(t_num) + ' cmdout: ' + str(self.mtout))
                return 'OK'
        else:
            logging.error('Problem to position to tapefile: ' + str(t_num) + ' cmdout: ' + str(self.mtout))
            return 'Fail'

    "Mount tape at last write position and return OK or Fail"
    ###############################################
    def MountWritePos2(self,t_type,t_block,t_format,t_prefix,t_location,full_t_id='',work_uuid=''):
        self.StorageMediumTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageMediumTable'))[0][0]
        self.StorageTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','StorageTable'))[0][0]
        self.RobotTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotTable'))[0][0]
        self.RobotDrivesTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotDrivesTable'))[0][0]
        #self.RobotReqTable = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','RobotReqTable'))[0][0]
        self.work_uuid = work_uuid
        self.full_t_id = full_t_id
        
        AgentIdentifierValue = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','AgentIdentifierValue'))[0][0]
        ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

        # If tape is full verify tape and then unmount
        if len(self.full_t_id) == 6:
            self.cmdres,errno,why = Check().AIPextract(self.full_t_id, prefix=t_prefix)
            if errno:
                # Mark tape as failed in StorageMediumTable
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                ('storageMediumID',self.full_t_id))
                if errno: logging.error('Failed to update Local DB: ' + str(self.full_t_id) + ' error: ' + str(why))
                if errno == 0 and ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                   ('storageMediumID',self.full_t_id))
                    if ext_errno: logging.error('Failed to update External DB: ' + str(self.full_t_id) + ' error: ' + str(ext_why))
                    else:
                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.full_t_id))
                        if errno: logging.error('Failed to update Local DB: ' + str(self.full_t_id) + ' error: ' + str(why))
                return 3, 'None', 'None', 'None'
            else:
                # Mark tape as full in StorageMediumTable
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','30',
                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                ('storageMediumID',self.full_t_id))
                if errno: logging.error('Failed to update Local DB: ' + str(self.full_t_id) + ' error: ' + str(why))
                if errno == 0 and ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','30',
                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                   ('storageMediumID',self.full_t_id))
                    if ext_errno: logging.error('Failed to update External DB: ' + str(self.full_t_id) + ' error: ' + str(ext_why))
                    else:
                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.full_t_id))
                        if errno: logging.error('Failed to update Local DB: ' + str(self.full_t_id) + ' error: ' + str(why))

        #Check if a write tape exist
        self.t_id,errno,why = ESSDB.DB().action(self.StorageMediumTable,'GET4',('storageMediumID','storageMediumUsedCapacity'),
                                                                               ('storageMediumStatus','=','"20"','AND',
                                                                                'storageMedium','=','"'+str(t_type)+'"','AND',
                                                                                'storageMediumBlockSize','=','"'+str(t_block)+'"','AND',
                                                                                'storageMediumFormat','=','"'+str(t_format)+'"','AND',
                                                                                'storageMediumID','LIKE','"'+str(t_prefix)+'%"'))
        if errno: logging.error('Failed to access Local DB, error: ' + str(why))
        self.new_tape_flag = 0
        if self.t_id:
            self.t_id = self.t_id[0][0]
            #Check if write tape is mounted
            self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id','drive_lock','drive_dev'),('t_id',self.t_id,'AND','status','Mounted'))
            if self.robotdrive:
                while 1:
                    self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_id','drive_lock','drive_dev'),('t_id',self.t_id,'AND','status','Mounted'))
                    self.drive_id = self.robotdrive[0][0]
                    self.current_lock = self.robotdrive[0][1]
                    self.tapedev = self.robotdrive[0][2]
                    ##########################################
                    #Tape is mounted, check if locked
                    if len(self.current_lock) > 0:
                        ########################################
                        # Tape is locked, check if req work_uuid = lock
                        if self.current_lock == self.work_uuid:
                            ########################################
                            # Tape is already locked with req work_uuid
                            logging.info('Already Mounted: ' + str(self.t_id) + ' and locked by req work_uuid: ' + str(self.work_uuid))
                            break
                        else:
                            ########################################
                            # Tape is locked with another work_uuid
                            logging.info('Tape: ' + str(self.t_id) + ' is busy and locked by: ' + str(self.current_lock) + ' and not req work_uuid: ' + str(self.work_uuid))
                    else:
                        ########################################
                        # Tape is not locked, lock the drive with req work_uuid
                        ESSDB.DB().action(self.RobotDrivesTable,'UPD',('drive_lock',self.work_uuid),('drive_id',self.drive_id))
                        logging.info('Tape: ' + str(self.t_id) + ' is available set lock to req work_uuid: ' + str(self.work_uuid))
                        break
                    time.sleep(5)
            else:
                #Tape is not mounted, mounting tape
                logging.info('Start to mount: ' + str(self.t_id))
                robotQueue_obj = robotQueue()
                robotQueue_obj.ReqUUID = self.work_uuid
                robotQueue_obj.ReqType = 50 # Mount
                robotQueue_obj.ReqPurpose = 'ESSPGM - MountWritePos2'
                robotQueue_obj.Status = 0 # Pending
                robotQueue_obj.MediumID = self.t_id
                robotQueue_obj.save()
                #ESSDB.DB().action(self.RobotReqTable,'INS',('job_prio','1','status','Pending','req_type','Mount','t_id',self.t_id,'work_uuid',self.work_uuid))
                while 1:
                    self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_dev',),('t_id',self.t_id,'AND','status','Mounted','AND','drive_lock',self.work_uuid))
                    if self.robotdrive:
                        logging.info('Mount succeeded: ' + str(self.t_id))
                        break
                    else:
                        if Debug: logging.info('Wait for mounting of: ' + str(self.t_id))
                    time.sleep(2)
                self.tapedev = self.robotdrive[0][0]
        else:
            #########################################
            # Try to mount a new tape from robot
            self.t_id,errno,why = ESSDB.DB().action(self.RobotTable,'GET4',('t_id',),('status','=','"Ready"','AND','t_id','LIKE','"'+t_prefix+'%"'))
            if errno: logging.error('Failed to access Local DB, error: ' + str(why))
            if self.t_id: 
                self.t_id=self.t_id[0][0]
                logging.info('No writetape found, start to mount new tape: ' + str(self.t_id))
                ##########################
                # Insert StorageMediumTable
                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                self.uuid=str(uuid.uuid1())
                storageMedium_obj = storageMedium()
                storageMedium_obj.storageMedium = t_type
                storageMedium_obj.storageMediumID = self.t_id
                #storageMedium_obj.storageMediumDate = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.storageMediumDate = self.timestamp_utc
                storageMedium_obj.storageMediumLocation = t_location
                storageMedium_obj.storageMediumLocationStatus = 50
                storageMedium_obj.storageMediumBlockSize = t_block
                storageMedium_obj.storageMediumUsedCapacity = '0'
                storageMedium_obj.storageMediumStatus = 20
                storageMedium_obj.storageMediumFormat = t_format
                storageMedium_obj.storageMediumMounts = 1
                storageMedium_obj.linkingAgentIdentifierValue = AgentIdentifierValue
                #storageMedium_obj.CreateDate = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.CreateDate = self.timestamp_utc
                storageMedium_obj.CreateAgentIdentifierValue = AgentIdentifierValue
                storageMedium_obj.storageMediumUUID = self.uuid
                #storageMedium_obj.LocalDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                storageMedium_obj.LocalDBdatetime = self.timestamp_utc
                storageMedium_obj.save()                                                        
#                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'INS',('storageMedium',t_type,
#                                                                                 'storageMediumID',self.t_id,
#                                                                                 'storageMediumDate',self.timestamp_utc.replace(tzinfo=None),
#                                                                                 'storageMediumLocation',t_location,
#                                                                                 'storageMediumLocationStatus',50,
#                                                                                 'storageMediumBlockSize',t_block,
#                                                                                 'storageMediumUsedCapacity','0',
#                                                                                 'storageMediumStatus',20,
#                                                                                 'storageMediumFormat',t_format,
#                                                                                 'storageMediumMounts',1,
#                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
#                                                                                 'CreateDate',self.timestamp_utc.replace(tzinfo=None),
#                                                                                 'CreateAgentIdentifierValue',AgentIdentifierValue,
#                                                                                 'storageMediumUUID',self.uuid,
#                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                if errno: logging.error('Failed to insert to Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
#                if errno == 0 and ExtDBupdate:
                if ExtDBupdate:
                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'INS',('storageMedium',t_type,
                                                                                                    'storageMediumID',self.t_id,
                                                                                                    'storageMediumDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                    'storageMediumLocation',t_location,
                                                                                                    'storageMediumLocationStatus',50,
                                                                                                    'storageMediumBlockSize',t_block,
                                                                                                    'storageMediumUsedCapacity',0,
                                                                                                    'storageMediumStatus',20,
                                                                                                    'storageMediumFormat',t_format,
                                                                                                    'storageMediumMounts',1,
                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                                    'CreateDate',self.timestamp_dst.replace(tzinfo=None),
                                                                                                    'CreateAgentIdentifierValue',AgentIdentifierValue,
                                                                                                    'StorageMediumGuid',self.uuid))
                    if ext_errno: logging.error('Failed to insert to External DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(ext_why))
                    else:
                        #storageMedium_obj.ExtDBdatetime = self.timestamp_utc.replace(tzinfo=None)
                        storageMedium_obj.ExtDBdatetime = self.timestamp_utc
                        storageMedium_obj.save()   
#                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
#                                                                                        ('storageMediumID',self.t_id))
#                        if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                ############################
                # Mounting new tape
                robotQueue_obj = robotQueue()
                robotQueue_obj.ReqUUID = self.work_uuid
                robotQueue_obj.ReqType = 50 # Mount
                robotQueue_obj.ReqPurpose = 'ESSPGM - MountWritePos2 - newtape'
                robotQueue_obj.Status = 0 # Pending
                robotQueue_obj.MediumID = self.t_id
                robotQueue_obj.save()
                #ESSDB.DB().action(self.RobotReqTable,'INS',('job_prio','1','status','Pending','req_type','Mount','t_id',self.t_id,'work_uuid',self.work_uuid))
                while 1:
                    self.robotdrive = ESSDB.DB().action(self.RobotDrivesTable,'GET',('drive_dev',),('t_id',self.t_id,'AND','status','Mounted','AND','drive_lock',self.work_uuid))
                    if self.robotdrive:
                        logging.info('Mount succeeded: ' + str(self.t_id))
                        self.tapedev = self.robotdrive[0][0]
                        ##########################################
                        # Write an xml tapelabel
                        # Create the minidom document
                        self.xml_labeldoc = Document() 
                        # Create the <label> base element
                        self.xml_label = self.xml_labeldoc.createElement("label")
                        self.xml_labeldoc.appendChild(self.xml_label)
                        # Create the <tape> element
                        self.xml_tape = self.xml_labeldoc.createElement("tape")
                        self.xml_tape.setAttribute("id", self.t_id)
                        self.xml_tape.setAttribute("date", self.timestamp_dst.isoformat())
                        self.xml_label.appendChild(self.xml_tape)
                        # Create the <format> element
                        self.xml_format = self.xml_labeldoc.createElement("format")
                        self.xml_format.setAttribute("format", str(t_format))
                        self.xml_format.setAttribute("blocksize", str(t_block))
                        self.xml_format.setAttribute("drivemanufacture", str(t_type))
                        self.xml_label.appendChild(self.xml_format)
                        # Write  tapelabel to file
                        self.xml_labelfilepath = '/ESSArch/log/label/'+self.t_id+'_label.xml'
                        self.xml_labelfile = open(self.xml_labelfilepath, "w")
                        self.xml_labeldoc.writexml(self.xml_labelfile,addindent="    ",newl="\n")
                        self.xml_labelfile.close()
                        self.xml_labeldoc.unlink()
                        ##########################################
                        # Write tapelabel to tape
                        try:     #Open tapedevice
                            self.tarfile = tarfile.open(name=self.tapedev,mode="w|",bufsize=512 * 20)
                        except (ValueError, OSError, tarfile.TarError),why:
                            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                            res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                             'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                             'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                            ('storageMediumID',self.t_id))
                            if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                            if errno == 0 and ExtDBupdate:
                                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                                'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                               ('storageMediumID',self.t_id))
                                if ext_errno: logging.error('Failed to update External DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(ext_why))
                                else:
                                    res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                                    if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                            logging.error(self.t_id + ' failed to open tapedevice, Message: ' + str(why))
                        else:
                            logging.info(self.t_id + ' succeed to open tapedevice')
                            try:      #Add tapelabel to tape
                                logging.info(self.t_id + ' start to add label tape')
                                self.tarinfo = self.tarfile.gettarinfo(self.xml_labelfilepath, self.t_id+'_label.xml')
                                self.tarfile.addfile(self.tarinfo, file(self.xml_labelfilepath))
                            except (ValueError, OSError, tarfile.TarError), (errno, why):
                                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                                ('storageMediumID',self.t_id))
                                if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                                if errno == 0 and ExtDBupdate:
                                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                                   ('storageMediumID',self.t_id))
                                    if ext_errno: logging.error('Failed to update External DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(ext_why))
                                    else:
                                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                                        if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                                logging.error(self.t_id + ' failed to write tapelabel, Message: ' + str(why))
                            else:
                                logging.info(self.t_id + ' succeed to label new media')
                            try:      #Close tapedevice
                                self.tarfile.close()                                                                                    #Close tapedevice
                            except (ValueError, OSError, tarfile.TarError),why:
                                self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
                                self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                                res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
                                                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)),
                                                                                                ('storageMediumID',self.t_id))
                                if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                                if errno == 0 and ExtDBupdate:
                                    ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(self.StorageMediumTable,'UPD',('storageMediumStatus','100',
                                                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue),
                                                                                                                   ('storageMediumID',self.t_id))
                                    if ext_errno: logging.error('Failed to update External DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(ext_why))
                                    else:
                                        res,errno,why = ESSDB.DB().action(self.StorageMediumTable,'UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('storageMediumID',self.t_id))
                                        if errno: logging.error('Failed to update Local DB: ' + str(self.t_id) + ' (ESSPGM) error: ' + str(why))
                                logging.error(self.t_id + ' failed to close tapedevice, Message: ' + str(why))
                            else:
                                logging.info(self.t_id + ' close tapedevice succeed')
                                self.new_tape_flag = 1
                        break
                    else:
                        if Debug: logging.info('Wait for mounting of: ' + str(self.t_id))
                    time.sleep(2)
            else:    
                logging.error('No empty tapes are avilable in robot with tape prefix: ' + str(t_prefix))
                return 2, 'None', 'None', 'None'
        if ESSDB.DB().action(self.StorageMediumTable,'GET',('storageMediumStatus',),('storageMediumID',self.t_id))[0][0]=='100':
            return 1, 'None', 'None', 'None'
        # Check if tape is in write position
        self.db_t_pos = ESSDB.DB().action(self.StorageTable,'GETlast',('id','contentLocationValue'),('storageMediumID','=','"'+self.t_id+'"'))
        if len(self.db_t_pos) == 0 and self.new_tape_flag == 1: 
            self.t_pos = 1
        elif len(self.db_t_pos):
            self.t_pos = int(self.db_t_pos[0][1]) + 1
        else:
            logging.error(str(self.t_id) + ' missing tape contentlocation in DB (StorageTable)')
            return 1, self.t_id, self.tapedev, 0
        logging.info(self.t_id + ' start to position to writeposition ' + str(self.t_pos))
        if Robot().MTPosition(self.tapedev, self.t_pos) == 'OK':
            # Tape is in write position
            logging.info(str(self.t_id) + ' is in writeposition ' + str(self.t_pos))
            return 0, self.t_id, self.tapedev, self.t_pos
        else:
            # Problem to position tape
            logging.error(str(self.t_id) + ' has problem to position to writeposition ' + str(self.t_pos))
            return 1, self.t_id, self.tapedev, self.t_pos
"""

class svardb:
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #                format='%(asctime)s %(levelname)-8s %(message)s',
        #                datefmt='%d %b %Y %H:%M:%S',
        #                filename='/tmp/ESSPGM_svardb.log')
        pass

    def ArchObjUpd(self,a_obj,a_num,t_id):
        self.url=ESSDB.DB().action('aplcfg','GET',('value',),('name','ext_db_batch'))[0][0]             #Get ext_db_batch url
        self.params = urllib.urlencode({'ArchObj': str(a_obj), 'ArchNumItems': str(a_num), 'TapeID': str(t_id), 'action': 6})
        #self.urlupdate = "http://212.181.19.10/web/svarfolder/admin/skanning/update_database.asp?%s"
        self.urlupdate = self.url + '?%s'
        self.conn = urllib.urlopen(self.urlupdate % self.params)
        self.data = self.conn.read()
        self.conn.close()
        if re.search('Lyckades',self.data):
            logging.info('Success to update PRJ_db with bacthinfo: ' + str(a_obj))
        else:
            logging.error('Problem to update PRJ_db with bacthinfo: ' + str(a_obj))

    def ArchObjVer(self,a_obj):
        self.url=ESSDB.DB().action('aplcfg','GET',('value',),('name','ext_db_batch_verify'))[0][0]     #Get ext_db_batch_verify url
        self.params = urllib.urlencode({'ArchObj': str(a_obj)})
        self.urlupdate = self.url + '?%s'
        self.conn = urllib.urlopen(self.urlupdate % self.params)
        self.data = self.conn.read()
        self.conn.close()
        if re.search('Lyckades',self.data):
            logging.info('Success to update PRJ_db with verifyinfo: ' + str(a_obj))
        else:
            logging.error('Problem to update PRJ_db with verifyinfo: ' + str(a_obj))

class ExtPrjDB:
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #                format='%(asctime)s %(levelname)-8s %(message)s',
        #                datefmt='%d %b %Y %H:%M:%S',
        #                filename='/tmp/ESSPGM_ExtPrjDB.log')
        pass

    def taped(self,object,tifnum,tifsum,date,time,t_id1,t_id2,t_pos1,t_pos2):
        self.url=ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtPrjTapedURL'))[0][0]             #Get ext_db_batch url
        self.params = urllib.urlencode({'object': str(object), 
                                        'tifnum': str(tifnum), 
                                        'tifsum': str(tifsum), 
                                        'date': str(date), 
                                        'time': str(time),
                                        't_id1': str(t_id1),
                                        't_id2': str(t_id2),
                                        't_pos1': str(t_pos1),
                                        't_pos2': str(t_pos2)})
        #self.urlupdate = "http://212.181.19.10/web/svarfolder/admin/skanning/update_database.asp?%s"
        self.urlupdate = self.url + '?%s'
        logging.info('Try to update ExtPrJDB with taped info: ' + str(object) + ' self.urlupdate: ' + str(self.urlupdate) + ' self.params: ' + str(self.params))
        try:
            self.conn = urllib.urlopen(self.urlupdate % self.params)
        except (IOError), (errno,why):
            logging.error('Problem to connect to URL: ' + str(self.url) + '?' + str(self.params) + ' Error: ' + str(why) + ' ' + str(errno))
        else:
            self.data = self.conn.read()
            self.conn.close()
            if re.search('OK ',self.data):
                logging.info('Success to update ExtPrJDB with taped info: ' + str(object) + ' cmdout: ' + str(self.data))
            else:
                logging.error('Problem to update ExtPrJDB with taped info: ' + str(object) + ' cmdout: ' + str(self.data))

class Events:
    TimeZone = timezone.get_default_timezone_name()
    tz=timezone.get_default_timezone()
    def __init__(self):
        #logging.basicConfig(level=logging.DEBUG,
        #                format='%(asctime)s %(levelname)-8s %(message)s',
        #                datefmt='%d %b %Y %H:%M:%S',
        #                filename='/tmp/ESSPGM_Events.log')
        pass

    def create(self,eventType,eventDetail,eventApplication,eventVersion,eventOutcome,eventOutcomeDetailNote,UpdateMode,ObjectIdentifierValue=None,storageMediumID=None,eventDateTime=None,linkingAgentIdentifierValue=None,storageMediumLocation=None,storageMediumDestination=None,RelatedEventIdentifierValue=None):
        # UpdateMode 0=MASTER, 1=SLAVE, 2=AIS
        db.close_old_connections()
        self.uuid=str(uuid.uuid1())
        if eventDateTime:
            if type(eventDateTime) == datetime.datetime:
                if eventDateTime.tzinfo == None:
                    logging.error('eventDateTime missing tzinfo(ex.+01:00): ' + str(eventDateTime))
                    return 3
                elif eventDateTime.tzinfo == pytz.utc:
                    self.timestamp_utc = eventDateTime.replace(microsecond=0)
                    self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
                else:
                    logging.error('eventDateTime tzinfo is not UTC(ex.+00:00): ' + str(eventDateTime))
                    return 4
            else:
                logging.error('eventDateTime is not type datetime.datetime: %s, %s' % (type(eventDateTime), str(eventDateTime)))
                return 5
        else:
            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
        if linkingAgentIdentifierValue:
            self.AgentIdentifierValue = linkingAgentIdentifierValue
        else:
            self.AgentIdentifierValue, errno, why = ESSDB.DB().action('ESSConfig','GET3',('Value',),('Name','AgentIdentifierValue'))
            if not errno and len(self.AgentIdentifierValue): 
                self.AgentIdentifierValue=self.AgentIdentifierValue[0][0]
            else: 
                return 1
        self.updateDB,errno,why=ESSDB.DB().action('eventType_codes','GET3',('localDB','externalDB'),('code',eventType))
        if not errno and self.updateDB:
            self.updateDB=self.updateDB[0]
        else:
            logging.error('eventType missing for code: ' + str(eventType))
            self.updateDB=(0,0)
            return 2
        ##########################################################
        #Update local eventDB for archive object 
        if self.updateDB[0] and ObjectIdentifierValue:
            try: 
                eventOutcomeDetailNote_MySQL = ESSDB.escape_string(eventOutcomeDetailNote)
                eventIdentifier_obj = eventIdentifier()
                eventIdentifier_obj.eventIdentifierValue = self.uuid
                eventIdentifier_obj.eventType = eventType
                #eventIdentifier_obj.eventDateTime = self.timestamp_utc.replace(tzinfo=None)
                eventIdentifier_obj.eventDateTime = self.timestamp_utc
                eventIdentifier_obj.eventDetail = eventDetail
                eventIdentifier_obj.eventApplication = eventApplication
                eventIdentifier_obj.eventVersion = eventVersion
                eventIdentifier_obj.eventOutcome = eventOutcome
                eventIdentifier_obj.eventOutcomeDetailNote = eventOutcomeDetailNote_MySQL
                eventIdentifier_obj.linkingAgentIdentifierValue = self.AgentIdentifierValue
                eventIdentifier_obj.linkingObjectIdentifierValue = ObjectIdentifierValue
                eventIdentifier_obj.save()
            #except _mysql_exceptions.Warning,why:
            except (MySQLdb.Warning, why):
                if why.startswith("Data truncated for column 'eventOutcomeDetailNote' at row 1"):
                    logging.warning('Problem to update local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', why: ' + Check().unicode2isostr(why))
                    return 5
                else:
                    logging.error('Problem to update local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', why: ' + Check().unicode2isostr(why)) 
                    return 10
#            res,errno,why=ESSDB.DB().action('eventIdentifier','INS',('eventIdentifierValue',self.uuid,
#                                                                     'eventType',eventType,
#                                                                     'eventDateTime',self.timestamp_utc.replace(tzinfo=None),
#                                                                     'eventDetail',eventDetail,
#                                                                     'eventApplication',eventApplication,
#                                                                     'eventVersion',eventVersion,
#                                                                     'eventOutcome',eventOutcome,
#                                                                     'eventOutcomeDetailNote',eventOutcomeDetailNote_MySQL,
#                                                                     'linkingAgentIdentifierValue',self.AgentIdentifierValue,
#                                                                     'linkingObjectIdentifierValue',ObjectIdentifierValue))
#            if errno==5:
#                logging.warning('Problem to update local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + Check().unicode2isostr(why))
#                return 5
#            elif errno:
#                logging.error('Problem to update local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + Check().unicode2isostr(why)) 
#                return 10

        ##########################################################
        #Update local eventDB for storagemedium object
        elif self.updateDB[0] and storageMediumID:
            try:
                eventIdentifier_obj = eventIdentifier()
                eventIdentifier_obj.eventIdentifierValue = self.uuid
                eventIdentifier_obj.eventType = eventType
                #eventIdentifier_obj.eventDateTime = self.timestamp_utc.replace(tzinfo=None)
                eventIdentifier_obj.eventDateTime = self.timestamp_utc
                eventIdentifier_obj.eventDetail = eventDetail
                eventIdentifier_obj.eventApplication = eventApplication
                eventIdentifier_obj.eventVersion = eventVersion
                eventIdentifier_obj.eventOutcome = eventOutcome
                eventIdentifier_obj.eventOutcomeDetailNote = eventOutcomeDetailNote
                eventIdentifier_obj.linkingAgentIdentifierValue = self.AgentIdentifierValue
                eventIdentifier_obj.linkingObjectIdentifierValue = storageMediumID
                eventIdentifier_obj.save()
            except (MySQLdb.Warning), (why):
                if why.startswith("Data truncated for column 'eventOutcomeDetailNote' at row 1"):
                    logging.warning('Problem to insert to local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', why: ' + Check().unicode2isostr(why))
                    return 5
                else:
                    logging.error('Problem to insert to local eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', why: ' + Check().unicode2isostr(why)) 
                    return 11

#            res,errno,why=ESSDB.DB().action('eventIdentifier','INS',('eventIdentifierValue',self.uuid,
#                                                                     'eventType',eventType,
#                                                                     'eventDateTime',self.timestamp_utc.replace(tzinfo=None),
#                                                                     'eventDetail',eventDetail,
#                                                                     'eventApplication',eventApplication,
#                                                                     'eventVersion',eventVersion,
#                                                                     'eventOutcome',eventOutcome,
#                                                                     'eventOutcomeDetailNote',eventOutcomeDetailNote,
#                                                                     'linkingAgentIdentifierValue',self.AgentIdentifierValue,
#                                                                     'linkingObjectIdentifierValue',storageMediumID))
#            if errno:
#                logging.error('Problem to update local eventDB for eventType: ' + str(eventType) + ', storageMediumID: ' + str(storageMediumID) + ', error: ' + str(errno) + ', why: ' + Check().unicode2isostr(why))
#                return 11

        ##########################################################
        #Update externalDB (AIS) for archive object
        if UpdateMode == 2 and self.updateDB[1] and ObjectIdentifierValue:
            eventOutcomeDetailNote_MSSQL = ESSMSSQL.escape_string(eventOutcomeDetailNote)
            res,errno,why=ESSMSSQL.DB().action('eventIdentifier','INS',('eventIdentifierValue',self.uuid,
                                                                        'eventType',eventType,
                                                                        'eventDateTime',self.timestamp_dst.replace(tzinfo=None),
                                                                        'eventDetail',eventDetail,
                                                                        'eventApplication',eventApplication,
                                                                        'eventVersion',eventVersion,
                                                                        'eventOutcome',eventOutcome,
                                                                        'eventOutcomeDetailNote',eventOutcomeDetailNote_MSSQL,
                                                                        'linkingAgentIdentifierValue',self.AgentIdentifierValue,
                                                                        'linkingObjectIdentifierValue',ObjectIdentifierValue))
            if errno:
                logging.error('Problem to update AIS eventDB for eventType: ' + str(eventType) + ', object: ' + Check().unicode2isostr(ObjectIdentifierValue) + ', error: ' + str(errno) + ', why: ' + Check().unicode2isostr(why))
                return 20

        ##########################################################
        #Update externalDB (AIS) for storagemedium object
        elif UpdateMode == 2 and self.updateDB[1] and storageMediumID:
            res,errno,why=ESSMSSQL.DB().action('eventStorageMedium','INS',('eventIdentifierValue',self.uuid,
                                                                           'eventType',eventType,
                                                                           'eventDateTime',self.timestamp_dst.replace(tzinfo=None),
                                                                           'eventDetail',eventDetail,
                                                                           'eventApplication',eventApplication,
                                                                           'eventVersion',eventVersion,
                                                                           'eventOutcome',eventOutcome,
                                                                           'eventOutcomeDetailNote',eventOutcomeDetailNote,
                                                                           'linkingAgentIdentifierValue',self.AgentIdentifierValue,
                                                                           'storageMediumID',storageMediumID,
                                                                           'storageMediumLocation',storageMediumLocation,
                                                                           'storageMediumDestination',storageMediumDestination,
                                                                           'RelatedEventIdentifierValue',RelatedEventIdentifierValue))

            if errno:
                logging.error('Problem to update AIS eventDB for eventType: ' + str(eventType) + ', storageMediumID: ' + str(storageMediumID) + ', error: ' + str(errno) + ', why: ' + Check().unicode2isostr(why))
                return 21
        return 0

class mail():
    ###############################################
    # sendmail
    def send(self,sender_address,recipient_address,subject,msg_text,msg_html=None,smtp_server=None,smtp_port=25,smtp_timeout=60):
        # Create message container - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender_address
        msg['To'] = recipient_address

        # Create the body of the message (a plain-text and an HTML version).
        #msg_text = "Hi!\nHow are you?\nHere is the link you wanted:\nhttp://www.python.org"
        #msg_html = """\
        #<html>
        #  <head></head>
        #  <body>
        #    <p>Hi!<br>
        #       How are you?<br>
        #       Here is the <a href="http://www.python.org">link</a> you wanted.
        #    </p>
        #  </body>
        #</html>
        #"""

        # Record the MIME types of both parts - text/plain and text/html.
        part1 = MIMEText(msg_text, 'plain', 'utf-8')
        if msg_html:
            part2 = MIMEText(msg_html, 'html', 'utf-8')

        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        msg.attach(part1)
        if msg_html:
            msg.attach(part2)

        # Send the message via local SMTP server.
        if smtp_server:
            s = smtplib.SMTP(host=smtp_server,port=smtp_port,timeout=smtp_timeout)
        else:
            s = smtplib.SMTP(timeout=smtp_timeout)
        # sendmail function takes 3 arguments: sender's address, recipient's address
        # and message to send - here it is sent as one string.
        s.sendmail(sender_address, recipient_address, msg.as_string())
        s.quit()

class writer():
    ###############################################
#    @classmethod
#    def open(cls):
    def open(self,packagefile,mode,blksize):
                    errno=0
                    why=''
                    self.packageobject=''
                    try:  #Open packagefile
                        self.packageobject = tarfile.open(name=packagefile,mode=mode,bufsize=512 * int(blksize))
                    except (ValueError,OSError,IOError, tarfile.TarError), (errno, why):
                        if Debug: print 'Failed to open tarfile',why
                    else:
                        if Debug: print 'Succeed to open tarfile'
                    return errno,why,self.packageobject
#    @classmethod
    def addfile(self,packageobject,sourcefile,archfile):
                    errno=0
                    why=''
                    try:  #Add sourcefile/archfile to packageobject
                        tarinfo = packageobject.gettarinfo(sourcefile, archfile)
                        packageobject.addfile(tarinfo, file(sourcefile))
                    except (ValueError,OSError, tarfile.TarError), (errno, why):
                        if Debug: print 'Failed to add files to tarfile'
                    else:
                        if Debug: print 'Succeed to add files to tarfile'
                    return errno,why
#    @classmethod
    def close(self,packageobject):
                    errno=0
                    why=''
                    try:  #Close packageobject
                        packageobject.close()#Close tapedevice
                    except (ValueError,OSError, tarfile.TarError), (errno, why):
                        if Debug: print 'Failed to close tarfile'
                    else:
                        if Debug: print 'Succeed to close tarfile'
                    return errno,why

    def hardclose(self,packageobject):
                    errno=0
                    why=''
                    try:  #HardClose packageobject
                        packageobject.hardclose()#Close tapedevice
                    except (ValueError,OSError, tarfile.TarError), (errno, why):
                        if Debug: print 'Failed to close tarfile'
                    else:
                        if Debug: print 'Succeed to close tarfile'
                    return errno,why

    def subtar(self,packagefile,blksize,workdir,SIPfile,Metafile,AICObjectFILE=None):
        errno=0
        why=''
        # Tar write tape
        if AICObjectFILE == None:
            self.cmd = subprocess.Popen(["tar","-b",str(blksize),"-c","-v","-f",str(packagefile),str(Metafile),str(SIPfile)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir)
        else:
            self.cmd = subprocess.Popen(["tar","-b",str(blksize),"-c","-v","-f",str(packagefile),str(Metafile),str(AICObjectFILE),str(SIPfile)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=workdir)
        self.tarout = self.cmd.communicate()
        if self.cmd.returncode == 0:
            if Debug: logging.info('Succeed to write files to tape, stdout: ' + str(self.tarout[0]) + ' stderr: ' + str(self.tarout[0]) + ' exitcode: ' + str(self.cmd.returncode))
        else:
            if Debug: logging.error('Problem to write files to tape, stdout: ' + str(self.tarout[0]) + ' stderr: ' + str(self.tarout[0]) + ' exitcode: ' + str(self.cmd.returncode))
        return self.cmd.returncode,self.tarout[0],self.tarout[1]





#c1packageobject=writer().open('/tmp/test1.tar','w','128')
#if c1packageobject[0]==0: print writer().addfile(c1packageobject[2],'/tmp/ESSPGM_Check.log','ESSPGM_Check.log')
#if c1packageobject[0]==0: print writer().close(c1packageobject[2])


#svardb().ArchObjUpd(a_obj='C0000556',a_num='164',t_id='GSU001')
#Robot().Inventory()
#Robot().GetVolserDB()
#Robot().Mount('LT0500')
#Robot().Unmount('JU0001',0)
#Robot().Unmount('FB2001',1)
#Robot().MTFilenum('/dev/nst0')
#Robot().TapeImport('prj1','/ESSArch/bin/db_data/JU0001.txt')
#Robot().MountWritePos2(t_type='304',t_block='512',t_format='1',t_prefix='FB1',t_location='IT_GLOBEN')
#Robot().MountWritePos2(t_type='304',t_block='512',t_format='1',t_prefix='FB2',t_location='IT_GLOBEN')
#APL().action('1','Start')
#print Check().checksum('/work/GSU_tapedir/C0001266.tar')

#Check().AIPextract('FB1002',object='00063221',delete=0)
#Check().AIPextract('FOA002', prefix='FOA')
#Check().AIPextract('FB1002',complete=1)
#Check().AIPextract('TSA002', prefix='TSA')

#print 'getFileSizeRES:',Check().getFileSizeRES('/ESSArch/bin/src/testdata/X0000001/TIFFEdit.RES')
#print 'getSEPathRES:',Check().getSEPathRES('/ESSArch/bin/src/testdata/X0000001/TIFFEdit.RES')
#print 'getFileSizeTAR:',Check().getFileSizeTAR('/store/SIP/X0000001.tar')
#getFileSizeRES: ([9, 160194908], 0, '')
#getSEPathRES: ('SE/RA/83002/2005/23', 0, '')
#getFileSizeTAR: ([10, 160197667], 0, '')

#Copy2HSM().copypackage2hsm('prj1','189')
#Check().CompleteVerifyTapeStandalone(t_id='JU0129',mount=1)
#PROC().action('Start','db_sync_ais')
#PROC().action('Start','RemoveSIP')
#PROC().action('Kill','AIPWriter')
#print 'result', ExtPrjDB().taped('00064142','419','6186904336','2008-05-21','17:51:25','FOB001','FOA001','1','1')
# eventType,eventDetail,eventApplication,eventVersion,eventOutcome,eventOutcomeDetailNote,ObjectIdentifierValue=None,storageMediumID=None,eventDateTime=None,linkingAgentIdentifierValue=None,storageMediumLocation=None,storageMediumDestination=None,RelatedEventIdentifierValue=None
#Events().create('10','test','ESSArch Ingest','2.12','0','Lyckades ta emot objekt X0000001','X0000001')

#print Events().create('1025','','ESSArch SIPValidateFormat','2.1.0','1','''Problem to get object_list from premis for information package: A0007600, errno: 20, detail: Error reading file '/IngestPath/A0007600/A0007600_PREMIS.xml': failed to load external entity "/IngestPath/A0007600/A0007600_PREMIS.xml"''','A0007600')
#Events().create('30','test','ESSArch Ingest','2.12','0','Flyttade band RA0001',storageMediumID='RA0001')
#Events().uuid_test()
#print Check().PREMISformat2MIMEtype('XML')
#Check().CleanRES_SIP()
#print Check().GetFiletree()
#print DB().GetAIC('003e3304-ae7b-11e1-a253-002215836551')
#print DB().GetIPs('f01e4796-9f4a-11e1-880b-002215836551')
#Check().Create_IP_package(ObjectIdentifierValue='test123', ObjectPath='/tmp/test123', Package_ObjectPath='/tmp/testobject123.tar', METS_ObjectPath='/tmp/test123/sip.xml')
#print Check().DiffCheck_IP(ObjectIdentifierValue='test123', ObjectPath='/tmp/test123', METS_ObjectPath='/tmp/test123/sip.xml')


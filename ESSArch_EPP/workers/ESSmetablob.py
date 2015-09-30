#!/usr/bin/env /ESSArch/pd/python/bin/python
# coding: iso-8859-1
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
import sys, ESSDB, ESSMSSQL, uuid, datetime, ESSMD, MySQLdb, ftplib, socket, os, pytz
from lxml import etree
from django.utils import timezone
from essarch.models import ArchiveObjectMetadata, ArchiveObject

MD_FTP_USER = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_USER'))[0][0]
MD_FTP_PASS = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_PASS'))[0][0]
MD_FTP_HOST = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_HOST'))[0][0]
MD_FTP_PORT = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_PORT'))[0][0]
MD_FTP_ROOT_PATH = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_ROOT_PATH'))[0][0]
MD_FTP_ROOT_KEY = ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','MD_FTP_ROOT_KEY'))[0][0]

class prod:
    TimeZone = timezone.get_default_timezone_name()
    tz=pytz.timezone(TimeZone)
    ###############################################
    def StoreMetadataBlob(self,ObjectUUID,ObjectIdentifierValue,ObjectMetadataType,AgentIdentifierValue,FTPflag=0,DBflag=0,DOC=None,FILENAME=None,FTPFileName=None):
        #ObjectMetadataType = 25   #ADDML-data
        #ObjectMetadataType = 26   #METS-data
        #ObjectMetadataType = 27   #PREMIS-data
        #ObjectMetadataType = 28   #RES-data

        #return res,errno,why
        #errno 0  = OK
        #errno 10 = file read error
        #errno 30 = Filename and DOC variable not present
        #errno 40 = Problem to update local DB
        #errno 41 = Problem to update ext DB
        #errno 42 = Problem to update local DB with ExtDBdatetime
        #errno 50 = Problem to FTPput

        #DOC = open('/ESSArch/bin/src/testdata/X0000001_METS.xml','rb').read()
        #DOC = open('/store/SIP/X0000001.RES','rb').read()
        if FILENAME:
            try:
                DOC = open(FILENAME,'rb').read()
            except IOError, why:
                return '',10,str(why)
        elif not DOC:
            return '',30,'Missing DOC var'
        
        #self.table = 'IngestObjectMetadata'
        ExtDBupdate = int(ESSDB.DB().action('ESSConfig','GET',('Value',),('Name','ExtDBupdate'))[0][0])

        if FTPflag: 
            self.ftp_res,errno,why = prod().FTPput(ObjectIdentifierValue=ObjectIdentifierValue,FileName=FILENAME,FTPFileName=FTPFileName)
            if errno: return '',50,'errno: %s, why: %s' % (str(errno),str(why)) 
            
        if DBflag:
            #print 'DOC',DOC 
            blob = MySQLdb.escape_string(DOC)
            #print 'blobStart#%s#END' % blob
            blob_mssql = ESSMSSQL.escape_string(DOC)
            #print 'blob_MSSQL2 Start#%s#END' % blob_mssql
        
        if FTPflag and DBflag:
            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
            ArchiveObject_obj = ArchiveObject.objects.get(ObjectUUID = ObjectUUID)
            ArchiveObjectMetadata_obj = ArchiveObjectMetadata()
            ArchiveObjectMetadata_obj.ObjectUUID = ArchiveObject_obj
            ArchiveObjectMetadata_obj.ObjectIdentifierValue = ObjectIdentifierValue
            ArchiveObjectMetadata_obj.ObjectMetadataType = ObjectMetadataType
            ArchiveObjectMetadata_obj.ObjectMetadataServer = self.ftp_res[0]
            ArchiveObjectMetadata_obj.ObjectMetadataURL = self.ftp_res[1]
            ArchiveObjectMetadata_obj.ObjectMetadataBLOB = blob
            ArchiveObjectMetadata_obj.linkingAgentIdentifierValue = AgentIdentifierValue
            ArchiveObjectMetadata_obj.LocalDBdatetime = self.timestamp_utc
            ArchiveObjectMetadata_obj.save()       
#            res,errno,why =  ESSDB.DB().action('IngestObjectMetadata','INS',('ObjectUUID',ObjectUUID,
#                                                                 'ObjectIdentifierValue',ObjectIdentifierValue,
#                                                                 'ObjectMetadataType',ObjectMetadataType,
#                                                                 'ObjectMetadataServer',self.ftp_res[0],
#                                                                 'ObjectMetadataURL',self.ftp_res[1],
#                                                                 'ObjectMetadataBLOB',blob,
#                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
#                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#            if errno: return '',40,'errno: %s, why: %s' % (str(errno),str(why))
#            if errno == 0 and ExtDBupdate:
            if ExtDBupdate:
                ext_res,ext_errno,ext_why =  ESSMSSQL.DB().action('IngestObjectMetadata','INS',('ObjectIdentifierValue',ObjectIdentifierValue,
                                                                                    'ObjectMetadataType',ObjectMetadataType,
                                                                                    'ObjectMetadataServer',self.ftp_res[0],
                                                                                    'ObjectMetadataURL',self.ftp_res[1],
                                                                                    'ObjectMetadataBLOB',blob_mssql,
                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue))
                if ext_errno: return '',41,'errno: %s, why: %s' % (str(ext_errno),str(ext_why))
                else:
                    ArchiveObjectMetadata_obj.ExtDBdatetime = self.timestamp_utc
                    ArchiveObjectMetadata_obj.save()
#                    res,errno,why = ESSDB.DB().action('IngestObjectMetadata','UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectUUID',ObjectUUID,'AND',
#                                                                                                         'ObjectIdentifierValue',ObjectIdentifierValue,'AND',
#                                                                                                         'ObjectMetadataType',ObjectMetadataType,'AND',
#                                                                                                         'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                    if errno: return '',42,'errno: %s, why: %s' % (str(errno),str(why))
        elif DBflag and not FTPflag:
            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
            ArchiveObject_obj = ArchiveObject.objects.get(ObjectUUID = ObjectUUID)
            ArchiveObjectMetadata_obj = ArchiveObjectMetadata()
            ArchiveObjectMetadata_obj.ObjectUUID = ArchiveObject_obj
            ArchiveObjectMetadata_obj.ObjectIdentifierValue = ObjectIdentifierValue
            ArchiveObjectMetadata_obj.ObjectMetadataType = ObjectMetadataType
            ArchiveObjectMetadata_obj.ObjectMetadataBLOB = blob
            ArchiveObjectMetadata_obj.linkingAgentIdentifierValue = AgentIdentifierValue
            ArchiveObjectMetadata_obj.LocalDBdatetime = self.timestamp_utc
            ArchiveObjectMetadata_obj.save()  
#            res,errno,why =  ESSDB.DB().action('IngestObjectMetadata','INS',('ObjectUUID',ObjectUUID,
#                                                                 'ObjectIdentifierValue',ObjectIdentifierValue,
#                                                                 'ObjectMetadataType',ObjectMetadataType,
#                                                                 'ObjectMetadataBLOB',blob,
#                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
#                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#            if errno: return '',40,'errno: %s, why: %s' % (str(errno),str(why)) 
#            if errno == 0 and ExtDBupdate:
            if ExtDBupdate:
                ext_res,ext_errno,ext_why =  ESSMSSQL.DB().action('IngestObjectMetadata','INS',('ObjectIdentifierValue',ObjectIdentifierValue,
                                                                                    'ObjectMetadataType',ObjectMetadataType,
                                                                                    'ObjectMetadataBLOB',blob_mssql,
                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue))
                if ext_errno: return '',41,'errno: %s, why: %s' % (str(ext_errno),str(ext_why))
                else:
                    ArchiveObjectMetadata_obj.ExtDBdatetime = self.timestamp_utc
                    ArchiveObjectMetadata_obj.save()
#                    res,errno,why = ESSDB.DB().action('IngestObjectMetadata','UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectUUID',ObjectUUID,'AND',
#                                                                                                         'ObjectIdentifierValue',ObjectIdentifierValue,'AND',
#                                                                                                         'ObjectMetadataType',ObjectMetadataType,'AND',
#                                                                                                         'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                    if errno: return '',42,'errno: %s, why: %s' % (str(errno),str(why))

        elif FTPflag and not DBflag:
            self.timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            self.timestamp_dst = self.timestamp_utc.astimezone(self.tz)
            ArchiveObject_obj = ArchiveObject.objects.get(ObjectUUID = ObjectUUID)
            ArchiveObjectMetadata_obj = ArchiveObjectMetadata()
            ArchiveObjectMetadata_obj.ObjectUUID = ArchiveObject_obj
            ArchiveObjectMetadata_obj.ObjectIdentifierValue = ObjectIdentifierValue
            ArchiveObjectMetadata_obj.ObjectMetadataType = ObjectMetadataType
            ArchiveObjectMetadata_obj.ObjectMetadataServer = self.ftp_res[0]
            ArchiveObjectMetadata_obj.ObjectMetadataURL = self.ftp_res[1]
            ArchiveObjectMetadata_obj.linkingAgentIdentifierValue = AgentIdentifierValue
            ArchiveObjectMetadata_obj.LocalDBdatetime = self.timestamp_utc
            ArchiveObjectMetadata_obj.save()  
#            res,errno,why =  ESSDB.DB().action('IngestObjectMetadata','INS',('ObjectUUID',ObjectUUID,
#                                                                 'ObjectIdentifierValue',ObjectIdentifierValue,
#                                                                 'ObjectMetadataType',ObjectMetadataType,
#                                                                 'ObjectMetadataServer',self.ftp_res[0],
#                                                                 'ObjectMetadataURL',self.ftp_res[1],
#                                                                 'linkingAgentIdentifierValue',AgentIdentifierValue,
#                                                                 'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#            if errno: return '',40,'errno: %s, why: %s' % (str(errno),str(why))
#            if errno == 0 and ExtDBupdate:
            if ExtDBupdate:
                ext_res,ext_errno,ext_why =  ESSMSSQL.DB().action('IngestObjectMetadata','INS',('ObjectIdentifierValue',ObjectIdentifierValue,
                                                                                    'ObjectMetadataType',ObjectMetadataType,
                                                                                    'ObjectMetadataServer',self.ftp_res[0],
                                                                                    'ObjectMetadataURL',self.ftp_res[1],
                                                                                    'linkingAgentIdentifierValue',AgentIdentifierValue))
                if ext_errno: return '',41,'errno: %s, why: %s' % (str(ext_errno),str(ext_why))
                else:
                    ArchiveObjectMetadata_obj.ExtDBdatetime = self.timestamp_utc
                    ArchiveObjectMetadata_obj.save()
#                    res,errno,why = ESSDB.DB().action('IngestObjectMetadata','UPD',('ExtDBdatetime',self.timestamp_utc.replace(tzinfo=None)),('ObjectUUID',ObjectUUID,'AND',
#                                                                                                         'ObjectIdentifierValue',ObjectIdentifierValue,'AND',
#                                                                                                         'ObjectMetadataType',ObjectMetadataType,'AND',
#                                                                                                         'LocalDBdatetime',self.timestamp_utc.replace(tzinfo=None)))
#                    if errno: return '',42,'errno: %s, why: %s' % (str(errno),str(why))

        return '',0,''

    ###############################################
    def FTPput(self,ObjectIdentifierValue,FileName,FileObject=None,FTPFileName=None):
        if FTPFileName is None:
            self.FTPFileName = FileName.lstrip(os.sep)
        else:
            self.FTPFileName = FTPFileName.lstrip(os.sep)
        self.URL_PATH = os.path.join(os.path.join(ObjectIdentifierValue[:4],ObjectIdentifierValue),self.FTPFileName)
        self.PATHhead = os.path.join(MD_FTP_ROOT_PATH,os.path.split(self.URL_PATH)[0])
        self.PATHhead_list = self.PATHhead.split(os.sep)
        self.MD_FTP_ROOT_KEY = MD_FTP_ROOT_KEY
        self.FileBaseName = os.path.basename(self.FTPFileName)
        self.FileObject = FileObject
        if FileName and not self.FileObject:
            try:
                self.FileObject = open(FileName,'rb')
            except IOError, why:
                return None,10,str(why)
        else:
            return None,30,'Missing FileName var'
        try:
            self.ftp = ftplib.FTP()
            self.ftp.set_debuglevel(0)
            self.ftp.connect(host=MD_FTP_HOST,port=MD_FTP_PORT,timeout=60)
            self.ftp.login(user=MD_FTP_USER,passwd=MD_FTP_PASS)
            #self.ftp.set_pasv(1)
            self.cwd_path = unicode(os.sep)
            for self.cwd_item in self.PATHhead_list:
                self.cwd_path = os.path.join(self.cwd_path,self.cwd_item)
                try:
                    self.ftp.cwd(self.cwd_path)
                except ftplib.error_perm, why:
                    self.ftp.mkd(self.cwd_path)
            try:
                self.ftp.cwd(self.cwd_path)
            except ftplib.error_perm, why:
                return None,50,str(why)
            self.command = 'STOR %s' % self.FileBaseName
            self.ftp.storbinary(self.command,self.FileObject)
            self.ftp.quit()
        except socket.error, why:
            return None,20,str(why)
        except ftplib.all_errors, why:
            return None,40,str(why)
        else:
            self.res = [int(self.MD_FTP_ROOT_KEY),self.URL_PATH]
            return self.res,0,''

class test:
    ###############################################
    def text2blob(self):
        #DOC,errno,why = ESSMETS.parseMetsFromFile('/ESSArch/bin/src/testdata/X0000001_METS.xml')
        DOC,errno,why = ESSMD.parseFromFile('/ESSArch/bin/src/testdata/X0000001_METS.xml')
        if errno:
            print why
        METSstr = etree.tostring(DOC,encoding='UTF-8', xml_declaration=True, pretty_print=True)
        blob = MySQLdb.escape_string(METSstr)
        print 'METSstr',METSstr
        print 'blob',blob
        #self.table = 'IngestObjectMetadata'
        ArchiveObjectMetadata_obj = ArchiveObjectMetadata()
        ArchiveObjectMetadata_obj.ObjectIdentifierValue = ObjectIdentifierValue
        ArchiveObjectMetadata_obj.ObjectMetadataType = 26
        ArchiveObjectMetadata_obj.ObjectMetadataBLOB = blob
        ArchiveObjectMetadata_obj.save() 
#        res,errno,why =  ESSDB.DB().action('IngestObjectMetadata','INS',('ObjectIdentifierValue','test123','ObjectMetadataType',26,'ObjectMetadataBLOB',blob))
#        if errno:
#            print 'why',why

    ###############################################
    def blob2text(self):
        #self.table = 'IngestObjectMetadata'
        res,errno,why =  ESSDB.DB().action('IngestObjectMetadata','GET3',('ObjectIdentifierValue','ObjectMetadataType','ObjectMetadataBLOB'),('id',9))
        if errno:
            print 'why',why
        print res[0][2]
        file = open('/ESSArch/bin/src/testdata/X0000003_MySQL.res','wb')
        file.write(res[0][2])
        file.close()


        #self.table = 'IngestObjectMetadata'
        res,errno,why =  ESSMSSQL.DB().action('IngestObjectMetadata','GET3',('ObjectIdentifierValue','ObjectMetadataType','ObjectMetadataBLOB'),('ObjectIdentifierValue','X0000003','AND','ObjectMetadataType',28))
        if errno:
            print 'why',why
        for i in res:
            print i[2]
        file = open('/ESSArch/bin/src/testdata/X0000003_MsSQL.res','wb')
        file.write(res[0][2])
        file.close()

    ###############################################
    def blob2ftp(self):
        AgentIdentifierValue = 'ESSArch_Marieberg'
        self.table = 'IngestObjectMetadata_old'
        res,errno,why = ESSDB.DB().action(self.table,'GET4',('id',),('ObjectMetadataServer','IS','NULL'))
        if errno:
            print 'Error: why',why
        else:
            print 'Found all metadataobject id (number: %s), res: %s' % (str(len(res)),str(res))
            for i in res:
                IngestObjectMetadata_row,errno,why = ESSDB.DB().action(self.table,'GET4',('id','ObjectUUID','ObjectIdentifierValue','ObjectMetadataBLOB'),('id','=',i[0]))
                if errno:
                    print 'Error1: why',why
                else:
                    Cmets_objpath = '/store/metablob/%s_Content_METS.xml' % str(IngestObjectMetadata_row[0][2])
                    print ('Store blob for rowid: %s object: %s to filename: %s') % (str(IngestObjectMetadata_row[0][0]),str(IngestObjectMetadata_row[0][2]),Cmets_objpath)
                    file = open(Cmets_objpath,'wb')
                    file.write(IngestObjectMetadata_row[0][3])
                    file.close()
                    res,errno,why = prod().StoreMetadataBlob(ObjectUUID=IngestObjectMetadata_row[0][1],
                                                         ObjectIdentifierValue=IngestObjectMetadata_row[0][2],
                                                         ObjectMetadataType=26,
                                                         FILENAME=Cmets_objpath,
                                                         FTPflag=1,
                                                         DBflag=0,
                                                         AgentIdentifierValue=AgentIdentifierValue)
                    if errno:
                        print 'Error2: why',why

#######################################################################################################
# Dep:
#######################################################################################################
if __name__ == '__main__':
    Debug=0
    ProcName = 'ESSmetablob'
    ProcVersion = __version__
    if len(sys.argv) > 1:
        if sys.argv[1] == '-d': Debug=1
        if sys.argv[1] == '-v' or sys.argv[1] == '-V':
            print ProcName,'Version',ProcVersion
            sys.exit()
    #test().text2blob()
    #test().blob2text()
    example_uuid = uuid.uuid1()
    res,errno,why = prod().StoreMetadataBlob(ObjectUUID=example_uuid,ObjectIdentifierValue='00009091',ObjectMetadataType=26,FILENAME='/home/arch/eARD_SIP/A0007600/sip.xml',FTPFileName='Q0000000/Q0000000_Content_METS.xml',FTPflag=1,DBflag=0,AgentIdentifierValue='ESSArch_Marieberg')
    #res,errno,why = test().FTPput(ObjectIdentifierValue='00009091',FileName='/store/TmpWorkDir/00009091_Content_METS.xml')
    #print 'res: %s, errno: %s, why: %s' % (str(res),str(errno),str(why))
    
    #print ('res: %s, errno: %s, why: %s') % (res,errno,why)
    #print ('errno: %s') % (errno)
    #test().blob2ftp()

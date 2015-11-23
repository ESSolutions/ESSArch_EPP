#!/usr/bin/env /ESSArch/python27/bin/python
# -*- coding: UTF-8 -*-
'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB

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

# own models etc
from configuration.models import Parameter, SchemaProfile, IPParameter, Path, ESSConfig, ESSProc, DefaultValue, ArchivePolicy, StorageMethod, StorageTarget, StorageTargets 
from essarch.models import eventType_codes, robotdrives, ArchiveObject, ArchiveObjectRel
from Storage.models import storage, storageMedium, IOQueue
from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType

import sys,datetime,os

import django
django.setup()

# settings
site_profile = "EC" # SE_NEW, SE, NO, EC
site_name = u'EARK' # Project E-ARK 
medium_location = u'Media_%s' % site_name # IT_EARK 
install_site = u'ESSArch_%s' % site_name 

def installdefaultpaths(): # default paths
    
    # First remove all existing data 
    Path.objects.all().delete()

    # create dictionaries for different site profile
    dct = {
          'path_reception':'/ESSArch/exchange/ingest/media',
          'path_gate':'/ESSArch/exchange/gate',
          'path_work':'/ESSArch/exchange/work',
          'path_control':'/ESSArch/exchange/control',
          'path_ingest':'/ESSArch/exchange/control/ingest',
          'path_mimetypesdefinition':'/ESSArch/Tools/env/data',
          }

    # create according to model with two fields
    for key in dct :
        print >> sys.stderr, "**", key
        try:
            le = Path( entity=key, value=dct[key] )
            le.save()
        except:
            pass
    
    return 0 
    
def installdefaultschemaprofiles(): # default schema profiles for site profile
    
    # First remove all existing data 
    SchemaProfile.objects.all().delete()

    dct = {
          'addml_namespace':'http://xml.ra.se/addml',
          'addml_schemalocation':'http://xml.ra.se/addml/ra_addml.xsd',
          'erms_schemalocation':'http://xml.ra.se/e-arkiv/ERMS/version10/Arendehantering.xsd',
          'mets_namespace': 'http://www.loc.gov/METS/',
          'mets_profile': 'http://www.ra.ee/METS/v01/SIP.xml',
          'mets_schemalocation': 'http://www.ra.ee/METS/v01/SIP.xsd',
          'mix_namespace':'http://xml.ra.se/MIX',
          'mix_schemalocation':'http://xml.ra.se/MIX/RA_MIX.xsd',
          'mods_namespace':'http://www.loc.gov/mods/v3',
          'personnel_schemalocation':'http://xml.ra.se/e-arkiv/Personnel/version10/Personal.xsd',
          'premis_namespace':'http://xml.ra.se/PREMIS',
          'premis_schemalocation':'http://xml.ra.se/PREMIS/ESS/RA_PREMIS_PreVersion.xsd',
          'premis_version':'2.0',
          'xhtml_namespace':'http://www.w3.org/1999/xhtml',
          'xhtml_schemalocation':'http://www.w3.org/MarkUp/SCHEMA/xhtml11.xsd',
          'xlink_namespace':'http://www.w3.org/1999/xlink',
          'xsd_namespace':'http://www.w3.org/2001/XMLSchema',
          'xsi_namespace':'http://www.w3.org/2001/XMLSchema-instance',
          }

    # create according to model with two fields
    for key in dct :
        print >> sys.stderr, "**", key
        try:
            le = SchemaProfile( entity=key, value=dct[key] )
            le.save()
        except:
            pass
    
    return 0
######################
def installdefaulteventType_codes(): # default eventType_codes

    eventType_codes_list=((1000,u'Received the object for long-term preservation',u'',1,0),
                          (1010,u'Verifying object against archive information system',u'',1,0),
                          (1020,u'Verifying object against project database',u'',1,0),
                          (1022,u'RES2PREMIS converting',u'',1,0),
                          (1025,u'Verifying object format',u'',1,0),
                          (1030,u'Create AIP',u'',1,0),
                          (1040,u'Create checksum for IP',u'',1,0),
                          (1041,u'Calculate checksum',u'',1,0),
                          (1042,u'Verify checksum',u'',1,0),
                          (1043,u'Verify content',u'',1,0),
                          (1050,u'Verify AIP',u'',1,0),
                          (1060,u'Remove the source to the SIP',u'',1,0),
                          (1100,u'Write AIP to long term storage',u'',1,0),
                          (1101,u'I/O request',u'',1,0),
                          (1102,u'Writing data to disk storage method',u'',1,0),
                          (1103,u'Reading from the disk storage method',u'',1,0),
                          (1104,u'Writing data to tape storage method',u'',1,0),
                          (1105,u'Reading from the tape storage method',u'',1,0),
                          (1150,u'Remove the source to the AIP',u'',1,0),
                          (1200,u'Dissemination',u'',1,0),
                          (1201,u'DIP Order Request',u'',1,0),
                          (1202,u'DIP Order Accept',u'',1,0),
                          (1203,u'DIP Order Complete',u'',1,0),
                          (1210,u'Unpack object',u'',1,0),
                          (1301,u'Ingest Order Request',u'',1,0),
                          (1302,u'Ingest Order Accept',u'',1,0),
                          (1303,u'Ingest Order Complete',u'',1,0),
                          (2000,u'Mounting the tape in tapedrive in the robot',u'',1,0),
                          (2010,u'Dismounting the tape from tapedrive in the robot',u'',1,0),
                          (2090,u'Deactivate storage medium',u'',1,0),
                          (2201,u'Media quickverify Order Request',u'',1,0),
                          (2202,u'Media quickverify Order Accept',u'',1,0),
                          (2203,u'Media quickverify Order Complete',u'',1,0),
                          (10,u'StorageLogistics Levererad',u'',1,0),
                          (20,u'StorageLogistics Mottagen',u'',1,0),
                          (30,u'StorageLogistics Placerad',u'',1,0),
                          (40,u'StorageLogistics Uttagen',u'',1,0),
                          (30000,u'CheckInFromReception',u'',1,0),
                          (31000,u'CheckOutToWork',u'',1,0),
                          (32000,u'CheckInFromWork',u'',1,0),
                          (33000,u'DiffCheck',u'',1,0),
                          (34000,u'IngestIP',u'',1,0),
                          (35000,u'CheckOutToGateFromWork',u'',1,0),
                          (36000,u'Delete IP',u'',1,0),
    )
    for row in eventType_codes_list:
        if not eventType_codes.objects.filter(code=row[0]).exists():
            print "Adding entry to eventType_codes for %s" % str(row[0])
            eventType_codes_obj = eventType_codes()
            eventType_codes_obj.code=row[0]
            eventType_codes_obj.desc_sv=row[1]
            eventType_codes_obj.desc_en=row[2]
            eventType_codes_obj.localDB=row[3]
            eventType_codes_obj.externalDB=row[4]
            eventType_codes_obj.save()

######################
def installdefaultESSConfig(): # default ESSConfig

    ESSConfig_list=((u'IngestTable',u'IngestObject'),
                    (u'PolicyTable',u'configuration_archivepolicy'),
                    (u'StorageTable',u'storage'),
                    (u'RobotTable',u'robot'),
                    (u'RobotDrivesTable',u'robotdrives'),
                    (u'RobotIETable',u'robotie'),
                    (u'RobotReqTable',u'robotreq'),
                    (u'StorageMediumTable',u'storageMedium'),
                    (u'ExtPrjTapedURL',u''),
                    (u'verifydir',u'/ESSArch/verify'),
                    (u'AgentIdentifierValue',install_site),
                    (u'ExtDBupdate',u'0'),
                    (u'storageMediumLocation',medium_location),
                    (u'MD_FTP_USER',u'meta'),
                    (u'MD_FTP_PASS',u'meta123'),
                    (u'MD_FTP_HOST',u'127.0.0.1'),
                    (u'MD_FTP_PORT',u'2222'),
                    (u'MD_FTP_ROOT_PATH',u'/metadata1'),
                    (u'MD_FTP_ROOT_KEY',u'16'),
                    (u'Robotdev',u'/dev/sg5'),
                    (u'OS',u'FEDORA'),
                    (u'smtp_server',u''),
                    (u'email_from',u'e-archive@essarch.org'),
    )

    for row in ESSConfig_list:
        if not ESSConfig.objects.filter(Name=row[0]).exists():
            print "Adding entry to ESSConfig for %s" % str(row[0])
            ESSConfig_obj = ESSConfig()
            ESSConfig_obj.Name=row[0]
            ESSConfig_obj.Value=row[1]
            ESSConfig_obj.save()

def installdefaultrobotdrives(): # default robotdrives

    robotdrives_list=((0,u'',0,u'Ready',0,u'/dev/nst0',u'IBM_LTO4',u'sn00001',u'fw0001',u'',0),
                      (1,u'',0,u'Ready',0,u'/dev/nst1',u'IBM_LTO4',u'sn00002',u'fw0001',u'',0),
    )
    for row in robotdrives_list:
        if not robotdrives.objects.filter(drive_id=row[0]).exists():
            print "Adding entry to robotdrives for %s" % str(row[0])
            robotdrives_obj = robotdrives()
            robotdrives_obj.drive_id=row[0]
            robotdrives_obj.t_id=row[1]
            robotdrives_obj.slot_id=row[2]
            robotdrives_obj.status=row[3]
            robotdrives_obj.num_mounts=row[4]
            robotdrives_obj.drive_dev=row[5]
            robotdrives_obj.drive_type=row[6]
            robotdrives_obj.drive_serial=row[7]
            robotdrives_obj.drive_firmware=row[8]
            robotdrives_obj.drive_lock=row[9]
            robotdrives_obj.IdleTime=row[10]
            robotdrives_obj.save()

def installdefaultArchivePolicy(): # default ArchivePolicy

    if not ArchivePolicy.objects.filter(id=u'70d0177ddeb7416c800349c2cdfdfdc7').exists():

        print "Adding test entry to ArchivePolicy..."
        ArchivePolicy_obj = ArchivePolicy()
        ArchivePolicy_obj.id=u'70d0177ddeb7416c800349c2cdfdfdc7'
        ArchivePolicy_obj.PolicyName=u'EARK policy 1'
        ArchivePolicy_obj.PolicyID=u'1'
        ArchivePolicy_obj.PolicyStat=u'1'
        ArchivePolicy_obj.AISProjectName=u''
        ArchivePolicy_obj.AISProjectID=u''
        ArchivePolicy_obj.Mode=u'0'
        ArchivePolicy_obj.WaitProjectApproval=u'2'
        ArchivePolicy_obj.ChecksumAlgorithm=u'2'
        ArchivePolicy_obj.ValidateChecksum=u'1'
        ArchivePolicy_obj.ValidateXML=u'1'
        ArchivePolicy_obj.ManualControll=u'0'
        ArchivePolicy_obj.AIPType=u'1'
        ArchivePolicy_obj.AIPpath=u'/ESSArch/essarch_temp'
        ArchivePolicy_obj.PreIngestMetadata=u'0'
        ArchivePolicy_obj.IngestMetadata=u'4'
        ArchivePolicy_obj.INFORMATIONCLASS=u'1'
        ArchivePolicy_obj.IngestPath=u'/ESSArch/exchange/control/ingest'
        ArchivePolicy_obj.IngestDelete=u'1'
        ArchivePolicy_obj.save()
        
    if not StorageMethod.objects.filter(id=u'caa8458a4c954b65affe8ae9867d7228').exists():

        print "Adding test entry to StorageMethod..."
        StorageMethod_obj = StorageMethod()
        StorageMethod_obj.id=u'caa8458a4c954b65affe8ae9867d7228'
        StorageMethod_obj.name=u'EARK policy 1 - SM 1'
        StorageMethod_obj.status=1
        StorageMethod_obj.type=200
        StorageMethod_obj.archivepolicy=ArchivePolicy.objects.get(id=u'70d0177ddeb7416c800349c2cdfdfdc7')
        StorageMethod_obj.save()

    if not StorageTargets.objects.filter(id=u'e55194eeb1ea4bf7b8c7494f4f2b0101').exists():

        print "Adding test entry to StorageTargets..."
        StorageTargets_obj = StorageTargets()
        StorageTargets_obj.id=u'e55194eeb1ea4bf7b8c7494f4f2b0101'
        StorageTargets_obj.name=u'disk1'
        StorageTargets_obj.status=1
        StorageTargets_obj.type=200
        StorageTargets_obj.format=103
        StorageTargets_obj.blocksize=1024
        StorageTargets_obj.maxCapacity=0
        StorageTargets_obj.minChunkSize=0
        StorageTargets_obj.minContainerSize=0
        StorageTargets_obj.minCapacityWarning=0
        StorageTargets_obj.target=u'/ESSArch/store/disk1'
        StorageTargets_obj.save()

    if not StorageTarget.objects.filter(id=u'79b902a9f00b4ac696b11fd5ad0f3ae1').exists():

        print "Adding test entry to StorageMethod - Target..."
        StorageTarget_obj = StorageTarget()
        StorageTarget_obj.id=u'79b902a9f00b4ac696b11fd5ad0f3ae1'
        StorageTarget_obj.name=u'EARK policy 1 - SM 1 - Target 1'
        StorageTarget_obj.status=1
        StorageTarget_obj.storagemethod=StorageMethod.objects.get(id=u'caa8458a4c954b65affe8ae9867d7228')
        StorageTarget_obj.target=StorageTargets.objects.get(id=u'e55194eeb1ea4bf7b8c7494f4f2b0101')
        StorageTarget_obj.save()

def installdefaultESSProc(): # default ESSProc
    workers_path = '/ESSArch/pd/python/lib/python2.7/site-packages/ESSArch_EPP/workers'
    ESSProc_list=(('1','SIPReceiver',os.path.join(workers_path, 'SIPReceiver.pyc'),'/ESSArch/log/SIPReceiver.log',1,30,0,0,0,0),
                   ('3','SIPValidateAIS',os.path.join(workers_path, 'SIPValidateAIS.pyc'),'/ESSArch/log/SIPValidateAIS.log',1,5,0,0,0,0),
                   ('4','SIPValidateApproval',os.path.join(workers_path, 'SIPValidateApproval.pyc'),'/ESSArch/log/SIPValidateApproval.log',1,5,0,0,0,0),
                   ('5','SIPValidateFormat',os.path.join(workers_path, 'SIPValidateFormat.pyc'),'/ESSArch/log/SIPValidateFormat.log',1,5,0,0,0,0),
                   ('6','AIPCreator',os.path.join(workers_path, 'AIPCreator.pyc'),'/ESSArch/log/AIPCreator.log',1,5,0,0,0,0),
                   ('7','AIPChecksum',os.path.join(workers_path, 'AIPChecksum.pyc'),'/ESSArch/log/AIPChecksum.log',1,5,0,0,0,0),
                   ('8','AIPValidate',os.path.join(workers_path, 'AIPValidate.pyc'),'/ESSArch/log/AIPValidate.log',1,5,0,0,0,0),
                   ('9','SIPRemove',os.path.join(workers_path, 'SIPRemove.pyc'),'/ESSArch/log/SIPRemove.log',1,5,0,0,0,0),
                   ('10','AIPWriter',os.path.join(workers_path, 'AIPWriter.pyc'),'/ESSArch/log/AIPWriter.log',1,15,0,0,0,0),
                   ('11','AIPPurge',os.path.join(workers_path, 'AIPPurge.pyc'),'/ESSArch/log/AIPPurge.log',1,5,0,0,0,0),
                   ('12','TLD',os.path.join(workers_path, 'TLD.pyc'),'/ESSArch/log/TLD.log',2,5,0,0,0,0),
                   #('13','IOEngine',os.path.join(workers_path, 'IOEngine.pyc'),'/ESSArch/log/IOEngine.log',8,5,0,0,0,0),
                   ('14','db_sync_ais',os.path.join(workers_path, 'db_sync_ais.pyc'),'/ESSArch/log/db_sync_ais.log',1,10,0,0,0,0),
                   ('16','ESSlogging',os.path.join(workers_path, 'ESSlogging.pyc'),'/ESSArch/log/ESSlogging.log',2,5,0,0,0,0),
                   ('17','AccessEngine',os.path.join(workers_path, 'AccessEngine.pyc'),'/ESSArch/log/AccessEngine.log',3,5,0,0,0,0),
                   ('18','FTPServer',os.path.join(workers_path, 'FTPServer.pyc'),'/ESSArch/log/FTPServer.log',2,5,0,0,0,0),
    )
    for row in ESSProc_list:
        if not ESSProc.objects.filter(Name=row[1]).exists():
            print "Adding entry to ESSProc for %s" % str(row[1])
            ESSProc_obj = ESSProc()
            ESSProc_obj.id=row[0]
            ESSProc_obj.Name=row[1]
            ESSProc_obj.Path=row[2]
            ESSProc_obj.LogFile=row[3]
            ESSProc_obj.expected_pids=row[4]
            ESSProc_obj.Time=row[5]
            ESSProc_obj.Status=row[6]
            ESSProc_obj.Run=row[7]
            ESSProc_obj.PID=row[8]
            ESSProc_obj.Pause=row[9]
            ESSProc_obj.save()

def installdefaultdefaultvalues(): # default default values

    dct = {
           'administration_storagemigration__temp_path': '/ESSArch/essarch_temp',
           'administration_storagemigration__copy_path': '',
           'access_new__ReqType': '5',
           }

    # create according to model with two fields
    for key in dct :
        if not DefaultValue.objects.filter(entity=key).exists():
            print "Adding entry to DefaultValue for %s" % key
            le = DefaultValue( entity=key, value=dct[key] )
            le.save()
    return 0

def installdefaultparameters(): # default config parameters
    
    # First remove all data 
    Parameter.objects.all().delete()

    # set default parameters according to site profile
    dct = {
       'site_profile':site_profile,
       'zone': 'zone3' ,
       'templatefile_log': 'ipevents.xml' ,
       'templatefile_specification':'ip.xml',
       'package_descriptionfile':'info.xml',
       'content_descriptionfile':'ip.xml',
       'ip_logfile':'ipevents.xml',
       'preservation_descriptionfile':'metadata/premis.xml',
       }

    # create according to model with two fields
    for key in dct :
        print >> sys.stderr, "**", key
        try:
            le = Parameter( entity=key, value=dct[key] )
            le.save()
        except:
            pass
    
    # install default configuration
    createdefaultusers()             # default users, groups and permissions
    installdefaultpaths()            # default paths
    installdefaultschemaprofiles()   # default schema profiles for Sweden or Norway
    installdefaultdefaultvalues()    # default values
    installIPParameter()             # default metadata for IP
    installdefaulteventType_codes()  # default eventType_codes
    installdefaultESSConfig()        # default ESSConfig
    installdefaultrobotdrives()      # default robotdrives
    installdefaultArchivePolicy()    # default ArchivePolicy
    installdefaultESSProc()          # default ESSProc
    
    return 0


def installIPParameter():  # default metadata for IP
    
    # First remove all data 
    IPParameter.objects.all().delete()
    
    # create dictionary for IP elements
    dct = {
          'objid':'UUID:550e8400-e29b-41d4-a716-446655440004',
          'label':'Example of SIP for delivery of personel information',
          'type':'SIP',
          'createdate':'2012-04-26T12:45:00+01:00',
          'recordstatus':'NEW',
          'deliverytype':'ERMS',
          'deliveryspecification':'FGS Personal, version 1',
          'submissionagreement':'RA 13-2011/5329; 2012-04-12',
          'previoussubmissionagreement':'FM 12-2387/12726, 2007-09-19',
          'datasubmissionsession':'Submission, 2012-04-15 15:00',
          'packagenumber':'SIP Number 2938',
          'referencecode':'SE/RA/123456/24/P',
          'previousreferencecode':'SE/FM/123/123.1/123.1.3',
          'appraisal':'Yes',
          'accessrestrict':'Secrecy and PUL',
          'archivist_organization':'Government X',
          'archivist_organization_id':'ORG:2010340987',
          'archivist_organization_software':'HR Employed',
          'archivist_organization_software_id':'5.0.34',
          'creator_organization':'Government X, Dep Y',
          'creator_organization_id':'ORG:2010340987',
          'creator_individual':'Mike Oldfield',
          'creator_individual_details':'+46 (0)8-12 34 56, Mike.Oldfield@company.se',
          'creator_software':'Packageprogram Packager',
          'creator_software_id':'1.0',
          'editor_organization':'Consultancy Company',
          'editor_organization_id':'ORG:2020345987',
          'preservation_organization':'National Archives of X',
          'preservation_organization_id':'ORG:2010340987',
          'preservation_organization_software':'ESSArch',
          'preservation_organization_software_id':'3.0.0',
          'startdate':'2012-01-01', ## kkkk
          'enddate':'2012-12-30',
          'aic_id':'e4d025bc-56b0-11e2-893f-002215836551',
          'informationclass':'1',
          'projectname':'Scanning',
          'policyid':'1',
          'receipt_email':'Mike.Oldfield@company.se',
          'file_id':'ID550e8400-e29b-41d4-a716-4466554400bg', ## kkkk
          'file_name':'file:personalexport.xml',
          'file_createdate':'2012-04-20T13:30:00,+01:00',
          'file_mime_type':'text/xml',
          'file_format':'PDF/A',
          'file_format_size':'8765324',
          'file_type':'Delivery file',
          'file_checksum':'574b69cf71ceb5534c8a2547f5547d',
          'file_checksum_type':'SHA-256',
          'file_transform_type':'DES',
          'file_transform_key':'574b69cf71ceb5534c8a2547f5547d',
          }

    #print dict1.keys()
    #print dict1.values()
    #print dict1.items()
    #print tt3.items()
    
    #new_dict = {}
    #new_lst = []
    
    #new_dict.update(dict2)
    #new_dict.update(dict3)
    #print new_dict.items() 
    
    # create according to model with many fields
    IPParameter.objects.create(**dct)
    #IPMetadata.objects.create(**dct1)  # create from dictionary
    #IPMetadata.objects.filter(id=1).update(**dct1)  # update from dictionary

    return 0

if __name__ == '__main__':
    installdefaultparameters()

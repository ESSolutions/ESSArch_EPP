'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2015  ES Solutions AB

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
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from models import MyFile, RequestFile
from essarch.models import ArchiveObject, ObjectMetadata, ArchiveObjectData, ArchiveObjectRel, eventIdentifier, PackageType_CHOICES, StatusProcess_CHOICES, \
                           ControlAreaQueue, ControlAreaForm, ControlAreaForm2, ControlAreaForm_reception, \
                           ControlAreaForm_CheckInFromWork, ControlAreaForm_CheckoutToWork, \
                           ControlAreaReqType_CHOICES, ReqStatus_CHOICES, ControlAreaForm_file, \
                           eventOutcome_CHOICES, IngestQueue
from configuration.models import Path, Parameter, SchemaProfile, IPParameter, ChecksumAlgorithm_CHOICES, ESSConfig, DefaultValue
import shutil, errno, essarch.log as logtool, ESSPGM, datetime, tarfile, sys,logging
import ESSMD
import os
import os.path as op
import uuid
from ESSPGM import Check as g_functions
import pytz, logging
from optparse import OptionParser
from lxml import etree
from jobtastic import JobtasticTask
from time import sleep

#from __future__ import absolute_import
#from celery import shared_task


#TODO lobby in sweden and logs in Norway
#ioessarch = '%s/lobby' % Path.objects.get(entity='path_gate').value
#ioessarch = '%s/logs' % Path.objects.get(entity='path_gate').value
ioessarch = Path.objects.get(entity='path_gate_reception').value

logger = logging.getLogger('essarch.controlarea')

class CheckInFromMottagTask(JobtasticTask):

    significant_kwargs = []

    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400
    def calculate_result(self,
                        source_path=None,
                        target_path=None,
                        Package=None,
                        ObjectIdentifierValue=None,
                        ReqUUID=None,
                        ReqPurpose=None,
                        creator=None,
                        system=None,
                        version=None,
                        agent_list=[],
                        altRecordID_list=[],
                        allow_unknown_filetypes=False,
                        linkingAgentIdentifierValue=None,
                        ):
        status_code = 0
        status_list = []
        error_list = []
        Pmets_obj = Parameter.objects.get(entity='package_descriptionfile').value
        Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
        premis_obj = Parameter.objects.get(entity='preservation_descriptionfile').value
        ip_logfile = Parameter.objects.get(entity='ip_logfile').value
        
        if status_code == 0:
            # Try to find filename for logfile with matching creator, system and version.
            logfilepath = ''
            return_code,status,file_list = logtool.get_logxml_filename(ObjectIdentifierValue=ObjectIdentifierValue,
                                                                       creator=creator,
                                                                       system=system,
                                                                       version=version,
                                                                       path=ioessarch)
            if return_code == 0:
                if len(file_list) == 1:
                    logfilepath = os.path.join(ioessarch,file_list[0])
                    event_info = 'Found logfile: %s for package: %s' % (logfilepath,Package)
                    status_list.append(event_info)
                    logger.info(event_info)
                elif len(file_list) > 1:
                    status_code = 1
                    event_info = 'ObjectIdentifierValue: %s match more then one logfile, logfilelist: %s' % (ObjectIdentifierValue,str(file_list))
                    error_list.append(event_info)
                    logger.error(event_info)
                else:
                    status_code = 2
                    event_info = 'ObjectIdentifierValue: %s do not match any logfile' % (ObjectIdentifierValue)
                    error_list.append(event_info)
                    logger.error(event_info)
            else:
                status_code = 9
                error_list.append('Status: %s, Error: %s' % (return_code,str(status))) 

        if status_code == 0:
            # Try to get IP_uuid and AIC_uuid from logfile
            return_code,status,info_entrys =  logtool.get_logxml_info(logfilepath)
            if return_code == 0:
                for i in info_entrys[0]:
                    IP_uuid = i[1]
                    for x in i[2]:
                        if x[0] == 'aic_object':
                            AIC_uuid = x[1]
                for i in info_entrys[1]:
                    pass
                    #print '------------------------------------------------------------------------'
                    #print 'EventIndentifierValue: %s, EventType: %s, EventDateTime: %s, eventDetail: %s, outcome: %s, outcomeDetail: %s, linkingObject: %s' % (i[1],i[2],i[3],i[4],i[5],i[6],i[10])
            else:
                status_code = 3
                event_info = 'Status: %s, Error: %s' % (return_code,str(status))
                error_list.append(event_info)
                logger.error(event_info)

        if status_code == 0:
            # Check if IP_uuid already exist in database.
            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid).exists()
            if ArchiveObject_qf is True:
                status_code = 6
                event_info = 'Entry in DB for IP_UUID: %s already exist, abort checkin.' % (IP_uuid)
                error_list.append(event_info)
                logger.info(event_info)
        if status_code == 0:
            # Copy AIC/IP structure from ioessarch to mottag area.
            aic_source_path = os.path.join(ioessarch,AIC_uuid)
            aic_target_path = os.path.join(target_path,AIC_uuid)
            try:
                event_info = 'Copy package structure %s to %s' % (aic_source_path,aic_target_path)
                status_list.append(event_info)
                logger.info(event_info)
                shutil.copytree(aic_source_path,aic_target_path)
                # After copy AIC/ip structure remove info.xml metsfile
                old_mets_filepath = op.join( aic_target_path, Pmets_obj )
                if op.exists(old_mets_filepath):
                    os.remove(old_mets_filepath)
            except (IOError, os.error), why:
                status_code = 4
                event_info = 'Problem to copy package structure %s to %s, ERROR: %s' % (aic_source_path,aic_target_path,str(why))
                error_list.append(event_info)
                logger.error(event_info)

        if status_code == 0:
            # Copy IP_information/data from CD/USB to "content" directory in AIC/IP structure in mottag area. 
            Package_root = os.path.join(aic_target_path,IP_uuid)
            Package_dmd = os.path.join(Package_root,'descriptive_metadata')
            Package_amd = os.path.join(Package_root,'administrative_metadata')
            Package_ro = os.path.join(Package_amd,'repository_operations')
            Package_content = os.path.join(Package_root,'content')
            try:
                event_info = 'Copy %s to package content directory: %s' % (Package,Package_content)
                status_list.append(event_info)
                logger.info(event_info)
                if op.isdir(op.join(source_path,Package)):
                    shutil.copytree(op.join(source_path,Package),op.join(Package_content,op.split(Package)[1]))
                else:
                    shutil.copy2(op.join(source_path,Package),op.join(Package_content,op.split(Package)[1]))
            except (IOError, os.error), why:
                status_code = 5
                event_info = 'Problem to Copy %s to package content directory: %s, ERROR: %s' % (Package,Package_content,str(why))
                error_list.append(event_info)
                logger.error(event_info)

        if status_code == 0:
            METS_agent_list = []
            METS_altRecordID_list = []
            METS_LABEL = None
            EntryAgentIdentifierValue = None
            EntryDate = ''
            METS_STARTDATE = None
            METS_ENDDATE = None
            Package_root_source = os.path.join(aic_source_path,IP_uuid)
            METS_ObjectPath_source = os.path.join( aic_source_path, Pmets_obj )
            if os.path.exists(METS_ObjectPath_source):        
                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=METS_ObjectPath_source)
                EntryDate = res_info[1][0]
                for agent in res_info[2]:
                    if agent[0] == 'ARCHIVIST' and agent[2] == 'ORGANIZATION' and agent[3] == None:
                        EntryAgentIdentifierValue = agent[4]
                    METS_agent_list.append(agent)
                METS_LABEL = res_info[0][0]
                for altRecordID in res_info[3]:
                    if altRecordID[0] == 'STARTDATE':
                        METS_STARTDATE = altRecordID[1]
                    elif altRecordID[0] == 'ENDDATE':
                        METS_ENDDATE = altRecordID[1]
                    METS_altRecordID_list.append(altRecordID)
                event_info = 'Success to get METS agents,altRecords and label from %s' % Pmets_obj
                status_list.append(event_info)
                logger.info(event_info)
                # Add extra agent and altRecordID
                for agent in agent_list:
                    METS_agent_list.append(agent)
                    event_info = 'Add agent %s to metsfile' % agent
                    status_list.append(event_info)
                    logger.info(event_info)
                for altRecordID in altRecordID_list:
                    METS_altRecordID_list.append(altRecordID)
                    event_info = 'Add altRecordID %s to metsfile' % altRecordID
                    status_list.append(event_info)
                    logger.info(event_info)
            else:
                event_info = '%s not found in SIP' % Pmets_obj
                status_list.append(event_info)
                logger.info(event_info)
            METS_ObjectPath = os.path.join( Package_root, Cmets_obj )
            PREMIS_ObjectPath = os.path.join( Package_root, premis_obj )
            errno, why = Functions().Create_IP_metadata(ObjectIdentifierValue=IP_uuid, 
                                                           METS_ObjectPath=METS_ObjectPath, 
                                                           ObjectPath=Package_root,
                                                           altRecordID_default=False,
                                                           agent_default=False,
                                                           agent_list=METS_agent_list,
                                                           altRecordID_list=METS_altRecordID_list,
                                                           file_list=[],
                                                           METS_LABEL=METS_LABEL,
                                                           PREMIS_ObjectPath=PREMIS_ObjectPath,
                                                           allow_unknown_filetypes=allow_unknown_filetypes,
                                                           )
            if errno:
                status_code = 8
            for s in why[0]:
                status_list.append(s)
            for e in why[1]:   
                error_list.append(e)

        if status_code == 0:    
            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = AIC_uuid).exists()
            if ArchiveObject_qf is False:
                event_info = 'Add new entry to DB for AIC_UUID: %s' % (AIC_uuid)
                status_list.append(event_info)
                logger.info(event_info)
                ObjectMetadata_obj = ObjectMetadata.objects.create(
                                                label=METS_LABEL,
                                                startdate=METS_STARTDATE,
                                                enddate=METS_ENDDATE)
                # Add AIC to ArchiveObject DBtable
                ArchiveObject_aic_new = ArchiveObject()
                setattr(ArchiveObject_aic_new, 'ObjectUUID', AIC_uuid)
                setattr(ArchiveObject_aic_new, 'ObjectIdentifierValue', AIC_uuid)
                setattr(ArchiveObject_aic_new, 'OAISPackageType', 1)
                setattr(ArchiveObject_aic_new, 'Status', 0)
                setattr(ArchiveObject_aic_new, 'StatusActivity', 0)
                setattr(ArchiveObject_aic_new, 'StatusProcess', 5000)
                setattr(ArchiveObject_aic_new, 'Generation', 0)
                setattr(ArchiveObject_aic_new, 'EntryAgentIdentifierValue', EntryAgentIdentifierValue)
                setattr(ArchiveObject_aic_new, 'EntryDate', EntryDate)
                setattr(ArchiveObject_aic_new, 'ObjectMetadata', ObjectMetadata_obj)
                ArchiveObject_aic_new.save()
            else:
                event_info = 'Entry in DB for AIC_UUID: %s already exist, skip to update.' % (AIC_uuid)
                status_list.append(event_info)
                logger.info(event_info)

            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid).exists()
            if ArchiveObject_qf is False:
                event_info = 'Add new entry to DB for IP_UUID: %s' % (IP_uuid)
                status_list.append(event_info)
                logger.info(event_info)
                ObjectMetadata_obj = ObjectMetadata.objects.create(
                                                label=METS_LABEL,
                                                startdate=METS_STARTDATE,
                                                enddate=METS_ENDDATE)
                # Add IP to ArchiveObject DBtable
                ArchiveObject_new = ArchiveObject()
                setattr(ArchiveObject_new, 'ObjectUUID', IP_uuid)
                setattr(ArchiveObject_new, 'ObjectIdentifierValue', IP_uuid)
                setattr(ArchiveObject_new, 'OAISPackageType', 0)
                #setattr(ArchiveObject_new, 'OAISPackageType', 2)
                setattr(ArchiveObject_new, 'Status', 0)
                setattr(ArchiveObject_new, 'StatusActivity', 0)
                setattr(ArchiveObject_new, 'StatusProcess', 5000)
                setattr(ArchiveObject_new, 'Generation', 0)
                setattr(ArchiveObject_new, 'EntryAgentIdentifierValue', EntryAgentIdentifierValue)
                setattr(ArchiveObject_new, 'EntryDate', EntryDate)
                setattr(ArchiveObject_new, 'ObjectMetadata', ObjectMetadata_obj)
                ArchiveObject_new.save()

                # Add rel AIC - IP to Object_rel DBtable
                Object_rel_new = ArchiveObjectRel()
                setattr(Object_rel_new, 'AIC_UUID', ArchiveObject_aic_new)
                setattr(Object_rel_new, 'UUID', ArchiveObject_new)
                Object_rel_new.save()

                Object_data_new = ArchiveObjectData()
                setattr(Object_data_new, 'UUID', ArchiveObject_new)
                setattr(Object_data_new, 'label', METS_LABEL)
                setattr(Object_data_new, 'startdate', METS_STARTDATE)
                setattr(Object_data_new, 'enddate', METS_ENDDATE)
                Object_data_new.save()
            else:
                status_code = 6
                event_info = 'Entry in DB for IP_UUID: %s already exist, skip to update.' % (IP_uuid)
                error_list.append(event_info)
                logger.error(event_info)

        if status_code == 0:
            # Import logentrys to database
            errno,why = AddLogEventsToDB(info_entrys)
            if errno:
                event_info = 'Failed to Add log events to DB, ERROR: %s' % why
                error_list.append(event_info)
                logger.error(event_info)
                status_code = 7
            else:
                for s in why[0]:
                    status_list.append(s)
                for s in why[1]:
                    error_list.append(s)

        if status_code == 0:
            # Import logentrys from log.xml in tarfile to database
            ip_tarfilename = op.join(Package_content,op.split(Package)[1])
            if os.path.isfile(ip_tarfilename):
                try:
                    tarf = tarfile.open(name=ip_tarfilename,mode='r')
                    logfile_obj = tarf.extractfile('%s/%s' % (IP_uuid,ip_logfile)) # uuid_xxxx/log.xml
                    return_code,status,info_entrys =  logtool.get_logxml_info(logfile_obj)
                    if return_code == 0:
                        errno,why = AddLogEventsToDB(info_entrys)
                        if errno:
                            event_info = 'Failed to Add log events to DB, ERROR: %s' % why
                            error_list.append(event_info)
                            logger.error(event_info)
                            status_code = 10
                        else:
                            for s in why[0]:
                                status_list.append(s)
                            for s in why[1]:
                                error_list.append(s)
                    else:
                        status_code = 11
                        event_info = 'Status: %s, Error: %s' % (return_code,str(status))
                        error_list.append(event_info)
                        logger.info(event_info)
                    tarf.close()
                except:
                    status_code = 12
                    event_info = 'Problem to get %s from tarfile, error: %s' % (ip_logfile,str(sys.exc_info()))
                    error_list.append(event_info)
                    logger.error(event_info)
            else:
                status_code = 13
                event_info = 'Problem to find tarfile in content directory, failed to get %s' % ip_logfile
                error_list.append(event_info)
                logger.error = event_info

        #return status_code,[status_list,error_list]
        if status_code:
            #self.object.Status=100
            event_info = 'Failed to CheckIn object: %s from reception, ReqUUID: %s, why: %s' % (ObjectIdentifierValue,
                                                                                                ReqUUID,
                                                                                                error_list,
                                                                                                )
            ESSPGM.Events().create('30000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        else:
            #self.object.Status=20
            event_info = 'Success to CheckIn object: %s from reception, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                                        ReqUUID,
                                                                                        )
            ESSPGM.Events().create('30000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
                                   
        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Check In from Reception'
        result['creator'] = creator
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result) 
        return result 
    
class CheckOutToWorkTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    #time_limit = 86400
    time_limit = 259200 # 3 days

    def calculate_result(self,source_path=None,target_path=None,Package=None,a_uid=None,a_gid=None,a_mode=None,read_only_access=False,ObjectIdentifierValue=None,ReqUUID=None,ReqPurpose=None,linkingAgentIdentifierValue=None):
        status_code = 0
        status_list = []
        error_list = []
        AIC_uuid,IP_uuid = op.split(Package)
        IP_uuid_source = IP_uuid
        ip_logfile = Parameter.objects.get(entity='ip_logfile').value
       
        if status_code == 0:
            # IF Checkout object is "DirType" - Copy IP_uuid from controlarea to IP_NEW_uuid in workarea
            if op.isdir(op.join(source_path,Package)):
                if not read_only_access:
                    IP_uuid = uuid.uuid1()
                    Package_new = op.join(AIC_uuid,'%s' % IP_uuid)
                    event_info = 'CheckOut Package: %s from source_path: %s to new Package: %s in target_path: %s' % (Package,source_path,Package_new,target_path)
                else:
                    Package_new = Package
                    event_info = 'CheckOut Package: %s from source_path: %s to target_path: %s' % (Package,source_path,target_path)
                status_list.append(event_info)
                logger.info(event_info)
                try:
                    shutil.copytree(op.join(source_path,Package),op.join(target_path,Package_new))
                    #
                    # Fix if uuid_Content_METS.xml exists
                    Cmets_objpath = op.join(op.join(target_path,Package_new),'%s_Content_METS.xml' % IP_uuid_source)
                    if os.path.exists(Cmets_objpath):
                        event_info = 'Rename %s_Content_METS.xml to mets.xml' % IP_uuid_source
                        status_list.append(event_info)
                        os.rename( Cmets_objpath , op.join(op.join(target_path,Package_new),'mets.xml') )
                    # Fix end
                except (shutil.Error, IOError, os.error), why:
                    event_info = 'Failed to CheckOut, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.info(event_info)
                    status_code = 1
                errno,why = SetPermission(op.join(target_path,Package_new),a_uid,a_gid,a_mode)
                if errno:
                    event_info = 'Failed to SetPermission, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 2
            # ELSE_IF Checkout object is "FileType" - Copy object from controlarea to workarea with same filename. 
            else:
                event_info = 'CheckOut Package: %s from source_path: %s to target_path: %s' % (Package,source_path,target_path)
                status_list.append(event_info)
                logger.info(event_info)
                try:
                    ensure_dir(op.join(target_path,Package))
                    shutil.copy2(op.join(source_path,Package),op.join(target_path,Package))
                except (shutil.Error, IOError, os.error), why:
                    event_info = 'Failed to CheckOut, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 3
                errno,why = SetPermission(op.join(target_path,Package),a_uid,a_gid,a_mode)
                if errno:
                    event_info = 'Failed to SetPermission, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 4

        if status_code == 0 and op.isdir(op.join(source_path,Package)):
            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = AIC_uuid).exists()
            if ArchiveObject_qf is False:
                event_info = 'Missing entry in DB for AIC_UUID: %s' % (AIC_uuid)
                status_list.append(event_info)
                logger.info(event_info)

            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid).exists()
            if ArchiveObject_qf is False:
                # Get AIC_uuid if I now IP_uuid
                AIC_uuid_test = ArchiveObjectRel.objects.filter(UUID=IP_uuid_source).get().AIC_UUID.ObjectUUID
                # Get AIC_uuid object
                AIC_Object_qf_IP_source = ArchiveObject.objects.filter(ObjectUUID=AIC_uuid_test).get()
                # Get the newest archiveObject (highest generation number)
                Newest_object = AIC_Object_qf_IP_source.relaic_set.order_by('-UUID__Generation')[:1].get().UUID
                # Get source_IP
                source_IP_Object = ArchiveObject.objects.filter(ObjectUUID = IP_uuid_source)[:1].get()
                
                event_info = 'Add new entry to DB for IP_UUID: %s' % (IP_uuid)
                status_list.append(event_info)
                logger.info(event_info)
                ObjectMetadata_obj = ObjectMetadata.objects.create(
                                label=getattr(source_IP_Object.ObjectMetadata, 'label', ''),
                                startdate=getattr(source_IP_Object.ObjectMetadata, 'startdate', None),
                                enddate=getattr(source_IP_Object.ObjectMetadata, 'enddate', None))
                # Add IP to ArchiveObject DBtable
                ArchiveObject_new = ArchiveObject()
                setattr(ArchiveObject_new, 'ObjectUUID', IP_uuid)
                setattr(ArchiveObject_new, 'ObjectIdentifierValue', IP_uuid)
                setattr(ArchiveObject_new, 'OAISPackageType', 0)
                #setattr(ArchiveObject_new, 'OAISPackageType', 2)
                setattr(ArchiveObject_new, 'Status', 0)
                setattr(ArchiveObject_new, 'StatusActivity', 0)
                setattr(ArchiveObject_new, 'StatusProcess', 5100)
                setattr(ArchiveObject_new, 'Generation', int(Newest_object.Generation)+1)
                setattr(ArchiveObject_new, 'EntryAgentIdentifierValue', source_IP_Object.EntryAgentIdentifierValue)
                setattr(ArchiveObject_new, 'EntryDate', source_IP_Object.EntryDate)
                setattr(ArchiveObject_new, 'ObjectMetadata', ObjectMetadata_obj)
                ArchiveObject_new.save()

                # Add rel AIC - IP to Object_rel DBtable
                Object_rel = ArchiveObjectRel()
                setattr(Object_rel, 'AIC_UUID', AIC_Object_qf_IP_source)
                setattr(Object_rel, 'UUID', ArchiveObject_new)
                Object_rel.save()

                Object_data_qf = ArchiveObjectData.objects.filter(UUID = IP_uuid_source)[:1]
                # Prepare Object data
                if Object_data_qf:
                    Object_data_qf = Object_data_qf.get()
                    label = Object_data_qf.label
                    startdate = Object_data_qf.startdate
                    enddate = Object_data_qf.enddate
                else:
                    label = ''
                    startdate = None
                    enddate = None
                # Add Object data to Object_data DBtable
                Object_data = ArchiveObjectData()
                setattr(Object_data, 'UUID', ArchiveObject_new)
                setattr(Object_data, 'label', label)
                setattr(Object_data, 'startdate', startdate)
                setattr(Object_data, 'enddate', enddate)
                Object_data.save()
            else:
                if not read_only_access:
                    event_info = 'Entry in DB for IP_UUID: %s already exist, skip to update.' % (IP_uuid)
                else:
                    # Update IP in ArchiveObject DBtable
                    ArchiveObject_upd = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid)[:1].get()
                    if ArchiveObject_upd.StatusActivity in [ 7, 8 ]:
                        setattr(ArchiveObject_upd, 'StatusActivity', 8)
                        # Commit DB updates
                        ArchiveObject_upd.save()
                        event_info = 'Entry in DB for IP_UUID: %s already exist, setting StatusActivity = 8 (WorkArea).' % (IP_uuid)
                    elif ArchiveObject_upd.StatusProcess == 5000:
                        event_info = 'You have to manual delete this IP: %s from your workarea filesystem when you do not need the information any more!!' % (op.join(target_path,Package_new))
                status_list.append(event_info)
                logger.info(event_info)

        if status_code == 0 and op.isdir(op.join(source_path,Package)):
            # Export logentrys from database to logfile
            return_code,return_status_list = logtool.ExportLogEventsToFile(logfilename = op.join(op.join(target_path,Package_new),ip_logfile), 
                                                                           ip_uuid = IP_uuid, 
                                                                           aic_uuid = AIC_uuid, 
                                                                           )
            for i in return_status_list[0]:
                status_list.append(i)
            for i in return_status_list[1]:
                error_list.append(i)
            status_code = return_code
        #return status_code,[status_list,error_list]
        if status_code:
            #self.object.Status=100
            event_info = 'Failed to CheckOut object: %s to workarea, ReqUUID: %s, why: %s' % (ObjectIdentifierValue,
                                                                                              ReqUUID,
                                                                                              error_list,
                                                                                              )
            ESSPGM.Events().create('31000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        else:
            #self.object.Status=20
            event_info = 'Success to CheckOut object: %s to workarea, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                                      ReqUUID,
                                                                                      )
            ESSPGM.Events().create('31000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        

        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Check out to work'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result) 
        return result

class CheckInFromWorkTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    #time_limit = 86400
    time_limit = 259200 # 3 days

    def calculate_result(self,source_path=None,target_path=None,Package=None,a_uid=None,a_gid=None,a_mode=None,allow_unknown_filetypes=False,ObjectIdentifierValue=None,ReqUUID=None,ReqPurpose=None,linkingAgentIdentifierValue=None):
        status_code = 0
        status_list = []
        error_list = []
        AIC_uuid,IP_uuid = op.split(Package)
        ObjectPath = op.join(target_path,Package)
        Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
        premis_obj = Parameter.objects.get(entity='preservation_descriptionfile').value
        ip_logfile = Parameter.objects.get(entity='ip_logfile').value

        if status_code == 0:
            # Import logentrys to database
            logfilepath = op.join(op.join(source_path,Package),ip_logfile)
            return_code,status,info_entrys =  logtool.get_logxml_info(logfilepath)
            if return_code == 0:
                errno,why = AddLogEventsToDB(info_entrys)
                if errno:
                    event_info = 'Failed to Add log events to DB, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 3
                else:
                    for s in why[0]:
                        status_list.append(s)
                    for s in why[1]:
                        error_list.append(s)
            else:
                status_code = 4
                event_info = 'Status: %s, Error: %s' % (return_code,str(status))
                error_list.append(event_info)
                logger.info(event_info)

        if status_code == 0:
            # Move package from workarea to controlarea.
            try:
                event_info = 'CheckIn Package: %s from source_path: %s to target_path: %s' % (Package,source_path,target_path)
                status_list.append(event_info)
                logger.info(event_info)
                shutil.move(op.join(source_path,Package),op.join(target_path,Package))
                logger.warning('unicode debug - TargetPath: %s, defencoding: %s' % (repr(target_path), sys.getfilesystemencoding()))
                errno,why = SetPermission(op.join(target_path,Package),a_uid,a_gid,a_mode)
                if errno:
                    event_info = 'Failed to SetPermission, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 1
            except (IOError, os.error), why:
                event_info = 'Failed to CheckIn, ERROR: %s' % why
                error_list.append(event_info)
                logger.error(event_info)
                status_code = 2
            
        if status_code == 0:
            METS_agent_list = []
            METS_altRecordID_list = []
            METS_LABEL = None
            METS_ObjectPath_source = os.path.join( ObjectPath, Cmets_obj )
            if os.path.exists(METS_ObjectPath_source):        
                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=METS_ObjectPath_source)
                for agent in res_info[2]:
                    METS_agent_list.append(agent)
                METS_LABEL = res_info[0][0]
                for altRecordID in res_info[3]:
                    METS_altRecordID_list.append(altRecordID)
                event_info = 'Success to get METS agents,altRecords and label from %s' % Cmets_obj
            else:
                event_info = '%s not found in SIP' % Cmets_obj
            status_list.append(event_info)
            logger.info(event_info)

        if status_code == 0:
            # Create new content METS file for IP
            METS_ObjectPath = os.path.join( ObjectPath, Cmets_obj )
            event_info = 'Create new content METS: %s' % METS_ObjectPath
            status_list.append(event_info)
            logger.info(event_info)
            logger.warning('unicode debug - ObjectPath: %s, defencoding: %s' % (repr(ObjectPath), sys.getfilesystemencoding()))
            PREMIS_ObjectPath = os.path.join( ObjectPath, premis_obj )
            errno, why = Functions().Create_IP_metadata(ObjectIdentifierValue=IP_uuid, 
                                                           METS_ObjectPath=METS_ObjectPath, 
                                                           ObjectPath=ObjectPath,
                                                           altRecordID_default=False,
                                                           agent_default=False,
                                                           agent_list=METS_agent_list,
                                                           altRecordID_list=METS_altRecordID_list,
                                                           file_list=[],
                                                           METS_LABEL=METS_LABEL,
                                                           PREMIS_ObjectPath=PREMIS_ObjectPath,
                                                           allow_unknown_filetypes=allow_unknown_filetypes,
                                                           )
            if errno:
                status_code = 5
            for s in why[0]:
                status_list.append(s)
            for e in why[1]:
                error_list.append(e)

        if status_code == 0:
            # Remove "empty" AIC_Dir from workarea
            try:
                event_info = 'Try to remove AIC_Dir: %s from source_path: %s' % (AIC_uuid,source_path)
                status_list.append(event_info)
                logger.info(event_info)
                os.rmdir(op.join(source_path,AIC_uuid))
            except (IOError, os.error), why:
                event_info = 'Varning AIC_Dir not removed, ERROR: %s' % why
                error_list.append(event_info)
                logger.error(event_info)
                #/status_code = 3

        if status_code == 0:
            # Update IP in ArchiveObject DBtable
            ArchiveObject_upd = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid)[:1].get()
            setattr(ArchiveObject_upd, 'StatusActivity', 0)
            setattr(ArchiveObject_upd, 'StatusProcess', 5000)
            # Commit DB updates
            ArchiveObject_upd.save()

        #return status_code,[status_list,error_list]
        if status_code:
            #self.object.Status=100
            event_info = 'Failed to CheckIn object: %s from workarea, ReqUUID: %s, why: %s' % (ObjectIdentifierValue,
                                                                                               ReqUUID,
                                                                                               error_list
                                                                                               )
            ESSPGM.Events().create('32000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        else:
            #self.object.Status=20
            event_info = 'Success to CheckIn object: %s from workarea, ReqUUID: %s' % (ObjectIdentifierValue,ReqUUID)
            ESSPGM.Events().create('32000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        
        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Check in from work'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result)
        return result
                                   
class DiffCheckTask(JobtasticTask):

    significant_kwargs = []
    herd_avoidance_timeout = 0 #120  # Give it two minutes
        
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
        
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
        #soft_time_limit = None
        
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,
                         ObjectIdentifierValue=None,
                         ObjectPath=None,
                         METS_ObjectPath=None,
                         ReqUUID=None,
                         linkingAgentIdentifierValue=None,
                         ReqPurpose=None):
        status_code, status_detail, res_list = g_functions().DiffCheck_IP(ObjectIdentifierValue=ObjectIdentifierValue,
                                                                          ObjectPath=ObjectPath, 
                                                                          METS_ObjectPath=METS_ObjectPath,
                                                                          )
        status_list = []
        error_list = []
        if status_code:
            #self.object.Status=100
            event_info_1 = 'Failed to DiffCheck object: %s, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                                   ReqUUID,
                                                                                   )
            event_info_2 = 'why: %s' % (status_detail[1])
            event_info = '%s, %s' % (event_info_1, event_info_2)
            ESSPGM.Events().create('33000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
            logger.error(event_info)
            status_list.append(event_info_1)
            status_list.append(event_info_2)
            for error_item in status_detail[1]:
                error_list.append(error_item)
        else:
            #self.object.Status=20
            status_summary = ''
            #for st in status_list:
            for st in status_detail[0]:
                if st.startswith('STATUS -'):
                    status_summary = st
            event_info_1 = 'Success to DiffCheck object: %s, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                                       ReqUUID,
                                                                                       )
            event_info_2 = 'Result: %s' % (status_summary)
            event_info = '%s, %s' % (event_info_1, event_info_2)
            ESSPGM.Events().create('33000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
            logger.info(event_info)
            status_list.append(event_info_1)
            status_list.append(status_summary)

        #Test functionality added to test monitoring of tasks in progress
        '''
        testdrive = 1
        testtime = 10
        update_frequency = 1
        while(testdrive < 11):
            self.update_progress(completed_count=testdrive,
                                total_count=testtime,
                                update_frequency=update_frequency,
                                )
            testdrive = testdrive + 1
            sleep(0.2)
         '''       
        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Diffcheck'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuscode'] = status_code
        result['statusdetail'] = status_detail
        #result['resultlist'] = res_list
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result) 
        return result

class PreserveIPTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
        
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
        
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
        #soft_time_limit = None
        
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,source_path=None,target_path=None,Package=None,a_uid=None,a_gid=None,a_mode=None,linkingAgentIdentifierValue=None,ReqPurpose=None,ObjectIdentifierValue=None,ReqUUID=None):
        status_code = 0
        status_list = []
        error_list = []
        AIC_uuid,IP_uuid = op.split(Package)
       
        if status_code == 0:
            # IF Checkout object is "DirType" - Copy IP_uuid from controlarea to ingestarea
            if op.isdir(op.join(source_path,Package)):
                event_info = 'Copy IP: %s from controlarea: %s to ingestpath: %s' % (Package,source_path,target_path)
                status_list.append(event_info)
                logger.info(event_info)
                try:
                    shutil.copytree(op.join(source_path,Package),op.join(target_path,IP_uuid))
                except (shutil.Error, IOError, os.error), why:
                    event_info = 'Failed to ingest, ERROR: %s' % why
                    error_list.append(event_info)
                    logger.error(event_info)
                    status_code = 1            

        if status_code == 0 and op.isdir(op.join(source_path,Package)):
            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = AIC_uuid).exists()
            if ArchiveObject_qf is False:
                event_info = 'Missing entry in DB for AIC_UUID: %s' % (AIC_uuid)
                status_list.append(event_info)
                logger.info(event_info)

            ArchiveObject_qf = ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid).exists()
            if ArchiveObject_qf is False:
                event_info = 'Missing entry in DB for IP_UUID: %s' % (IP_uuid)
                status_list.append(event_info)
                logger.info(event_info)
        #return status_code,[status_list,error_list]
        if status_code:
            #self.object.Status=100
            event_info = 'Failed to PreserveIP object: %s, ReqUUID: %s, why: %s' % (ObjectIdentifierValue,
                                                                                    ReqUUID,
                                                                                    error_list,
                                                                                    )
            ESSPGM.Events().create('34000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        else:
            #self.object.Status=20
            IngestQueue_req = IngestQueue()
            IngestQueue_req.ReqUUID = ReqUUID
            IngestQueue_req.ReqType = 2
            IngestQueue_req.ReqPurpose = ReqPurpose
            IngestQueue_req.user = linkingAgentIdentifierValue
            IngestQueue_req.ObjectIdentifierValue = ObjectIdentifierValue
            IngestQueue_req.Status = 0
            IngestQueue_req.save()
            event_info = 'Success to PreserveIP object: %s, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                          ReqUUID,
                                                                          )
            ESSPGM.Events().create('34000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue=ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )            
            # Update ip_obj with StatusProcess = 0 to enable ingest to discover new IP.
            ArchiveObject.objects.filter(ObjectIdentifierValue = IP_uuid).update(StatusProcess = 0)
            #self.ip_obj = 
            #self.ip_obj.StatusProcess = 0
            #self.ip_obj.save()
        
        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Preserve IP'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result) 
        return result     
            
class CopyFilelistTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,source_path=None,target_path=None,filelist=None,ReqUUID=None,ReqType=None,ReqPurpose=None,user=None,ObjectIdentifierValue=None,posted=None,reqfilename=None,linkingAgentIdentifierValue=None):
        status_code = 0
        status_list = []
        error_list = []

        for Package in filelist:
            # Copy file or directorytree
            try:
                if op.isdir(op.join(source_path,Package)):
                    shutil.copytree(op.join(source_path,Package),op.join(target_path,Package))
                else:
                    target = op.join(target_path,Package)
                    targetdir = op.split(target)[0]
                    if not op.isdir(targetdir):
                        os.makedirs(targetdir)
                    shutil.copy2(op.join(source_path,Package),target)
            except (IOError, os.error), why:
                event_info = 'Failed to copy: %s from source_path: %s to target_path: %s ERROR: %s' % (Package,source_path,target_path,why),Package
                error_list.append(event_info)
                logger.error(event_info)
                status_code = 1
            else:
                event_info = 'Success to copy: %s from source_path: %s to target_path: %s' % (Package,source_path,target_path),Package
                status_list.append(event_info)
                logger.info(event_info)
        #return status_code,[status_list,error_list]
        '''if status_code:
            self.object.Status=100
        else:
            self.object.Status=20'''
        status_detail = [[],[]]
        req_filelist = []
        for item in status_list:
            event_info = '%s, ReqUUID: %s' % (item[0],ReqUUID)
            ESSPGM.Events().create('35000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,item[1],linkingAgentIdentifierValue=linkingAgentIdentifierValue)
            status_detail[0].append(item[0])
            req_filelist.append(item[1])
        for item in error_list:
            event_info = '%s, ReqUUID: %s' % (item[0],ReqUUID)
            ESSPGM.Events().create('35000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,item[1],linkingAgentIdentifierValue=linkingAgentIdentifierValue)
            status_detail[1].append(item[0])
            req_filelist.append(item[1])
        
        TimeZone = timezone.get_default_timezone_name()
        loc_timezone=pytz.timezone(TimeZone)
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
        #self.object.posted = loc_dt_isoformat
        self.createExchangeRequestFile(ReqUUID=ReqUUID, 
                              ReqType = ReqType, 
                              ReqPurpose = ReqPurpose, 
                              user = linkingAgentIdentifierValue, 
                              ObjectIdentifierValue = ObjectIdentifierValue, 
                              posted = loc_dt_isoformat, 
                              filelist = req_filelist, 
                              reqfilename = os.path.join(target_path,'request.xml'),
                              )
        result = {}
        result['category'] = 'controlarea'
        if ReqType=='6':
            result['label'] = 'Check out to gatarea'
        elif ReqType=='7':
            result['label'] = 'Check in from gatarea'
        else:
            result['label'] = 'Check out to gatarea'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result)
        return result

    def createExchangeRequestFile(self,ReqUUID=None,ReqType=None,ReqPurpose=None,user=None,ObjectIdentifierValue=None,posted=None,filelist=None,reqfilename=None):
        EL_root = etree.Element('exchange')
        EL_request = etree.SubElement(EL_root, 'request', attrib={'ReqUUID':ReqUUID,
                                                                  'ReqType':ReqType,
                                                                  'ReqPurpose':ReqPurpose,
                                                                  'user':user,
                                                                  'ObjectIdentifierValue':ObjectIdentifierValue,
                                                                  'posted':posted,
                                                                  })
        EL_fileSec = etree.SubElement(EL_root,'fileSec')
        EL_fileGrp = etree.SubElement(EL_fileSec,'fileGrp',attrib={'ID':'fgrp001','USE':'FILES'})
        for item in filelist:
            EL_file = etree.SubElement(EL_fileGrp,'file',attrib={'name':item})
        doc = etree.ElementTree(element=EL_root, file=None)
        ESSMD.writeToFile(doc,reqfilename)

class GetExchangeRequestFileContentTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,reqfilename=None):
        status_code = 0
        status_list = []
        error_list = []
        res = None
        if reqfilename:
            try:
                DOC  =  etree.ElementTree ( file=reqfilename )
            except etree.XMLSyntaxError, detail:
                status_code = 10
                error_list.append(str(detail))
            except IOError, detail:
                status_code = 20
                error_list.append(str(detail))
            EL_root = DOC.getroot()
        
        if status_code == 0:
            filelist = []
        
            EL_request = EL_root.find("request")
            a_ReqUUID = EL_request.get('ReqUUID')
            a_ReqType = EL_request.get('ReqType')
            a_ReqPurpose = EL_request.get('ReqPurpose')
            a_user = EL_request.get('user')
            a_ObjectIdentifierValue = EL_request.get('ObjectIdientifierValue')
            a_posted = EL_request.get('posted')
            
            fileSec = EL_root.find("fileSec")
            fileGrp_all = fileSec.findall("fileGrp")
            for fileGrp in fileGrp_all:
                file_all = fileGrp.findall("file")
                for EL_file in file_all:
                    a_name = EL_file.get('name')
                    filelist.append(a_name)
            res = [a_ReqUUID,a_ReqType,a_ReqPurpose,a_user,a_ObjectIdentifierValue,a_posted,filelist]
        return {'res':res,
                'status_code':status_code,
                'status_list':[status_list,error_list]
                }

class DeleteIPTask(JobtasticTask):

    significant_kwargs = []
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,
                        source_path=None,
                        target_path=None,
                        Package=None,
                        ObjectIdentifierValue=None,                        
                        ReqUUID=None,
                        ReqPurpose=None,
                        linkingAgentIdentifierValue=None):
        status_code = 0
        status_list = []
        error_list = []
        AIC_uuid,IP_uuid = op.split(Package)
       
        if status_code == 0:
            remove_list = [op.join(source_path,Package),op.join(target_path,Package)]
            for remove_item in remove_list:
                if op.exists(remove_item):
                    try:
                        if op.isdir(remove_item):
                            event_info = 'Try to remove directory tree: %s' % (remove_item)
                            shutil.rmtree(remove_item)
                        else:
                            event_info = 'Try to remove file: %s' % (remove_item)
                            os.remove(remove_item)
                        status_list.append(event_info)
                        logger.info(event_info)
                    except (shutil.Error, IOError, os.error), why:
                        event_info = 'Failed to remove %s, ERROR: %s' % (remove_item,why)
                        error_list.append(event_info)
                        logger.error(event_info)
                        status_code = 1

        if status_code == 0:
            remove_list = [op.join(source_path,AIC_uuid),op.join(target_path,AIC_uuid)]
            for remove_item in remove_list:
                remove_item_tmpextract = op.join(remove_item,'.tmpextract')
                if op.exists(remove_item_tmpextract):
                    try:
                        shutil.rmtree(remove_item_tmpextract)                    
                    except (shutil.Error, IOError, os.error), why:
                        event_info = 'Warning, problem to remove .tmpextract directory %s, ERROR: %s' % (remove_item_tmpextract,why)
                        error_list.append(event_info)
                        logger.error(event_info)  
                remove_item_AIC_METS = op.join(remove_item,'%s_AIC_METS.xml' % AIC_uuid)
                if op.exists(remove_item_AIC_METS):
                    try:
                        os.remove(remove_item_AIC_METS)                    
                    except (shutil.Error, IOError, os.error), why:
                        event_info = 'Warning, problem to remove %s, ERROR: %s' % (remove_item_AIC_METS,why)
                        error_list.append(event_info)
                        logger.error(event_info)                            
                if op.exists(remove_item):
                    try:
                        event_info = 'Try to remove AIC directory: %s' % (remove_item)
                        status_list.append(event_info)
                        logger.info(event_info)
                        os.rmdir(remove_item)                    
                    except (shutil.Error, IOError, os.error), why:
                        event_info = 'Warning, problem to remove AIC directory %s, ERROR: %s' % (remove_item,why)
                        error_list.append(event_info)
                        logger.error(event_info)
                        #status_code = 1    

        #return status_code,[status_list,error_list]
        if status_code:
            #self.object.Status=100
            event_info = 'Failed to delete object: %s, ReqUUID: %s, why: %s' % (ObjectIdentifierValue,
                                                                                ReqUUID,
                                                                                error_list,
                                                                                )
            ESSPGM.Events().create('36000',ReqPurpose,'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        else:
            #self.object.Status=20
            event_info = 'Success to delete object: %s, ReqUUID: %s' % (ObjectIdentifierValue,
                                                                        ReqUUID
                                                                        )
            ESSPGM.Events().create('36000',ReqPurpose,'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
            deleted_obj = ArchiveObject.objects.get(ObjectIdentifierValue = IP_uuid) #filter
            #self.ip_obj.
            if deleted_obj.StatusProcess in range(0,3001) and deleted_obj.StatusActivity in [ 7, 8 ]:
                # ip_obj is archived update StatusActivity = 0
                #self.ip_obj.StatusActivity = 0
                #self.ip_obj.save()
                deleted_obj.StatusActivity = 0
                deleted_obj.save()
            else:
                # Update ip_obj with StatusProcess = 9999 to mark as deleted.
                #self.ip_obj.StatusProcess = 9999
                #self.ip_obj.StatusActivity = 0
                #self.ip_obj.ObjectActive = 0
                #self.ip_obj.save()
                deleted_obj.StatusProcess = 9999
                deleted_obj.StatusActivity = 0
                deleted_obj.ObjectActive = 0
                deleted_obj.save()

        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Delete IP'
        result['reqpurpose'] = ReqPurpose
        result['user'] = linkingAgentIdentifierValue
        result['statuslist'] = status_list
        result['errorlist'] = error_list
        result['ipuuid'] = ObjectIdentifierValue
        if status_code != 0:
            raise ControlareaException(result)          
        return result
                
def SetPermission(path,uid=None,gid=None,mode=0770):
    try:
        if uid is None:
            uid = os.getuid()
        if gid is None:
            gid = os.getgid()
        for root, dirs, files in os.walk(path):
            for momo in dirs:
                os.chown(os.path.join(root, momo), uid,gid)
                os.chmod(os.path.join(root, momo), mode)
            for momo in files:
                os.chown(os.path.join(root, momo), uid, gid)
                os.chmod(os.path.join(root, momo), mode)
    except (IOError, os.error), why:
        return 1,[why]
    else:
        return 0,[]

def ensure_dir(f):
    d = os.path.dirname(f)
    if not os.path.exists(d):
        os.makedirs(d)

def AddLogEventsToDB(info_entrys):
    status_code = 0
    status_list = []
    error_list = []

    for i in info_entrys[1]:
        #print '------------------------------------------------------------------------'
        #print 'EventIndentifierValue: %s, EventType: %s, EventDateTime: %s, eventDetail: %s, outcome: %s, outcomeDetail: %s, linkingObject: %s' % (i[1],i[2],i[3],i[4],i[5],i[6],i[10])
        eventIdentifierValue = i[1]
        eventType = i[2]
        eventDateTime = i[3]
        eventDetail = i[4]
        eventApplication = ''
        eventVersion = ''
        eventOutcome = i[5]
        eventOutcomeDetailNote = i[6]
        linkingAgentIdentifierValue = i[8]
        linkingObjectIdentifierValue = i[10] 

        eventIdentifier_qf = eventIdentifier.objects.filter(eventIdentifierValue = eventIdentifierValue).exists()
        if eventIdentifier_qf is False:
            event_info = 'Add new entry to DB for eventIdentifierValue: %s' % (eventIdentifierValue)
            status_list.append(event_info)
            logger.info(event_info)
            # Add eventIdentifierValue to eventIdentifier DBtable
            eventIdentifier_new = eventIdentifier()
            setattr(eventIdentifier_new, 'eventIdentifierValue', eventIdentifierValue)
            setattr(eventIdentifier_new, 'eventType', eventType)
            setattr(eventIdentifier_new, 'eventDateTime', eventDateTime)
            setattr(eventIdentifier_new, 'eventDetail', eventDetail)
            setattr(eventIdentifier_new, 'eventApplication', eventApplication)
            setattr(eventIdentifier_new, 'eventVersion', eventVersion)
            setattr(eventIdentifier_new, 'eventOutcome', eventOutcome)
            setattr(eventIdentifier_new, 'eventOutcomeDetailNote', eventOutcomeDetailNote)
            setattr(eventIdentifier_new, 'linkingAgentIdentifierValue', linkingAgentIdentifierValue)
            setattr(eventIdentifier_new, 'linkingObjectIdentifierValue', linkingObjectIdentifierValue)
            eventIdentifier_new.save()
        else:
            event_info = 'Entry in DB for eventIdentifierValue: %s already exist, skip to update.' % (eventIdentifierValue)
            status_list.append(event_info)
            logger.info(event_info)
    return status_code,[status_list,error_list]
        
class Functions:
    "Create IP mets"
    ###############################################
    def Create_IP_metadata(self,ObjectIdentifierValue,METS_ObjectPath,ObjectPath=None,agent_list=[],agent_default=False,altRecordID_list=[],altRecordID_default=False,file_list=[],namespacedef=None,METS_LABEL=None,METS_PROFILE=None,METS_TYPE='SIP',METS_RECORDSTATUS=None,METS_DocumentID=None,PREMIS_ObjectPath=None,allow_unknown_filetypes=False,ChecksumAlgorithm=None):
        status_code = 0
        status_list = []
        error_list = []
        details_flag = False

        TimeZone = timezone.get_default_timezone_name()
        self.Cmets_objpath = METS_ObjectPath
        self.ObjectIdentifierValue = ObjectIdentifierValue
        IPParameter_obj = IPParameter.objects.filter(type='SIP')[0]
        
        if ChecksumAlgorithm is None:
            try:
                ChecksumAlgorithm_obj = DefaultValue.objects.get(entity='ChecksumAlgorithm')
            except DefaultValue.DoesNotExist:
                ChecksumAlgorithm = 2
            else:
                try:
                    ChecksumAlgorithm = int(ChecksumAlgorithm_obj.value)
                except ValueError:
                    ChecksumAlgorithm = 2
        else:
            try:
                ChecksumAlgorithm = int(ChecksumAlgorithm_obj.value)
            except ValueError:
                ChecksumAlgorithm = 2
        
        #ChecksumAlgorithm = 2
        CA = dict(ChecksumAlgorithm_CHOICES)[ChecksumAlgorithm]
        
        if status_code == 0:
            self.ObjectIdentifierValue = ObjectIdentifierValue
       
            # create mets root
            if METS_LABEL is None:
                self.METS_LABEL = IPParameter_obj.label
            else:
                self.METS_LABEL = METS_LABEL
            if METS_PROFILE is None:
                self.METS_PROFILE = SchemaProfile.objects.get(entity='mets_profile').value
            else:
                self.METS_PROFILE = METS_PROFILE
        
            # create mets header
            self.METS_agent_list = agent_list
            if agent_default is True:
                ARCHIVIST_ORGANIZATION = IPParameter_obj.archivist_organization
                ARCHIVIST_ORGANIZATION_note = [IPParameter_obj.archivist_organization_id]
                ARCHIVIST_SOFTWARE = IPParameter_obj.archivist_organization_software
                ARCHIVIST_SOFTWARE_note = [IPParameter_obj.archivist_organization_software_id]
                CREATOR_ORGANIZATION = IPParameter_obj.creator_organization
                CREATOR_ORGANIZATION_note = [IPParameter_obj.creator_organization_id]
                CREATOR_INDIVIDUAL = IPParameter_obj.creator_individual
                CREATOR_INDIVIDUAL_note = [IPParameter_obj.creator_individual_details]
                CREATOR_SOFTWARE = IPParameter_obj.creator_software
                CREATOR_SOFTWARE_note = [IPParameter_obj.creator_software_id]
                PRESERVATION_ORGANIZATION = IPParameter_obj.preservation_organization
                PRESERVATION_ORGANIZATION_note = [IPParameter_obj.preservation_organization_id]
                PRESERVATION_SOFTWARE = IPParameter_obj.preservation_organization_software
                PRESERVATION_SOFTWARE_note = [IPParameter_obj.preservation_organization_software_id]
                self.METS_agent_list.append(['ARCHIVIST',None,'ORGANIZATION',None,ARCHIVIST_ORGANIZATION,ARCHIVIST_ORGANIZATION_note])
                self.METS_agent_list.append(['ARCHIVIST',None,'OTHER','SOFTWARE',ARCHIVIST_SOFTWARE,ARCHIVIST_SOFTWARE_note])
                self.METS_agent_list.append(['CREATOR',None,'ORGANIZATION',None,CREATOR_ORGANIZATION,CREATOR_ORGANIZATION_note])
                self.METS_agent_list.append(['CREATOR',None,'INDIVIDUAL',None,CREATOR_INDIVIDUAL,CREATOR_INDIVIDUAL_note])
                self.METS_agent_list.append(['CREATOR',None,'OTHER','SOFTWARE',CREATOR_SOFTWARE, CREATOR_SOFTWARE_note])
                self.METS_agent_list.append(['PRESERVATION',None,'ORGANIZATION',None,PRESERVATION_ORGANIZATION,PRESERVATION_ORGANIZATION_note])
                self.METS_agent_list.append(['PRESERVATION',None,'OTHER','SOFTWARE',PRESERVATION_SOFTWARE,PRESERVATION_SOFTWARE_note])
            self.METS_altRecordID_list = altRecordID_list
            if altRecordID_default is True:
                DELIVERYTYPE = IPParameter_obj.deliverytype
                DELIVERYSPECIFICATION = IPParameter_obj.deliveryspecification
                SUBMISSIONAGREEMENT = IPParameter_obj.submissionagreement
                INFORMATIONCLASS = IPParameter_obj.informationclass
                PROJECTNAME = IPParameter_obj.projectname
                POLICYID = str(IPParameter_obj.policyid)
                RECEIPT_EMAIL = IPParameter_obj.receipt_email
                self.METS_altRecordID_list.append(['DELIVERYTYPE',DELIVERYTYPE]) 
                self.METS_altRecordID_list.append(['DELIVERYSPECIFICATION',DELIVERYSPECIFICATION])
                self.METS_altRecordID_list.append(['SUBMISSIONAGREEMENT',SUBMISSIONAGREEMENT])
                #self.METS_altRecordID_list.append(['DATASUBMISSIONSESSION','xyz'])
                self.METS_altRecordID_list.append(['INFORMATIONCLASS',INFORMATIONCLASS])
                self.METS_altRecordID_list.append(['PROJECTNAME',PROJECTNAME])
                self.METS_altRecordID_list.append(['POLICYID',POLICYID])
                self.METS_altRecordID_list.append(['RECEIPT_EMAIL',RECEIPT_EMAIL])
            if METS_DocumentID is None:
                self.METS_DocumentID = os.path.split(self.Cmets_objpath)[1]
            else:
                self.METS_DocumentID = METS_DocumentID
            self.METS_RECORDSTATUS = METS_RECORDSTATUS
            
            # create amdSec / structMap / fileSec
            self.ms_files = file_list
            if ObjectPath is not None:
                if details_flag: logger.info('Object: %s, GetFiletree2 - start' % ObjectIdentifierValue)
                Filetree_list, errno, [status_list2,error_list2]  = ESSPGM.Check().GetFiletree2(ObjectPath,ChecksumAlgorithm,allow_unknown_filetypes)
                if details_flag: logger.info('Object: %s, GetFiletree2 - len: %s - end' % (ObjectIdentifierValue, len(Filetree_list)))
                if not errno:
                    for ss in status_list2:
                        status_list.append(ss)
                    for ee in error_list2:
                        error_list.append(ee)    
                    for f in Filetree_list:
                        f_name = f[0]
                        f_size = f[1].st_size
                        f_created = datetime.datetime.fromtimestamp(f[1].st_mtime,pytz.timezone(TimeZone)).replace(microsecond=0).isoformat()
                        f_checksum = f[2]
                        f_mimetype = f[3]
                        # Don't add mets.xml
                        if f_name == self.METS_DocumentID:
                            continue
                        # Don't add 'administrative_metadata/premis.xml'
                        elif f_name == PREMIS_ObjectPath.replace( ObjectPath + '/', '' ):
                            continue
                        #elif f_name[-10:] == 'premis.xml':
                        #    self.ms_files.append(['amdSec', None, 'digiprovMD', 'digiprovMD001', None,
                        #                     None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % f_name, 'simple',
                        #                     f_checksum, 'MD5', f_size, 'text/xml', f_created,
                        #                     'PREMIS', None, None])     
                        else:
                            self.ms_files.append(['fileSec', None, None, None, None,
                                                  None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % f_name, 'simple',
                                                  f_checksum, CA, f_size, f_mimetype, f_created,
                                                  'Datafile', 'digiprovMD001', None])
                        
                        # ms_files example
                        #ms_files.append([Sec_NAME, Sec_ID, Grp_NAME, Grp_ID, Grp_USE,
                        #                 md_type, a_ID, a_LOCTYPE, a_href, a_type,
                        #                 a_CHECKSUM, a_CHECKSUMTYPE, a_SIZE, a_MIMETYPE, a_CREATED,
                        #                 a_MDTYPE/a_USE, a_OTHERMDTYPE/a_ADMID, a_DMDID])
                else:
                    status_code = 1
                    error_list.append('Problem to get filelist from objectpath: %s, errno: %s' % (ObjectPath,errno))
                    for ss in status_list2:
                        status_list.append(ss)
                    for ee in error_list2:
                        error_list.append(ee)
            # Create PREMISfile
            if PREMIS_ObjectPath is not None:
                if details_flag: logger.info('Object: %s, create PREMIS - len: %s - start' % (ObjectIdentifierValue, len(self.ms_files)))
                status_list.append('Create new PREMIS: %s' % PREMIS_ObjectPath)
                P_ObjectIdentifierValue = self.ObjectIdentifierValue  
                P_preservationLevelValue = 'full'
                P_compositionLevel = '0'
                P_formatName = 'tar'
                xml_PREMIS = ESSMD.createPremis(FILE=['simple','','NO/RA',P_ObjectIdentifierValue,P_preservationLevelValue,[],P_compositionLevel,P_formatName,'','bevarandesystemet',[]])
                for res_file in self.ms_files:
                    if res_file[0] == 'fileSec':
                        F_objectIdentifierValue = '%s/%s' % (ObjectIdentifierValue,res_file[8][5:])
                        F_messageDigest = res_file[10]
                        F_messageDigestAlgorithm = res_file[11]
                        F_size = str(res_file[12])
                        F_formatName = res_file[13]
                        F_formatName = ESSPGM.Check().MIMEtype2PREMISformat(res_file[13])
                        xml_PREMIS = ESSMD.AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','NO/RA',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_messageDigest,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_ObjectIdentifierValue,'']],[['structural','is part of','NO/RA',P_ObjectIdentifierValue]])])
        
                xml_PREMIS = ESSMD.AddPremisAgent(xml_PREMIS,[('NO/RA','ESSArch','ESSArch E-Arkiv','software')])
                if details_flag: logger.info('Object: %s, create PREMIS - len: %s - end' % (ObjectIdentifierValue, len(self.ms_files)))
                if details_flag: logger.info('Object: %s, validate PREMIS - len: %s - start' % (ObjectIdentifierValue, len(self.ms_files)))
                errno,why = ESSMD.validate(xml_PREMIS)
                if errno:
                    status_code = 2
                    error_list.append('Problem to validate "PREMISfile: %s", errno: %s, why: %s' % (PREMIS_ObjectPath,errno,str(why)))
                if details_flag: logger.info('Object: %s, validate PREMIS - len: %s - end' % (ObjectIdentifierValue, len(self.ms_files)))
                if details_flag: logger.info('Object: %s, write PREMIS - len: %s - start' % (ObjectIdentifierValue, len(self.ms_files)))
                errno,why = ESSMD.writeToFile(xml_PREMIS,PREMIS_ObjectPath)
                if errno:
                    status_code = 3
                    error_list.append('Problem to write "PREMISfile: %s", errno: %s, why: %s' % (PREMIS_ObjectPath,errno,str(why)))
                if details_flag: logger.info('Object: %s, write PREMIS - len: %s - end' % (ObjectIdentifierValue, len(self.ms_files)))
                #errno,why = ESSMD.validate(FILENAME = PREMIS_ObjectPath, XMLSchema='http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd')
                #if errno:
                #    status_code = 2
                #    error_list.append('Problem to validate "PREMISfile: %s", errno: %s, why: %s' % (PREMIS_ObjectPath,errno,str(why)))
                
                # Add PREMISfile to METS filelist
                f_name = PREMIS_ObjectPath.replace( ObjectPath + '/', '' )
                f_stat = os.stat(PREMIS_ObjectPath)
                f_size = f_stat.st_size
                f_created = datetime.datetime.fromtimestamp(f_stat.st_mtime,pytz.timezone(TimeZone)).replace(microsecond=0).isoformat()
                f_checksum = ESSPGM.Check().calcsum(PREMIS_ObjectPath, CA)
                f_mimetype = 'text/xml'            
                self.ms_files.append(['amdSec', None, 'digiprovMD', 'digiprovMD001', None,
                                     None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % f_name, 'simple',
                                     f_checksum, CA, f_size, 'text/xml', f_created,
                                     'PREMIS', None, None,
                                     ])
                
          
            # define namespaces
            if namespacedef is None:
                METS_NAMESPACE = SchemaProfile.objects.get(entity='mets_namespace').value
                METS_SCHEMALOCATION = SchemaProfile.objects.get(entity='mets_schemalocation').value
                XLINK_NAMESPACE = SchemaProfile.objects.get(entity='xlink_namespace').value
                XSI_NAMESPACE = SchemaProfile.objects.get(entity='xsi_namespace').value
                self.namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
                self.namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
                self.namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
                self.namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
            else:
                self.namespacedef = namespacedef
    
            if status_code == 0:
                if details_flag: logger.info('Object: %s, create METS - len: %s - start' % (ObjectIdentifierValue, len(self.ms_files)))
                errno,info_list = ESSMD.Create_IP_mets(ObjectIdentifierValue = self.ObjectIdentifierValue, 
                                                       METS_ObjectPath = self.Cmets_objpath,
                                                       agent_list = self.METS_agent_list, 
                                                       altRecordID_list = self.METS_altRecordID_list, 
                                                       file_list = self.ms_files, 
                                                       namespacedef = self.namespacedef, 
                                                       METS_LABEL = self.METS_LABEL, 
                                                       METS_PROFILE = self.METS_PROFILE, 
                                                       METS_TYPE = METS_TYPE, 
                                                       METS_RECORDSTATUS = self.METS_RECORDSTATUS, 
                                                       METS_DocumentID = self.METS_DocumentID,
                                                       TimeZone = TimeZone)
                status_code = errno
                for s in info_list[0]:
                    status_list.append(s)
                for e in info_list[1]:
                    error_list.append(e)
                if details_flag: logger.info('Object: %s, create METS - len: %s - end' % (ObjectIdentifierValue, len(self.ms_files)))
        return status_code,[status_list,error_list]

        
class TestTask(JobtasticTask):

    significant_kwargs = [
        ('TestString', str),
        ('timetorun', str),                          
                          ]
    
    herd_avoidance_timeout = 0 #120  # Give it two minutes
    
    # Cache for 10 minutes if they haven't added any todos
    cache_duration = 0 #600
    
    # Soft time limit. Defaults to the CELERYD_TASK_SOFT_TIME_LIMIT setting.
    #soft_time_limit = None
    
    # Hard time limit. Defaults to the CELERYD_TASK_TIME_LIMIT setting.
    time_limit = 86400

    def calculate_result(self,TestString, timetorun,  **kwargs):
        testdrive = 1
        update_frequency = 1
        runs = int(timetorun)
        while(testdrive < runs):
            self.update_progress(completed_count=testdrive,
                                total_count=runs,
                                update_frequency=update_frequency,
                                )
            logger.info('testdrive nummber: %s, timetorun: %s' % (testdrive, timetorun))
            testdrive = testdrive + 1
            sleep(1)
       
        result = {}
        result['category'] = 'controlarea'
        result['label'] = 'Test task'
        result['reqpurpose'] = TestString
        result['user'] = 'testuser'
        #raise ControlareaException(result)    
        return result
    
class ControlareaException(Exception):
    def __init__(self, value):
        self.value = value
        super(ControlareaException, self).__init__(value)
        

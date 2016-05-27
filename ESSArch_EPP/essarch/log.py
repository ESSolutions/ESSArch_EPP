#!/usr/bin/env /ESSArch/pd/python/bin/python
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
from optparse import OptionParser
from lxml import etree
import sys

ESSDB_flag = 1

import ESSMD,pytz,datetime,uuid,ESSPGM,stat,os,os.path as op

if ESSDB_flag == 1:
    from configuration.models import Parameter, SchemaProfile, Path, IPParameter
    from essarch.models import ArchiveObject, eventIdentifier, PackageType_CHOICES
    from django.utils import timezone

if ESSDB_flag == 0: ioessarch = 'W:\ioessarch\logs'
elif ESSDB_flag == 1: ioessarch = Path.objects.get(entity='path_gate_reception').value

# Configuration
eventType_keys = {
    1:['Leveransen forbereds og genereras','10000'],
    2:['Leverans sker','10001'],
    3:['Mottagning av leverans','10002'],
    4:['Overlamning av leverans','10003'],
    5:['Mottagning av leverans','10004'],
    6:['Registrering av leverans','10005'],
    7:['Journalforing i journalsystem','10006'],
    8:['Registrering i arkivsystem','10007'],
    9:['Mottakskvittering sendes','10008'],
    10:['Skapa loggcirkular','10009'],
    11:['UUID skapas for leverans','10010'],
    12:['Skapa AIC_UUID katalogstruktur','10011'],
    13:['Loggcirkular skapas under AIC_UUID','10012'],
    14:['Viruskontroll','10013'],
    15:['Leveransen kontrolleras','10014'],
    16:['Overlamning av leverans','10015'],
    17:['Mottagning av leverans','10016'],
    18:['Overlamning av leverans','10017'],
    19:['Bearbeiding av katalogstruktur IP','10144'],
    20:['Utpakking av materialet','10145'],
    21:['Testing av materialet','10146'],
    22:['Endring i materialet','10147'],
    23:['Innhenting av tilleggsinformasjon','10148'],
    24:['Endring av metadata','10149'],
    25:['Brev till arkivskaper','10150'],
}

# Namespaces
if ESSDB_flag == 0: METS_NAMESPACE = u"http://www.loc.gov/METS/"
elif ESSDB_flag == 1: METS_NAMESPACE = SchemaProfile.objects.get(entity='mets_namespace').value

MODS_NAMESPACE = u"http://www.loc.gov/mods/v3"

if ESSDB_flag == 0: METS_SCHEMALOCATION = u"http://schema.arkivverket.no/METS/v1.9/DIAS_METS.xsd"
elif ESSDB_flag == 1: METS_SCHEMALOCATION = SchemaProfile.objects.get(entity='mets_schemalocation').value

if ESSDB_flag == 0: METS_PROFILE = u"http://xml.ra.se/mets/SWEIP.xml"
elif ESSDB_flag == 1: METS_PROFILE = SchemaProfile.objects.get(entity='mets_profile').value

if ESSDB_flag == 0: PREMIS_NAMESPACE = u"http://arkivverket.no/standarder/PREMIS" 
elif ESSDB_flag == 1: PREMIS_NAMESPACE = SchemaProfile.objects.get(entity='premis_namespace').value

if ESSDB_flag == 0: PREMIS_SCHEMALOCATION = u"http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd"
elif ESSDB_flag == 1: PREMIS_SCHEMALOCATION = SchemaProfile.objects.get(entity='premis_schemalocation').value

if ESSDB_flag == 0: PREMIS_VERSION = u"2.0"
elif ESSDB_flag == 1: PREMIS_VERSION = SchemaProfile.objects.get(entity='premis_version').value

if ESSDB_flag == 0: XLINK_NAMESPACE = u"http://www.w3.org/1999/xlink"
elif ESSDB_flag == 1: XLINK_NAMESPACE = SchemaProfile.objects.get(entity='xlink_namespace').value

if ESSDB_flag == 0: XSI_NAMESPACE = u"http://www.w3.org/2001/XMLSchema-instance"
elif ESSDB_flag == 1: XSI_NAMESPACE = SchemaProfile.objects.get(entity='xsi_namespace').value

if ESSDB_flag == 0: XSD_NAMESPACE = u"http://www.w3.org/2001/XMLSchema"
elif ESSDB_flag == 1: XSD_NAMESPACE = SchemaProfile.objects.get(entity='xsd_namespace').value

if ESSDB_flag == 0: MIX_NAMESPACE = u"http://xml.ra.se/MIX"
elif ESSDB_flag == 1: MIX_NAMESPACE = SchemaProfile.objects.get(entity='mix_namespace').value

if ESSDB_flag == 0: MIX_SCHEMALOCATION = u"http://xml.ra.se/MIX/RA_MIX.xsd"
elif ESSDB_flag == 1: MIX_SCHEMALOCATION = SchemaProfile.objects.get(entity='mix_schemalocation').value

if ESSDB_flag == 0: ADDML_NAMESPACE = u"http://arkivverket.no/Standarder/addml"
elif ESSDB_flag == 1: ADDML_NAMESPACE = SchemaProfile.objects.get(entity='addml_namespace').value

if ESSDB_flag == 0: ADDML_SCHEMALOCATION = u"http://schema.arkivverket.no/ADDML/v8.2/addml.xsd"
elif ESSDB_flag == 1: ADDML_SCHEMALOCATION = SchemaProfile.objects.get(entity='addml_schemalocation').value

if ESSDB_flag == 0: XHTML_NAMESPACE = u"http://www.w3.org/1999/xhtml"
elif ESSDB_flag == 1: XHTML_NAMESPACE = SchemaProfile.objects.get(entity='xhtml_namespace').value

if ESSDB_flag == 0: XHTML_SCHEMALOCATION = u"http://www.w3.org/MarkUp/SCHEMA/xhtml11.xsd"
elif ESSDB_flag == 1: XHTML_SCHEMALOCATION = SchemaProfile.objects.get(entity='xhtml_schemalocation').value

def eventType_list():
    print '------------------------------------------------------------------------'
    print 'select - description - eventType'
    print '------------------------------------------------------------------------'
    for i in eventType_keys.keys():
        print '%s - %s - %s' % (i, eventType_keys[i][0], eventType_keys[i][1])
    print '------------------------------------------------------------------------'

def create_new_log(info_file, target_path,agentIdentifierValue='ESSArch'):
    status_code = 0
    status_list = []
    error_list = []
    significantProperties = []

    if status_code == 0:
        return_code,status,info_entrys = get_infoxml_info(info_file)
        if return_code == 0:
            for info_entry in info_entrys:
                if info_entry[0] == 'creator':
                    creator=info_entry[1]
                    significantProperties.append(['creator',creator])
                elif info_entry[0] == 'system':
                    system=info_entry[1]
                    significantProperties.append(['system',system])
                elif info_entry[0] == 'version':
                    version=info_entry[1]
                    significantProperties.append(['version',version])
        else:
            error_list.append('Problem with info.xml, Status: %s, Error: %s' % (return_code,str(status)))
            status_code = 1

    if status_code == 0:
        logfilepath = ''
        return_code,status,file_list = get_logxml_filename(creator=creator,
                                                           system=system,
                                                           version=version)
        if return_code == 0:
            if len(file_list):
                error_list.append('Creator: %s , System: %s, Version: %s , already exist in logfilelist: %s' % (creator,system,version,str(file_list)))
                status_code = 2
        else:
            error_list.append('Problem to check if logfile already exist, Status: %s Error: %s' % (return_code,str(status)))
            status_code = 3

    if status_code == 0:
        AIC_uuid = str(uuid.uuid1())
        IP_uuid = str(uuid.uuid1())
        AIC_root = os.path.join(target_path,AIC_uuid)
        Package_root = os.path.join(AIC_root,IP_uuid)
        Package_dmd = os.path.join(Package_root,'descriptive_metadata')
        Package_amd = os.path.join(Package_root,'administrative_metadata')
        Package_ro = os.path.join(Package_amd,'repository_operations')
        Package_content = os.path.join(Package_root,'content')
        try:
            status_list.append('Create new package directory structure: %s' % Package_root)
            os.mkdir(AIC_root)
            os.mkdir(Package_root)
            os.mkdir(Package_dmd)
            os.mkdir(Package_amd)
            os.mkdir(Package_ro)
            os.mkdir(Package_content)
        except (os.error), why:
            status_code = 2
            error_list.append('Problem to create package structure, ERROR: %s' % str(why))

    if status_code == 0:
        logfile_path=os.path.join(AIC_root,'log.xml')
        return_code,status = log(logfile_path,
                                 IP_uuid,
                                 u'10009',
                                 u'Skapa loggcirkular',
                                 u'0',
                                 u'Success to create %s' % logfile_path,
                                 significantProperties,
                                 agentIdentifierValue=agentIdentifierValue,
                                 aic_object=AIC_uuid,
                                 new_flag=True)
        if return_code == 0:
            status_list.append('Success to create new logfile: %s' % logfile_path)
        else:
            error_list.append('Problem to create new logfile: %s, Status: %s, Error: %s' % (logfile_path,return_code,str(status)))
            status_code = 3

    if status_code == 0:
        #print 'Success to create_new_log.'
        return status_code,[status_list,error_list],[AIC_uuid,IP_uuid,logfile_path]
    else:
        #print 'Failed to create_new_log, ERROR: %s' % str(error_list)
        return status_code,[status_list,error_list],['','','']

def log(logfile,objectIdentifierValue,eventType,eventDetail,eventOutcome,eventOutcomeDetailNote,significantProperties,agentIdentifierValue='ESSArch',aic_object=None,new_flag=False):

    status_code = 0
    status_list = []
    error_list = []
    res = []

    stockholm=timezone.get_default_timezone()
    IdentifierType = 'NO/RA'
 
    DOC = None

    if logfile and not new_flag:
        try:
            DOC  =  etree.ElementTree ( file=logfile )
        except etree.XMLSyntaxError, detail:
            error_list.append([10,str(detail)])
            status_code=10
        except IOError, detail:
            error_list.append([20,str(detail)])
            status_code=20

    if status_code == 0:
        if not DOC:
            relation=[]
            if aic_object:
                significantProperties.append(['aic_object',aic_object])
                relation.append(['structural','is part of',IdentifierType,aic_object])
            xml_PREMIS = ESSMD.createPremis(FILE=['simple','',IdentifierType,objectIdentifierValue,'full',significantProperties,'0','tar','','bevarandesystemet',relation])
        else:
            #xml_PREMIS = DOC.getroot()
            xml_PREMIS = DOC
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(stockholm).isoformat()
        eventDateTime = loc_dt_isoformat
        #eventOutcomeDetailNote = 'test av event'
        #agentIdentifierValue = 'ESSArch'
        #objectIdentifierValue = 'test object 1'
        xml_PREMIS = ESSMD.AddPremisEvent(xml_PREMIS,[(IdentifierType,str(uuid.uuid1()),eventType,eventDateTime,eventDetail,eventOutcome,eventOutcomeDetailNote,[[IdentifierType,agentIdentifierValue]],[[IdentifierType,objectIdentifierValue]])])
        if not DOC:
            xml_PREMIS = ESSMD.AddPremisAgent(xml_PREMIS,[(IdentifierType,'ESSArch','ESSArch E-Arkiv','software')])
        #errno,why = ESSMD.validate(xml_PREMIS)
        #if errno:
        #    print 'errno: %s, why: %s' % (str(errno),str(why))
        #print etree.tostring(xml_PREMIS,encoding='UTF-8', xml_declaration=True, pretty_print=True)
        return_code,status = ESSMD.writeToFile(xml_PREMIS,logfile)
        if return_code == 0:
            status_list.append('Success to create log entry in file: %s' % logfile)
        else:
            status_code = 1
            error_list.append('errno: %s, why: %s' % (str(return_code),str(status)))

    if status_code == 0:
        #print '%s' % str(status_list)
        return status_code,[status_list,error_list]
    else:
        #print 'Failed, ERROR: %s' % str(error_list)
        return status_code,[status_list,error_list]

def get_infoxml_info(logfile):
    status_code = 0
    status_list = []
    error_list = []
    res = []

    DOC = None

    if logfile:
        try:
            DOC  =  etree.ElementTree ( file=logfile )
        except etree.XMLSyntaxError, detail:
            error_list.append([10,str(detail)])
            status_code=10
        except IOError, detail:
            error_list.append([20,str(detail)])
            status_code=20

    if DOC is None:
        status_code = 1

    if status_code == 0:
        EL_root = DOC.getroot()
    
        if 'info' in EL_root.nsmap:
            info_NS = "{%s}" % EL_root.nsmap['info']
        elif None in EL_root.nsmap:
            info_NS = "{%s}" % EL_root.nsmap[None]

        # Fix for elementFormDefault="qualified" in schema, and xmlns=""
        #info_NS =""
    
        EL_arkivskaperInfo = EL_root.find("%sarkivskaperInfo" % (info_NS))
        if EL_arkivskaperInfo is not None:
            EL_arkivskaper = EL_arkivskaperInfo.find("%sarkivskaper[@navn]" % (info_NS))
            if EL_arkivskaper is not None:
                creator = ESSPGM.Check().str2unicode(EL_arkivskaper.attrib['navn'])
                res.append([u'creator',creator])
    
        EL_system = DOC.find("%ssystem" % (info_NS))
        if EL_system is not None:
            EL_systemName = EL_system.find("%ssystemNavn" % (info_NS))
            if EL_systemName is not None:
                system = ESSPGM.Check().str2unicode(EL_systemName.text)
                res.append([u'system',system])
            EL_systemVersion = EL_system.find("%sversjon" % (info_NS))
            if EL_systemVersion is not None:
                version = ESSPGM.Check().str2unicode(EL_systemVersion.text)
                res.append([u'version',version])

    if status_code == 0:
            return status_code,[status_list,error_list],res
    else:
            return status_code,[status_list,error_list],res

def get_logxml_info(logfile):
    status_code = 0
    status_list = []
    error_list = []
    res = []
    res_0 = []
    res_1 = []

    DOC = None

    if logfile:
        try:
            DOC  =  etree.ElementTree ( file=logfile )
        except etree.XMLSyntaxError, detail:
            error_list.append([10,str(detail)])
            status_code=10
        except IOError, detail:
            error_list.append([20,str(detail)])
            status_code=20

    if DOC is None:
        status_code = 1

    if status_code == 0:
        EL_root = DOC.getroot()
    
        premis_NS = "{%s}" % EL_root.nsmap['premis']

        ELs_object = DOC.findall("%sobject" % (premis_NS))
        for EL_object in ELs_object:
            objectIdentifierType = ''
            objectIdentifierValue = ''
            significantPropertiesType = ''
            significantPropertiesValue = ''
            significantProperties_list = []
            messageDigestAlgorithm = ''
            messageDigest = ''
            messageDigestOriginator = ''
            size = ''
            formatName = ''
            formatVersion = ''
            EL_objectIdentifierType = EL_object.find("%sobjectIdentifier/%sobjectIdentifierType" % (premis_NS,premis_NS))
            if EL_objectIdentifierType is not None:
                objectIdentifierType = ESSPGM.Check().str2unicode(EL_objectIdentifierType.text)
            EL_objectIdentifierValue = EL_object.find("%sobjectIdentifier/%sobjectIdentifierValue" % (premis_NS,premis_NS))
            if EL_objectIdentifierValue is not None:
                objectIdentifierValue = ESSPGM.Check().str2unicode(EL_objectIdentifierValue.text)
            ELs_significantProperties = EL_object.findall("%ssignificantProperties" % (premis_NS))
            for EL_significantProperties in ELs_significantProperties:
                EL_significantPropertiesType = EL_significantProperties.find("%ssignificantPropertiesType" % (premis_NS))
                if EL_significantPropertiesType is not None:
                    significantPropertiesType = ESSPGM.Check().str2unicode(EL_significantPropertiesType.text)
                EL_significantPropertiesValue = EL_significantProperties.find("%ssignificantPropertiesValue" % (premis_NS))
                if EL_significantPropertiesValue is not None:
                    significantPropertiesValue = ESSPGM.Check().str2unicode(EL_significantPropertiesValue.text)
                significantProperties_list.append([significantPropertiesType,significantPropertiesValue])
            EL_objectCharacteristics = EL_object.find("%sobjectCharacteristics" % premis_NS)
            if EL_objectCharacteristics is not None:
                EL_messageDigestAlgorithm = EL_objectCharacteristics.find("%sfixity/%smessageDigestAlgorithm" % (premis_NS,premis_NS))
                if EL_messageDigestAlgorithm is not None:
                    messageDigestAlgorithm = ESSPGM.Check().str2unicode(EL_messageDigestAlgorithm.text)
                EL_messageDigest = EL_objectCharacteristics.find("%sfixity/%smessageDigest" % (premis_NS,premis_NS))
                if EL_messageDigest is not None:
                    messageDigest = ESSPGM.Check().str2unicode(EL_messageDigest.text)
                EL_messageDigestOriginator = EL_objectCharacteristics.find("%sfixity/%smessageDigestOriginator" % (premis_NS,premis_NS))
                if EL_messageDigestOriginator is not None:
                    messageDigestOriginator = ESSPGM.Check().str2unicode(EL_messageDigestOriginator.text)
                EL_size = EL_objectCharacteristics.find("%ssize" % premis_NS)
                if EL_size is not None:
                    size = ESSPGM.Check().str2unicode(EL_size.text)
                EL_formatName = EL_objectCharacteristics.find("%sformat/%sformatDesignation/%sformatName" % (premis_NS,premis_NS,premis_NS))
                if EL_formatName is not None:
                    formatName = ESSPGM.Check().str2unicode(EL_formatName.text)
                EL_formatVersion = EL_objectCharacteristics.find("%sformat/%sformatDesignation/%sformatVersion" % (premis_NS,premis_NS,premis_NS))
                if EL_formatVersion is not None:
                    formatVersion = ESSPGM.Check().str2unicode(EL_formatVersion.text)
            res_0.append([objectIdentifierType,objectIdentifierValue,significantProperties_list,messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,formatName,formatVersion])

        ELs_event = DOC.findall("%sevent" % (premis_NS))
        for EL_event in ELs_event:
            eventIdentifierType = ''
            eventIdentifierValue = ''
            eventType = ''
            eventDateTime = ''
            eventDetail = ''
            eventOutcome = ''
            eventOutcomeDetailNote = ''
            linkingAgentIdentifierType = ''
            linkingAgentIdentifierValue = ''
            linkingObjectIdentifierType = ''
            linkingObjectIdentifierValue = ''
            EL_eventIdentifierType = EL_event.find("%seventIdentifier/%seventIdentifierType" % (premis_NS,premis_NS))
            if EL_eventIdentifierType is not None:
                eventIdentifierType = ESSPGM.Check().str2unicode(EL_eventIdentifierType.text)
            EL_eventIdentifierValue = EL_event.find("%seventIdentifier/%seventIdentifierValue" % (premis_NS,premis_NS))
            if EL_eventIdentifierValue is not None:
                eventIdentifierValue = ESSPGM.Check().str2unicode(EL_eventIdentifierValue.text)
            EL_eventType = EL_event.find("%seventType" % (premis_NS))
            if EL_eventType is not None:
                eventType = ESSPGM.Check().str2unicode(EL_eventType.text)
            EL_eventDateTime = EL_event.find("%seventDateTime" % (premis_NS))
            if EL_eventDateTime is not None:
                eventDateTime = ESSPGM.Check().str2unicode(EL_eventDateTime.text)
            EL_eventDetail = EL_event.find("%seventDetail" % (premis_NS))
            if EL_eventDetail is not None:
                eventDetail = ESSPGM.Check().str2unicode(EL_eventDetail.text)
            EL_eventOutcome = EL_event.find("%seventOutcomeInformation/%seventOutcome" % (premis_NS,premis_NS))
            if EL_eventOutcome is not None:
                eventOutcome = ESSPGM.Check().str2unicode(EL_eventOutcome.text)
            EL_eventOutcomeDetailNote = EL_event.find("%seventOutcomeInformation/%seventOutcomeDetail/%seventOutcomeDetailNote" % (premis_NS,premis_NS,premis_NS))
            if EL_eventOutcomeDetailNote is not None:
                eventOutcomeDetailNote = ESSPGM.Check().str2unicode(EL_eventOutcomeDetailNote.text)
            EL_linkingAgentIdentifierType = EL_event.find("%slinkingAgentIdentifier/%slinkingAgentIdentifierType" % (premis_NS,premis_NS))
            if EL_linkingAgentIdentifierType is not None:
                linkingAgentIdentifierType = ESSPGM.Check().str2unicode(EL_linkingAgentIdentifierType.text)
            EL_linkingAgentIdentifierValue = EL_event.find("%slinkingAgentIdentifier/%slinkingAgentIdentifierValue" % (premis_NS,premis_NS))
            if EL_linkingAgentIdentifierValue is not None:
                linkingAgentIdentifierValue = ESSPGM.Check().str2unicode(EL_linkingAgentIdentifierValue.text)
            EL_linkingObjectIdentifierType = EL_event.find("%slinkingObjectIdentifier/%slinkingObjectIdentifierType" % (premis_NS,premis_NS))
            if EL_linkingObjectIdentifierType is not None:
                linkingObjectIdentifierType = ESSPGM.Check().str2unicode(EL_linkingObjectIdentifierType.text)
            EL_linkingObjectIdentifierValue = EL_event.find("%slinkingObjectIdentifier/%slinkingObjectIdentifierValue" % (premis_NS,premis_NS))
            if EL_linkingObjectIdentifierValue is not None:
                linkingObjectIdentifierValue = ESSPGM.Check().str2unicode(EL_linkingObjectIdentifierValue.text)
            res_1.append([eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,eventOutcome,eventOutcomeDetailNote,linkingAgentIdentifierType,linkingAgentIdentifierValue,linkingObjectIdentifierType,linkingObjectIdentifierValue])
        res=[res_0,res_1]
    if status_code == 0:
            return status_code,[status_list,error_list],res
    else:
            return status_code,[status_list,error_list],res

def ExportLogEventsToFile(logfilename, ip_uuid=None, aic_uuid=None, StatusProcess=None, TimeZone=timezone.get_default_timezone_name()):
    #######################################################################################################################
    # Export logevents from database to logfile
    #
    status_code = 0
    status_list = []
    error_list = []
    ip_obj_list = []
    
    if aic_uuid:
        ip_obj_list = ArchiveObject.objects.filter(reluuid_set__AIC_UUID=aic_uuid).order_by('Generation')
        if StatusProcess:
            ip_obj_list = ip_obj_list.filter(StatusProcess=StatusProcess)
            
    if ip_uuid and not aic_uuid:
        ip_obj = ArchiveObject.objects.filter(ObjectUUID = ip_uuid)[:1]
        if ip_obj:
            ip_obj = ip_obj.get()
            ip_obj_list.append(ip_obj)
    
    IdentifierType = 'NO/RA'
    object_list = []
    event_list = []
    for ip_obj in ip_obj_list:
        ip_obj_data = ip_obj.archiveobjectdata_set.all()[:1]
        significantProperties_list = []
        significantProperties_list.append(['createdate',ip_obj.EntryDate.astimezone(pytz.timezone(TimeZone)).isoformat()])
        significantProperties_list.append(['archivist_organization',ip_obj.EntryAgentIdentifierValue])
        if ip_obj_data:
            ip_obj_data = ip_obj_data[0]
            significantProperties_list.append(['label',ip_obj_data.label])
            if not ip_obj_data.startdate is None:
                significantProperties_list.append(['startdate',ip_obj_data.startdate.astimezone(pytz.timezone(TimeZone)).isoformat()])
            if not ip_obj_data.enddate is None:
                significantProperties_list.append(['enddate',ip_obj_data.enddate.astimezone(pytz.timezone(TimeZone)).isoformat()])    
        significantProperties_list.append(['iptype',dict(PackageType_CHOICES)[ip_obj.OAISPackageType]])
        significantProperties_list.append(['generation',str(ip_obj.Generation)])
        object_list.append([IdentifierType,
                            ip_obj.ObjectIdentifierValue,
                            significantProperties_list,
                            '',
                            '',
                            '',
                            '',
                            'tar',
                            '',
                            ])
        # object_list = [objectIdentifierType,objectIdentifierValue,significantProperties_list,
        #                messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,
        #                formatName,formatVersion]

        event_obj_list = eventIdentifier.objects.filter(linkingObjectIdentifierValue = ip_obj.ObjectIdentifierValue).all()
        for event_obj in event_obj_list:
            event_list.append([IdentifierType,
                               event_obj.eventIdentifierValue,
                               str(event_obj.eventType),
                               event_obj.eventDateTime.astimezone(pytz.timezone(TimeZone)).isoformat(),
                               event_obj.eventDetail,
                               str(event_obj.eventOutcome),
                               event_obj.eventOutcomeDetailNote,
                               IdentifierType,
                               event_obj.linkingAgentIdentifierValue,
                               IdentifierType,
                               event_obj.linkingObjectIdentifierValue,
                               ])
                # event_list = [eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,
                #               eventOutcome,eventOutcomeDetailNote,linkingAgentIdentifierType,linkingAgentIdentifierValue,
                #               linkingObjectIdentifierType,linkingObjectIdentifierValue] 
     
    if ip_uuid and aic_uuid:
        ip_obj = ArchiveObject.objects.filter(ObjectUUID = ip_uuid)[:1]
        if ip_obj:
            object_list = []
            ip_obj = ip_obj.get()
            ip_obj_data = ip_obj.archiveobjectdata_set.all()[:1]
            significantProperties_list = []
            significantProperties_list.append(['createdate',ip_obj.EntryDate.astimezone(pytz.timezone(TimeZone)).isoformat()])
            significantProperties_list.append(['archivist_organization',ip_obj.EntryAgentIdentifierValue])
            if ip_obj_data:
                ip_obj_data = ip_obj_data[0]
                significantProperties_list.append(['label',ip_obj_data.label])
                if not ip_obj_data.startdate is None:
                    significantProperties_list.append(['startdate',ip_obj_data.startdate.astimezone(pytz.timezone(TimeZone)).isoformat()])
                if not ip_obj_data.enddate is None:
                    significantProperties_list.append(['enddate',ip_obj_data.enddate.astimezone(pytz.timezone(TimeZone)).isoformat()])    
            significantProperties_list.append(['iptype',dict(PackageType_CHOICES)[ip_obj.OAISPackageType]])
            significantProperties_list.append(['generation',str(ip_obj.Generation)])
            object_list.append([IdentifierType,
                                ip_obj.ObjectIdentifierValue,
                                significantProperties_list,
                                '',
                                '',
                                '',
                                '',
                                'tar',
                                '',
                                ])
            # object_list = [objectIdentifierType,objectIdentifierValue,significantProperties_list,
            #                messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,
            #                formatName,formatVersion]
       
    if status_code == 0:             
        return_code,return_status_list = Create_logfile(logfilename, object_list, event_list, aic_uuid)
        for i in return_status_list[0]:
            status_list.append(i)
        for i in return_status_list[1]:
            error_list.append(i)
        status_code = return_code

    return status_code,[status_list,error_list]

def Create_logfile(logfilename,object_list,event_list,aic_object=None):
    #######################################################################################################################
    # Create_logfile
    #
    # parameters:
    # logfilename = "/IP_xxxx/log.xml"
    # aic_object = "e8a239b6-807a-11e2-b920-002215836551"
    #
    # object_list = [objectIdentifierType,objectIdentifierValue,significantProperties_list,
    #                messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,
    #                formatName,formatVersion]
    #
    # event_list = [eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,
    #               eventOutcome,eventOutcomeDetailNote,linkingAgentIdentifierType,linkingAgentIdentifierValue,
    #               linkingObjectIdentifierType,linkingObjectIdentifierValue] 
    #
    status_code = 0
    status_list = []
    error_list = []
 
    if status_code == 0:
        obj_num = 0
        for obj in object_list:
            #print 'obj: %s' % obj
            objectIdentifierType = obj[0] # 'SE/RA' or 'NO/RA' or 'SE/ESS'
            objectIdentifierValue = obj[1]
            significantProperties_list = obj[2]
            messageDigestAlgorithm = obj[3]
            messageDigest = obj[4]
            messageDigestOriginator = obj[5]
            size = obj[6]
            formatName = obj[7] # 'tar'
            formatVersion = obj[8]
            relation=[]
            xlink_type = 'simple'
            xlink_href = ''
            preservationLevelValue = 'full'
            compositionLevel = '0'
            storageMedium = 'Preservation platform ESSArch' # 'bevarandesystemet'
            if obj_num == 0:
                if aic_object:
                    significantProperties_list.append(['aic_object',aic_object])
                    relation.append(['structural','is part of',objectIdentifierType,aic_object])
                xml_PREMIS = ESSMD.createPremis(FILE=[xlink_type,
                                                      xlink_href,
                                                      objectIdentifierType,
                                                      objectIdentifierValue,
                                                      preservationLevelValue,
                                                      significantProperties_list,
                                                      compositionLevel,
                                                      formatName,
                                                      formatVersion,
                                                      storageMedium,
                                                      relation])
            else:
                xml_PREMIS = ESSMD.AddPremisFileObject(xml_PREMIS,FILES=[(xlink_type,
                                                                          xlink_href,
                                                                          objectIdentifierType,
                                                                          objectIdentifierValue,
                                                                          preservationLevelValue,
                                                                          significantProperties_list,
                                                                          compositionLevel,
                                                                          [], #[[messageDigestAlgorithm,messageDigest,messageDigestOriginator]],
                                                                          size,
                                                                          formatName,
                                                                          formatVersion,
                                                                          '', #[[objectCharacteristicsExtension XML etree.Elemt]],
                                                                          [['','','','',storageMedium]], #[[xlink_type,xlink_href,contentLocationType,contentLocationValue,storageMedium],...],
                                                                          relation,
                                                                          )])
            obj_num += 1

    if status_code == 0:
        for event in event_list:
            #print 'event %s' % event
            eventIdentifierType = event[0]
            eventIdentifierValue = event[1]
            eventType = event[2]
            eventDateTime = event[3]
            eventDetail = event[4]
            eventOutcome = event[5]
            eventOutcomeDetailNote = event[6]
            linkingAgentIdentifierType = event[7]
            linkingAgentIdentifierValue = event[8]
            linkingObjectIdentifierType = event[9]
            linkingObjectIdentifierValue = event[10]

            xml_PREMIS = ESSMD.AddPremisEvent(xml_PREMIS,[(eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,eventOutcome,eventOutcomeDetailNote,[[linkingAgentIdentifierType,linkingAgentIdentifierValue]],[[linkingObjectIdentifierType,linkingObjectIdentifierValue]])])
        #xml_PREMIS = ESSMD.AddPremisAgent(xml_PREMIS,[(IdentifierType,'ESSArch','ESSArch E-Arkiv','software')])
        #errno,why = ESSMD.validate(xml_PREMIS)
        #if errno:
        #    print 'errno: %s, why: %s' % (str(errno),str(why))
        #print etree.tostring(xml_PREMIS,encoding='UTF-8', xml_declaration=True, pretty_print=True)
        return_code,status = ESSMD.writeToFile(xml_PREMIS,logfilename)
        if return_code == 0:
            status_list.append('Success to create logfile: %s' % logfilename)
        else:
            status_code = 1
            error_list.append('errno: %s, why: %s' % (str(return_code),str(status)))
    return status_code,[status_list,error_list]

def get_logxml_filename(ObjectIdentifierValue=None, creator=None, system= None, version=None, path=ioessarch):
    status_code = 0
    status_list = []
    error_list = []
    res = []
    if status_code == 0:
        return_code,status,filelist = Functions().GetFiletree(path,['test1','log1.xml','log.xml'])
        if return_code == 0:
            for i in filelist:
                match_flag = 1
                #ObjectIdentifierValue_flag = 0
                #creator_flag = 0
                #system_flag = 0
                #version_flag = 0
                return_code,status,info_entrys =  get_logxml_info(os.path.join(path,i[0]))
                if return_code == 0:
                    if ObjectIdentifierValue is not None:
                        if info_entrys[0][0][1] == ObjectIdentifierValue:
                            #print 'object OK'
                            pass
                        else:
                            #print 'false'
                            match_flag = 0
                    if match_flag == 1: 
                        for info_entry in info_entrys[0]:
                            #print '------------------------------------------------------------------------'
                            #print 'ObjectType: %s, ObjectIndentifierValue: %s' % (info_entry[0],info_entry[1])
                            #print '------------------------------------------------------------------------'
                            for x in info_entry[2]:
                                #print 'Element: %s = %s' % (x[0],x[1])
                                if creator is not None: 
                                    if x == ['creator',creator]:
                                        #print 'creator OK'
                                        pass
                                    elif x[0] == 'creator':
                                        match_flag = 0
                                        #print 'set match_flag to 000'
                                if system is not None: 
                                    if x == ['system',system]:
                                        #print 'system OK'
                                        pass
                                    elif x[0] == 'system':
                                        match_flag = 0
                                        #print 'set match_flag to 0'
                                if version is not None: 
                                    if x == ['version',version]:
                                        #print 'version OK'
                                        pass
                                    elif x[0] == 'version':
                                        match_flag = 0
                                        #print 'set match_flag to 0222'
                else:
                    status_code = 2
                    error_list.append('Error: %s, Status: %s' % (return_code,status))
                if return_code == 0:
                    if match_flag == 1:
                        res.append(os.path.join(path,i[0]))
        else:
            status_code = 1
            error_list.append('Error: %s, Status: %s' % (return_code,status))

    if status_code == 0:
            return status_code,[status_list,error_list],res
    else:
            return status_code,[status_list,error_list],res

def get_arkivuttrekk_info(logfile):
    stockholm=timezone.get_default_timezone()
    status_code = 0
    status_list = []
    error_list = []
    res = []

    DOC = None

    if logfile:
        try:
            DOC  =  etree.ElementTree ( file=logfile )
        except etree.XMLSyntaxError, detail:
            error_list.append([10,str(detail)])
            status_code=10
        except IOError, detail:
            error_list.append([20,str(detail)])
            status_code=20

    if DOC is None:
        status_code = 1
    if status_code == 0:
        EL_root = DOC.getroot()

        if 'addml' in EL_root.nsmap:
            addml_NS = "{%s}" % EL_root.nsmap['addml']
        elif None in EL_root.nsmap:
            addml_NS = "{%s}" % EL_root.nsmap[None]

        description = ''
        additionalElement_list = []


        EL_dataset = DOC.find("%sdataset" % (addml_NS))
        EL_description = EL_dataset.find("%sdescription" % (addml_NS))
        if EL_description is not None:
            description = ESSPGM.Check().str2unicode(EL_description.text)

        EL_additionalElements = DOC.findall("//%sadditionalElement[@name]" % (addml_NS))
        for EL_additionalElement in EL_additionalElements:
            name = ESSPGM.Check().str2unicode(EL_additionalElement.attrib['name'])
            if EL_additionalElement.find("%svalue" % (addml_NS)) is not None:
                value = ESSPGM.Check().str2unicode(EL_additionalElement.find("%svalue" % (addml_NS)).text)
                #print 'name: %s, value: %s' % (name,value)
                if name == 'recordCreator':
                    additionalElement_list.append([u'creator',value])
                elif name == 'systemName':
                    additionalElement_list.append([u'system',value])
                elif name == 'version':
                    additionalElement_list.append([u'version',value])
#        EL_version = DOC.find('//%sproperty[@name="info"]/%sproperties/%sproperty[@name="type"]/%sproperties/%sproperty[@name="version"]/%svalue' % (addml_NS,addml_NS,addml_NS,addml_NS,addml_NS,addml_NS))
#        if EL_version is not None:
#            version = ESSPGM.Check().str2unicode(EL_version.text)
#            additionalElement_list.append([u'version',version])

        res = [description,additionalElement_list]
    if status_code == 0:
        return status_code,[status_list,error_list],res
    else:
        return status_code,[status_list,error_list],res

class Functions:
    "Get filetree"
    ###############################################
    def GetFiletree(self,path,find_names=[]):
        self.status_code = 0
        self.status_list = []
        self.error_list = []
        self.res = []
        try:
            if os.path.exists(path):
                if os.access(path, os.R_OK) and os.access(path, os.W_OK) and os.access(path, os.X_OK):
                    for self.f in os.listdir(path):
                        self.path = os.path.join(path,self.f)
                        if os.access(self.path, os.R_OK):
                            self.mode = os.stat(self.path)
                            if stat.S_ISREG(self.mode[0]):                   # It's a file
                                if find_names: 
                                    if self.f in find_names:
                                        self.res.append([self.f, os.stat(self.path)])
                                else:
                                    self.res.append([self.f, os.stat(self.path)])
                            elif stat.S_ISDIR(self.mode[0]):                 # It's a directory
                                return_code,status,self.dir_file_list = Functions().GetFiletree(self.path,find_names)
                                if return_code == 0:
                                    for self.df in self.dir_file_list:
                                        self.res.append([self.f + '/' + self.df[0], self.df[1]])
                                else:
                                    return return_code,status,self.res 
                        else:
                            self.status_code = 12
                            self.error_list.append('Permision problem for path: %s' % self.path)
                else:
                    self.status_code = 11
                    self.error_list.append('Permision problem for path: %s' % path)
            else:
                self.status_code = 13
                self.error_list.append('No such file or directory: %s' % path)
        except OSError:
            self.status_code = sys.exc_info()[1][0]
            self.error_list.append(sys.exc_info()[1][1] + ': ' + path)
        if self.status_code == 0:
            return self.status_code,[self.status_list,self.error_list],self.res
        else:
            return self.status_code,[self.status_list,self.error_list],self.res

def main():
    op = OptionParser(usage="usage: %prog [options] arg", version="%prog 2.0")
    op.add_option("-e", "--listtype", help="List eventType's", action="store_true", dest="list_eventType_flag")
    op.add_option("-l", "--listlog", help="List logfile content", action="store_true", dest="list_log_flag")
    op.add_option("-i", "--infofile", help="infofile", dest="infofile")
    op.add_option("-n", "--new", help="New package", action="store_true", dest="new")
    op.add_option("-f", "--logfile", help="logfile", dest="logfile")
    op.add_option("-a", "--agent", help="Agent", dest="agentIdentifierValue")
    op.add_option("-o", "--object", help="Object", dest="objectIdentifierValue")
    op.add_option("-c", "--type", help="Select type, see -e", dest="eventType")
    op.add_option("-x", "--outcome", help="eventOutcome", dest="eventOutcome")
    op.add_option("-z", "--outdetail", help="eventOutcomeDetailNote", dest="eventOutcomeDetailNote")
    op.add_option("--creator", help="creator", dest="creator")
    op.add_option("--system", help="system", dest="system")
    op.add_option("--ver", help="version", dest="version")
    op.add_option("-g", "--findlogfiles", help="List logfilename's", action="store_true", dest="find_log_files_flag")
    op.add_option("--listarkivuttrekk", help="List arkivuttrekk content", action="store_true", dest="list_arkivuttrekk_flag")
    op.add_option("--listinfoxml", help="List infoxml content", action="store_true", dest="list_infoxml_flag")
    op.add_option("--diffinfo2arkivuttrekk", help="Diff info.xml/arkivuttrekk.xml", action="store_true", dest="diff_info2arkiv_flag")
    options, args = op.parse_args()
 
    significantProperties = []
    if options.creator:
        significantProperties.append(['creator',options.creator])
    if options.system:
        significantProperties.append(['system',options.system])
    if options.version:
        significantProperties.append(['version',options.version])

    if not options.agentIdentifierValue:
        options.agentIdentifierValue = 'ESSArch'
    
    if options.list_eventType_flag:
        eventType_list()

    elif options.list_log_flag:
        if options.logfile:
            return_code,status,info_entrys =  get_logxml_info(options.logfile)
            if return_code == 0:
                for i in info_entrys[0]:
                    print '------------------------------------------------------------------------'
                    print 'ObjectType: %s, ObjectIndentifierValue: %s' % (i[0],i[1])
                    print '------------------------------------------------------------------------'
                    for x in i[2]:
                        print 'Element: %s = %s' % (x[0],x[1])
                for i in info_entrys[1]:
                    print '------------------------------------------------------------------------'
                    print 'EventIndentifierValue: %s, EventType: %s, EventDateTime: %s, eventDetail: %s, outcome: %s, outcomeDetail: %s, linkingObject: %s' % (i[1],i[2],i[3],i[4],i[5],i[6],i[10])
            else:
                print 'Status: %s, Error: %s' % (return_code,str(status))
        else:
            print 'Missing option "logfile"'

    elif options.find_log_files_flag:
        return_code,status,file_list = get_logxml_filename(ObjectIdentifierValue=options.objectIdentifierValue,
                                                           creator=options.creator,
                                                           system=options.system,
                                                           version=options.version)
        if return_code == 0:
            print '------------------------------------------------------------------------'
            if len(file_list):
                for i in file_list:
                    print 'Found filename: %s' % (i)
            else:
                print 'No match found.'
            print '------------------------------------------------------------------------'
        else:
            print 'error:%s status:%s file_list:%s' % (return_code,status,file_list)

    elif options.list_arkivuttrekk_flag:
        if options.logfile:
            return_code,status,res =  get_arkivuttrekk_info(options.logfile)
            if return_code == 0:
                creator = ''
                system = ''
                version = ''
                description = res[0]
                for item in res[1]:
                    if item[0] == 'creator':
                        creator = item[1]
                    elif item[0] == 'system':
                        system = item[1]
                    elif item[0] == 'version':
                        version = item[1]
                print 'Description: %s' % description
                print 'Creator: %s' % creator
                print 'System: %s' % system
                print 'Version: %s' % version
            else:
                print 'Status: %s, Error: %s' % (return_code,str(status))
        else:
            print 'Missing option "logfile"'

    elif options.list_infoxml_flag:
        if options.infofile:
            return_code,status,res =  get_infoxml_info(options.infofile)
            if return_code == 0:
                creator = ''
                system = ''
                version = ''
                #description = res[0]
                for item in res:
                    if item[0] == 'creator':
                        creator = item[1]
                    elif item[0] == 'system':
                        system = item[1]
                    elif item[0] == 'version':
                        version = item[1]
                #print 'Description: %s' % description
                print 'Creator: %s' % creator
                print 'System: %s' % system
                print 'Version: %s' % version
            else:
                print 'Status: %s, Error: %s' % (return_code,str(status))
        else:
            print 'Missing option "infofile"'

    elif options.diff_info2arkiv_flag:
        ok_flag = 1

        if options.infofile:
            pass
        else:
            ok_flag = 0
            print 'Missing option "infofile"'

        if options.logfile:
            pass
        else:
            ok_flag = 0
            print 'Missing option "logfile"'

        if ok_flag == 1:
            creator_i = ''
            system_i = ''
            version_i = ''
            return_code,status,res =  get_infoxml_info(options.infofile)
            if return_code == 0:
                for item in res:
                    if item[0] == 'creator':
                        creator_i = item[1]
                    elif item[0] == 'system':
                        system_i = item[1]
                    elif item[0] == 'version':
                        version_i = item[1]
            else:
                ok_flag = 0
                print 'Status: %s, Error: %s' % (return_code,str(status))
        if ok_flag == 1:
            creator_a = ''
            system_a = ''
            version_a = ''
            return_code,status,res =  get_arkivuttrekk_info(options.logfile)
            if return_code == 0:
                description_a = res[0]
                for item in res[1]:
                    if item[0] == 'creator':
                        creator_a = item[1]
                    elif item[0] == 'system':
                        system_a = item[1]
                    elif item[0] == 'version':
                        version_a = item[1]
            else:
                ok_flag = 0
                print 'Status: %s, Error: %s' % (return_code,str(status))
        if ok_flag == 1:
            if creator_i == creator_a:
                print 'OK - info.xml creator: "%s" is equal to arkivuttrekk.xml creator: "%s"' % (creator_i,creator_a)
            else:
                print 'Error -  info.xml creator: "%s" is not equal to arkivuttrekk.xml creator: "%s"' % (creator_i,creator_a)
            if system_i == system_a:
                print 'OK - info.xml system: "%s" is equal to arkivuttrekk.xml system: "%s"' % (system_i,system_a)
            else:
                print 'Error -  info.xml system: "%s" is not equal to arkivuttrekk.xml system: "%s"' % (system_i,system_a)
            if version_i == version_a:
                print 'OK - info.xml version: "%s" is equal to arkivuttrekk.xml version: "%s"' % (version_i,version_a)
            else:
                print 'Error -  info.xml version: "%s" is not equal to arkivuttrekk.xml version: "%s"' % (version_i,version_a)

    elif options.new:
        if options.infofile:
            return_code,status,res = create_new_log(options.infofile,ioessarch,options.agentIdentifierValue)
            aic_uuid = res[0]
            ip_uuid = res[1]
            logfilepath = res[2]
            if return_code == 0:
                print 'Success to create packagestructure AIC: %s / IP: %s and logfile %s' % (aic_uuid,ip_uuid,logfilepath)
                #print 'Debug status: %s' % str(status)
            else:
                print 'Problem, Status: %s, Error: %s' % (return_code,str(status)) 
        else:
            print 'Missing option "infofile"'
 
    elif options.logfile:
        try:
            eventType = eventType_keys[int(options.eventType)][1]
            eventDetail = eventType_keys[int(options.eventType)][0]
        except KeyError:
            print 'Invalid eventtype'
        else:
            return_code,status = log(options.logfile,
                                 options.objectIdentifierValue,
                                 eventType,
                                 eventDetail,
                                 options.eventOutcome,
                                 options.eventOutcomeDetailNote,
                                 significantProperties,
                                 options.agentIdentifierValue)
            if return_code == 0:
                print 'Success to create logevent: "%s" for object: %s' % (eventType_keys[int(options.eventType)][1] + ', ' + eventType_keys[int(options.eventType)][0], options.objectIdentifierValue)
                #print 'Debug status: %s' % str(status)
            else:
                print 'Status: %s, Error: %s' % (return_code,str(status))
    else:
        print 'Missing option'

if __name__ == "__main__":
    main()

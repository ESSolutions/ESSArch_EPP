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

#Imports
import pytz, datetime, string, csv, os, uuid, ESSPGM, ESSDB, time, urllib, logging, shutil
from lxml import etree
import mets_eARD as m
from configuration.models import SchemaProfile, ArchivePolicy
from django.utils import timezone

# Namespaces
#METS_NAMESPACE = u"http://www.loc.gov/METS/"
#METS_NAMESPACE = u"http://arkivverket.no/standarder/METS"
METS_NAMESPACE = SchemaProfile.objects.get(entity = 'mets_namespace').value

MODS_NAMESPACE = u"http://www.loc.gov/mods/v3"

#METS_SCHEMALOCATION = u"http://www.loc.gov/mets/mets.xsd"
#METS_SCHEMALOCATION = u"http://xml.ra.se/METS/RA_METS_SWERA003.xsd"
#METS_SCHEMALOCATION = u"http://schema.arkivverket.no/METS/v1.9/DIAS_METS.xsd"
METS_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'mets_schemalocation').value

#METS_PROFILE = u"http://xml.ra.se/METS/SWERA003.xml"
#METS_PROFILE = u"http://xml.ra.se/mets/SWEIP.xml"
METS_PROFILE = SchemaProfile.objects.get(entity = 'mets_profile').value

#PREMIS_NAMESPACE = u"http://xml.ra.se/PREMIS"
#PREMIS_NAMESPACE = u"http://arkivverket.no/standarder/PREMIS"
#PREMIS_NAMESPACE = u"info:lc/xmlns/premis-v2"
PREMIS_NAMESPACE = SchemaProfile.objects.get(entity = 'premis_namespace').value 

#PREMIS_SCHEMALOCATION = u"http://xml.ra.se/PREMIS/RA_PREMIS.xsd"
#PREMIS_SCHEMALOCATION = u"http://schema.arkivverket.no/PREMIS/v2.0/DIAS_PREMIS.xsd"
#PREMIS_SCHEMALOCATION = u"http://www.loc.gov/standards/premis/v2/premis-v2-0.xsd"
PREMIS_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'premis_schemalocation').value 

#PREMIS_VERSION = u"2.0" 
PREMIS_VERSION = SchemaProfile.objects.get(entity = 'premis_version').value

#XLINK_NAMESPACE = u"http://www.w3.org/1999/xlink"
XLINK_NAMESPACE = SchemaProfile.objects.get(entity = 'xlink_namespace').value

#XSI_NAMESPACE = u"http://www.w3.org/2001/XMLSchema-instance" 
XSI_NAMESPACE = SchemaProfile.objects.get(entity = 'xsi_namespace').value

#XSD_NAMESPACE = u"http://www.w3.org/2001/XMLSchema" 
XSD_NAMESPACE = SchemaProfile.objects.get(entity = 'xsd_namespace').value

#MIX_NAMESPACE = u"http://xml.ra.se/MIX" 
MIX_NAMESPACE = SchemaProfile.objects.get(entity = 'mix_namespace').value

#MIX_SCHEMALOCATION = u"http://xml.ra.se/MIX/RA_MIX.xsd"
MIX_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'mix_schemalocation').value 

#ADDML_NAMESPACE = u"http://xml.ra.se/ADDML"
#ADDML_NAMESPACE = u"http://arkivverket.no/Standarder/addml" 
ADDML_NAMESPACE = SchemaProfile.objects.get(entity = 'addml_namespace').value

#ADDML_SCHEMALOCATION = u"http://schema.arkivverket.no/ADDML/v8.2/addml.xsd" 
ADDML_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'addml_schemalocation').value

#XHTML_NAMESPACE = u"http://www.w3.org/1999/xhtml"
XHTML_NAMESPACE = SchemaProfile.objects.get(entity = 'xhtml_namespace').value

#XHTML_SCHEMALOCATION = u"http://www.w3.org/MarkUp/SCHEMA/xhtml11.xsd"
XHTML_SCHEMALOCATION = SchemaProfile.objects.get(entity = 'xhtml_schemalocation').value

def getFileSizeFgrp001(DOC=None,USE=['ALL'],MIMETYPE=["ALL"],FILENAME=None):
    #MIMETYPE=["ALL","image/tiff","text/xml","video/mpeg","application/pdf","audio/mpeg"]
    #USE=["ALL","RA Datafile","Datafile","Information","RA Information"]
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [0,0],10,str(detail)
        except IOError, detail:
            return [0,0],20,str(detail)
    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    #mets_NS = "{%s}" % METS_NAMESPACE
    EL_fileGrp = None
    TotalSize = 0
    TotalNum = 0
    fileGrp_all = DOC.findall("%sfileSec/%sfileGrp[@ID]" % (mets_NS,mets_NS))
    for fileGrp in fileGrp_all:
        if fileGrp.get("ID") == "fgrp001":
            EL_fileGrp = fileGrp
    if EL_fileGrp is not None:
        file_all = EL_fileGrp.findall("%sfile" % mets_NS)
        for file_elem in file_all:
            file_attrib = file_elem.attrib
            if file_attrib['USE'] in USE or 'ALL' in USE and file_attrib['MIMETYPE'] in MIMETYPE or 'ALL' in MIMETYPE:
                TotalSize += int(file_attrib['SIZE']) 
                TotalNum += 1
        return [TotalNum,TotalSize],0,'' 
    else:
        return [TotalNum,TotalSize],1,'fileGRP with ID="fgrp001" in METS not found' 

def getFileSizePremis(DOC=None,formatName=['ALL'],formatVersion=["ALL"],FILENAME=None):
    #formatName=["ALL","image/tiff","text/xml","video/mpeg","application/pdf","audio/mpeg","TIFF 6.0"]
    #formatVersion=["ALL","6.0"]
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [0,0],10,str(detail)
        except IOError, detail:
            return [0,0],20,str(detail)
        if DOC is None:
            return [0,0],25,'Problem to parse filename: %s' % FILENAME
    if DOC is None:
        return [0,0],26,'Missing DOC, DOC is None'
    object_list,errno,why = getPremisObjects(DOC)
    if errno == 0:
        pass
    else:
        return [0,0],30,'getPremisObjects errno: %s, why: %s' % (str(errno),str(why))
    TotalSize = 0
    TotalNum = 0
    a = 0
    for object in object_list:
        if a == 0:
            a = 1
        else:
            if object[5] in formatName or 'ALL' in formatName and object[6] in formatVersion or 'ALL' in formatVersion:
                TotalSize += int(object[4])
                TotalNum += 1
    return [TotalNum,TotalSize],0,''

def getAIPObjects(DOC=None,USE=['ALL'],MIMETYPE=['ALL'],FILENAME=None):
    #MIMETYPE=["ALL","image/tiff","text/xml","video/mpeg","application/pdf","audio/mpeg"]
    #USE=["ALL","RA Datafile","Datafile","Information","RA Information"]
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [],10,str(detail)
        except IOError, detail:
            return [],20,str(detail)
    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    xlink_NS = "{%s}" % EL_root.nsmap['xlink']
    #mets_NS = "{%s}" % METS_NAMESPACE
    #xlink_NS = "{%s}" % XLINK_NAMESPACE
    fileGrp_all = DOC.findall("%sfileSec/%sfileGrp[@USE]" % (mets_NS,mets_NS))
    for fileGrp in fileGrp_all:
        if fileGrp.get("USE") == "FILES":
            EL_fileGrp = fileGrp
    res = []
    file_all = EL_fileGrp.findall("%sfile" % mets_NS)
    for file_elem in file_all:
        EL_file_FLocat = file_elem.find("%sFLocat" % mets_NS)
        file_FLocat_attrib = EL_file_FLocat.attrib
        file_attrib = file_elem.attrib
        if (file_attrib['USE'] in USE or 'ALL' in USE) and (file_attrib['MIMETYPE'] in MIMETYPE or 'ALL' in MIMETYPE):
            objectIdentifierValue_url = file_FLocat_attrib['%shref' % xlink_NS][5:]
            objectIdentifierValue = ESSPGM.Check().str2unicode(urllib.url2pathname(objectIdentifierValue_url))
            messageDigest = file_attrib['CHECKSUM']
            messageDigestAlgorithm = file_attrib['CHECKSUMTYPE']
            a_MIMETYPE = file_attrib['MIMETYPE']
            a_SIZE = file_attrib['SIZE']
            res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE])
    techMD_all = DOC.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
    for techMD in techMD_all:
        if techMD.get("ID") == "techMD001":
            techMD_techMD001 = techMD
            mdRef_all = techMD_techMD001.findall("%smdRef" % mets_NS)
            for mdRef in mdRef_all:
                mdRef_attrib = mdRef.attrib
                objectIdentifierValue_url = mdRef_attrib['%shref' % xlink_NS][5:]
                objectIdentifierValue = ESSPGM.Check().str2unicode(urllib.url2pathname(objectIdentifierValue_url))
                messageDigest = mdRef_attrib['CHECKSUM']
                messageDigestAlgorithm = mdRef_attrib['CHECKSUMTYPE']
                a_MIMETYPE = mdRef_attrib['MIMETYPE']
                a_SIZE = int(mdRef_attrib['SIZE'])
                res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE])
    digiprovMD_all = DOC.findall("%samdSec/%sdigiprovMD[@ID]" % (mets_NS,mets_NS))
    for digiprovMD in digiprovMD_all:
        mdRef_all = digiprovMD.findall("%smdRef" % mets_NS)
        for mdRef in mdRef_all:
            mdRef_attrib = mdRef.attrib
            objectIdentifierValue_url = mdRef_attrib['%shref' % xlink_NS][5:]
            objectIdentifierValue = ESSPGM.Check().str2unicode(urllib.url2pathname(objectIdentifierValue_url))
            messageDigest = mdRef_attrib['CHECKSUM']
            messageDigestAlgorithm = mdRef_attrib['CHECKSUMTYPE']
            a_MIMETYPE = mdRef_attrib['MIMETYPE']
            a_SIZE = int(mdRef_attrib['SIZE'])
            res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE])
    return res,0,''

def getPMETSInfo(DOC=None,USE=['ALL'],MIMETYPE=["ALL"],FILENAME=None):
    #MIMETYPE=["ALL","application/x-tar"]
    #USE=["ALL","PACKAGE"]
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [['',0,'','',''],['',0,'','','']],10,str(detail)
        except IOError, detail:
            return [['',0,'','',''],['',0,'','','']],20,str(detail)

    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    xlink_NS = "{%s}" % EL_root.nsmap['xlink']
    #mets_NS = "{%s}" % METS_NAMESPACE
    #xlink_NS = "{%s}" % XLINK_NAMESPACE
    res = []
    fileGrp_all = DOC.findall("%sfileSec/%sfileGrp" % (mets_NS,mets_NS))
    for fileGrp in fileGrp_all:
        if fileGrp.get("ID") == "fgrp001":
            fileGrp_fgrp001 = fileGrp
    file_all = fileGrp_fgrp001.findall("%sfile" % mets_NS)
    if not len(file_all) == 1:
        return [['',0,'','',''],['',0,'','','']],30,str(file_all)
    for file_elem in file_all:
        EL_file_FLocat = file_elem.find("%sFLocat" % mets_NS)
        file_FLocat_attrib = EL_file_FLocat.attrib
        file_attrib = file_elem.attrib
        if file_attrib['USE'] in USE or 'ALL' in USE and file_attrib['MIMETYPE'] in MIMETYPE or 'ALL' in MIMETYPE:
            objectIdentifierValue = file_FLocat_attrib['%shref' % xlink_NS][5:]
            messageDigest = file_attrib['CHECKSUM']
            messageDigestAlgorithm = file_attrib['CHECKSUMTYPE']
            a_MIMETYPE = file_attrib['MIMETYPE']
            a_SIZE = int(file_attrib['SIZE'])
            res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE])
    techMD_all = DOC.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
    for techMD in techMD_all:
        if techMD.get("ID") == "techMD001":
            techMD_techMD001 = techMD
            mdRef_all = techMD_techMD001.findall("%smdRef" % mets_NS)
            for mdRef in mdRef_all:
                mdRef_attrib = mdRef.attrib
                objectIdentifierValue = mdRef_attrib['%shref' % xlink_NS][5:]
                messageDigest = mdRef_attrib['CHECKSUM']
                messageDigestAlgorithm = mdRef_attrib['CHECKSUMTYPE']
                a_MIMETYPE = mdRef_attrib['MIMETYPE']
                a_SIZE = int(mdRef_attrib['SIZE'])
                res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,a_SIZE,a_MIMETYPE])
    return res,0,str(file_all)

def getdiv(EL):
    mets_NS = "{%s}" % EL.nsmap['mets']
    xlink_NS = "{%s}" % EL.nsmap['xlink']
    res = []
    ###############################################
    # div
    div_all = EL.findall("%sdiv" % mets_NS)
    for div in div_all:
        a_FILEID = None
        a_LABEL = div.get('LABEL')
        a_ADMID = div.get('ADMID')
        a_DMDID = div.get('DMDID')
        EL_fptr_all = div.findall("%sfptr" % mets_NS)
        if len(EL_fptr_all):
            for EL_fptr in EL_fptr_all:
                a_FILEID = EL_fptr.get('FILEID')
                res.append([a_LABEL, a_ADMID, a_DMDID, a_FILEID])
        else:
            res.append([a_LABEL, a_ADMID, a_DMDID, a_FILEID])
        newdata = getdiv(div)
        if len(newdata):
            res.append(newdata)
    return res

def getmd(EL,Sec_NAME,Sec_ID,Grp_NAME,Grp_ID,Grp_USE):
    mets_NS = "{%s}" % EL.nsmap['mets']
    xlink_NS = "{%s}" % EL.nsmap['xlink']
    res = []
    ###############################################
    # mdRef
    mdRef_all = EL.findall("%smdRef" % mets_NS)
    md_type = 'mdRef'
    for mdRef in mdRef_all:
        a_CREATED = mdRef.get('CREATED')
        a_MDTYPE = mdRef.get('MDTYPE')
        a_OTHERMDTYPE = mdRef.get('OTHERMDTYPE')
        a_ID = mdRef.get('ID')
        a_SIZE = int(mdRef.get('SIZE'))
        a_MIMETYPE = mdRef.get('MIMETYPE')
        a_CHECKSUMTYPE = mdRef.get('CHECKSUMTYPE')
        a_CHECKSUM = mdRef.get('CHECKSUM')
        a_LOCTYPE = mdRef.get('LOCTYPE')
        a_href = mdRef.get('%shref' % xlink_NS)
        a_type = mdRef.get('%stype' % xlink_NS)
        res.append([Sec_NAME,
                    Sec_ID,
                    Grp_NAME,
                    Grp_ID,
                    Grp_USE,
                    md_type,
                    a_ID,
                    a_LOCTYPE,
                    a_href,
                    a_type,
                    a_CHECKSUM,
                    a_CHECKSUMTYPE,
                    a_SIZE,
                    a_MIMETYPE,
                    a_CREATED,
                    a_MDTYPE,
                    a_OTHERMDTYPE,
        ])
    ###############################################
    # mdWrap
    mdWrap_all = EL.findall("%smdWrap" % mets_NS)
    md_type = 'mdWrap'
    for mdWrap in mdWrap_all:
        a_MDTYPE = mdWrap.get('MDTYPE')
        a_OTHERMDTYPE = mdWrap.get('OTHERMDTYPE')
        binData = mdWrap.find("%sbinData" % mets_NS)
        xmlData = mdWrap.find("%sxmlData" % mets_NS)
        if binData is not None:
            mdWrap_type = 'binData'
            mdWrap_data = binData
        elif xmlData is not None:
            mdWrap_type = 'xmlData'
            mdWrap_data = xmlData
        else:
            mdWrap_type = None
            mdWrap_data = None
        res.append([Sec_NAME,
                    Sec_ID,
                    Grp_NAME,
                    Grp_ID,
                    Grp_USE,
                    md_type,
                    mdWrap_type,
                    mdWrap_data,
                    a_MDTYPE,
                    a_OTHERMDTYPE,
       ])
    return res

def getMETSFileList(DOC=None,SecTYPE=['ALL'],ID=['ALL'],USE=['ALL'],MIMETYPE=["ALL"],FILENAME=None):
    #MIMETYPE=["ALL","application/x-tar"]
    #USE=["ALL","PACKAGE"]
    #SecTYPE=["ALL","dmdSec","amdSec","fileSec"]
    #ID=["ALL","fgrp001","techMD001"]

    res = []
    Hdr_res = []
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [],[],[],10,str(detail)
        except IOError, detail:
            return [],[],[],20,str(detail)

    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    xlink_NS = "{%s}" % EL_root.nsmap['xlink']

    ###############################################
    # mets root
    a_LABEL = EL_root.get('LABEL')
    a_OBJID = EL_root.get('OBJID')
    a_PROFILE = EL_root.get('PROFILE')
    a_TYPE = EL_root.get('TYPE')
    a_ID = EL_root.get('ID')
    Hdr_res.append([a_LABEL,a_OBJID,a_PROFILE,a_TYPE,a_ID])

    ###############################################
    # metsHdr
    metsHdr = DOC.find("%smetsHdr" % mets_NS)
    a_CREATEDATE = metsHdr.get('CREATEDATE')
    metsDocumentID = metsHdr.find("%smetsDocumentID" % mets_NS)
    if metsDocumentID is not None:
        t_metsDocumentID = metsDocumentID.text
    else:
        t_metsDocumentID = None
    Hdr_res.append([a_CREATEDATE,t_metsDocumentID])
    agent_all = metsHdr.findall("%sagent" % mets_NS)
    agent_res = []
    for agent in agent_all:
        a_ROLE = agent.get('ROLE')
        a_OTHERROLE = agent.get('OTHERROLE')
        a_TYPE = agent.get('TYPE')
        a_OTHERTYPE = agent.get('OTHERTYPE')
        name = agent.find("%sname" % mets_NS)
        if name is not None:
            t_name = name.text
        else:
            t_name = None
        note_res = []
        note_all = agent.findall("%snote" % mets_NS)
        for note in note_all:
            t_note = note.text
            note_res.append(t_note)
        agent_res.append([a_ROLE,a_OTHERROLE,a_TYPE,a_OTHERTYPE,t_name,note_res])
    Hdr_res.append(agent_res)
    altRecordID_all = metsHdr.findall("%saltRecordID" % mets_NS)
    altRecordID_res = []
    for altRecordID in altRecordID_all:
        a_TYPE = altRecordID.get('TYPE')
        altRecordID_value = altRecordID.text
        altRecordID_res.append([a_TYPE,altRecordID_value])
    Hdr_res.append(altRecordID_res)
    
    if 'dmdSec' in SecTYPE or 'ALL' in SecTYPE:
        ###############################################
        # dmdSec
        Sec_NAME = 'dmdSec'
        dmdSec_all = DOC.findall("%sdmdSec[@ID]" % mets_NS)
        for dmdSec in dmdSec_all:
            Sec_ID = dmdSec.get("ID")
            Grp_NAME = None
            Grp_ID = None
            Grp_USE = None
            ###############################################
            # MD
            for md in getmd(dmdSec,Sec_NAME,Sec_ID,Grp_NAME,Grp_ID,Grp_USE):
                res.append(md)

    if 'amdSec' in SecTYPE or 'ALL' in SecTYPE:
        ###############################################
        # amdSec
        Sec_NAME = 'amdSec'
        amdSec_all = DOC.findall("%samdSec[@ID]" % mets_NS)
        for amdSec in amdSec_all:
            Sec_ID = amdSec.get("ID")
            ###############################################
            # techMD
            techMD_all = amdSec.findall("%stechMD[@ID]" % mets_NS)
            for techMD in techMD_all:
                Grp_NAME = 'techMD'
                Grp_ID = techMD.get("ID")
                Grp_USE = techMD.get("USE")
                if techMD.get("ID") in ID or 'ALL' in ID:
                    for md in getmd(techMD,Sec_NAME,Sec_ID,Grp_NAME,Grp_ID,Grp_USE):
                        res.append(md)    
            ###############################################
            # digiprovMD
            digiprovMD_all = amdSec.findall("%sdigiprovMD[@ID]" % mets_NS)
            for digiprovMD in digiprovMD_all:
                Grp_NAME = 'digiprovMD'
                Grp_ID = digiprovMD.get("ID")
                Grp_USE = digiprovMD.get("USE")
                if digiprovMD.get("ID") in ID or 'ALL' in ID:
                    for md in getmd(digiprovMD,Sec_NAME,Sec_ID,Grp_NAME,Grp_ID,Grp_USE):
                        res.append(md)

    if 'fileSec' in SecTYPE or 'ALL' in SecTYPE:
        ###############################################
        # fileSec
        Sec_NAME = 'fileSec'
        fileSec = DOC.find("%sfileSec" % mets_NS)
        Sec_ID = fileSec.get("ID")
        fileGrp_all = fileSec.findall("%sfileGrp" % mets_NS)
        for fileGrp in fileGrp_all:
            Grp_NAME = 'fileGrp'
            Grp_ID = fileGrp.get("ID")
            Grp_USE = fileGrp.get("USE")
            if fileGrp.get("ID") in ID or 'ALL' in ID:
                ###############################################
                # file
                md_type = 'file'
                file_all = fileGrp.findall("%sfile" % mets_NS)
                for EL_file in file_all:
                    if EL_file.get('USE') in USE or 'ALL' in USE and EL_file.get('MIMETYPE') in MIMETYPE or 'ALL' in MIMETYPE:
                        a_ID = EL_file.get('ID')
                        a_MIMETYPE = EL_file.get('MIMETYPE')
                        a_CREATED = EL_file.get('CREATED')
                        a_CHECKSUM = EL_file.get('CHECKSUM')
                        a_CHECKSUMTYPE = EL_file.get('CHECKSUMTYPE')
                        a_USE = EL_file.get('USE')
                        a_SIZE = int(EL_file.get('SIZE'))
                        a_ADMID = EL_file.get('ADMID')
                        a_DMDID = EL_file.get('DMDID')
                        EL_FLocat = EL_file.find("%sFLocat" % mets_NS)
                        a_LOCTYPE = EL_FLocat.get('LOCTYPE')
                        a_href = EL_FLocat.get('%shref' % xlink_NS)
                        a_href = ESSPGM.Check().str2unicode(urllib.url2pathname(a_href))
                        a_type = EL_FLocat.get('%stype' % xlink_NS)
                        res.append([Sec_NAME,
                                    Sec_ID,
                                    Grp_NAME,
                                    Grp_ID,
                                    Grp_USE,
                                    md_type,
                                    a_ID,
                                    a_LOCTYPE,
                                    a_href,
                                    a_type,
                                    a_CHECKSUM,
                                    a_CHECKSUMTYPE,
                                    a_SIZE,
                                    a_MIMETYPE,
                                    a_CREATED,
                                    a_USE,
                                    a_ADMID,
                                    a_DMDID,
                        ])

    ###############################################
    # structMap
    structMap = DOC.find("%sstructMap" % mets_NS)
    
    a_LABEL = structMap.get("LABEL")
    struct_res = [a_LABEL, getdiv(structMap)]

    return Hdr_res, res,struct_res,0,None

def getContentInfo(DOC=None,FILENAME=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [['',0,'','']],10,str(detail)
        except IOError, detail:
            return [['',0,'','']],20,str(detail)
    res=[]
    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    xlink_NS = "{%s}" % EL_root.nsmap['xlink']
    #xlink_NS = "{%s}" % XLINK_NAMESPACE
    #mets_NS = "{%s}" % METS_NAMESPACE
    techMD_all = DOC.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
    for techMD in techMD_all:
        if techMD.get("ID") == "techMD001":
            techMD_techMD001 = techMD
            mdRef_all = techMD_techMD001.findall("%smdRef" % mets_NS)
            for mdRef in mdRef_all:
                mdRef_attrib = mdRef.attrib
                ID = mdRef_attrib['ID'][4:]
                SIZE = int(mdRef_attrib['SIZE'])
                CREATED = mdRef_attrib['CREATED']
                TYPE = mdRef_attrib['OTHERMDTYPE']
                res.append([ID,SIZE,CREATED,TYPE])
    digiprovMD_all = DOC.findall("%samdSec/%sdigiprovMD[@ID]" % (mets_NS,mets_NS))
    if digiprovMD_all:    
        for digiprovMD in digiprovMD_all:
            if digiprovMD.get("ID") == "digiprovMD001":
                digiprovMD_digiprovMD001 = digiprovMD
                mdRef_all = digiprovMD_digiprovMD001.findall("%smdRef" % mets_NS)
                for mdRef in mdRef_all:
                    mdRef_attrib = mdRef.attrib
                    ID = mdRef_attrib['ID'][4:]
                    SIZE = int(mdRef_attrib['SIZE'])
                    CREATED = mdRef_attrib['CREATED']
                    TYPE = mdRef_attrib['MDTYPE']
                    res.append([ID,SIZE,CREATED,TYPE])
    return res,0,''

def getSchemaLocation(DOC=None,FILENAME=None,NS='http://xml.ra.se/PREMIS',PREFIX='premis'):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [['','']],10,str(detail)
        except IOError, detail:
            return [['','']],20,str(detail)
    res=[]

    EL_root = DOC.getroot()
    
    xsi_NS = "{%s}" % EL_root.nsmap['xsi']
    all_schemaLocations = DOC.findall("[@%sschemaLocation]" % xsi_NS)
    for schemaLocation in all_schemaLocations:
        a = 0
        for item in schemaLocation.attrib["%sschemaLocation" % xsi_NS].split():
            if a == 0:
                ns_item = item
                a = 1
            elif a == 1: 
                res.append([ns_item,item])
                a = 0
    all_schemaLocations = DOC.findall(".//*[@%sschemaLocation]" % xsi_NS)
    for schemaLocation in all_schemaLocations:
        a = 0
        for item in schemaLocation.attrib["%sschemaLocation" % xsi_NS].split():
            if a == 0:
                ns_item = item
                a = 1
            elif a == 1:
                res.append([ns_item,item])
                a = 0
    return res,0,''

def getTotalSize(DOC=None,USE=['ALL'],MIMETYPE=["ALL"],FILENAME=None):
    #MIMETYPE=["ALL","image/tiff","text/xml","video/mpeg","application/pdf","audio/mpeg"]
    #USE=["ALL","RA Datafile","Datafile","Information","RA Information"]
    res=[]
    TotalSize=0
    TotalNum=0
    if FILENAME:
        Fgrp002,errno,why = getFileSizeFgrp001(USE=USE,MIMETYPE=MIMETYPE,FILENAME=FILENAME)
    else:
        Fgrp002,errno,why = getFileSizeFgrp001(DOC=DOC,USE=USE,MIMETYPE=MIMETYPE)
    if not errno:
        TotalNum,TotalSize = Fgrp002
    else:
        return [0,0],30,str(why)

    if FILENAME:
        ContentInfo,errno,why = getContentInfo(FILENAME=FILENAME)
    else:
        ContentInfo,errno,why = getContentInfo(DOC)
    if not errno:
        for i in ContentInfo:
            TotalNum += 1
            TotalSize += i[1]
        return [TotalNum,TotalSize],0,''
    else:
        return [0,0],31,str(why)
    return [0,0],40,''
        
#######################################################################################################################
# AddDataFiles
#
# Syntax: AddDataFiles(DOC,LABEL,USE,FILES=[(ID,SIZE,CREATED,MIMETYPE,ADMID,USE,LOCTYPE,xlink_type),...])
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# LABEL='Datafiles' or 'Information' or 'RA Datafiles' or 'RA Information'
# USE='PACKAGES' or 'FILES'
# FILES=[(ID,SIZE,CREATED,MIMETYPE,ADMID,USE,LOCTYPE,xlink_type),...]
#   ID=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(ID) 			example: '000001.tif'
#      /mets.structMap/mets.div/mets.div(LABEL=*Datafiles)/mets.fptr(FILEID)
#   SIZE=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(SIZE)			example: '123'
#   CREATED=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(CREATED)		example: '2008-10-14T12:45:00+01:00'
#   MIMETYPE=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(MIMETYPE)		example: 'image/tiff'
#   ADMID=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(ADMID)		example: 'digiprovMD001 techMD001'
#   USE=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file(USE)			example: 'Datafile' or 'Information'
#   LOCTYPE=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file/mets.FLocat(LOCTYPE)	example: 'URL'
#   xlink_type=/mets.fileSec/mets.fileGrp(ID=fgrp002)/mets.file/mets.FLocat(xlink:type)	example: 'simple'
#
#   ('000001.tif','123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','URL','simple')
#   ('000001.tif','123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','RA Datafile','URL','simple')
#   ('000001.res','123','2008-10-14T12:45:00+01:00','text/csv','digiprovMD001','Information','URL','simple')
#   ('000001.res','123','2008-10-14T12:45:00+01:00','text/csv','digiprovMD001','RA Information','URL','simple')
#
def AddDataFiles(DOC=None,LABEL=None,USE='FILES',ADMID='',FILES=[('000001.tif','123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','MD5','12345aaabb','URL','simple'),('000001.res','123','2008-10-14T12:45:00+01:00','text/csv','digiprovMD001','RA Information','MD5','22345aaabb','URL','simple')]):

    mets_NS = "{%s}" % METS_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE

    # Find fileGrp with attribute USE=USE
    EL_fileGrp = None
    fileGrp_all = DOC.findall("%sfileSec/%sfileGrp[@USE]" % (mets_NS,mets_NS))
    for fileGrp in fileGrp_all:
        if fileGrp.get("USE") == USE:
            #fileGrp_fgrp002 = fileGrp
            EL_fileGrp = fileGrp
    # Check if fileGrp USE exist, if not then create it
    if EL_fileGrp is None:
        # Get new fileGrp ID
        fileGrp_all = DOC.findall("%sfileSec/%sfileGrp[@ID]" % (mets_NS,mets_NS))
        fileGrp_num = string.zfill(len(fileGrp_all) + 1, 3)
        fileGrp_ID = 'fgrp' + fileGrp_num
        # Get fileSec element
        EL_fileSec = DOC.find("%sfileSec" % mets_NS) 
        # Create new fileGrp
        EL_fileGrp = etree.SubElement(EL_fileSec, mets_NS + "fileGrp", attrib={"USE" : "%s" % USE,
                                                                               "ID" : "%s" % fileGrp_ID})

    # Find structMap with attribute LABEL=LABEL
    EL_structMap_div = None
    ELs_structMap = DOC.findall("%sstructMap/%sdiv/%sdiv[@LABEL]" % (mets_NS,mets_NS,mets_NS))
    for i_structMap in ELs_structMap:
        if i_structMap.get("LABEL") == LABEL:
            EL_structMap_div = i_structMap
    # Check if structMap LABEL exist, if not then create it
    if EL_structMap_div is None:
        EL_structMap = DOC.find("%sstructMap/%sdiv" % (mets_NS,mets_NS))
        EL_structMap_div = etree.SubElement(EL_structMap, mets_NS + "div", attrib={"LABEL" : "%s" % LABEL,
                                                                                   "ADMID" : "%s" % ADMID})
    for file in FILES:
        file_id_iso = ESSPGM.Check().unicode2str(file[0])
        a_ID = str(uuid.uuid1())
        a_href = urllib.pathname2url(file_id_iso)
        a_SIZE = file[1]
        a_CREATED = file[2]
        a_MIMETYPE = file[3]
        a_ADMID = file[4]
        a_USE = file[5]
        a_CHECKSUMTYPE = file[6]
        a_CHECKSUM = file[7]
        a_LOCTYPE = file[8]
        a_xlink_type = file[9]
        EL_fptr = etree.SubElement(EL_structMap_div, mets_NS + "fptr", attrib={"FILEID" : "guid"+a_ID})
        EL_file = etree.SubElement(EL_fileGrp, mets_NS + "file", attrib={"ID" : "guid%s" % a_ID,
                                                                         "MIMETYPE" : a_MIMETYPE,
                                                                         "SIZE" : str(a_SIZE),
                                                                         "CREATED" : a_CREATED,
                                                                         "CHECKSUM" : a_CHECKSUM,
                                                                         "CHECKSUMTYPE" : a_CHECKSUMTYPE,
                                                                         "USE" : a_USE,
                                                                         "ADMID" : a_ADMID})
        EL_FLocat = etree.SubElement(EL_file, mets_NS + "FLocat", attrib={"LOCTYPE" : a_LOCTYPE,
                                                                          xlink_NS + "type" : a_xlink_type,
                                                                          xlink_NS + "href" : "file:%s" % a_href})
    return DOC

#######################################################################################################################
# getPackageADMID
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# FILENAME=xmlFilenamePATH
#
def getPackageADMID(DOC=None,FILENAME=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return '',10,str(detail)
        except IOError, detail:
            return '',20,str(detail)
    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']
    #mets_NS = "{%s}" % METS_NAMESPACE
    EL_structMap_div1 = None
    ELs_structMap = DOC.findall("%sstructMap/%sdiv[@LABEL]" % (mets_NS,mets_NS))
    for i_structMap in ELs_structMap:
        if i_structMap.get("LABEL") == 'Package':
            EL_structMap_div1 = i_structMap
            a_structMap_div1_ADMID = EL_structMap_div1.get("ADMID")
    if EL_structMap_div1 is None:
        return '',1,'structMap with LABEL=Package not found'
    else:
        return a_structMap_div1_ADMID,0,'OK'

#######################################################################################################################
# updatePackageADMID
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# ADMID=['techMD001'] or ['techMD001','techMD002',...] 
# FILENAME=xmlFilenamePATH
#
def updatePackageADMID(DOC=None,ADMID=['techMD001'],FILENAME=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return '',10,str(detail)
        except IOError, detail:
            return '',20,str(detail)
    mets_NS = "{%s}" % METS_NAMESPACE
    EL_structMap_div1 = None
    ELs_structMap = DOC.findall("%sstructMap/%sdiv[@LABEL]" % (mets_NS,mets_NS))
    for i_structMap in ELs_structMap:
        if i_structMap.get("LABEL") == 'Package':
            EL_structMap_div1 = i_structMap
            a_structMap_div1_ADMID = EL_structMap_div1.get("ADMID")
    if not len(EL_structMap_div1):
        return '',1,'structMap with LABEL=Package not found'
    else:
        ELs_fileGrp = DOC.findall("%sfileSec/%sfileGrp[@ID]" % (mets_NS,mets_NS))
        for i_fileGrp in ELs_fileGrp:
            if i_fileGrp.get("ID") == "fgrp001":
                EL_fileGrp_fgrp001 = i_fileGrp
                EL_fileGrp_fgrp001_file = EL_fileGrp_fgrp001.find("%sfile" % mets_NS)
        for i_ADMID in ADMID:
            if not i_ADMID in a_structMap_div1_ADMID:
                if len(a_structMap_div1_ADMID):
                    techMD_ADMID = []
                    digiprovMD_ADMID = []
                    for i_a_structMap_div1_ADMID in a_structMap_div1_ADMID.split():
                        if i_a_structMap_div1_ADMID[:-3] == 'techMD':
                            techMD_ADMID.append(i_a_structMap_div1_ADMID)
                        elif i_a_structMap_div1_ADMID[:-3] == 'digiprovMD':
                            digiprovMD_ADMID.append(i_a_structMap_div1_ADMID)
                    if i_ADMID[:-3] == 'techMD':
                        techMD_ADMID.append(i_ADMID)
                    elif i_ADMID[:-3] == 'digiprovMD':
                        digiprovMD_ADMID.append(i_ADMID)
                    a_ADMID = ''
                    for i_sorted_ADMID in sorted(techMD_ADMID) + sorted(digiprovMD_ADMID):
                        if a_ADMID == '':
                            a_ADMID = i_sorted_ADMID
                        else:
                            a_ADMID += " %s" % i_sorted_ADMID

                    EL_structMap_div1.set("ADMID", "%s" % a_ADMID)
                    EL_fileGrp_fgrp001_file.set("ADMID", "%s" % a_ADMID)
                else:
                    EL_structMap_div1.set("ADMID", "%s" % i_ADMID)
                    EL_fileGrp_fgrp001_file.set("ADMID", "%s" % i_ADMID)
        a_structMap_div1_ADMID = EL_structMap_div1.get("ADMID")
        return a_structMap_div1_ADMID,0,'OK'

#######################################################################################################################
# updateFilesADMID
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# FILENAME=xmlFilenamePATH
#
def updateFilesADMID(DOC=None,FILENAME=None,USE='FILES'):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return '',10,str(detail)
        except IOError, detail:
            return '',20,str(detail)
    mets_NS = "{%s}" % METS_NAMESPACE
    # Get attrib ADMID from Package and assign to a_structMap_div1_ADMID
    a_structMap_div1_ADMID,errno,why = getPackageADMID(DOC)
    # Findall files except Package_div in structMap and set ADMID to a_structMap_div1_ADMID
    ELs_structMap = DOC.findall("%sstructMap/%sdiv/%sdiv[@ADMID]" % (mets_NS,mets_NS,mets_NS))
    for EL_structMap_div in ELs_structMap:
        EL_structMap_div.set("ADMID", "%s" % a_structMap_div1_ADMID)
    # Findall files in fgrp in fileSec and set ADMID to a_structMap_div1_ADMID
    ELs_fileGrp = DOC.findall("%sfileSec/%sfileGrp[@USE]" % (mets_NS,mets_NS))
    for i_fileGrp in ELs_fileGrp:
        if i_fileGrp.get("USE") == USE:
            EL_fileGrp = i_fileGrp
            ELs_fileGrp_file = EL_fileGrp.findall("%sfile[@ADMID]" % mets_NS)
            for EL_fileGrp_file in ELs_fileGrp_file:
                EL_fileGrp_file.set("ADMID", "%s" % a_structMap_div1_ADMID)
    return a_structMap_div1_ADMID,0,'OK'

#######################################################################################################################
# updatePackage
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# FILENAME=xmlFilenamePATH
#
def updatePackage(DOC=None,FILENAME=None,TYPE=None,CREATED=None,metsDocumentID=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return '',10,str(detail)
        except IOError, detail:
            return '',20,str(detail)
    EL_root = DOC.getroot()
    mets_NS = "{%s}" % EL_root.nsmap['mets']

    if TYPE is not None:
        EL_root.attrib["TYPE"] = TYPE
    
    EL_metsHdr = DOC.find("%smetsHdr" % mets_NS)
    if CREATED is not None:
        EL_metsHdr.attrib["CREATEDATE"] = CREATED

    EL_metsDocumentID = EL_metsHdr.find("%smetsDocumentID" % mets_NS) 
    if metsDocumentID is not None:
        EL_metsDocumentID.text = metsDocumentID

    return DOC
        
#######################################################################################################################
# AddContentFiles
#
# Syntax: AddContentFiles(DOC,LABEL,FILES=[(ID,SIZE,CREATED,MIMETYPE,MDTYPE,OTHERMDTYPE,LOCTYPE,xlink_type),...])
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# LABEL='Content description'
# FILES=[(ID,SIZE,CREATED,MIMETYPE,MDTYPE,OTHERMDTYPE,LOCTYPE,xlink_type),...]
#   ID=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(ID)			example: '000001.tif'
#      /mets.structMap/mets.div/mets.div(LABEL=Content description)/mets.fptr(FILEID)
#   SIZE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(SIZE) 		example: '123'
#   CREATED=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(CREATED)	example: '2008-10-14T12:45:00+01:00'
#   MIMETYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(MIMETYPE)	example: 'text/xml'
#   MDTYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(MDTYPE)		example: 'OTHER' or 'PREMIS'
#   OTHERMDTYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(OTHERMDTYPE)	example: 'ADDML' or 'RES' or ''
#   LOCTYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(LOCTYPE)	example: 'URL'
#   xlink_type=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdRef(xlink:type)	example: 'simple'
#
def AddContentFiles(DOC=None,LABEL="Content description",ADMID='',FILES=[('000001.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','ADDML','MD5','12345aaabb','URL','simple')]):

    xlink_NS = "{%s}" % XLINK_NAMESPACE
    mets_NS = "{%s}" % METS_NAMESPACE

    # Find amdSec with ID=amdSec001 and assign to EL_amdSec
    ELs_amdSec = DOC.findall("%samdSec[@ID]" % mets_NS)
    for i_amdSec in ELs_amdSec:
        if i_amdSec.get("ID") == "amdSec001":
            EL_amdSec = i_amdSec

    # Find structMap with attribute LABEL=LABEL
    EL_structMap_div = None
    ELs_structMap = DOC.findall("%sstructMap/%sdiv/%sdiv[@LABEL]" % (mets_NS,mets_NS,mets_NS))
    for i_structMap in ELs_structMap:
        if i_structMap.get("LABEL") == LABEL:
            EL_structMap_div = i_structMap
    # Check if structMap LABEL exist, if not then create it
    if EL_structMap_div is None:
        EL_structMap = DOC.find("%sstructMap/%sdiv" % (mets_NS,mets_NS))
        EL_structMap_div = etree.SubElement(EL_structMap, mets_NS + "div", attrib={"LABEL" : "%s" % LABEL})
        if ADMID:
            EL_structMap_div.attrib["ADMID"] = "%s" % ADMID

    for file in FILES:
        file_id_iso = ESSPGM.Check().unicode2str(file[0])
        a_ID = str(uuid.uuid1())
        a_href = urllib.pathname2url(file_id_iso)
        a_SIZE = file[1]
        a_CREATED = file[2]
        a_MIMETYPE = file[3]
        a_MDTYPE = file[4]
        a_OTHERMDTYPE = file[5]
        a_CHECKSUMTYPE = file[6]
        a_CHECKSUM = file[7]
        a_LOCTYPE = file[8]
        a_xlink_type = file[9]
        # Add an entry in structMap for Content description file
        EL_fptr = etree.SubElement(EL_structMap_div, mets_NS + "fptr", attrib={"FILEID" : "guid%s" % a_ID})
        if a_MDTYPE=='OTHER':
            # Create a new techMD element
            techMD_all = DOC.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
            techMD_num = string.zfill(len(techMD_all) + 1, 3)
            techMD_ID = 'techMD' + techMD_num 
            # Use insert istead of "etree.SubElement" to insert all techMD in number order before "digiprovMD"
            EL_amdSec.insert(len(techMD_all), etree.Element(mets_NS + "techMD", attrib={"ID" : "%s" % techMD_ID}))
            ELs_techMD = EL_amdSec.findall("%stechMD[@ID]" % (mets_NS))
            for i_techMD in ELs_techMD:
                if i_techMD.get("ID") == techMD_ID:
                    EL_techMD = i_techMD
            res,errno,why = updatePackageADMID(DOC,[techMD_ID])
          
            EL_mdRef = etree.SubElement(EL_techMD, mets_NS + "mdRef", attrib={"ID" : "guid%s" % a_ID,
                                                                              "LOCTYPE" : a_LOCTYPE,
                                                                              "MDTYPE" : a_MDTYPE,
                                                                              "OTHERMDTYPE" : a_OTHERMDTYPE,
                                                                              "MIMETYPE" : a_MIMETYPE,
                                                                              "SIZE" : str(a_SIZE),
                                                                              "CREATED" : a_CREATED,
                                                                              "CHECKSUM" : a_CHECKSUM,
                                                                              "CHECKSUMTYPE" : a_CHECKSUMTYPE,
                                                                              xlink_NS + "type" : a_xlink_type,
                                                                              xlink_NS + "href" : "file:%s" % a_href})
        elif a_MDTYPE=='PREMIS':
            # Create a new digiprovMD element
            digiprovMD_all = DOC.findall("%samdSec/%sdigiprovMD[@ID]" % (mets_NS,mets_NS))
            digiprovMD_num = string.zfill(len(digiprovMD_all) + 1, 3)
            digiprovMD_ID = 'digiprovMD' + digiprovMD_num
            EL_digiprovMD = etree.SubElement(EL_amdSec, mets_NS + "digiprovMD", attrib={"ID" : "%s" % digiprovMD_ID})
            res,errno,why = updatePackageADMID(DOC,[digiprovMD_ID])

            EL_mdRef = etree.SubElement(EL_digiprovMD, mets_NS + "mdRef", attrib={"ID" : "guid%s" % a_ID,
                                                                                  "LOCTYPE" : a_LOCTYPE,
                                                                                  "MDTYPE" : a_MDTYPE,
                                                                                  "MIMETYPE" : a_MIMETYPE,
                                                                                  "SIZE" : str(a_SIZE),
                                                                                  "CREATED" : a_CREATED,
                                                                                  "CHECKSUM" : a_CHECKSUM,
                                                                                  "CHECKSUMTYPE" : a_CHECKSUMTYPE,
                                                                                  xlink_NS + "type" : a_xlink_type,
                                                                                  xlink_NS + "href" : "file:%s" % a_href})
    return DOC

#######################################################################################################################
# AddContentEtree
#
# Syntax: AddContentEtree(DOC,FILES=[(ID,MDTYPE,OTHERMDTYPE),...])
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# FILES=[(ID,MDTYPE,OTHERMDTYPE),...]
#   ID=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdWrap/xxxx.xmlData 		example: 'etree.ElementTree'
#   MDTYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdWrap(MDTYPE) 		example: 'OTHER' or 'PREMIS'
#   OTHERMDTYPE=/mets.amdSec/mets.xxxxxxMD(ID=xxxxMDnnn)/mets.mdWrap(OTHERMDTYPE)	example: 'ADDML' or 'RES' or ''
#
def AddContentEtree(DOC=None,FILES=[('etree.ElementTree','OTHER','RES')]):

    xlink_NS = "{%s}" % XLINK_NAMESPACE
    mets_NS = "{%s}" % METS_NAMESPACE

    # Find amdSec with ID=amdSec001 and assign to EL_amdSec
    ELs_amdSec = DOC.findall("%samdSec[@ID]" % mets_NS)
    for i_amdSec in ELs_amdSec:
        if i_amdSec.get("ID") == "amdSec001":
            EL_amdSec = i_amdSec

    for file in FILES:
        a_ID = file[0]
        a_MDTYPE = file[1]
        a_OTHERMDTYPE = file[2]
        if a_MDTYPE=='OTHER':
            # Create a new techMD element
            techMD_all = DOC.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
            techMD_num = string.zfill(len(techMD_all) + 1, 3)
            techMD_ID = 'techMD' + techMD_num
            # Use "insert" istead of "etree.SubElement" to insert all techMD in number order before "digiprovMD"
            EL_amdSec.insert(len(techMD_all), etree.Element(mets_NS + "techMD", attrib={"ID" : "%s" % techMD_ID}))
            ELs_techMD = EL_amdSec.findall("%stechMD[@ID]" % (mets_NS))
            for i_techMD in ELs_techMD:
                if i_techMD.get("ID") == techMD_ID:
                    EL_techMD = i_techMD
            res,errno,why = updatePackageADMID(DOC,[techMD_ID])

            EL_mdWrap = etree.SubElement(EL_techMD, mets_NS + "mdWrap", attrib={"MDTYPE" : a_MDTYPE, "OTHERMDTYPE" : a_OTHERMDTYPE})
            EL_xmlData = etree.SubElement(EL_mdWrap, mets_NS + "xmlData")
            # Get root element from elementtree
            EL_wrap_xml_root = a_ID.getroot()
            EL_wrap_xml = EL_xmlData.append(EL_wrap_xml_root)

        elif a_MDTYPE=='PREMIS':
            # Create a new digiprovMD element
            digiprovMD_all = DOC.findall("%samdSec/%sdigiprovMD[@ID]" % (mets_NS,mets_NS))
            digiprovMD_num = string.zfill(len(digiprovMD_all) + 1, 3)
            digiprovMD_ID = 'digiprovMD' + digiprovMD_num
            EL_digiprovMD = etree.SubElement(EL_amdSec, mets_NS + "digiprovMD", attrib={"ID" : "%s" % digiprovMD_ID})
            res,errno,why = updatePackageADMID(DOC,[digiprovMD_ID])

            EL_mdWrap = etree.SubElement(EL_digiprovMD, mets_NS + "mdWrap", attrib={"MDTYPE" : a_MDTYPE})
            EL_xmlData = etree.SubElement(EL_mdWrap, mets_NS + "xmlData")
            # Get root element from elementtree
            EL_wrap_xml_root = a_ID.getroot()
            EL_wrap_xml = EL_xmlData.append(EL_wrap_xml_root)
    return DOC

def SetAIPattrib(DOC=None,SIZE=None,CREATED=None,CHECKSUM=None,CHECKSUMTYPE=None):
    mets_NS = "{%s}" % METS_NAMESPACE
    fileGrp_all = DOC.findall("%sfileSec/%sfileGrp[@ID]" % (mets_NS,mets_NS))
    for fileGrp in fileGrp_all:
        if fileGrp.get("ID") == "fgrp001":
            fileGrp_fgrp001 = fileGrp
            fileGrp_fgrp001_file = fileGrp_fgrp001.find("%sfile" % mets_NS)
            fileGrp_fgrp001_file.attrib["SIZE"] = str(SIZE)
            fileGrp_fgrp001_file.attrib["CREATED"] = CREATED
            fileGrp_fgrp001_file.attrib["CHECKSUM"] = CHECKSUM
            fileGrp_fgrp001_file.attrib["CHECKSUMTYPE"] = CHECKSUMTYPE
    return DOC

def updateMETSattrib(DOC=None,FILENAME=None,NS=None,PREFIX=None,schemaLocation=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return '',10,str(detail)
        except IOError, detail:
            return '',20,str(detail)
    test_XMLNS = u"xmlns"
    xmlns_NS = "{%s}" % test_XMLNS
    mets_NS = "{%s}" % METS_NAMESPACE
    EL_mets = DOC.getroot()
    xsi_NS = "{%s}" % EL_mets.nsmap['xsi']
    
    print EL_mets.nsmap
    if PREFIX in EL_mets.nsmap:
        print 'Prefix: %s already exist! {%s}' % (PREFIX,EL_mets.nsmap[PREFIX])
    else:
        print 'try to add: %s' % PREFIX
        nsmap_dict = EL_mets.nsmap
        nsmap_dict[PREFIX] = 'test123'
        new_EL_mets = etree.Element(EL_mets.tag, EL_mets.attrib,nsmap = nsmap_dict)
        new_EL_mets[:] = EL_mets[:]
        EL_mets = new_EL_mets
        NSMAP = {'mets' : METS_NAMESPACE,
                 'test' : XLINK_NAMESPACE}
        new_NSMAP = {'mets' : METS_NAMESPACE,
                     'mix' : 'mixtest'}
        root = etree.Element(mets_NS + "root",nsmap = NSMAP)
        root2 = etree.SubElement(root,mets_NS + "newel",attrib={'att1' : '123'})
        print etree.tostring(root,encoding='UTF-8', xml_declaration=True, pretty_print=True)
        new_root = etree.Element(root.tag, root.attrib,nsmap = new_NSMAP)
        new_root[:] = root[:]
        print etree.tostring(new_root,encoding='UTF-8', xml_declaration=True, pretty_print=True)

        

    #doc = etree.ElementTree(element=EL_mets, file=None, nsmap=NSMAP)
    print EL_mets.nsmap
    print 'attrib:', EL_mets.attrib
    print EL_mets.keys()
    print EL_mets.values()
    print 'base:', EL_mets.base
    print 'test1:',str(EL_mets.tag)
    #print 'test2:', lookup
    print etree.tostring(EL_mets,encoding='UTF-8', xml_declaration=True, pretty_print=True)

    schemaLocation_list = []
    a_schemaLocation_all = EL_mets.attrib["%sschemaLocation" % xsi_NS]
    a = 0
    for schemaLocation in a_schemaLocation_all.split():
        if a == 0:
            ns_item = schemaLocation
            a = 1
        elif a == 1:
            schemaLocation_list.append([ns_item,schemaLocation])
            a = 0
    print 'schemaLocation_list: %s' % str(schemaLocation_list)

    return DOC,0,''

def updateSchemaLocation(DOC=None,FILENAME=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return None,10,str(detail)
        except IOError, detail:
            return None,20,str(detail)

    root_schemaLocation_list=[]
    other_schemaLocation_list=[]

    EL_root = DOC.getroot()

    xlink_NS = "{%s}" % EL_root.nsmap['xlink']
    xsi_NS = "{%s}" % EL_root.nsmap['xsi']
    ################################################
    # Get root schema location
    all_schemaLocations = DOC.findall("[@%sschemaLocation]" % xsi_NS)
    for root_schemaLocation in all_schemaLocations:
        a = 0
        for item in root_schemaLocation.attrib["%sschemaLocation" % xsi_NS].split():
            if a == 0:
                ns_item = item
                a = 1
            elif a == 1:
                root_schemaLocation_list.append([ns_item,item])
                a = 0
    ################################################
    # Get all other schema locations  (not root schema location)
    all_schemaLocations = DOC.findall(".//*[@%sschemaLocation]" % xsi_NS)
    for schemaLocation in all_schemaLocations:
        a = 0
        for item in schemaLocation.attrib["%sschemaLocation" % xsi_NS].split():
            if a == 0:
                ns_item = item
                a = 1
            elif a == 1:
                other_schemaLocation_list.append([ns_item,item])
                a = 0
        #####################################################
        # Delete other schemaLocation.attrib
        del schemaLocation.attrib["%sschemaLocation" % xsi_NS]
    ####################################################
    # append all missing schema locations to root_schemaLocation_list
    for schemaLocation in other_schemaLocation_list:
        if schemaLocation in root_schemaLocation_list:
            pass
        else:
            root_schemaLocation_list.append(schemaLocation)
    #####################################################
    # convert root_schemaLocation_list to schemaLocation attrib
    schemaLocation = ""
    for schema in root_schemaLocation_list:
        if len(schemaLocation):
            schemaLocation += " %s %s" % (schema[0], schema[1])
        else:
            schemaLocation = "%s %s" % (schema[0], schema[1])
    ########################################################
    # update root_schemaLocation.attrib
    root_schemaLocation.attrib[xsi_NS + "schemaLocation"] = schemaLocation

    return DOC,0,''

def validate(DOC=None,FILENAME=None,XMLSchema=None):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return 10,str(detail)
        except IOError, detail:
            return 20,str(detail)
    if XMLSchema:
        try:
            root = etree.parse(XMLSchema)
        except etree.XMLSyntaxError, detail:
            return 11,str(detail)
        except IOError, detail:
            return 21,str(detail)
    else:
        # Create validation schema
        xsd_NS = "{%s}" % XSD_NAMESPACE
        NSMAP = {'xsd' : XSD_NAMESPACE}
        root = etree.Element(xsd_NS + "schema", nsmap=NSMAP) # lxml only!
        root.attrib["elementFormDefault"] = "qualified"
        RootEL_schema = etree.ElementTree(element=root, file=None)
        SchemaLocations,errno,why = getSchemaLocation(DOC)
        for SCHEMALOCATION in SchemaLocations:
            etree.SubElement(root, xsd_NS + "import", attrib={"namespace" : SCHEMALOCATION[0],
                                                              "schemaLocation" : SCHEMALOCATION[1]})
        #print etree.tostring(RootEL_schema,encoding='UTF-8', xml_declaration=True, pretty_print=True)
    try:
        xmlschema = etree.XMLSchema(root)
    except etree.XMLSchemaParseError, details:
        ################# Debug start #######################
        # Write XMLSchema to debugfile
        debugfile = '/ESSArch/log/debug/XMLSchema_1_%s.xsd' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        errno_ignore,why_ignore = writeToFile(RootEL_schema,debugfile)
        # Write XMLdoc to debugfile
        debugfile = '/ESSArch/log/debug/XML_DOC_1_%s.xml' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        errno_ignore,why_ignore = writeToFile(DOC,debugfile)
        # Write getSchemaLocation to debugfile
        debugfile = '/ESSArch/log/debug/getSchemaLocation_1_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        debugfile_object = open(debugfile, 'w')
        debugfile_object.write(str(SchemaLocations))
        debugfile_object.close()
        # Write ParseError_details to debugfile
        debugfile = '/ESSArch/log/debug/ParseError_details_1_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        debugfile_object = open(debugfile, 'w')
        debugfile_object.write(str(details))
        debugfile_object.close()
        ################# Debug end #######################
        time.sleep(60)
        try:
            xmlschema = etree.XMLSchema(root)
        except etree.XMLSchemaParseError, details:
            ################# Debug start #######################
            # Write XMLSchema to debugfile
            debugfile = '/ESSArch/log/debug/XMLSchema_2_%s.xsd' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            errno_ignore,why_ignore = writeToFile(RootEL_schema,debugfile)
            # Write XMLdoc to debugfile
            debugfile = '/ESSArch/log/debug/XML_DOC_2_%s.xml' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            errno_ignore,why_ignore = writeToFile(DOC,debugfile)
            # Write getSchemaLocation to debugfile
            debugfile = '/ESSArch/log/debug/getSchemaLocation_2_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            debugfile_object = open(debugfile, 'w')
            debugfile_object.write(str(SchemaLocations))
            debugfile_object.close()
            # Write ParseError_details to debugfile
            debugfile = '/ESSArch/log/debug/ParseError_details_2_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
            debugfile_object = open(debugfile, 'w')
            debugfile_object.write(str(details))
            debugfile_object.close()
            ################# Debug end #######################
            time.sleep(300)
            try:
                xmlschema = etree.XMLSchema(root)
            except etree.XMLSchemaParseError, details:
                ################# Debug start #######################
                # Write XMLSchema to debugfile
                debugfile = '/ESSArch/log/debug/XMLSchema_3_%s.xsd' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                errno_ignore,why_ignore = writeToFile(RootEL_schema,debugfile)
                # Write XMLdoc to debugfile
                debugfile = '/ESSArch/log/debug/XML_DOC_3_%s.xml' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                errno_ignore,why_ignore = writeToFile(DOC,debugfile)
                # Write getSchemaLocation to debugfile
                debugfile = '/ESSArch/log/debug/getSchemaLocation_3_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                debugfile_object = open(debugfile, 'w')
                debugfile_object.write(str(SchemaLocations))
                debugfile_object.close()
                # Write ParseError_details to debugfile
                debugfile = '/ESSArch/log/debug/ParseError_details_3_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
                debugfile_object = open(debugfile, 'w')
                debugfile_object.write(str(details))
                debugfile_object.close()
                ################# Debug end #######################
                return 30,str(details)
        #return 30,str(details)
    if not xmlschema.validate(DOC):
        # Convert xmlschema.error_log to python list
        error_log = [['column','domain','domain_name','filename','level','level_name','line','message','type','type_name']]
        for LogEntry in xmlschema.error_log:
            error_log.append([LogEntry.column,LogEntry.domain,LogEntry.domain_name,LogEntry.filename,LogEntry.level,LogEntry.level_name,LogEntry.line,unicode(LogEntry.message.encode('iso-8859-1'), 'iso-8859-1'),LogEntry.type,LogEntry.type_name])

        ################# Debug start #######################
        # Write xmlshcme.error_log to debugfile
        debugfile = '/ESSArch/log/debug/validate_error_log_%s.log' % datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        debugfile_object = open(debugfile, 'w')
        for log_entry in error_log:
            debugfile_object.write(str(log_entry)+'\n')
        debugfile_object.close()
        ################# Debug end #######################

        #print str(error_log)
        return 1,str(error_log)
    logging.debug('return 0 after try to validate XML')
    return 0,'OK'

def writeToFile(DOC=None,FILENAME=None):
    try:
        DOC.write(FILENAME,encoding='UTF-8',xml_declaration=True,pretty_print=True)
    except etree.XMLSyntaxError, detail:
        return 10,str(detail)
    except IOError, detail:
        return 20,str(detail)
    else:
        return 0,'OK'

def parseFromFile(FILENAME=None):
    try:
        DOC  =  etree.ElementTree ( file=FILENAME )
    except etree.XMLSyntaxError, detail:
        return None,10,str(detail)
    except IOError, detail:
        return None,20,str(detail)
    else:
        return DOC,0,'OK'

#######################################################################################################################
# createMets
#
# Syntax: createMets(ID,LABEL,AGENT)
#
# parameters:
# 0     ID=/mets.mets(ID) "Q+ID+_METS.xml"		example: 'A0000002'
#	   /mets.mets(OBJID)          
#	   /mets.mets/mets.fileSec/mets.fileGrp(ID=fgrp001)/mets.file(ID) "file+ID+.tar"
#	   /mets.mets/mets.fileSec/mets.fileGrp(ID=fgrp001)/mets.file(ID)/mets.FLocat(href) "file:+href+.tar"
#	   /mets.mets/mets.structMap/mets.div(LABEL=Package)/mets.fptr(FILEID) "file+FILEID+.tar"
# 1     LABEL=/mets.mets(LABEL)		example: 'Exempel born-digital AIP RA' or 'Exempel imaging AIP RA'
# 2     AGENT=/mets.mets/mets.metsHdr/mets.agent/mets.name		example: [[ROLE,TYPE,OTHERTYPE,name,[note,...]],...]
#
# createMets(ID='Q0000002',LABEL='Exempel born-digital AIP RA',AGENT=[['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]],['CREATOR','ORGANIZATION','','Riksarkivet',[]],['CREATOR','INDIVIDUAL','','ESSArch_Marieberg',[]],['CREATOR','OTHER','SOFTWARE','ESSArch',['VERSION=2.0']]],NSlist=[]) 
#
def createMets(ID='Q0000002',LABEL='Exempel born-digital AIP RA',AGENT=[['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]],['CREATOR','ORGANIZATION','','Riksarkivet',[]],['CREATOR','INDIVIDUAL','','ESSArch_Marieberg',[]],['CREATOR','OTHER','SOFTWARE','ESSArch',['VERSION=2.0']]],NSlist=[],TYPE='AIP'):
    #LABEL = "Exempel born-digital AIP RA"
    #LABEL = "Exempel imaging AIP RA"

    tz=timezone.get_default_timezone()

    mets_NS = "{%s}" % METS_NAMESPACE
    xsi_NS = "{%s}" % XSI_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    NSMAP = {}
    NSMAP['mets'] = METS_NAMESPACE
    NSMAP['xlink'] = XLINK_NAMESPACE
    NSMAP['xsi'] = XSI_NAMESPACE
    schemaLocation = "%s %s" % (METS_NAMESPACE, METS_SCHEMALOCATION)
    for NS in NSlist:
        if NS == 'premis':
            NSMAP[NS] = PREMIS_NAMESPACE
            schemaLocation += " %s %s" % (PREMIS_NAMESPACE, PREMIS_SCHEMALOCATION)
        elif NS == 'addml':
            NSMAP[NS] = ADDML_NAMESPACE
            schemaLocation += " %s %s" % (ADDML_NAMESPACE, ADDML_SCHEMALOCATION)
        elif NS == 'mix':
            NSMAP[NS] = MIX_NAMESPACE
            schemaLocation += " %s %s" % (MIX_NAMESPACE, MIX_SCHEMALOCATION)
        elif NS == 'xhtml':
            NSMAP[NS] = XHTML_NAMESPACE
            schemaLocation += " %s %s" % (XHTML_NAMESPACE, XHTML_SCHEMALOCATION)

    root = etree.Element(mets_NS + "mets", nsmap=NSMAP) # lxml only!
    root.attrib[xsi_NS + "schemaLocation"] = schemaLocation
    root.attrib["PROFILE"] = METS_PROFILE
    root.attrib["OBJID"] = ID
    root.attrib["LABEL"] = LABEL
    root.attrib["TYPE"] = TYPE

    doc = etree.ElementTree(element=root, file=None)
    #########################################
    # metsHdr
    dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
    loc_dt_isoformat = dt.astimezone(tz).isoformat()
    EL_metsHdr = etree.SubElement(root, mets_NS + "metsHdr", attrib={"CREATEDATE" : loc_dt_isoformat})
    for i_agent in AGENT:
        EL_agent = etree.SubElement(EL_metsHdr, mets_NS + "agent", attrib={"ROLE" : "%s" % i_agent[0],
                                                                           "TYPE" : "%s" % i_agent[1]})
        if i_agent[1] == 'OTHER':
            EL_agent.attrib["OTHERTYPE"] = "%s" % i_agent[2]
        EL_name = etree.SubElement(EL_agent, mets_NS + "name").text = i_agent[3]
        for i_note in i_agent[4]:
            EL_note = etree.SubElement(EL_agent, mets_NS + "note").text = i_note
    if not TYPE == 'AIC':
        EL_metsDocumentID = etree.SubElement(EL_metsHdr, mets_NS + "metsDocumentID").text = "%s_Content_METS.xml" % ID

    if TYPE == 'AIP':
        #########################################
        # amdSec
        amdSec = etree.SubElement(root, mets_NS + "amdSec", attrib={"ID" : "amdSec001"})

    #########################################
    # fileSec
    fileSec = etree.SubElement(root, mets_NS + "fileSec")

    #########################################
    # structMap
    structMap = etree.SubElement(root, mets_NS + "structMap")
    div1 = etree.SubElement(structMap, mets_NS + "div", attrib={"LABEL" : "Package",
                                                                "ADMID" : ""})
    return doc

def createPMets(ID='Q0000002',LABEL='Exempel born-digital AIP RA',AGENT=[['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]],['CREATOR','ORGANIZATION','','Riksarkivet',[]],['CREATOR','INDIVIDUAL','','ESSArch_Marieberg',[]],['CREATOR','OTHER','SOFTWARE','ESSArch',['VERSION=2.0']]],P_SIZE='123',P_CREATED='2008-10-14T12:45:00+01:00',P_CHECKSUM='123aaa',P_CHECKSUMTYPE='MD5',M_SIZE='123',M_CREATED='2008-10-14T12:45:00+01:00',M_CHECKSUM='123aaa',M_CHECKSUMTYPE='MD5',TYPE='AIP'):
    #LABEL = "Exempel born-digital AIP RA"
    #LABEL = "Exempel imaging AIP RA"

    tz=timezone.get_default_timezone()

    mets_NS = "{%s}" % METS_NAMESPACE
    xsi_NS = "{%s}" % XSI_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    NSMAP = {'mets' : METS_NAMESPACE,
#    NSMAP = {None : METS_NAMESPACE,
             'xlink' : XLINK_NAMESPACE,
             'xsi' : XSI_NAMESPACE}
    root = etree.Element(mets_NS + "mets", nsmap=NSMAP) # lxml only!
    root.attrib[xsi_NS + "schemaLocation"] = "%s %s" % (METS_NAMESPACE, METS_SCHEMALOCATION)
    root.attrib["PROFILE"] = METS_PROFILE
    #root.attrib["ID"] = "Q%s_Package_METS.xml" % ID
    root.attrib["OBJID"] = ID
    root.attrib["LABEL"] = LABEL
    root.attrib["TYPE"] = TYPE

    doc = etree.ElementTree(element=root, file=None)
    #########################################
    # metsHdr
    dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
    loc_dt_isoformat = dt.astimezone(tz).isoformat()
    EL_metsHdr = etree.SubElement(root, mets_NS + "metsHdr", attrib={"CREATEDATE" : loc_dt_isoformat})
    for i_agent in AGENT:
        EL_agent = etree.SubElement(EL_metsHdr, mets_NS + "agent", attrib={"ROLE" : "%s" % i_agent[0],
                                                                           "TYPE" : "%s" % i_agent[1]})
        if i_agent[1] == 'OTHER':
            EL_agent.attrib["OTHERTYPE"] = "%s" % i_agent[2]
        EL_name = etree.SubElement(EL_agent, mets_NS + "name").text = i_agent[3]
        for i_note in i_agent[4]:
            EL_note = etree.SubElement(EL_agent, mets_NS + "note").text = i_note
    EL_metsDocumentID = etree.SubElement(EL_metsHdr, mets_NS + "metsDocumentID").text = "%s_Package_METS.xml" % ID

    #########################################
    # amdSec
    EL_amdSec = etree.SubElement(root, mets_NS + "amdSec", attrib={"ID" : "amdSec001"})

    #########################################
    # fileSec
    fileSec = etree.SubElement(root, mets_NS + "fileSec")
    fileGrp001 = etree.SubElement(fileSec, mets_NS + "fileGrp", attrib={"ID" : "fgrp001",
                                                                        "USE" : "PACKAGES"})
    file001 = etree.SubElement(fileGrp001, mets_NS + "file", attrib={"ID" : "file%s.tar" % ID,
                                                                     "MIMETYPE" : "application/x-tar",
                                                                     "SIZE" : str(P_SIZE),
                                                                     "CREATED" : P_CREATED,
                                                                     "CHECKSUM" : P_CHECKSUM,
                                                                     "CHECKSUMTYPE" : P_CHECKSUMTYPE,
                                                                     "USE" : "PACKAGE",
                                                                     "ADMID" : "techMD001"})
    FLocat001 = etree.SubElement(file001, mets_NS + "FLocat", attrib={"LOCTYPE" : "URL",
                                                                      xlink_NS + "type" : "simple",
                                                                      xlink_NS + "href" : "file:%s.tar" % ID})
    #########################################
    # techMD
    # Create a new techMD element
    techMD_all = doc.findall("%samdSec/%stechMD[@ID]" % (mets_NS,mets_NS))
    techMD_num = string.zfill(len(techMD_all) + 1, 3)
    techMD_ID = 'techMD' + techMD_num
    # Use insert istead of "etree.SubElement" to insert all techMD in number order before "digiprovMD"
    EL_amdSec.insert(len(techMD_all), etree.Element(mets_NS + "techMD", attrib={"ID" : "%s" % techMD_ID}))
    ELs_techMD = EL_amdSec.findall("%stechMD[@ID]" % (mets_NS))
    for i_techMD in ELs_techMD:
        if i_techMD.get("ID") == techMD_ID:
            EL_techMD = i_techMD

    EL_mdRef = etree.SubElement(EL_techMD, mets_NS + "mdRef", attrib={"ID" : "file%s_Content_METS.xml" % ID,
                                                                      "LOCTYPE" : 'URL',
                                                                      "MDTYPE" : 'OTHER',
                                                                      "OTHERMDTYPE" : 'METS',
                                                                      "MIMETYPE" : 'text/xml',
                                                                      "SIZE" : str(M_SIZE),
                                                                      "CREATED" : M_CREATED,
                                                                      "CHECKSUM" : M_CHECKSUM,
                                                                      "CHECKSUMTYPE" : M_CHECKSUMTYPE,
                                                                      xlink_NS + "type" : 'simple',
                                                                      xlink_NS + "href" : "file:%s_Content_METS.xml" % ID})

    #########################################
    # structMap
    structMap = etree.SubElement(root, mets_NS + "structMap")
    div1 = etree.SubElement(structMap, mets_NS + "div", attrib={"LABEL" : "Package",
                                                                "ADMID" : "techMD001"})
    fptr = etree.SubElement(div1, mets_NS + "fptr", attrib={"FILEID" : "file%s.tar" % ID})
    EL_structMap_div2 = etree.SubElement(div1, mets_NS + "div", attrib={"LABEL" : "Content description"})
    EL_fptr = etree.SubElement(EL_structMap_div2, mets_NS + "fptr", attrib={"FILEID" : "file%s_Content_METS.xml" % ID})

    return doc

#######################################################################################################################
# createPremis
#
# Syntax: createPremis(FILE=[xlink_type,xlink_href,objectIdentifierType,objectIdentifierValue,preservationLevelValue,compositionLevel,formatName,[[objectCharacteristicsExtension XML etree.Elemt],...],storageMedium,[[relationshipType,relationshipSubType,relatedObjectIdentifierType,relatedObjectIdentifierValue],...]],NSlist=[xxx,...])
#
# parameters:
# FILE=[xlink_type,xlink_href,objectIdentifierType,objectIdentifierValue,preservationLevelValue,compositionLevel,formatName,[[objectCharacteristicsExtension XML etree.Elemt],...],storageMedium]
# 0     xlink_type=/premis.object/premis.objectIdentifier(xlink:type)                           example: 'simple'
# 1     xlink_href=/premis.object/premis.objectIdentifier(xlink:href)                           example: ''
# 2     objectIdentifierType=/premis.object/premis.objectIdentifier/premis.objectIdentifierType example: 'SE/RA'
# 3     objectIdentifierValue=/premis.object/premis.objectIdentifier/premis.objectIdentifierValue       example: '00067990'
# 4     preservationLevelValue=/premis.object/premis.preservationLevel/premis.preservationLevelValue
# 5     significantProperties=/premis.object/premis.significantProperties       example: [significantProperties list]
# 5.0     significantPropertiesType=/premis.object/premis.significantProperties/premis.significantPropertiesType        example: 'PageName'
# 5.1     significantPropertiesValue=/premis.object/premis.significantProperties/premis.significantPropertiesValue      example: 'SE/RA/83002/2005/23/00067990/00000002.TIF'
# 6     compositionLevel=/premis.object/premis.objectCharacteristics/premis.compositionLevel    example: '0'
# 7     formatName=/premis.object/premis.objectCharacteristics/premis.format/premis.formatDesignation/premis.formatName example: 'tar'
# 8	objectCharacteristicsExtension=/premis.object/premis.objectCharacteristics/premis.objectCharacteristicsExtension        [objectCharacteristicsExtension list]
# 8.0	  xml=/premis.object/premis.objectCharacteristics/premis.objectCharacteristicsExtension/xxx.xml example: 'etree.Element'
# 9.0	  storageMedium=/premis.object/premis.storage/premis.storageMedium	example: 'bevarandesystemet'
# 10    relationship=/premis.object/premis.relationship       [relationship list]
# 10.0    relationshipType=/premis.object/premis.relationship/premis.relationshipType       example: 'structural'
# 10.1    relationshipSubType=/premis.object/premis.relationship/premis.relationshipSubType       example: 'is part of'
# 10.2    relatedObjectIdentifierType=/premis.object/premis.relationship/premis.relatedObjectIdentification/premis.relatedObjectIdentifierType       example: 'SE/RA'
# 10.3    relatedObjectIdentifierValue=/premis.object/premis.relationship/premis.relatedObjectIdentification/premis.relatedObjectIdentifierValue       example: '00067990'
# NSlist=[xxx,...]	example: ['mix']
#
# createPremis(FILE=['simple','','SE/RA','00067990','full','0','tar','','bevarandesystemet',['structural','is part of','SE/RA','00067990']],NSlist=['mix'])
#
def createPremis(FILE=['simple','','SE/RA','00067990','full',[],'0','tar','','bevarandesystemet',['structural','is part of','SE/RA','00067990']],NSlist=[]):
    premis_NS = "{%s}" % PREMIS_NAMESPACE
    xsi_NS = "{%s}" % XSI_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    NSMAP = {}
    NSMAP['premis'] = PREMIS_NAMESPACE
    NSMAP['xlink'] = XLINK_NAMESPACE
    NSMAP['xsi'] = XSI_NAMESPACE
    a_schemaLocation = '%s %s' % (PREMIS_NAMESPACE, PREMIS_SCHEMALOCATION)
    for NS in NSlist:
        if NS == 'mix':
            NSMAP[NS] = MIX_NAMESPACE
            a_schemaLocation += " %s %s" % (MIX_NAMESPACE, MIX_SCHEMALOCATION)

    #NSMAP = {'premis' : PREMIS_NAMESPACE,
    #         'xlink' : XLINK_NAMESPACE,
    #         'xsi' : XSI_NAMESPACE}
    #if 'MIX' in TYPE:
    #    NSMAP.update({'mix' : MIX_NAMESPACE})
    #    a_schemaLocation += ' %s %s' % (MIX_NAMESPACE, MIX_SCHEMALOCATION)
    #if 'XHTML' in TYPE
    #    NSMAP.update({'xhtml' : xhtml_NS})
    #    a_schemaLocation += ' %s %s' % (XHTML_NAMESPACE, XHTML_SCHEMALOCATION)
    root = etree.Element(premis_NS + "premis", nsmap=NSMAP) # lxml only!
    #root.attrib[xsi_NS + "schemaLocation"] = "%s %s" % (PREMIS_NAMESPACE, PREMIS_SCHEMALOCATION)
    root.attrib[xsi_NS + "schemaLocation"] = a_schemaLocation
    root.attrib["version"] = PREMIS_VERSION

    doc = etree.ElementTree(element=root, file=None)
    if FILE:
        AddPremisFileObject(doc,FILES=[(FILE[0],FILE[1],FILE[2],FILE[3],FILE[4],FILE[5],FILE[6],[],'',FILE[7],'',FILE[8],[['','','','',FILE[9]]],FILE[10])])

    return doc

#######################################################################################################################
# AddPremisFileObject
#
# Syntax: AddPremisFileObject(DOC,FILES=[(xlink_type,xlink_href,objectIdentifierType,objectIdentifierValue,preservationLevelValue,[[significantPropertiesType,significantPropertiesValue],...],compositionLevel,[[messageDigestAlgorithm,messageDigest,messageDigestOriginator],...],size,formatName,formatVersion,[[objectCharacteristicsExtension XML etree.Elemt],...],[[xlink_type,xlink_href,contentLocationType,contentLocationValue,storageMedium],...],[[relationshipType,relationshipSubType,relatedObjectIdentifierType,relatedObjectIdentifierValue],...])],...)
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# FILES=[(xlink_type,xlink_href,objectIdentifierType,objectIdentifierValue,preservationLevelValue,[[significantPropertiesType,significantPropertiesValue],...],compositionLevel,[[messageDigestAlgorithm,messageDigest,messageDigestOriginator],...],size,formatName,formatVersion,[[objectCharacteristicsExtension XML etree.Elemt],...],[[xlink_type,xlink_href,contentLocationType,contentLocationValue,storageMedium],...],[[relationshipType,relationshipSubType,relatedObjectIdentifierType,relatedObjectIdentifierValue],...]),...]
# 0	xlink_type=/premis.object/premis.objectIdentifier(xlink:type) 				example: 'simple'
# 1	xlink_href=/premis.object/premis.objectIdentifier(xlink:href) 				example: ''
# 2	objectIdentifierType=/premis.object/premis.objectIdentifier/premis.objectIdentifierType	example: 'SE/RA'
# 3	objectIdentifierValue=/premis.object/premis.objectIdentifier/premis.objectIdentifierValue	example: '00067990/00000001.TIF'
# 4     preservationLevelValue=/premis.object/premis.preservationLevel/premis.preservationLevelValue
# 5	significantProperties=/premis.object/premis.significantProperties	example: [significantProperties list]
# 5.0	  significantPropertiesType=/premis.object/premis.significantProperties/premis.significantPropertiesType	example: 'PageName'
# 5.1	  significantPropertiesValue=/premis.object/premis.significantProperties/premis.significantPropertiesValue	example: 'SE/RA/83002/2005/23/00067990/00000002.TIF'
# 6	compositionLevel=/premis.object/premis.objectCharacteristics/premis.compositionLevel	example: '0'
# 7	fixity=/premis.object/premis.fixity		[fixity list]
# 7.0	  messageDigestAlgorithm=/premis.object/premis.objectCharacteristics/premis.fixity/premis.messageDigestAlgorithm	example: 'MD5'
# 7.1	  messageDigest=/premis.object/premis.objectCharacteristics/premis.fixity/premis.messageDigest	example: '1342314dfsrewqer12'
# 7.2	  messageDigestOriginator=/premis.object/premis.objectCharacteristics/premis.fixity/premis.messageDigestOriginator	example: 'ESSArch'
# 8	size=/premis.object/premis.objectCharacteristics/premis.size	example: '16744'
# 9	formatName=/premis.object/premis.objectCharacteristics/premis.format/premis.formatDesignation/premis.formatName	example: 'image/tiff'
# 10	formatVersion=/premis.object/premis.objectCharacteristics/premis.format/premis.formatDesignation/premis.formatVersion	example: '6.0'
# 11	objectCharacteristicsExtension=/premis.object/premis.objectCharacteristics/premis.objectCharacteristicsExtension	[objectCharacteristicsExtension list]
# 11.1	  xml=/premis.object/premis.objectCharacteristics/premis.objectCharacteristicsExtension/xxx.xml	example: 'etree.Element'
# 12	storage=/premis.object/premis.storage	[storage list]
# 12.0	  xlink_type=/premis.object/premis.storage/premis.contentLocation(xlink:type)	example: 'simple'
# 12.1	  xlink_href=/premis.object/premis.storage/premis.contentLocation(xlink:href)	example: ''
# 12.2	  contentLocationType=/premis.object/premis.storage/premis.contentLocation/premis.contentLocationType	example: 'AIP'
# 12.3	  contentLocationValue=/premis.object/premis.storage/premis.contentLocation/premis.contentLocationValue	example: '00067990'
# 12.4	  storageMedium=/premis.object/premis.storage/premis.storageMedium	example: '' or 'disk123'
# 13	relationship=/premis.object/premis.relationship       [relationship list]
# 13.0	  relationshipType=/premis.object/premis.relationship/premis.relationshipType       example: 'structural'
# 13.1	  relationshipSubType=/premis.object/premis.relationship/premis.relationshipSubType       example: 'is part of'
# 13.2    relatedObjectIdentifierType=/premis.object/premis.relationship/premis.relatedObjectIdentification/premis.relatedObjectIdentifierType       example: 'SE/RA'
# 13.3    relatedObjectIdentifierValue=/premis.object/premis.relationship/premis.relatedObjectIdentification/premis.relatedObjectIdentifierValue       example: '00067990'
#
# AddPremisFileObject(XMLDOC,FILES=[('simple','','SE/RA','00067990/00000001.TIF',[['PageName','SE/RA/83002/2005/23/00067990/00000001.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch'],...],'16744','image/tiff','6.0',[['etree.Element']],[['simple','','AIP','00067990']],[['structural','is part of','SE/RA','00067990']]),('simple','','SE/RA','00067990/00000002.TIF',[['PageName','SE/RA/83002/2005/23/00067990/00000002.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch'],...],'16744','image/tiff','6.0',[['etree.Element']],[['simple','','AIP','00067990','']],[['structural','is part of','SE/RA','00067990']])])
#
def AddPremisFileObject(DOC=None,FILES=[('simple','','SE/RA','00067990/00000001.TIF','',[['PageName','SE/RA/83002/2005/23/00067990/00000001.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch']],'16744','image/tiff','6.0',[['etree.Element']],[['simple','','AIP','00067990','']],[['structural','is part of','SE/RA','00067990']]),('simple','','SE/RA','00067990/00000002.TIF','',[['PageName','SE/RA/83002/2005/23/00067990/00000002.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch']],'16744','image/tiff','6.0',[['etree.Element']],[['simple','','AIP','00067990','']],[['structural','is part of','SE/RA','00067990']])]):
    premis_NS = "{%s}" % PREMIS_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    xsi_NS = "{%s}" % XSI_NAMESPACE

    root = DOC.getroot()

    for file in FILES:
        ELs_object = DOC.findall("%sobject" % (premis_NS))
        if len(ELs_object):
            # Add new "object" element at the end of object section
            EL_object_last = ELs_object[len(ELs_object)-1]
            EL_premis = EL_object_last.getparent()
            root.insert(EL_premis.index(EL_object_last)+1, etree.Element(premis_NS + "object", attrib={xsi_NS + "type" : "premis:file"}))

            # Position to last event
            ELs_object = DOC.findall("%sobject" % (premis_NS))
            EL_object = ELs_object[len(ELs_object)-1]
        else:
            # Add the first "object" element to XML file
            EL_object = etree.SubElement(root, premis_NS + "object", attrib={xsi_NS + "type" : "premis:file"})

        # 1.1 objectIdentifier (M, R)
        EL_objectIdentifier = etree.SubElement(EL_object, premis_NS + "objectIdentifier")
        if file[1]:
            EL_objectIdentifier.attrib[xlink_NS + "type"] = file[0]
            EL_objectIdentifier.attrib[xlink_NS + "href"] = file[1]
        # 1.1.1 objectIdentifierType (M, NR)
        EL_objectIdentifierType = etree.SubElement(EL_objectIdentifier, premis_NS + "objectIdentifierType").text = file[2] 
        # 1.1.2 objectIdentifierValue (M, NR)
        EL_objectIdentifierValue = etree.SubElement(EL_objectIdentifier, premis_NS + "objectIdentifierValue").text = file[3] 
        if file[4]:
            # 1.3 preservationLevel (O, R) [representation, file]
            EL_preservationLevel = etree.SubElement(EL_object, premis_NS + "preservationLevel")
            # 1.3.1 preservationLevelValue (M, NR) [representation, file]
            EL_preservationLevelValue = etree.SubElement(EL_preservationLevel, premis_NS + "preservationLevelValue").text = file[4]
        if file[5]:
            for significantProperties in file[5]:
                # 1.4 significantProperties (O, R)
                EL_significantProperties = etree.SubElement(EL_object, premis_NS + "significantProperties")
                # 1.4.1 significantPropertiesType (O, NR)
                EL_significantPropertiesType = etree.SubElement(EL_significantProperties, premis_NS + "significantPropertiesType").text = significantProperties[0]
                # 1.4.2 significantPropertiesValue (O, NR)
                EL_significantPropertiesValue = etree.SubElement(EL_significantProperties, premis_NS + "significantPropertiesValue").text = significantProperties[1]
        # 1.5 objectCharacteristics (M, R) [file, bitstream]
        EL_objectCharacteristics = etree.SubElement(EL_object, premis_NS + "objectCharacteristics")
        # 1.5.1 compositionLevel (M, NR) [file, bitstream]
        EL_compositionLevel = etree.SubElement(EL_objectCharacteristics, premis_NS + "compositionLevel").text = file[6] 
        if file[7]:
            for fixity in file[7]:
                # 1.5.2 fixity (O, R) [file, bitstream]
                EL_fixity = etree.SubElement(EL_objectCharacteristics, premis_NS + "fixity") 
                # 1.5.2.1 messageDigestAlgorithm (M, NR) [file, bitstream]
                EL_messageDigestAlgorithm = etree.SubElement(EL_fixity, premis_NS + "messageDigestAlgorithm").text = fixity[0] 
                # 1.5.2.2 messageDigest (M, NR) [file, bitstream]
                EL_messageDigest = etree.SubElement(EL_fixity, premis_NS + "messageDigest").text = fixity[1] 
                # 1.5.2.3 messageDigestOriginator (O, NR) [file, bitstream]
                EL_messageDigestOriginator = etree.SubElement(EL_fixity, premis_NS + "messageDigestOriginator").text = fixity[2] 
        if file[8]:
            # 1.5.3 size (O, NR) [file, bitstream]
            EL_size = etree.SubElement(EL_objectCharacteristics, premis_NS + "size").text = file[8] 
        # 1.5.4 format (M, R) [file, bitstream]
        EL_format = etree.SubElement(EL_objectCharacteristics, premis_NS + "format") 
        # 1.5.4.1 formatDesignation (O, NR) [file, bitstream]
        EL_formatDesignation = etree.SubElement(EL_format, premis_NS + "formatDesignation") 
        # 1.5.4.1.1 formatName (M, NR) [file, bitstream]
        EL_formatName = etree.SubElement(EL_formatDesignation, premis_NS + "formatName").text = file[9] 
        if file[10]:
            # 1.5.4.1.2 formatVersion (O, NR) [file, bitstream]
            EL_formatVersion = etree.SubElement(EL_formatDesignation, premis_NS + "formatVersion").text = file[10] 
        if file[11]:
            for objectCharacteristicsExtension in file[11]: 
                # 1.5.7 objectCharacteristicsExtension (O, R) [file, bitstream]
                EL_objectCharacteristicsExtension = etree.SubElement(EL_objectCharacteristics, premis_NS + "objectCharacteristicsExtension") 
                # Append XML
                EL_objectCharacteristicsExtension.append(objectCharacteristicsExtension[0])
        for storage in file[12]:
            # 1.7 storage (M, R) [file, bitstream]
            EL_storage = etree.SubElement(EL_object, premis_NS + "storage") 
            if storage[2] and storage[3]:
                # 1.7.1 contentLocation (O, NR) [file, bitstream]
                EL_contentLocation = etree.SubElement(EL_storage, premis_NS + "contentLocation")
                if storage[1]:
                    EL_contentLocation.attrib[xlink_NS + "type"] = storage[0]
                    EL_contentLocation.attrib[xlink_NS + "href"] = storage[1]
                # 1.7.1.1 contentLocationType (M, NR) [file, bitstream]
                EL_contentLocationType = etree.SubElement(EL_contentLocation, premis_NS + "contentLocationType").text = storage[2]
                # 1.7.1.2 contentLocationValue (M, NR) [file, bitstream]
                EL_contentLocationValue = etree.SubElement(EL_contentLocation, premis_NS + "contentLocationValue").text = storage[3]
            if storage[4]:
                # 1.7.2 storageMedium (O, NR) [file, bitstream]  
                EL_storageMedium = etree.SubElement(EL_storage, premis_NS + "storageMedium").text = storage[4]
        if file[13]:
            for relation in file[13]:
                # 1.10 relationship (O, R)
                EL_relationship = etree.SubElement(EL_object, premis_NS + "relationship") 
                # 1.10.1 relationshipType (M, NR)
                EL_relationshipType = etree.SubElement(EL_relationship, premis_NS + "relationshipType").text = relation[0]
                # 1.10.2 relationshipSubType (M, NR)
                EL_relationshipSubType = etree.SubElement(EL_relationship, premis_NS + "relationshipSubType").text = relation[1]
                # 1.10.3 relatedObjectIdentification (M, R)
                EL_relatedObjectIdentification = etree.SubElement(EL_relationship, premis_NS + "relatedObjectIdentification")
                # 1.10.3.1 relatedObjectIdentifierType (M, NR)
                EL_relatedObjectIdentifierType = etree.SubElement(EL_relatedObjectIdentification, premis_NS + "relatedObjectIdentifierType").text = relation[2]
                # 1.10.3.2 relatedObjectIdentifierValue (M, NR)
                EL_relatedObjectIdentifierValue = etree.SubElement(EL_relatedObjectIdentification, premis_NS + "relatedObjectIdentifierValue").text = relation[3]

    return DOC

#######################################################################################################################
# AddPremisEvent
#
# Syntax: AddPremisEvent(DOC,EVENTS=[(eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,eventOutcome,eventOutcomeDetailNote,[[linkingAgentIdentifierType,linkingAgentIdentifierValue],...],[[linkingObjectIdentifierType,linkingObjectIdentifierValue],...])],...)
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# EVENTS=[(eventIdentifierType,eventIdentifierValue,eventType,eventDateTime,eventDetail,eventOutcome,eventOutcomeDetailNote,[[linkingAgentIdentifierType,linkingAgentIdentifierValue],...],[[linkingObjectIdentifierType,linkingObjectIdentifierValue],...])]
# 0     eventIdentifierType=/premis.event/premis.eventIdentifier/premis.eventIdentifierType	example: 'SE/RA'
# 1     eventIdentifierValue=/premis.event/premis.eventIdentifier/premis.eventIdentifierValue	example: 'GUID123xasd'
# 2     eventType=/premis.event/premis.eventType	example: '1000' or 'TIFF editering'
# 3     eventDateTime=/premis.event/premis.eventDateTime	example: '2005-11-08 12:24:09'
# 4     eventDetail=/premis.event/premis.eventDetail	example: 'TIFF editering'
# 5     eventOutcome=/premis.event/premis.eventOutcomeInformation/premis.eventOutcome	example: 'Status: OK'
# 6     eventOutcomeDetailNote=/premis.event/premis.eventOutcomeInformation/premis.eventOutcomeDetail/premis.eventOutcomeDetailNote	example: 'Profil: GREY;gsuidxx123'
# 7.0	linkingAgentIdentifierType=/premis.event/premis.linkingAgentIdentifier/premis.linkingAgentIdentifierType	example: 'SE/RA'
# 7.1	linkingAgentIdentifierValue=/premis.event/premis.linkingAgentIdentifier/premis.linkingAgentIdentifierValue	example: 'TIFFedit_MKC'
# 8.0	linkingObjectIdentifierType=/premis.event/premis.linkingObjectIdentifier/premis.linkingObjectIdentifierType	example: 'SE/RA'
# 8.1	linkingObjectIdentifierValue=/premis.event/premis.linkingObjectIdentifier/premis.linkingObjectIdentifierValue	example: '00067990/00000001.TIF'
#
# AddPremisEvent(DOC=None,EVENTS=[('SE/RA','GUID123xasd','TIFF editering','2005-11-08 12:24:09','TIFF editering','Status: OK','Profil: GREY;gsuidxx123',[['SE/RA','TIFFedit_MKC']],[['SE/RA','00067990/00000001.TIF']])]) 
#
def AddPremisEvent(DOC=None,EVENTS=[('SE/RA','GUID123xasd','TIFF editering','2005-11-08 12:24:09','TIFF editering','Status: OK','Profil: GREY;gsuidxx123',[['SE/RA','TIFFedit_MKC']],[['SE/RA','00067990/00000001.TIF']])]):
    premis_NS = "{%s}" % PREMIS_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE

    root = DOC.getroot()

    for event in EVENTS:
        ELs_event = DOC.findall("%sevent" % (premis_NS))
        if len(ELs_event):
            # Add new "event" element at the end of event section
            EL_event_last = ELs_event[len(ELs_event)-1]
            EL_premis = EL_event_last.getparent()
            root.insert(EL_premis.index(EL_event_last)+1, etree.Element(premis_NS + "event"))

            # Position to last event
            ELs_event = DOC.findall("%sevent" % (premis_NS))
            EL_event = ELs_event[len(ELs_event)-1]
        else:
            # Add the first "event" element to XML file
            EL_event = etree.SubElement(root, premis_NS + "event")

        # 2.1 eventIdentifier (M, NR)
        EL_eventIdentifier = etree.SubElement(EL_event, premis_NS + "eventIdentifier")
        # 2.1.1 eventIdentifierType (M, NR)
        EL_eventIdentifierType = etree.SubElement(EL_eventIdentifier, premis_NS + "eventIdentifierType").text = event[0]
        # 2.1.2 eventIdentifierValue (M, NR)
        EL_eventIdentifierValue = etree.SubElement(EL_eventIdentifier, premis_NS + "eventIdentifierValue").text = event[1]
        # 2.2 eventType (M, NR)
        EL_eventType = etree.SubElement(EL_event, premis_NS + "eventType").text = event[2]
        # 2.3 eventDateTime (M, NR)
        EL_eventDateTime = etree.SubElement(EL_event, premis_NS + "eventDateTime").text = event[3]
        # 2.4 eventDetail (O, NR)
        if event[4]:
            EL_eventDetail = etree.SubElement(EL_event, premis_NS + "eventDetail").text = event[4]
        # 2.5 eventOutcomeInformation (O, R)
        EL_eventOutcomeInformation = etree.SubElement(EL_event, premis_NS + "eventOutcomeInformation")
        # 2.5.1 eventOutcome (O, NR)
        EL_eventOutcome = etree.SubElement(EL_eventOutcomeInformation, premis_NS + "eventOutcome").text = event[5]
        # 2.5.2 eventOutcomeDetail (O, R)
        EL_eventOutcomeDetail = etree.SubElement(EL_eventOutcomeInformation, premis_NS + "eventOutcomeDetail")
        # 2.5.2.1 eventOutcomeDetailNote (O, NR)
        EL_eventOutcomeDetailNote = etree.SubElement(EL_eventOutcomeDetail, premis_NS + "eventOutcomeDetailNote").text = event[6]
        #* 2.5.2.2 eventOutcomeDetailExtension (O, R)
        for linkingAgentIdentifier in event[7]:
            # 2.6 linkingAgentIdentifier (O, R)
            EL_linkingAgentIdentifier = etree.SubElement(EL_event, premis_NS + "linkingAgentIdentifier")
            # 2.6.1 linkingAgentIdentifierType (M, NR)
            EL_linkingAgentIdentifierType = etree.SubElement(EL_linkingAgentIdentifier, premis_NS + "linkingAgentIdentifierType").text = linkingAgentIdentifier[0]
            # 2.6.2 linkingAgentIdentifierValue (M, NR)
            EL_linkingAgentIdentifierValue = etree.SubElement(EL_linkingAgentIdentifier, premis_NS + "linkingAgentIdentifierValue").text = linkingAgentIdentifier[1]
            #* 2.6.3 linkingAgentRole (O, R)
        for linkingObjectIdentifier in event[8]:
            # 2.7 linkingObjectIdentifier (O, R)
            EL_linkingObjectIdentifier = etree.SubElement(EL_event, premis_NS + "linkingObjectIdentifier")
            # 2.7.1 linkingObjectIdentifierType (M, NR)
            EL_linkingObjectIdentifierType = etree.SubElement(EL_linkingObjectIdentifier, premis_NS + "linkingObjectIdentifierType").text = linkingObjectIdentifier[0]
            # 2.7.2 linkingObjectIdentifierValue (M, NR)
            EL_linkingObjectIdentifierValue = etree.SubElement(EL_linkingObjectIdentifier, premis_NS + "linkingObjectIdentifierValue").text = linkingObjectIdentifier[1]
            #* 2.7.3 linkingObjectRole (O, R)
    return DOC

#######################################################################################################################
# AddPremisAgent
#
# Syntax: AddPremisAgent(DOC,AGENTS=[(AgentIdentifierType,AgentIdentifierValue,agentName,agentType)],...)
#
# parameters:
# DOC=etree.Element or etree.ElementTree
# AGENTS=[(AgentIdentifierType,AgentIdentifierValue,agentName,agentType)]
# 0     agentIdentifierType=/premis.agent/premis.agentIdentifier/premis.agentIdentifierType     example: 'SE/RA'
# 1     agentIdentifierValue=/premis.agent/premis.agentIdentifier/premis.agentIdentifierValue     example: 'TIFFedit_MKC'
# 2     agentName=/premis.agent/premis.agentName	example: 'TIFFedit vid MKC'
# 3     agentType=/premis.agent/premis.agentType	example: 'software'
#
# AddPremisAgent(DOC=None,AGENTS=[('SE/RA','TIFFedit_MKC','TIFFedit vid MKC','software')])
#
def AddPremisAgent(DOC=None,AGENTS=[('SE/RA','TIFFedit_MKC','TIFFedit vid MKC','software')]):
    premis_NS = "{%s}" % PREMIS_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    root = DOC.getroot()
    # 3 agent
    EL_agent = etree.SubElement(root, premis_NS + "agent")
    for agent in AGENTS:
        # 3.1 agentIdentifier (R, M)
        EL_agentIdentifier = etree.SubElement(EL_agent, premis_NS + "agentIdentifier")
        # 3.1.1 agentIdentifierType (M, NR)
        EL_agentIdentifierType = etree.SubElement(EL_agentIdentifier, premis_NS + "agentIdentifierType").text = agent[0]
        # 3.1.2 agentIdentifierValue (M, NR)
        EL_agentIdentifierValue = etree.SubElement(EL_agentIdentifier, premis_NS + "agentIdentifierValue").text = agent[1]
        # 3.2 agentName (O, R)
        EL_agentName = etree.SubElement(EL_agent, premis_NS + "agentName").text = agent[2]
        # 3.3 agentType (O, NR)
        EL_agentType = etree.SubElement(EL_agent, premis_NS + "agentType").text = agent[3]
    return DOC

#######################################################################################################################
# createMIX
#
# syntax: createMIX(MIX_byteOrder,MIX_compressionScheme,MIX_imageWidth,MIX_imageHeight,MIX_colorSpace,MIX_sourceID=[[sourceIDType,sourceIDValue],...],MIX_dateTimeCreated,MIX_imageProducer,MIX_scannerManufacturer,MIX_scannerModelName,MIX_scanningSoftwareName,MIX_orientation,MIX_samplingFrequencyUnit,MIX_numerator_x,MIX_numerator_y,MIX_bitsPerSampleValue,MIX_bitsPerSampleUnit,MIX_samplesPerPixel,MIX_schemaLocation)
#
# parameters:
# 0	MIX_byteOrder		example: None or 'little endian'
# 1	MIX_compressionScheme		example: 'Grupp 4 Fax'
# 2	MIX_imageWidth		example: '3339'
# 3	MIX_imageHeight		example: '4652'
# 4	MIX_colorSpace		example: 'WhiteIsZero'
# 5	MIX_sourceID		[MIX_sourceID list]
# 5.0	  sourceIDType		example: 'SE/RA' or 'ImageDescription'
# 5.1	  sourceIDValue		example: 'SE/VA/13012/A II c/37' or '17  Arvika �stra (sfs) A II c/37 1970-1991' 
# 6	MIX_dateTimeCreated	example: '2008-06-18T10:15:11'
# 7	MIX_imageProducer	example: 'V�rmlandsarkiv'
# 8	MIX_scannerManufacturer	example: 'KODAK   |'
# 9	MIX_scannerModelName	example: 'i830 Scanner'
# 10	MIX_scanningSoftwareName	example: 'xVCS V3.5      '
# 11	MIX_orientation		example: 'normal*'
# 12	MIX_samplingFrequencyUnit	example: 'in.'
# 13	MIX_numerator_x		example: '400'
# 14	MIX_numerator_y		example: '400'
# 15	MIX_bitsPerSampleValue		example: '1'
# 16	MIX_bitsPerSampleUnit		example: 'integer'
# 17	MIX_samplesPerPixel		example: '1'
# 18	MIX_schemaLocation		example: None or 'http://xml.ra.se/MIX/RA_MIX.xsd'
#
# createMIX(MIX_byteOrder=None,MIX_compressionScheme='Grupp 4 Fax',MIX_imageWidth='3339',MIX_imageHeight='4652',MIX_colorSpace='WhiteIsZero',MIX_sourceID=[['SE/RA','SE/VA/13012/A II c/37'],['ImageDescription','17  Arvika �stra (sfs) A II c/37 1970-1991']],MIX_dateTimeCreated='2008-06-18T10:15:11',MIX_imageProducer='V�rmlandsarkiv',MIX_scannerManufacturer='KODAK   |',MIX_scannerModelName='i830 Scanner',MIX_scanningSoftwareName='xVCS V3.5      ',MIX_orientation='normal*',MIX_samplingFrequencyUnit='in.',MIX_numerator_x='400',MIX_numerator_y='400',MIX_bitsPerSampleValue='1',MIX_bitsPerSampleUnit='integer',MIX_samplesPerPixel='1',MIX_schemaLocation=None)
#
def createMIX(MIX_byteOrder=None,MIX_compressionScheme='Grupp 4 Fax',MIX_imageWidth='3339',MIX_imageHeight='4652',MIX_colorSpace='WhiteIsZero',MIX_sourceID=[['SE/RA','SE/VA/13012/A II c/37'],['ImageDescription','17  Arvika �stra (sfs) A II c/37 1970-1991']],MIX_dateTimeCreated='2008-06-18T10:15:11',MIX_imageProducer='V�rmlandsarkiv',MIX_scannerManufacturer='KODAK   |',MIX_scannerModelName='i830 Scanner',MIX_scanningSoftwareName='xVCS V3.5      ',MIX_orientation='normal*',MIX_samplingFrequencyUnit='in.',MIX_numerator_x='400',MIX_numerator_y='400',MIX_bitsPerSampleValue='1',MIX_bitsPerSampleUnit='integer',MIX_samplesPerPixel='1',MIX_schemaLocation=None):
    DEBUG = 0
    mix_NS = "{%s}" % MIX_NAMESPACE
    xsi_NS = "{%s}" % XSI_NAMESPACE
    xlink_NS = "{%s}" % XLINK_NAMESPACE
    NSMAP = {'mix' : MIX_NAMESPACE,
             'xlink' : XLINK_NAMESPACE,
             'xsi' : XSI_NAMESPACE}
    root = etree.Element(mix_NS + "mix", nsmap=NSMAP) # lxml only!
    if MIX_schemaLocation:
        root.attrib[xsi_NS + "schemaLocation"] = "%s %s" % (MIX_NAMESPACE, MIX_schemaLocation)

    # BasicDigitalObjectInformation
    # 6
    EL_BasicDigitalObjectInformation = etree.SubElement(root, mix_NS + "BasicDigitalObjectInformation")
    # 6.5
    if MIX_byteOrder:
        EL_byteOrder = etree.SubElement(EL_BasicDigitalObjectInformation, mix_NS + "byteOrder").text = MIX_byteOrder 
    # 6.6
    EL_Compression = etree.SubElement(EL_BasicDigitalObjectInformation, mix_NS + "Compression") 
    # 6.6.1
    EL_compressionScheme = etree.SubElement(EL_Compression, mix_NS + "compressionScheme").text = MIX_compressionScheme 
    
    # BasicImageInformation
    # 7
    EL_BasicImageInformation = etree.SubElement(root, mix_NS + "BasicImageInformation")
    # 7.1
    EL_BasicImageCharacteristics = etree.SubElement(EL_BasicImageInformation, mix_NS + "BasicImageCharacteristics")
    # 7.1.1
    EL_imageWidth = etree.SubElement(EL_BasicImageCharacteristics, mix_NS + "imageWidth").text = MIX_imageWidth 
    # 7.1.2
    EL_imageHeight = etree.SubElement(EL_BasicImageCharacteristics, mix_NS + "imageHeight").text = MIX_imageHeight 
    # 7.1.3
    EL_PhotometricInterpretation = etree.SubElement(EL_BasicImageCharacteristics, mix_NS + "PhotometricInterpretation") 
    # 7.1.3.1
    EL_colorSpace = etree.SubElement(EL_PhotometricInterpretation, mix_NS + "colorSpace").text = MIX_colorSpace 

    # ImageCaptureMetadata
    # 8
    EL_ImageCaptureMetadata = etree.SubElement(root, mix_NS + "ImageCaptureMetadata")
    # 8.1
    EL_SourceInformation = etree.SubElement(EL_ImageCaptureMetadata, mix_NS + "SourceInformation")
    for item in MIX_sourceID:
        # 8.1.2
        EL_SourceID = etree.SubElement(EL_SourceInformation, mix_NS + "SourceID")
        # 8.1.2.1
        EL_sourceIDType = etree.SubElement(EL_SourceID, mix_NS + "sourceIDType").text = item[0].decode('iso-8859-1') 
        # 8.1.2.2
        EL_sourceIDValue = etree.SubElement(EL_SourceID, mix_NS + "sourceIDValue").text = item[1].decode('iso-8859-1') 
        
        #EL_sourceIDValue = etree.SubElement(EL_SourceID, mix_NS + "sourceIDValue").text = item[1] 
    # 8.2
    EL_GeneralCaptureInformation = etree.SubElement(EL_ImageCaptureMetadata, mix_NS + "GeneralCaptureInformation")
    # 8.2.1
    EL_dateTimeCreated = etree.SubElement(EL_GeneralCaptureInformation, mix_NS + "dateTimeCreated").text = MIX_dateTimeCreated 
    # 8.2.2
    EL_imageProducer = etree.SubElement(EL_GeneralCaptureInformation, mix_NS + "imageProducer").text = MIX_imageProducer.decode('iso-8859-1') 
    #EL_imageProducer = etree.SubElement(EL_GeneralCaptureInformation, mix_NS + "imageProducer").text = MIX_imageProducer 
    # 8.3
    EL_ScannerCapture = etree.SubElement(EL_ImageCaptureMetadata, mix_NS + "ScannerCapture")
    # 8.3.1
    EL_scannerManufacturer = etree.SubElement(EL_ScannerCapture, mix_NS + "scannerManufacturer").text = MIX_scannerManufacturer.decode('iso-8859-1') 
    # 8.3.2
    EL_ScannerModel = etree.SubElement(EL_ScannerCapture, mix_NS + "ScannerModel") 
    # 8.3.2.1
    EL_scannerModelName = etree.SubElement(EL_ScannerModel, mix_NS + "scannerModelName").text = MIX_scannerModelName.decode('iso-8859-1') 
    # 8.3.5
    EL_ScanningSystemSoftware = etree.SubElement(EL_ScannerCapture, mix_NS + "ScanningSystemSoftware")
    # 8.3.5.1
    EL_scanningSoftwareName = etree.SubElement(EL_ScanningSystemSoftware, mix_NS + "scanningSoftwareName").text = MIX_scanningSoftwareName.decode('iso-8859-1')
    # 8.5
    EL_orientation = etree.SubElement(EL_ImageCaptureMetadata, mix_NS + "orientation").text = MIX_orientation

    # ImageAssessmentMetadata
    # 9
    EL_ImageAssessmentMetadata = etree.SubElement(root, mix_NS + "ImageAssessmentMetadata")
    # 9.1
    EL_SpatialMetrics = etree.SubElement(EL_ImageAssessmentMetadata, mix_NS + "SpatialMetrics")
    # 9.1.2
    EL_samplingFrequencyUnit = etree.SubElement(EL_SpatialMetrics, mix_NS + "samplingFrequencyUnit").text = MIX_samplingFrequencyUnit
    # 9.1.2.1
    EL_xSamplingFrequency = etree.SubElement(EL_SpatialMetrics, mix_NS + "xSamplingFrequency")
    EL_numerator = etree.SubElement(EL_xSamplingFrequency, mix_NS + "numerator").text = MIX_numerator_x
    # 9.1.2.2
    EL_ySamplingFrequency = etree.SubElement(EL_SpatialMetrics, mix_NS + "ySamplingFrequency")
    EL_numerator = etree.SubElement(EL_ySamplingFrequency, mix_NS + "numerator").text = MIX_numerator_y
    # 9.2
    EL_ImageColorEncoding = etree.SubElement(EL_ImageAssessmentMetadata, mix_NS + "ImageColorEncoding")
    # 9.2.1
    EL_BitsPerSample = etree.SubElement(EL_ImageColorEncoding, mix_NS + "BitsPerSample")
    # 9.2.1.1
    EL_bitsPerSampleValue = etree.SubElement(EL_BitsPerSample, mix_NS + "bitsPerSampleValue").text = MIX_bitsPerSampleValue
    # 9.2.1.2
    EL_bitsPerSampleUnit = etree.SubElement(EL_BitsPerSample, mix_NS + "bitsPerSampleUnit").text = MIX_bitsPerSampleUnit
    # 9.2.2
    EL_samplesPerPixel = etree.SubElement(EL_ImageColorEncoding, mix_NS + "samplesPerPixel").text = MIX_samplesPerPixel

    return root

def getPremisObjects(DOC=None,FILENAME=None,NS='http://xml.ra.se/PREMIS',PREFIX='premis',eARD=False):
    if FILENAME:
        try:
            DOC  =  etree.ElementTree ( file=FILENAME )
        except etree.XMLSyntaxError, detail:
            return [],10,str(detail)
        except IOError, detail:
            return [],20,str(detail)
    res=[]

    EL_root = DOC.getroot()
    premis_NS = "{%s}" % EL_root.nsmap['premis']
    #mets_NS = "{%s}" % EL_root.nsmap['mets']
    #premis_NS = "{%s}" % PREMIS_NAMESPACE
    #mets_NS = "{%s}" % METS_NAMESPACE

    ELs_object = DOC.findall("%sobject" % (premis_NS))
    #####################################################################
    # if no objects found try to find PREMIS objects in METS layout
    if len(ELs_object) == 0:
        try:
            mets_NS = "{%s}" % EL_root.nsmap['mets']
        except:
            pass
        ELs_object = DOC.findall("%samdSec/%sdigiprovMD/%smdWrap/%sxmlData/%spremis/%sobject" % (mets_NS,mets_NS,mets_NS,mets_NS,premis_NS,premis_NS))
    firstPremisObjectFlag = 1
    for EL_object in ELs_object:
        objectIdentifierValue = ''
        messageDigestAlgorithm = ''
        messageDigest = ''
        messageDigestOriginator = ''
        size = ''
        formatName = ''
        formatVersion = ''
        EL_objectIdentifierValue = EL_object.find("%sobjectIdentifier/%sobjectIdentifierValue" % (premis_NS,premis_NS))
        if EL_objectIdentifierValue is not None:
            objectIdentifierValue = ESSPGM.Check().str2unicode(EL_objectIdentifierValue.text)
            if eARD:
                if firstPremisObjectFlag == 1:
                    P_objectIdentifierValue = objectIdentifierValue 
                    firstPremisObjectFlag = 0
                else:
                    objectIdentifierValue = objectIdentifierValue.replace('%s/' % P_objectIdentifierValue,'')
        EL_objectCharacteristics = EL_object.find("%sobjectCharacteristics" % premis_NS)
        if EL_objectCharacteristics is not None:
            EL_messageDigestAlgorithm = EL_objectCharacteristics.find("%sfixity/%smessageDigestAlgorithm" % (premis_NS,premis_NS))
            if EL_messageDigestAlgorithm is not None:
                messageDigestAlgorithm = EL_messageDigestAlgorithm.text
            EL_messageDigest = EL_objectCharacteristics.find("%sfixity/%smessageDigest" % (premis_NS,premis_NS))
            if EL_messageDigest is not None:
                messageDigest = EL_messageDigest.text
            EL_messageDigestOriginator = EL_objectCharacteristics.find("%sfixity/%smessageDigestOriginator" % (premis_NS,premis_NS))
            if EL_messageDigestOriginator is not None:
                messageDigestOriginator = EL_messageDigestOriginator.text
            EL_size = EL_objectCharacteristics.find("%ssize" % premis_NS)
            if EL_size is not None:
                size = EL_size.text
            EL_formatName = EL_objectCharacteristics.find("%sformat/%sformatDesignation/%sformatName" % (premis_NS,premis_NS,premis_NS))
            if EL_formatName is not None:
                formatName = EL_formatName.text
            EL_formatVersion = EL_objectCharacteristics.find("%sformat/%sformatDesignation/%sformatVersion" % (premis_NS,premis_NS,premis_NS))
            if EL_formatVersion is not None:
                formatVersion = EL_formatVersion.text
        res.append([objectIdentifierValue,messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,formatName,formatVersion])
    return res,0,''

"Convert RESfile to PREMISfile"
###############################################
def RES2PREMIS(AIPpath, ID='xxx', PREMISfile=None, eARD=False):
    agentIdentifierValue = 'TIFFedit_%s' % ID
    agentName = 'TIFFedit vid %s' % ID
    tz=timezone.get_default_timezone()
    DEBUG = 0
    WarningNote = ''
    try:
        if eARD:
            RES_ObjectPath = os.path.join(AIPpath,'c/TIFFEdit.RES')
        else:
            RES_ObjectPath = os.path.join(AIPpath,'TIFFEdit.RES')
        RESobjects = csv.reader(open(RES_ObjectPath, "rb"))
        for RESobject in RESobjects:
            F_PREMIS_significantProperties = []
            if DEBUG: print 'Line %s' % RESobjects.line_num
            if DEBUG: print 'f1: ###%s###' % RESobject[0]
            F_objectIdentifierValue = string.replace(RESobject[0],'\\','/')
            P_objectIdentifierValue, F_ID = os.path.split(F_objectIdentifierValue)
            if DEBUG: print 'P_objectIdentifierValue: ###%s###' % P_objectIdentifierValue
            if DEBUG: print 'F_objectIdentifierValue: ###%s###' % F_objectIdentifierValue
            if eARD:
                F_objectIdentifierValue = '%s/c/%s' % (P_objectIdentifierValue,F_ID)
                F_ID = 'c/%s' % F_ID
            if not PREMISfile:
                PREMISfile=os.path.join(AIPpath,'%s_PREMIS.xml') % P_objectIdentifierValue

            if DEBUG: print 'f2: ###%s###' % RESobject[1]
            F_formatName = RESobject[1] 
            if DEBUG: print 'F_formatName: ###%s###' % F_formatName

            if DEBUG: print 'f3: ###%s###' % RESobject[2]
            F_size = RESobject[2]
            if DEBUG: print 'F_size: ###%s###' % F_size
         
            if DEBUG: print 'f4: ###%s###' % RESobject[3]
            F_eventOutcomeDetailNote = 'Profil:%s' % RESobject[3]
            if DEBUG: print 'F_eventOutcomeDetailNote: ###%s###' % F_eventOutcomeDetailNote
            
            if DEBUG: print 'f5: ###%s###' % RESobject[4]
            F_eventDateTime = datetime.datetime.strptime(RESobject[4], '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz).isoformat()
            if DEBUG: print 'F_eventDateTime: ###%s###' % F_eventDateTime
                
            if DEBUG: print 'f6: ###%s###' % RESobject[5]
            if DEBUG: print 'f7: ###%s###' % RESobject[6]

            if DEBUG: print 'f8: ###%s###' % RESobject[7]
            F_imageHeight = RESobject[7]
            if DEBUG: print 'F_imageHeight: ###%s###' % F_imageHeight

            if DEBUG: print 'f9: ###%s###' % RESobject[8]
            F_imageWidth = RESobject[8]
            if DEBUG: print 'F_imageWith: ###%s###' % F_imageWidth

            if DEBUG: print 'f10: ###%s###' % RESobject[9]
            F_bitsPerSampleUnit = 'integer'
            F_bitsPerSampleValue = RESobject[9]
            if DEBUG: print 'F_bitsPerSampleValue: ###%s###' % F_bitsPerSampleValue

            if DEBUG: print 'f11: ###%s###' % RESobject[10]
            compressionScheme_dict = dict({-1:'Uncompressed',
                                           1:'Uncompressed', 
                                           2:'CCITT 1D',
                                           3:'Group 3 Fax',
                                           4:'Group 4 Fax',
                                           5:'LZW', 
                                           6:'JPEG',
                                           7:'JPEG',
                                           8:'Deflate',
                                           32773:'PackBits'})
            try:
                F_compressionScheme = compressionScheme_dict[int(RESobject[10])]
            except KeyError, detail:
                return '',52,'Problem to set F_compressionScheme (RESobject[10]) value: %s' % str(detail)
            if DEBUG: print 'F_compressionScheme: ###%s###' % F_compressionScheme

            if DEBUG: print 'f12: ###%s###' % RESobject[11]
            colorSpace_dict = dict({-1 : 'BlackIsZero',
                                    0 : 'WhiteIsZero',
                                    1 : 'BlackIsZero',
                                    2 : 'RGB',
                                    3 : 'RGB Palette',
                                    4 : 'Transparency mask',
                                    5 : 'CMYK',
                                    6 : 'YcbCr',
                                    8 : 'CIELab'})
            try:
                F_colorSpace = colorSpace_dict[int(RESobject[11])]
            except KeyError, detail:
                return '',53,'Problem to set F_colorSpace (RESobject[11]) value: %s' % str(detail)
            if DEBUG: print 'F_colorSpace: ###%s###' % F_colorSpace

            if DEBUG: print 'f13: ###%s###' % RESobject[12]

            if DEBUG: print 'f14: ###%s###' % RESobject[13]
            if DEBUG: print 'f15: ###%s###' % RESobject[14]
            F_sourceID = []
            F_sourceIDType = 'DocumentName'
            F_sourceIDValue = RESobject[13]
            F_sourceID.append([F_sourceIDType,F_sourceIDValue])
            F_sourceIDType = 'ImageDescription'
            F_sourceIDValue = RESobject[14]
            F_sourceID.append([F_sourceIDType,F_sourceIDValue])
            if DEBUG: print 'F_sourceID: ###%s###' % F_sourceID
           
            if DEBUG: print 'f16: ###%s###' % RESobject[15]
            F_scannerManufacturer = RESobject[15]
            if DEBUG: print 'F_scannerManufacturer: ###%s###' % F_scannerManufacturer

            if DEBUG: print 'f17: ###%s###' % RESobject[16]
            F_scannerModelName = RESobject[16]
            if DEBUG: print 'F_scannerModelName: ###%s###' % F_scannerModelName

            if DEBUG: print 'f18: ###%s###' % RESobject[17]
            orientation_dict = dict({-1 : 'normal*',
                                     1 : 'normal*',
                                     2 : 'normal, image flipped',
                                     3 : 'normal, rotated 180�',
                                     4 : 'normal, image flipped, rotated 180�',
                                     5 : 'normal, image flipped, rotated cw 90�',
                                     6 : 'normal, rotated ccw 90�',
                                     7 : 'normal, image flipped, rotated ccw 90�',
                                     8 : 'normal, rotated cw 90�',
                                     9 : 'unknown'})
            try:
                F_orientation = orientation_dict[int(RESobject[17])]
            except KeyError, detail:
                return '',54,'Problem to set F_orientation (RESobject[17]) value: %s' % str(detail)
            if DEBUG: print 'F_orientation: ###%s###' % F_orientation

            if DEBUG: print 'f19: ###%s###' % RESobject[18]
            if RESobject[18] == '-1':
                F_samplesPerPixel = '1'
            else:
                F_samplesPerPixel = RESobject[18]
            if DEBUG: print 'F_samplesPerPixel: ###%s###' % F_samplesPerPixel

            if DEBUG: print 'f20: ###%s###' % RESobject[19]
            F_xSamplingFrequency = RESobject[19]
            if DEBUG: print 'F_xSamplingFrequency: ###%s###' % F_xSamplingFrequency

            if DEBUG: print 'f21: ###%s###' % RESobject[20]
            F_ySamplingFrequency = RESobject[20]
            if DEBUG: print 'F_ySamplingFrequency: ###%s###' % F_ySamplingFrequency

            if DEBUG: print 'f22: ###%s###' % RESobject[21]

            if DEBUG: print 'f23: ###%s###' % RESobject[22]
            F_PREMIS_significantPropertiesType = u'PageName'
            F_PREMIS_significantPropertiesValue = ESSPGM.Check().str2unicode(RESobject[22])
            F_PREMIS_significantProperties.append([F_PREMIS_significantPropertiesType,F_PREMIS_significantPropertiesValue])
            if DEBUG: print 'F_PREMIS_significantProperties: ###%s###' % F_PREMIS_significantProperties

            if DEBUG: print 'f24: ###%s###' % RESobject[23]
            samplingFrequencyUnit_dict = dict({-1 : 'in.',
                                               1 : 'no absolute unit of measurement',
                                               2 : 'in.',
                                               3 : 'cm'})
            try:
                F_samplingFrequencyUnit = samplingFrequencyUnit_dict[int(RESobject[23])]
            except KeyError, detail:
                return '',51,'Problem to set F_samplingFrequencyUnit (RESobject[23]) value: %s' % str(detail)
            if DEBUG: print 'F_samplingFrequencyUnit: ###%s###' % F_samplingFrequencyUnit

            if DEBUG: print 'f25: ###%s###' % RESobject[24]
            F_scanningSoftwareName = RESobject[24]
            if DEBUG: print 'F_scanningSoftwareName: ###%s###' % F_scanningSoftwareName

            if DEBUG: print 'f26: ###%s###' % RESobject[25]
            try:
                F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%Y:%m:%d %H:%M:%S').replace(tzinfo=tz).isoformat()
            except ValueError, why:
                try:
                    F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%Y: %m:%d %H:%M:%S').replace(tzinfo=tz).isoformat()
                except ValueError, why:
                    try:
                        F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%Y/%m/%d %H:%M:%S').replace(tzinfo=tz).isoformat()
                    except ValueError, why:
                        try:
                            F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%Y-%m-%d %H:%M:%S').replace(tzinfo=tz).isoformat()
                        except ValueError, why:
                            try:
                                F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%a %b %d %H:%M:%S %Y').replace(tzinfo=tz).isoformat()
                            except ValueError, why:
                                try:
                                    F_dateTimeCreated = datetime.datetime.strptime(RESobject[25], '%d.%m.%Y %H:%M:%S').replace(tzinfo=tz).isoformat()
                                except ValueError, why:
                                    F_dateTimeCreated = F_eventDateTime
                                    F_eventOutcomeDetailNote += ';dateTimeCreated=eventDateTime' 
                                    WarningNote += ';dateTimeCreated=eventDateTime' 
            if DEBUG: print 'F_dateTimeCreated: ###%s###' % F_dateTimeCreated
            
            if DEBUG: print 'f27: ###%s###' % RESobject[26]
            F_imageProducer = RESobject[26]
            if DEBUG: print 'F_imageProducer: ###%s###' % F_imageProducer

            if DEBUG: print 'f28: ###%s###' % RESobject[27]

            if len(RESobject) == 29:
                if DEBUG: print 'f29: ###%s###' % RESobject[28]
                F_eventOutcomeDetailNote += ';Gsuid:%s' % RESobject[28]
                if DEBUG: print 'F_eventOutcomeDetailNote: ###%s###' % F_eventOutcomeDetailNote
            F_MD5SUM,errno,why = ESSPGM.Check().checksum(os.path.join(AIPpath,F_ID)) # MD5 Checksum
            if RESobjects.line_num == 1:
                xml_PREMIS = createPremis(FILE=['simple','','SE/RA',P_objectIdentifierValue,'full',[],'0','tar','','bevarandesystemet',[]],NSlist=['mix'])
            EL_MIX = createMIX(MIX_byteOrder='',MIX_compressionScheme=F_compressionScheme,MIX_imageWidth=F_imageWidth,MIX_imageHeight=F_imageHeight,MIX_colorSpace=F_colorSpace,MIX_sourceID=F_sourceID,MIX_dateTimeCreated=F_dateTimeCreated,MIX_imageProducer=F_imageProducer,MIX_scannerManufacturer=F_scannerManufacturer,MIX_scannerModelName=F_scannerModelName,MIX_scanningSoftwareName=F_scanningSoftwareName,MIX_orientation=F_orientation,MIX_samplingFrequencyUnit=F_samplingFrequencyUnit,MIX_numerator_x=F_xSamplingFrequency,MIX_numerator_y=F_ySamplingFrequency,MIX_bitsPerSampleValue=F_bitsPerSampleValue,MIX_bitsPerSampleUnit=F_bitsPerSampleUnit,MIX_samplesPerPixel=F_samplesPerPixel)
            xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/RA',F_objectIdentifierValue,'',F_PREMIS_significantProperties,'0',[['MD5',F_MD5SUM,'ESSArch']],F_size,F_formatName,'',[[EL_MIX]],[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/RA',P_objectIdentifierValue]])])
            xml_PREMIS = AddPremisEvent(xml_PREMIS,[('SE/RA',str(uuid.uuid1()),'TIFF editering',F_eventDateTime,'TIFF editering','Status: OK',F_eventOutcomeDetailNote,[['SE/RA',agentIdentifierValue]],[['SE/RA',F_objectIdentifierValue]])])
        # Add RES file to PREMIS.
        if eARD:
            F_objectIdentifierValue = 'c/TIFFEdit.RES'
        else:
            F_objectIdentifierValue = os.path.join(os.path.split(AIPpath)[1],'TIFFEdit.RES')
        F_MD5SUM,errno,why = ESSPGM.Check().checksum(RES_ObjectPath) # MD5 Checksum
        F_formatName = 'res'
        F_size = str(os.stat(RES_ObjectPath)[6])
        xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/RA',F_objectIdentifierValue,'','','0',[['MD5',F_MD5SUM,'ESSArch']],F_size,F_formatName,'','',[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/RA',P_objectIdentifierValue]])])
        xml_PREMIS = AddPremisAgent(xml_PREMIS,[('SE/RA',agentIdentifierValue,agentName,'software')])
        if DEBUG: print 'start to validate'
        errno,why = validate(xml_PREMIS) 
        if errno:
            print '',30,str(why)
            #return '',30,str(why)
        if DEBUG: print 'Validate errno: %s ,why: %s' % (errno,why) 
        errno,why = writeToFile(xml_PREMIS,PREMISfile)
        if errno:
            return '',40,str(why)
        if DEBUG: print 'Write errno: %s ,why: %s' % (errno,why)
    except csv.Error, detail:
        return '',10,'file %s, line %s: %s' % (RES_ObjectPath, RESobjects.line_num, detail)
    except IOError, detail:
        return '',20,str(detail)
    else:
        if WarningNote:
            return xml_PREMIS,1,str(WarningNote)
        else:
            return xml_PREMIS,0,''

"Get object list from RESfile"
###############################################
def getRESObjects(FILENAME):
    DEBUG = 0
    res=[]
    try:
        RESobjects = csv.reader(open(FILENAME, "rb"))
        for RESobject in RESobjects:
            if DEBUG: print 'Line %s' % RESobjects.line_num
            if DEBUG: print 'f1: ###%s###' % RESobject[0]
            F_objectIdentifierValue = string.replace(RESobject[0],'\\','/')
            P_objectIdentifierValue, F_ID = os.path.split(F_objectIdentifierValue)
            if DEBUG: print 'P_objectIdentifierValue: ###%s###' % P_objectIdentifierValue
            if DEBUG: print 'F_objectIdentifierValue: ###%s###' % F_objectIdentifierValue

            if DEBUG: print 'f3: ###%s###' % RESobject[2]
            F_size = RESobject[2]
            if DEBUG: print 'F_size: ###%s###' % F_size
            res.append([F_objectIdentifierValue,F_size])
    except csv.Error, detail:
        return '',10,'file %s, line %s: %s' % (FILENAME, RESobjects.line_num, detail)
    except IOError, detail:
        return '',20,str(detail)
    else:
        return res,0,''

"Create a new METSfile from PREMIS"
###############################################
def PREMIS2METS(SIPpath,ObjectIdentifierValue,AgentIdentifierValue,altRecordID_dict={'POLICYID':10,'PROJECTNAME':'xyz123'},METSfile=None):
    ProcVersion = '2.2'
    tz=timezone.get_default_timezone()
    error_list = []
    error_code = 0
    ok=1
    ###########################################################
    # get policy info
    logging.info('Start to create METS for: %s', ObjectIdentifierValue)
    ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1, PolicyID=altRecordID_dict['POLICYID'])[:1]
    if ok:
        if not ArchivePolicy_objs:
            logging.error('POLICYID: %s for object: %s is not valid' % (altRecordID_dict['POLICYID'], ObjectIdentifierValue))
            error_list.append('POLICYID: %s for object: %s is not valid' % (altRecordID_dict['POLICYID'], ObjectIdentifierValue))
            error_code = 1
            ok = 0
        else:
            ArchivePolicy_obj = ArchivePolicy_objs.get()
    if ok:
        ###########################################################
        # set variables
        AIPpath = ArchivePolicy_obj.AIPpath
        metatype = ArchivePolicy_obj.IngestMetadata
        ChecksumAlgorithm = ArchivePolicy_obj.ChecksumAlgorithm
#    if metatype in [1,2,3]:
    if ok:
        ###########################################################
        # get object_list from PREMIS file
        premis_obj = '%s/%s_PREMIS.xml' % ('m',ObjectIdentifierValue)
        premis_filepath = os.path.join(SIPpath, premis_obj)
        premis_filepath_iso = ESSPGM.Check().unicode2str(premis_filepath)
        object_list,errno,why = getPremisObjects(FILENAME=premis_filepath,eARD=True)
        # list [objectIdentifierValue,messageDigestAlgorithm,messageDigest,messageDigestOriginator,size,formatName,formatVersion]
        if errno == 0:
            logging.info('Succeeded to get object_list from premis for information package: %s', ObjectIdentifierValue)
        else:
            event_info = 'Problem to get object_list from premis for information package: %s, errno: %s, detail: %s' % (ObjectIdentifierValue,str(errno),str(why))
            logging.error(event_info)
            ok = 0
    if ok:
        ###########################################################
        # create SIP content METS file
        METS_agent_list = []
        METS_altRecordID_list = []
        ms_files = []

        METS_LABEL = 'Imaging AIP RA'
        METS_agent_list.append(['ARCHIVIST','ORGANIZATION',None,'Riksarkivet',['ORG:2021001074']])
        METS_agent_list.append(['ARCHIVIST','OTHER','SOFTWARE','Digitala kedjan',[]])
        METS_agent_list.append(['CREATOR','ORGANIZATION',None,'Riksarkivet',['ORG:2021001074']])
        METS_agent_list.append(['CREATOR','INDIVIDUAL',None,AgentIdentifierValue,[]])
        METS_agent_list.append(['CREATOR', 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=%s' % ProcVersion]])
        METS_agent_list.append(['PRESERVATION','ORGANIZATION',None,'Riksarkivet',['ORG:2021001074']])
        METS_agent_list.append(['PRESERVATION','OTHER','SOFTWARE','ESSArch',['VERSION=%s' % ProcVersion]])
        
        METS_altRecordID_list.append(['DELIVERYTYPE','RA Imaging'])
        METS_altRecordID_list.append(['DELIVERYSPECIFICATION','Digitala kedjan, RA 13-2010/464'])
        METS_altRecordID_list.append(['SUBMISSIONAGREEMENT','Digitala kedjan, RA 13-2010/464'])
        #METS_altRecordID_list.append(['DATASUBMISSIONSESSION','xyz'])
        METS_altRecordID_list.append(['INFORMATIONCLASS','1'])
        METS_altRecordID_list.append(['PROJECTNAME',altRecordID_dict['PROJECTNAME']])
        METS_altRecordID_list.append(['POLICYID',str(altRecordID_dict['POLICYID'])])
        
        file_statinfo = os.stat(premis_filepath_iso)
        file_size = file_statinfo.st_size
        file_checksum, errno, why = ESSPGM.Check().checksum(premis_filepath,ChecksumAlgorithm)
        if errno:
            event_info = 'Problem to get checksum for PREMIS object for AIP package: ' + str(ObjectIdentifierValue)
            logging.error(event_info)
            ok = 0
        file_utc_mtime = datetime.datetime.utcfromtimestamp(file_statinfo.st_mtime).replace(tzinfo=pytz.utc)
        file_lociso_mtime = file_utc_mtime.astimezone(tz).isoformat()
        ms_files.append(['amdSec', None, 'digiprovMD', 'digiprovMD001', None,
                         None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % premis_obj, 'simple',
                         file_checksum, 'MD5', file_size, 'text/xml', file_lociso_mtime,
                         'PREMIS', None, None])
        firstPremisObjectFlag = 1
        DataObjectNumItems = 0
        DataObjectSize = 0
        MetaObjectSize = 0
        MetaObjectIdentifier = 'None'
        for object in object_list:
            filepath = os.path.join(SIPpath, object[0])
            filepath_iso = ESSPGM.Check().unicode2str(filepath)
            a_filepath = object[0]
            if firstPremisObjectFlag:
                if object[0] == ObjectIdentifierValue:
                    logging.info('First premis object match information package: %s', ObjectIdentifierValue)
                    firstPremisObjectFlag = 0
                    continue
                else:
                    event_info = 'First premis object do not match information package: %s, premis_object: %s' % (ObjectIdentifierValue,object[0])
                    logging.error(event_info)
                    ok = 0
            elif os.access(filepath_iso,os.R_OK):
                file_statinfo = os.stat(filepath_iso)
                file_size = file_statinfo.st_size
                file_utc_mtime = datetime.datetime.utcfromtimestamp(file_statinfo.st_mtime).replace(tzinfo=pytz.utc)
                file_lociso_mtime = file_utc_mtime.astimezone(tz).isoformat()
                file_MIMETYPE = ESSPGM.Check().PREMISformat2MIMEtype(object[5])
                #print 'object: %s MIME: %s' % (str(object),file_MIMETYPE)
                ms_files.append(['fileSec', None, None, None, None,
                         None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % object[0], 'simple',
                         object[2], object[1], file_size, file_MIMETYPE, file_lociso_mtime,
                         object[5], 'digiprovMD001', None])
            else:
                event_info = 'Object path: %s do not exist or is not readable!' % filepath
                logging.error(event_info)
                ok = 0
        if ok:
            try:
                OBJID = str(uuid.UUID(ObjectIdentifierValue))
            except ValueError, why:
                logging.warning('ObjectIdentifierValue: %s is not a valid UUID, why: %s , setting OBJID prefix to RAID: in METS' % (ObjectIdentifierValue, str(why)))
                OBJID = 'RAID:%s' % ObjectIdentifierValue
            else:
                OBJID = 'UUID:%s' % ObjectIdentifierValue

            # create mets root
            _mets = m.mets(PROFILE=METS_PROFILE,
                           LABEL=METS_LABEL,
                           TYPE='SIP',
                           OBJID=OBJID,
                           ID='ID%s' % str(uuid.uuid1()),
                           )
            # create mets header
            dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            loc_dt_isoformat = dt.astimezone(tz).isoformat()
            _metsHdr = m.metsHdrType(CREATEDATE=loc_dt_isoformat)
            for agent in METS_agent_list:
                _metsHdr.add_agent(m.agentType(ROLE=agent[0], TYPE=agent[1], OTHERTYPE=agent[2], name=agent[3], note=agent[4]))
            for altRecordID in METS_altRecordID_list:
                _metsHdr.add_altRecordID(m.altRecordIDType(TYPE=altRecordID[0],valueOf_=altRecordID[1]))
            _metsHdr.set_metsDocumentID(m.metsDocumentIDType(valueOf_=os.path.split(METSfile)[1]))
            _mets.set_metsHdr(_metsHdr)

            # create amdSec / structMap / fileSec
            _amdSec = m.amdSecType(ID='amdSec001')
            div_Package = m.divType(LABEL="Package")
            div_ContentDesc = m.divType(LABEL="Content Description", ADMID="amdSec001")
            div_Datafiles = m.divType(LABEL="Datafiles", ADMID="amdSec001")
            div_Package.add_div(div_ContentDesc)
            div_Package.add_div(div_Datafiles)
            _structMap = m.structMapType(div=div_Package)

            _fileSec = m.fileSecType()
            _fileGrp = m.fileGrpType(ID="fgrp001", USE='FILES')
            _fileSec.add_fileGrp(_fileGrp)

            for file in ms_files:
                if file[0] == 'fileSec':
                    # add entry to fileSec
                    _file = m.fileType(
                                     ID=file[6],
                                     SIZE=file[12],
                                     CREATED=file[14],
                                     MIMETYPE = file[13],
                                     ADMID = file[16],
                                     DMDID = file[17],
                                     USE = file[15],
                                     CHECKSUMTYPE = file[11],
                                     CHECKSUM = file[10],
                                      )
                    _FLocat = m.FLocatType(
                                     LOCTYPE=file[7],
                                     type_=file[9],
                                     href=file[8],
                                      )

                    _file.set_FLocat(_FLocat)
                    _fileGrp.add_file(_file)

                    # add entry to structMap
                    div_Datafiles.add_fptr(m.fptrType(FILEID=file[6]))

                if file[0] == 'amdSec':
                    # add entry to amdSec
                    _mdRef = m.mdRefType(ID=file[6], LOCTYPE=file[7],
                                         MDTYPE=file[15], OTHERMDTYPE=file[16], MIMETYPE=file[13],
                                         type_=file[9], href=file[8],
                                         SIZE=file[12], CREATED=file[14],
                                         CHECKSUM=file[10], CHECKSUMTYPE=file[11],
                                        )

                    _mdSec = m.mdSecType(ID=file[3], mdRef=_mdRef)
                    if file[2] == 'techMD':
                        _amdSec.add_techMD(_mdSec)
                    elif file[2] == 'digiprovMD':
                        _amdSec.add_digiprovMD(_mdSec)

            _mets.add_amdSec(_amdSec)
            _mets.add_structMap(_structMap)
            _mets.set_fileSec(_fileSec)

        # define namespaces
        namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
        namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
        namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
        namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)

        # write mets to file
        METSfile_fileobj = open(METSfile,'w')
        METSfile_fileobj.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        _mets.export(METSfile_fileobj,0,namespace_="mets:",namespacedef_=namespacedef)
        METSfile_fileobj.close()
    
    return error_code,error_list
        

"Create PREMISfile from METSfile"
###############################################
def METS2PREMIS(self,path,ObjectIdentifierValue):
    xml_PREMIS = None
    error_list = []
    METSfile = ObjectIdentifierValue + '_Content_METS.xml'
    METSfilepath = os.path.join(path,METSfile)

    # Create metadata directory and copy SIP Conent METS to metadata directory
    root_metadatapath_x = os.path.join(ObjectIdentifierValue, 'metadata')
    root_metadatapath = os.path.join(path,root_metadatapath_x)
    SIP_metadatapath_x = os.path.join(root_metadatapath_x, 'SIP')
    SIP_metadatapath = os.path.join(root_metadatapath, 'SIP')

    SIP_METSfilepath_x = os.path.join(SIP_metadatapath_x,METSfile)
    SIP_METSfilepath = os.path.join(SIP_metadatapath,METSfile)
    if not os.path.isdir(root_metadatapath):
        os.mkdir(root_metadatapath)
        os.mkdir(SIP_metadatapath)
    elif not os.path.isdir(SIP_metadatapath):
        os.mkdir(SIP_metadatapath)
    shutil.copy2(METSfilepath, SIP_METSfilepath) 

    # Get metadata from METS file
    res_info, res_files, res_struct, error, why = getMETSFileList(FILENAME=METSfilepath)
    if not error:
        P_objectIdentifierValue = res_info[0][1]
        P_preservationLevelValue = 'full'
        P_compositionLevel = '0'
        P_formatName = 'tar'
        xml_PREMIS = createPremis(FILE=['simple','','SE/ESS',P_objectIdentifierValue,P_preservationLevelValue,[],P_compositionLevel,P_formatName,'','bevarandesystemet',[]])
        for res_file in res_files:
            if res_file[0] == 'fileSec' and \
               res_file[2] == 'fileGrp':
                F_objectIdentifierValue = res_file[8][5:]
                F_messageDigest = res_file[10]
                F_messageDigestAlgorithm = res_file[11]
                F_size = str(res_file[12])
                F_formatName = res_file[13]
                F_formatName = ESSPGM.Check().MIMEtype2PREMISformat(res_file[13])
                xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/ESS',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_messageDigest,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/ESS',P_objectIdentifierValue]])])
        # Add SIP Content METS file to PREMIS.
        F_objectIdentifierValue = SIP_METSfilepath_x 
        F_Checksum,errno,why = ESSPGM.Check().checksum(SIP_METSfilepath, F_messageDigestAlgorithm) # Checksum
        F_formatName = 'xml'
        F_size = str(os.stat(SIP_METSfilepath)[6])
        xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/ESS',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_Checksum,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/ESS',P_objectIdentifierValue]])])

        xml_PREMIS = AddPremisAgent(xml_PREMIS,[('SE/ESS','ESSArch','ESSArch E-Arkiv','software')])
        errno,why = validate(xml_PREMIS)
        if errno:
            return xml_PREMIS, 1, why
        PREMISfilepath = os.path.join(path,P_objectIdentifierValue + '/' + P_objectIdentifierValue + '_PREMIS.xml')
        errno,why = writeToFile(xml_PREMIS,PREMISfilepath)
        if errno:
            return xml_PREMIS, 2, why
    else:
        return xml_PREMIS, 3, why
    return xml_PREMIS, 0, None
#def METS2PREMIS(ObjectIdentifierValue,METS_ObjectPath,PREMIS_ObjectPath):
#    xml_PREMIS = None
#
#    # Get metadata from METS file
#    res_info, res_files, res_struct, error, why = getMETSFileList(FILENAME=METS_ObjectPath)
#    if not error:
#        if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
#            P_ObjectIdentifierValue = res_info[0][1][5:]
#        else:
#            P_ObjectIdentifierValue = res_info[0][1]  
#        P_preservationLevelValue = 'full'
#        P_compositionLevel = '0'
#        P_formatName = 'tar'
#        xml_PREMIS = createPremis(FILE=['simple','','SE/ESS',P_ObjectIdentifierValue,P_preservationLevelValue,[],P_compositionLevel,P_formatName,'','bevarandesystemet',[]])
#        for res_file in res_files:
#            if res_file[0] == 'fileSec' and \
#               res_file[2] == 'fileGrp':
#                F_objectIdentifierValue = '%s/%s' % (ObjectIdentifierValue,res_file[8][5:])
#                F_messageDigest = res_file[10]
#                F_messageDigestAlgorithm = res_file[11]
#                F_size = str(res_file[12])
#                F_formatName = res_file[13]
#                F_formatName = ESSPGM.Check().MIMEtype2PREMISformat(res_file[13])
#                xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/ESS',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_messageDigest,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_ObjectIdentifierValue,'']],[['structural','is part of','SE/ESS',P_ObjectIdentifierValue]])])
#        xml_PREMIS = AddPremisAgent(xml_PREMIS,[('SE/ESS','ESSArch','ESSArch E-Arkiv','software')])
#        errno,why = validate(xml_PREMIS)
#        if errno:
#            return xml_PREMIS, 1, why
#        errno,why = writeToFile(xml_PREMIS,PREMIS_ObjectPath)
#        if errno:
#            return xml_PREMIS, 2, why
#    else:
#        return xml_PREMIS, 3, why
#    return xml_PREMIS, 0, None

def CreateMetsHdr(agent_list=[],altRecordID_list=[],DocumentID='',TimeZone=timezone.get_default_timezone_name(),CREATEDATE=None, RECORDSTATUS=None):
    # create mets header
    loc_timezone=pytz.timezone(TimeZone)
    if CREATEDATE is None:
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
    else:
        loc_dt_isoformat = CREATEDATE
    _metsHdr = m.metsHdrType(CREATEDATE=loc_dt_isoformat,RECORDSTATUS=RECORDSTATUS)
    for agent in agent_list:
        _metsHdr.add_agent(m.agentType(ROLE=agent[0], OTHERROLE=agent[1] , TYPE=agent[2], OTHERTYPE=agent[3], name=agent[4], note=agent[5]))
    for altRecordID in altRecordID_list:
        _metsHdr.add_altRecordID(m.altRecordIDType(TYPE=altRecordID[0],valueOf_=altRecordID[1]))
    _metsHdr.set_metsDocumentID(m.metsDocumentIDType(valueOf_=DocumentID))
    return _metsHdr

def CreateMetsFileInfo(file_list=[]):
    # create amdSec / structMap / fileSec
    _dmdSec = None
    _amdSec = None
    div_Package = m.divType(LABEL="Package")
    div_ContentDesc = m.divType(LABEL="Content Description")
    div_Datafiles = m.divType(LABEL="Datafiles")
    div_Package.add_div(div_ContentDesc)
    div_Package.add_div(div_Datafiles)
    _structMap = m.structMapType(div=div_Package)

    _fileSec = m.fileSecType()
    _fileGrp = m.fileGrpType(ID="fgrp001", USE='FILES')
    _fileSec.add_fileGrp(_fileGrp)

    for item in file_list:
        if item[0] == 'fileSec':
            # add entry to fileSec
            _file = m.fileType(
                             ID=item[6],
                             SIZE=item[12],
                             CREATED=item[14],
                             MIMETYPE = item[13],
                             ADMID = item[16],
                             DMDID = item[17],
                             USE = item[15],
                             CHECKSUMTYPE = item[11],
                             CHECKSUM = item[10],
                              )
            _FLocat = m.FLocatType(
                             LOCTYPE=item[7],
                             type_=item[9],
                             href=item[8],
                              )

            _file.set_FLocat(_FLocat)
            _fileGrp.add_file(_file)

            # add entry to structMap
            div_Datafiles.add_fptr(m.fptrType(FILEID=item[6]))

        if item[0] == 'amdSec':
            # add admSec001 if it not exists
            if _amdSec is None:
                _amdSec = m.amdSecType(ID='amdSec001')
            # add entry to amdSec
            _mdRef = m.mdRefType(ID=item[6], LOCTYPE=item[7],
                                 MDTYPE=item[15], OTHERMDTYPE=item[16], MIMETYPE=item[13],
                                 type_=item[9], href=item[8],
                                 SIZE=item[12], CREATED=item[14],
                                 CHECKSUM=item[10], CHECKSUMTYPE=item[11],
                                )

            _mdSec = m.mdSecType(ID=item[3], mdRef=_mdRef)
            if item[2] == 'techMD':
                _amdSec.add_techMD(_mdSec)
            elif item[2] == 'digiprovMD':
                _amdSec.add_digiprovMD(_mdSec)

            # add entry to structMap
            div_ContentDesc.add_fptr(m.fptrType(FILEID=item[6]))
    
    if _amdSec is not None:
        # if _amdSec exists update ADMID with 'admSec001' for div_ContentDesc and div_Datafiles
        div_ContentDesc.ADMID = _amdSec.ID
        div_Datafiles.ADMID = _amdSec.ID
            
    return _dmdSec, _amdSec, _fileSec, _structMap

"Create IP mets"
###############################################
def Create_IP_mets(ObjectIdentifierValue,METS_ObjectPath,agent_list=[],altRecordID_list=[],file_list=[],namespacedef=None,METS_LABEL=None,METS_PROFILE=None,METS_TYPE='SIP',METS_RECORDSTATUS=None,METS_DocumentID=None,TimeZone=timezone.get_default_timezone_name()):
    #######################################################################################################################
    # Create_IP_mets
    #
    # parameters:
    # ObjectIdentifierValue = 'unikt ID'                          example: '3u4d6f88a-b097-11e1-9bb6-002215836551'
    # METS_ObjectPath = 'path to new metsfile'                    example: '/path/sip.xml'
    # agent_list = ['ROLE', 'OTHERROLE', 'TYPE','OTHERTYPE','name',['note']]    example: ['ARCHIVIST',None,'ORGANIZATION',None,'ES Solutions AB',['ORG:11122334455']]
    # altRecordID_list = ['TYPE','value']                         example: ['DELIVERYTYPE','Database']
    # file_list = [Sec_NAME, Sec_ID, Grp_NAME, Grp_ID, Grp_USE,
    #              md_type, a_ID, a_LOCTYPE, a_href, a_type,
    #              a_CHECKSUM, a_CHECKSUMTYPE, a_SIZE, a_MIMETYPE, a_CREATED,
    #              a_MDTYPE/a_USE, a_OTHERMDTYPE/a_ADMID, a_DMDID]
    #
    #             metafile example:
    #             ['amdSec', None, 'digiprovMD', 'digiprovMD001', None,
    #             None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % f_name, 'simple',
    #             f_checksum, 'MD5', f_size, 'text/xml', f_created,
    #             'PREMIS', None, None] 
    #
    #             datafile exmaple:
    #             ['fileSec', None, None, None, None,
    #             None, 'ID%s' % str(uuid.uuid1()), 'URL', 'file:%s' % f_name, 'simple',
    #             f_checksum, 'MD5', f_size, f_mimetype, f_created,
    #             'Datafile', 'digiprovMD001', None]
    # namespacedef = 'xmlns:mets="http://www.loc.gov/METS/" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.loc.gov/METS/ http://xml.ra.se/METS/RA_METS_eARD.xsd"'
    #                
    #                example:
    #                METS_NAMESPACE = "http://www.loc.gov/METS/"
    #                METS_SCHEMALOCATION = "http://xml.ra.se/METS/RA_METS_eARD.xsd"
    #                XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
    #                XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    #                namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
    #                namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
    #                namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
    #                namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
    # METS_LABEL = 'description for IP'
    # METS_PROFILE = "http://xml.ra.se/METS/RA_METS_eARD.xml"
    # METS_TYPE = 'SIP'     example 'SIP','AIP','AIU','AIC','DIP'
    # METS_RECORDSTATUS = 'NEW'     default: None
    # METS_DocumentID = 'filename for metsdocument'    example: 'sip.xml'   
    # TimeZone = timezone.get_default_timezone_name()
    #
    status_code = 0
    status_list = []
    error_list = [] 
    
    if status_code == 0:
        #status_list.append('Start to create METS for IP: %s' % ObjectIdentifierValue)
        ObjectIdentifierValue = ObjectIdentifierValue
        try:
            OBJID = str(uuid.UUID(ObjectIdentifierValue))
        except ValueError, why:
            status_list.append('ObjectIdentifierValue: %s is not a valid UUID, why: %s , setting OBJID prefix to RAID: in METS' % (ObjectIdentifierValue, str(why)))
            OBJID = 'RAID:%s' % ObjectIdentifierValue
        else:
            OBJID = 'UUID:%s' % ObjectIdentifierValue
   
        _mets = m.mets(PROFILE=METS_PROFILE, 
                       LABEL=METS_LABEL,  
                       TYPE=METS_TYPE, 
                       OBJID=OBJID, 
                       ID='ID%s' % str(uuid.uuid1()), 
                       )
    
        # create mets header
        METS_agent_list = agent_list
        METS_altRecordID_list = altRecordID_list
        if METS_DocumentID is None:
            METS_DocumentID = os.path.split(METS_ObjectPath)[1]
        else:
            METS_DocumentID = METS_DocumentID
            
        _metsHdr = CreateMetsHdr(agent_list=METS_agent_list,
                                 altRecordID_list=METS_altRecordID_list,
                                 DocumentID=METS_DocumentID,
                                 TimeZone=TimeZone,
                                 RECORDSTATUS=METS_RECORDSTATUS
                                 )
        _mets.set_metsHdr(_metsHdr)
        
        # create amdSec / structMap / fileSec
        ms_files = file_list

        _dmdSec, _amdSec, _fileSec, _structMap = CreateMetsFileInfo(file_list=ms_files)
        if _dmdSec is not None:
            _mets.add_dmdSec(_dmdSec)
        if _amdSec is not None:
            _mets.add_amdSec(_amdSec)
        if _fileSec is not None:
            _mets.set_fileSec(_fileSec)
        if _structMap is not None:
            _mets.add_structMap(_structMap)

        # define namespaces
        if namespacedef is None:
            namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
            namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
            namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
            namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
  
        # write mets to file
        mets_fileobj = open(METS_ObjectPath,'w')
        mets_fileobj.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        _mets.export(mets_fileobj,0,namespace_="mets:",namespacedef_=namespacedef)
        mets_fileobj.close()    
    
    return status_code,[status_list,error_list]    

class metsRoot(object):
    format = 2    #example: 1='eArd', 2='E-ARK' 
    a_LABEL = None  #example 'description for IP'
    a_PROFILE = "http://webb.eark/package/METS/IP_CS.xml"
    a_TYPE = 'SIP'     #example 'SIP','AIP','AIU','AIC','DIP'
    a_OBJID = None  #example "UUID:550e8400-e29b-41d4-a716-446655440004" or 'RAID:%s' % ObjectIdentifierValue
    a_ID = None #default: 'ID%s' % str(uuid.uuid1())
    namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
    namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
    namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
    namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
    #                example:
    #                METS_NAMESPACE = "http://www.loc.gov/METS/"
    #                METS_SCHEMALOCATION = "http://xml.ra.se/METS/RA_METS_eARD.xsd"
    #                XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
    #                XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    #                namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
    #                namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
    #                namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
    #                namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
    def __init__(self, **kwargs):
        for key in kwargs:
            getattr(self, key) 
            setattr(self, key, kwargs[key])

class metsHdr(object):
    a_CREATEDATE = None     #default curent timestamp
    a_RECORDSTATUS = None   #example: 'NEW'
    metsDocumentID = None #example: 'filename for metsdocument - IP.xml'
    TimeZone = timezone.get_default_timezone_name()
    def __init__(self, **kwargs):
        for key in kwargs:
            getattr(self, key) 
            setattr(self, key, kwargs[key])

class metsStructFile(object):
    Sec_NAME = 'fileSec'    #example 'fileSec','admSec' or 'dmdSec'
    Sec_ID = None
    Grp_NAME = None     #example 'digiprovMD'
    Grp_ID = None       #example 'digiprovMD001'
    Struct_LABEL = 'Content'    #example - format 1: 'Datafiles', 'Content Description' - format 2: 'Content', 'Documentation', 'Metadata' 
    a_ID = None #default: 'ID%s' % str(uuid.uuid1())
    a_LOCTYPE = 'URL'
    a_href = None #example 'file:filx.txt'
    a_type = 'simple'
    a_CHECKSUM = None
    a_CHECKSUMTYPE = None #example 'MD5', 'SHA-256'
    a_SIZE = None
    a_MIMETYPE = None     #example 'text/xml'
    a_CREATED = None
    a_MDTYPE = None #example 'PREMIS'
    a_USE = 'Datafile' #example 'Datafile'
    a_OTHERMDTYPE = None
    a_ADMID = None #example 'digiprovMD001'
    a_DMDID = None
    def __init__(self, **kwargs):
        for key in kwargs:
            getattr(self, key) 
            setattr(self, key, kwargs[key])

class metsAgent(object):
    a_ROLE = None   #example 'ARCHIVIST'
    a_OTHERROLE = None
    a_TYPE = None   #example 'ORGANIZATION'
    a_OTHERTYPE = None  #example 'SOFTWARE'
    name = None
    note = []
    def __init__(self, **kwargs):
        for key in kwargs:
            getattr(self, key) 
            setattr(self, key, kwargs[key])

class metsAltRecordID(object):
    a_TYPE = None   #example 'DELIVERYTYPE'
    value = None  #example 'Database'
    def __init__(self, **kwargs):
        for key in kwargs:
            getattr(self, key) 
            setattr(self, key, kwargs[key])
    
def CreateMetsHdr2(metsHdr=metsHdr(), agent_list=[],altRecordID_list=[]):
    # create mets header
    loc_timezone=pytz.timezone(metsHdr.TimeZone)
    if metsHdr.a_CREATEDATE is None:
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
    else:
        loc_dt_isoformat = metsHdr.a_CREATEDATE
    _metsHdr = m.metsHdrType(CREATEDATE=loc_dt_isoformat,RECORDSTATUS=metsHdr.a_RECORDSTATUS)
    for agent in agent_list:
        #agent=metsAgent()
        _metsHdr.add_agent(m.agentType(ROLE=agent.a_ROLE, OTHERROLE=agent.a_OTHERROLE , TYPE=agent.a_TYPE, OTHERTYPE=agent.a_OTHERTYPE, name=agent.name, note=agent.note))
    for altRecordID in altRecordID_list:
        #altRecordID=metsAltRecordID()
        _metsHdr.add_altRecordID(m.altRecordIDType(TYPE=altRecordID.a_TYPE,valueOf_=altRecordID.value))
    _metsHdr.set_metsDocumentID(m.metsDocumentIDType(valueOf_= metsHdr.metsDocumentID))
    return _metsHdr

def CreateMetsFileInfo2(file_list=[], metsRoot=metsRoot()):
    # create amdSec / structMap / fileSec
    _dmdSec = []
    _amdSec = None
    if metsRoot.format == 1:
        div_root = m.divType(LABEL="Package")
        div_ContentDesc = m.divType(LABEL="Content Description")
        div_Datafiles = m.divType(LABEL="Datafiles")
        div_root.add_div(div_ContentDesc)
        div_root.add_div(div_Datafiles)
        _structMap = m.structMapType(div=div_root)
    elif metsRoot.format == 2:
        div_root = m.divType(LABEL="Package")
        div_Content = m.divType(LABEL="Content")
        div_Documentation = m.divType(LABEL="Documentation")
        div_Metadata = m.divType(LABEL="Metadata")
        div_root.add_div(div_Content)
        div_root.add_div(div_Documentation)
        div_root.add_div(div_Metadata)
        _structMap = m.structMapType(div=div_root,LABEL="Simple grouping")

    _fileSec = m.fileSecType()
    if metsRoot.format == 1:
        _fileGrp = m.fileGrpType(ID="fgrp001", USE='FILES')
    elif metsRoot.format == 2:
        _fileGrp = m.fileGrpType(ID='ID%s' % str(uuid.uuid1()))
    _fileSec.add_fileGrp(_fileGrp)

    if hasattr(file_list,'itervalues'):
        file_list_iter = file_list.itervalues()
    else:
        file_list_iter = file_list
        
    for item in file_list_iter:
        #item = metsStructFile()
        if item.a_ID is None:
            item.a_ID = 'ID%s' % str(uuid.uuid1())
        if item.Sec_NAME == 'fileSec':
            # add entry to fileSec
            _file = m.fileType(
                             ID=item.a_ID,
                             SIZE=item.a_SIZE,
                             CREATED=item.a_CREATED,
                             MIMETYPE = item.a_MIMETYPE,
                             CHECKSUMTYPE = item.a_CHECKSUMTYPE,
                             CHECKSUM = item.a_CHECKSUM,
                             ADMID = item.a_ADMID,
                             DMDID = item.a_DMDID,
                             USE = item.a_USE,
                              )
            _FLocat = m.FLocatType(
                             LOCTYPE=item.a_LOCTYPE,
                             type_=item.a_type,
                             href=item.a_href,
                              )

            _file.set_FLocat(_FLocat)
            _fileGrp.add_file(_file)

            # add entry to structMap
            #print 'locals: %s' % locals()
            if 'div_%s' % item.Struct_LABEL in locals():
                #print 'found content: %s' % item.Struct_LABEL
                locals()['div_%s' % item.Struct_LABEL].add_fptr(m.fptrType(FILEID=item.a_ID))
            else:
                #print 'found content: %s' % item.Struct_LABEL
                div_root.add_fptr(m.fptrType(FILEID=item.a_ID))

        elif item.Sec_NAME == 'amdSec':
            if metsRoot.format == 1:
                # add admSec001 if it not exists
                if _amdSec is None:
                    _amdSec = m.amdSecType(ID='amdSec001')
            elif metsRoot.format == 2:
                # add admSec_x if it not exists
                if _amdSec is None:
                    _amdSec = m.amdSecType(ID='ID%s' % str(uuid.uuid1()))
            # add entry to amdSec
            _mdRef = m.mdRefType(
                                 ID=item.a_ID, 
                                 SIZE=item.a_SIZE, 
                                 CREATED=item.a_CREATED,
                                 MIMETYPE=item.a_MIMETYPE,
                                 CHECKSUMTYPE=item.a_CHECKSUMTYPE,
                                 CHECKSUM=item.a_CHECKSUM, 
                                 LOCTYPE=item.a_LOCTYPE,
                                 type_=item.a_type, 
                                 href=item.a_href,
                                 MDTYPE=item.a_MDTYPE, 
                                 OTHERMDTYPE=item.a_OTHERMDTYPE, 
                                )
            if item.Grp_ID is None:
                _mdSec = m.mdSecType(ID='ID%s' % str(uuid.uuid1()), mdRef=_mdRef)
            else:
                _mdSec = m.mdSecType(ID=item.Grp_ID, mdRef=_mdRef)
            if item.Grp_NAME == 'techMD':
                _amdSec.add_techMD(_mdSec)
            elif item.Grp_NAME == 'digiprovMD':
                _amdSec.add_digiprovMD(_mdSec)

            # add entry to structMap
            if 'div_%s' % item.Struct_LABEL in locals():
                locals()['div_%s' % item.Struct_LABEL].add_fptr(m.fptrType(FILEID=item.a_ID))
            else:
                div_root.add_fptr(m.fptrType(FILEID=item.a_ID))            
            if metsRoot.format == 2:
                # add mdSec:ID as ADMID to root div in structMap
                if div_root.ADMID is None:
                    div_root.ADMID = _mdSec.ID
                else:
                    div_root.ADMID = '%s %s' % (div_root.ADMID, _mdSec.ID)    

        elif item.Sec_NAME == 'dmdSec':
            # add entry to mdSec
            _mdRef = m.mdRefType(
                                 ID=item.a_ID, 
                                 SIZE=item.a_SIZE, 
                                 CREATED=item.a_CREATED,
                                 MIMETYPE=item.a_MIMETYPE,
                                 CHECKSUMTYPE=item.a_CHECKSUMTYPE,
                                 CHECKSUM=item.a_CHECKSUM, 
                                 LOCTYPE=item.a_LOCTYPE,
                                 type_=item.a_type, 
                                 href=item.a_href,
                                 MDTYPE=item.a_MDTYPE, 
                                 OTHERMDTYPE=item.a_OTHERMDTYPE, 
                                )
            if item.Grp_ID is None:
                _mdSec = m.mdSecType(ID='ID%s' % str(uuid.uuid1()), mdRef=_mdRef)
            else:
                _mdSec = m.mdSecType(ID=item.Grp_ID, mdRef=_mdRef)
            _dmdSec.append(_mdSec)

            # add entry to structMap
            if 'div_%s' % item.Struct_LABEL in locals():
                locals()['div_%s' % item.Struct_LABEL].add_fptr(m.fptrType(FILEID=item.a_ID))
            else:
                div_root.add_fptr(m.fptrType(FILEID=item.a_ID))
            # add mdSec:ID as DMDID to root div in structMap
            if div_root.DMDID is None:
                div_root.DMDID = _mdSec.ID
            else:
                div_root.DMDID = '%s %s' % (div_root.DMDID, _mdSec.ID)            

    if _amdSec is not None:
        if metsRoot.format == 1:
            # if _amdSec exists update ADMID with 'admSec001' for div_ContentDesc and div_Datafiles
            div_ContentDesc.ADMID = _amdSec.ID
            div_Datafiles.ADMID = _amdSec.ID
        #elif metsRoot.format == 2:
        #    # if _amdSec exists update ADMID with 'IDx' for div_ContentDesc and div_Datafiles
        #    div_root.ADMID = _amdSec.ID    

    return _dmdSec, _amdSec, _fileSec, _structMap

"Create IP mets"
###############################################
def Create_IP_mets2(METS_ObjectPath,metsRoot=metsRoot(),metsHdr=metsHdr(),agent_list=[],altRecordID_list=[],file_list=[]):
    '''
    #######################################################################################################################
    # Create_IP_mets
    #
    # parameters:
    # METS_ObjectPath = 'path to new metsfile'                    example: '/path/sip.xml'
    # metsRoot object:
    #                        format = 2    #example: 1='eArd', 2='E-ARK' 
    #                        a_LABEL = None  #example 'description for IP'
    #                        a_PROFILE = "http://webb.eark/package/METS/IP_CS.xml"
    #                        a_TYPE = 'SIP'     #example 'SIP','AIP','AIU','AIC','DIP'
    #                        a_OBJID = None  #example "UUID:550e8400-e29b-41d4-a716-446655440004" or 'RAID:%s' % ObjectIdentifierValue
    #                        a_ID = 'ID%s' % str(uuid.uuid1())
    #                        namespacedef = default values from schemaprofile
    #                            example:
    #                                        METS_NAMESPACE = "http://www.loc.gov/METS/"
    #                                        METS_SCHEMALOCATION = "http://xml.ra.se/METS/RA_METS_eARD.xsd"
    #                                        XLINK_NAMESPACE = "http://www.w3.org/1999/xlink"
    #                                        XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
    #                                        namespacedef = 'xmlns:mets="%s"' % METS_NAMESPACE
    #                                        namespacedef += ' xmlns:xlink="%s"' % XLINK_NAMESPACE
    #                                        namespacedef += ' xmlns:xsi="%s"' % XSI_NAMESPACE
    #                                        namespacedef += ' xsi:schemaLocation="%s %s"' % (METS_NAMESPACE, METS_SCHEMALOCATION)
    # metsHdr object:
    #                        a_CREATEDATE = None #default curent timestamp
    #                        a_RECORDSTATUS = None   #example: 'NEW'
    #                        metsDocumentID = None #default value: 'filename for metsdocument - IP.xml'
    #                        TimeZone = timezone.get_default_timezone_name()
    # agent_list = [metsAgent,...] - list of one or many metsAgent object 
    #        metsAgent object:
    #                        a_ROLE = None   #example 'ARCHIVIST'
    #                        a_OTHERROLE = None
    #                        a_TYPE = None   #example 'ORGANIZATION'
    #                        a_OTHERTYPE = None  #example 'SOFTWARE'
    #                        name = None    #example 'ES Solutions AB'
    #                        note = []    #example ['ORG:11122334455']
    # altRecordID_list = [metsAltRecordID,...] - list of one or many metsAltRecordID object
    #        metsAltRecordID object:
    #                         a_TYPE = None   #example 'DELIVERYTYPE'
    #                        value = None  #example 'Database'
    # file_list = [metsStructFile,...] - list of one or many metsStructFile object
    #        metsStructFile object:
    #                        Sec_NAME = 'fileSec'    #example 'fileSec','admSec' or 'dmdSec'
    #                        Sec_ID = None
    #                        Grp_NAME = None     #example 'digiprovMD'
    #                        Grp_ID = None       #example 'digiprovMD001'
    #                        Struct_LABEL = 'Content'    #example - format 1: 'Datafiles', 'Content Description' - format 2: 'Content', 'Documentation', 'Metadata' 
    #                        a_ID = 'ID%s' % str(uuid.uuid1())
    #                        a_LOCTYPE = 'URL'
    #                        a_href = None #example 'file:filx.txt'
    #                        a_type = 'simple'
    #                        a_CHECKSUM = None
    #                        a_CHECKSUMTYPE = None #example 'MD5', 'SHA-256'
    #                        a_SIZE = None
    #                        a_MIMETYPE = None     #example 'text/xml'
    #                        a_CREATED = None
    #                        a_MDTYPE = None #example 'PREMIS'
    #                        a_USE = None #example 'Datafile'
    #                        a_OTHERMDTYPE = None
    #                        a_ADMID = None #example 'digiprovMD001'
    #                        a_DMDID = None
    '''

    status_code = 0
    status_list = []
    error_list = [] 
    
    if status_code == 0:
        # create mets root
        if metsRoot.a_ID is None:
            metsRoot.a_ID = 'ID%s' % str(uuid.uuid1())
        _mets = m.mets(PROFILE=metsRoot.a_PROFILE, 
                       LABEL=metsRoot.a_LABEL,  
                       TYPE=metsRoot.a_TYPE, 
                       OBJID=metsRoot.a_OBJID, 
                       ID=metsRoot.a_ID, 
                       )
        _mets.dmdSec
        # create mets header
        if metsHdr.metsDocumentID is None:
            metsHdr.metsDocumentID = os.path.split(METS_ObjectPath)[1]
            
        _metsHdr = CreateMetsHdr2(
                                 metsHdr=metsHdr,
                                 agent_list=agent_list,
                                 altRecordID_list=altRecordID_list,
                                 )
        _mets.set_metsHdr(_metsHdr)
        
        # create amdSec / structMap / fileSec
        _dmdSec, _amdSec, _fileSec, _structMap = CreateMetsFileInfo2(file_list=file_list, metsRoot=metsRoot)
        for _dmdSec_item in _dmdSec:
            _mets.add_dmdSec(_dmdSec_item)
        if _amdSec is not None:
            _mets.add_amdSec(_amdSec)
        if _fileSec is not None:
            _mets.set_fileSec(_fileSec)
        if _structMap is not None:
            _mets.add_structMap(_structMap)
  
        # write mets to file
        mets_fileobj = open(METS_ObjectPath,'w')
        mets_fileobj.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        _mets.export(mets_fileobj,0,namespace_="mets:",namespacedef_=metsRoot.namespacedef)
        mets_fileobj.close()    
    
    return status_code,[status_list,error_list]    

def main4():
    AgentIdentifierValue = 'ESSArch_Marieberg'
    ObjectIdentifierValue = 'A0007600' 
    altRecordID_dict = {}
    altRecordID_dict['POLICYID'] = 10
    altRecordID_dict['PROJECTNAME'] = 'xyz12345'
    SIPpath = '/home/arch/eARD_SIP' 
    SIProotpath = os.path.join(SIPpath,ObjectIdentifierValue)
    SIPcontentpath = os.path.join(SIProotpath,'c')
    SIPmetapath = os.path.join(SIProotpath,'m')
    Premis_filepath = os.path.join(SIPmetapath,'%s_PREMIS.xml' % ObjectIdentifierValue) 
    Mets_filepath = os.path.join(SIProotpath,'sip.xml') 
    

    ############################################
    # Convert SIP filestructur to eARD
    if not os.path.isdir(SIPcontentpath):
        os.mkdir(SIPcontentpath)
    if not os.path.isdir(SIPmetapath):
        os.mkdir(SIPmetapath)
    res,errno,why = getRESObjects(os.path.join(SIProotpath,'TIFFEdit.RES'))
    if not errno:
        for f in res:
            src_f = os.path.join(SIPpath,f[0])
            if os.path.exists(src_f):
                shutil.move(os.path.join(SIPpath,f[0]),SIPcontentpath)
            else:
                logging.warning('missing file: %s' % src_f)
        shutil.move(os.path.join(SIProotpath,'TIFFEdit.RES'),SIPcontentpath)
    else:
        logging.warning('missing RESfile: %s' % os.path.join(SIProotpath,'TIFFEdit.RES'))
    
    ############################################
    # Create PREMIS/mix from RESfile
    res,errno,why = RES2PREMIS(SIProotpath,AgentIdentifierValue,Premis_filepath, eARD=True)
    print 'RES2PREMIS errno: %s ,why: %s' % (errno,why) 
    if not errno:
        errno,why = validate(FILENAME=Premis_filepath)
        print 'Validate errno: %s ,why: %s' % (errno,why)

    #res,errno,why = getPremisObjects(FILENAME=Premis_filepath,eARD=True)
    #print res
    ############################################
    # Create eARD METS sip.xml from PREMISfile
    PREMIS2METS(SIProotpath,ObjectIdentifierValue,AgentIdentifierValue,altRecordID_dict,Mets_filepath)
    errno,why = validate(FILENAME=Mets_filepath)
    print 'Validate errno: %s ,why: %s' % (errno,why)

    ############################################
    # Clean SIP from "junk" files
    errno,why = ESSPGM.Check().CleanRES_SIP(SIProotpath)
    if errno:
        event_info = 'Problem to clean RES SIP from "junk files" for SIP package: %s, error.num: %s  error.desc: %s' % (ObjectIdentifierValue,str(errno),str(why))
        logging.error(event_info)
        ok = 0

def main1():
    #RES2PREMIS('/store/test/A0007600.RES','/tmp/RES_PREMIS.xml')
    res,errno,why = getRESObjects('/store/test/A0007600.RES')
    print 'getRESObjects: %s errno: %s ,why: %s' % (res,errno,why)

def main():
    #res,errno,why = getPremisObjects(FILENAME='/tmp/test123/A0007600_Content_METS.xml')
    #res,errno,why = getPremisObjects(FILENAME='/store/metablob/00011484_Content_METS.xml')
    #res,errno,why = getPremisObjects(FILENAME='/KRAM/Ingest/Q1717161/Q1717161_PREMIS.xml')
    res,errno,why = getPremisObjects(FILENAME='/IngestPath/Q0000150/Q0000150_PREMIS.xml')
    if not errno:
        print 'Antal objekt i fil: %s' % str(len(res))
        for i in res:
            F_MD5SUM,errno,why = ESSPGM.Check().checksum('/IngestPath/' + i[0].encode('utf-8'))
            if not errno:
                print 'Checksum: %s Object: %s' % (F_MD5SUM, str(i))    
            else:
                print 'Problem Checksum: %s , %s Object: %s' % (F_MD5SUM, why, str(i))    

        for filesystem_object in ESSPGM.Check().GetFiletree('/IngestPath/Q0000150'):
            missmatch_flag = 0
            for object in res:
                if os.path.join('Q0000150',filesystem_object) == object[0].encode('utf-8'):
                    missmatch_flag = 0
                    break
                else:
                    missmatch_flag = 1
            if missmatch_flag:
                print 'problem########### %s' % filesystem_object
                

    else:
        print 'getPremisObjects: %s errno: %s ,why: %s' % (res,errno,why)

def main5():
    #res,errno,why = RES2PREMIS('/IngestPath/00010249','Marieberg','/tmp/RES_PREMIS.xml')
    #res,errno,why = RES2PREMIS('/tmp/RA_20120410/Z0000137','Marieberg','/tmp/RES_PREMIS.xml')
    res,errno,why = RES2PREMIS('/tmp/RA_20120410/Z0000165','Marieberg','/tmp/RES_PREMIS_165.xml')
    print 'RES2PREMIS errno: %s ,why: %s' % (errno,why)
    #errno,why = validate(FILENAME='/store/disk1/A0007600_Content_METS.xml')
    #errno,why = validate(FILENAME='/ESSArch/testdata/A0007600_Content_METS_RA_ver2.xml')
    #errno,why = validate(FILENAME='/ESSArch/testdata/A0007600_Content_METS_RA.xml')
    errno,why = validate(FILENAME='/tmp/RES_PREMIS.xml')
    print 'Validate errno: %s ,why: %s' % (errno,why)

def main3():
    res,errno,why = updateMETSattrib(FILENAME='/ESSArch/testdata/A0007600_Content_METS_RA.xml',NS='http://xml.ra.se/METS/',PREFIX='mix',schemaLocation=None)
    print 'updateMETSattrib: %s errno: %s ,why: %s' % (res,errno,why)

def main7():
    #errno,why = validate(FILENAME='/store/DIP/00010224_test_Content_METS.xml')
    #errno,why = validate(FILENAME='/kontroll/access/IP_d0e96edc-53f5-11e1-9438-002215836551_version_new_Package_METS.xml')
    errno,why = validate(FILENAME='/tmp/5cd4d7b4-575d-11e1-914e-441ea139852e_Package_METS.xml')
    print 'Validate errno: %s ,why: %s' % (errno,why)

def main6():
    #errno,why = validateMets(FILENAME='/tmp/METS-RES.xml')
    #errno,why = validate(FILENAME='/tmp/METS-RES.xml')
    #print 'Validate errno: %s ,why: %s' % (errno,why)
#    RES2PREMIS('/store/test/A0007600.RES','/tmp/RES_PREMIS.xml')

#    ############################
#    # Create PREMIS
#    xml_PREMIS = createPremis(FILE=['simple','','SE/RA','00067991','0','tar','','bevarandesystemet',[]],NSlist=['mix'])
#    # Add first datafile
#    EL_MIX = createMIX(MIX_byteOrder='little endian',MIX_compressionScheme='Grupp 4 Fax',MIX_imageWidth='3339',MIX_imageHeight='4652',MIX_colorSpace='WhiteIsZero',MIX_sourceID=[['SE/RA','SE/�LA/11059/K I/2'],['ImageDescription','23 Hede K I/2 1835-1847']],MIX_dateTimeCreated='2008-06-18 10:15:11',MIX_imageProducer='Landsarkivet i �stersund',MIX_scannerManufacturer='',MIX_scannerModelName='i830 Scanner',MIX_scanningSoftwareName='xVCS V3.5      ',MIX_orientation='normal*',MIX_samplingFrequencyUnit='in.',MIX_numerator_x='400',MIX_numerator_y='400',MIX_bitsPerSampleValue='1',MIX_bitsPerSampleUnit='integer',MIX_samplesPerPixel='1')
#    xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/RA','00067990/00000001.TIF',[['PageName','SE/RA/83002/2005/23/00067990/00000001.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch']],'16744','image/tiff','6.0',[[EL_MIX]],[['simple','','AIP','00067990','']],[['structural','is part of','simple','','SE/RA','00067990']])])
#    # Add second datafile
#    EL_MIX = createMIX('','Grupp 4 Fax','3339','4652','WhiteIsZero',[['SE/RA','SE/VA/13012/A II c/37'],['ImageDescription','18  Arvika �stra (sfs) A II c/37 1970-1991']],'2008-06-18T10:15:11','V�rmlandsarkiv','KODAK   |','i830 Scanner','xVCS V3.5      ','normal*','in.','400','400','1','integer','1')
#    xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/RA','00067990/00000002.TIF',[['PageName','SE/RA/83002/2005/23/00067990/00000002.TIF']],'0',[['MD5','1342314dfsrewqer12','ESSArch']],'16744','image/tiff','6.0',[[EL_MIX]],[['simple','','AIP','00067990','']],[['structural','is part of','simple','','SE/RA','00067990']])])
#    # Add event
#    xml_PREMIS = AddPremisEvent(xml_PREMIS,[('simple','','SE/RA','GUID123xasd','TIFF editering','2005-11-08T12:24:09','Status: OK','Profil: GREY;gsuidxx123',[['simple','','SE/RA','TIFFedit_MKC']],[['simple','','SE/RA','00067990/00000001.TIF']])])
#    # Add agent
#    xml_PREMIS = AddPremisAgent(xml_PREMIS,[('simple','','SE/RA','TIFFedit_MKC','TIFFedit vid MKC','software')])
#    errno,why = validate(xml_PREMIS) 
#    print 'Validate errno: %s ,why: %s' % (errno,why) 
##    print etree.tostring(xml,encoding='UTF-8', xml_declaration=True, pretty_print=True)
#
#    errno,why = writeToFile(xml_PREMIS,'/tmp/PREMIS.xml')
#    print 'Write errno: %s ,why: %s' % (errno,why)

#    xml2,errno,why = parseFromFile('/tmp/METS-RES.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#     
#    print 'Premis###########################'
#    print etree.tostring(xml,encoding='UTF-8', xml_declaration=True, pretty_print=True)
#    print 'METS###########################'
#    print etree.tostring(xml2,encoding='UTF-8', xml_declaration=True, pretty_print=True)

#    ###################################
#    # Create PREMIS from RESfile
#    xml_PREMIS,errno,why = RES2PREMIS('/IngestPath/A0007605','/tmp/RES_PREMIS.xml')
#    print 'RES2PREMIS errno: %s ,why: %s' % (errno,why)
#
#    test_xml_PREMIS,errno,why = RES2PREMIS('/IngestPath/X0000001','')
#    print 'RES2PREMIS errno: %s ,why: %s' % (errno,why)
#
#
#    objects,errno,why = getPremisObjects(xml_PREMIS)
#    print 'objects: %s' % objects
#
#    xml_PREMIS2,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_PREMIS.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#
#    xml_ADDML,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_ADDML.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#
#    objects,errno,why = getPremisObjects(FILENAME='/store/SIP/X0000001_METS.xml')
#    print 'objects: %s , errno: %s, why: %s' % (objects,errno,why)
#    
#    print 'getFileSizePremis METS/PREMIS',getFileSizePremis(FILENAME='/store/SIP/X0000001_METS.xml')
#    print 'getFileSizeFgrp001 METS/PREMIS',getFileSizeFgrp001(FILENAME='/store/SIP/X0000001_METS.xml')


#
#    ############################
#    # Create ADDML METS
#    xml = createMets('Q0000001','ADDML','ESSArch_Marieberg')
#    xml = AddDataFiles(xml,'ADDML',[('0001.tif',1234,'2008-10-14T12:45:00+01:00','image/tiff')])
#    xml = AddDataFiles(xml,'ADDML',[('2002-0000003513-003.mp3',2222,'2008-10-15T12:45:00+01:00','audio/mpeg')])
#    xml = AddContentFiles(xml,'ADDML',[('000001_ADDML.xml','333','2008-10-12T12:45:00+01:00')])
#    xml = AddContentFiles(xml,'PREMIS',[('000001_PREMIS.xml','444','2008-10-11T12:45:00+01:00')])
#    xml = AddInformationFiles(xml,'ADDML',[('Archival_description_20060620T120000890.xml','111','2008-11-14T12:45:00+01:00','text/xml')])
#    xml = AddRAInformationFiles(xml,'ADDML',[('2002-0000003514-005.pdf','222','2008-12-14T12:45:00+01:00','application/pdf')])
#    xml = SetAIPattrib(xml,'ADDML',11223,'2008-10-14T12:45:00+01:00','1234234213','MD5')
#    errno,why = validateMets(xml) 
#    print 'Validate errno: %s ,why: %s' % (errno,why) 
#    errno,why = writeToFile(xml,'/tmp/METS-ADDML.xml')
#    print 'Write errno: %s ,why: %s' % (errno,why) 
#    errno,why = validateMets(FILENAME='/tmp/METS-ADDML.xml')
#    print 'Validate2 errno: %s ,why: %s' % (errno,why)
#
#
    ############################
    # Create RES METS
    xml2 = createMets('00067990','Exempel born-digital AIP RA',[['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]],['CREATOR','ORGANIZATION','','Riksarkivet',[]],['CREATOR','INDIVIDUAL','','ESSArch_Marieberg',[]],['CREATOR','OTHER','SOFTWARE','ESSArch',['VERSION=2.0']]],['premis','mix','addml','xhtml'])
#    xml2 = AddDataFiles(xml2,'Datafiles',FILES=[(u'\xe5000001.tif'.encode('iso-8859-1'),'123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','MD5','12345','URL','simple')])
    xml2 = AddDataFiles(xml2,'Datafiles',FILES=[(u'/hej/a-/b c\xe5000001.tif','123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','MD5','12345','URL','simple')])
    xml2 = AddDataFiles(xml2,'RA Datafiles',FILES=[('A000123_000002.tif','223','2008-10-14T12:45:00+01:02','image/tiff','digiprovMD001','RA Datafile','MD5','22345','URL','simple')])
    xml2 = AddDataFiles(xml2,'RA Information',FILES=[('00067990.res','123','2008-10-14T12:45:00+01:00','text/csv','techMD001','RA Information','MD5','32345','URL','simple')])

    #xml2 = AddDataFiles(xml2,'RES',[('0001.tif',1234,'2008-10-14T12:45:00+01:00','image/tiff')])
    #xml2 = AddDataFiles(xml2,'RES',[('0002.tif',1234,'2008-10-14T12:45:00+01:00','image/tiff')])
    #xml2 = AddContentFiles(xml2,'RES',[('000001_RES.res','222','2008-10-14T12:45:00+01:00')])
    #xml2 = AddContentFiles(xml2,'PREMISwrap',[(xml,'','')])
    xml2 = AddContentFiles(xml2,'Content description',FILES=[('000001.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','42345','URL','simple')])
    xml2 = AddContentFiles(xml2,'Content description',FILES=[('000002.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','52345','URL','simple')])
#    xml2 = AddContentEtree(xml2,[(xml_PREMIS,'PREMIS','')])
#    xml_PREMIS2,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_PREMIS.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#    xml2 = AddContentEtree(xml2,[(xml_PREMIS2,'PREMIS','')])
#    xml_ADDML,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_ADDML.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#    xml2 = AddContentEtree(xml2,[(xml_ADDML,'OTHER','ADDML')])
#    xml2 = AddContentFiles(xml2,'Content description',FILES=[('000003.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','62345','URL','simple')])
#    #xml2 = AddContentEtree(xml2,[(xml,'OTHER','ADDML')])
    errno,why = writeToFile(xml2,'/tmp/METS-RES.xml')
    print 'Write errno: %s ,why: %s' % (errno,why)

    res,errno,why = updateFilesADMID(xml2)
#    print 'ADMID update res: %s, errno: %s, why: %s' % (res,errno,why)
    xml2 = SetAIPattrib(xml2,11223,'2008-10-14T12:45:00+01:00','1234234213','MD5')
    errno,why = writeToFile(xml2,'/tmp/METS-RES.xml')
    print 'Write errno: %s ,why: %s' % (errno,why)
    #errno,why = validateMets(FILENAME='/tmp/METS-RES.xml')
    errno,why = validate(FILENAME='/tmp/METS-RES.xml')
    print 'Validate errno: %s ,why: %s' % (errno,why)
#    xml3 = createPMets(ID='00067990',LABEL='Exempel born-digital AIP RA',AGENT='ESSArch_Marieberg',P_SIZE='123',P_CREATED='2008-10-14T12:45:00+01:00',P_CHECKSUM='123aaa',P_CHECKSUMTYPE='MD5',M_SIZE='333',M_CREATED='2098-10-14T12:45:00+01:00',M_CHECKSUM='333aaa',M_CHECKSUMTYPE='MD5')
#    errno,why = writeToFile(xml3,'/tmp/PMETS.xml')
#    print 'Write errno: %s ,why: %s' % (errno,why)
#    errno,why = validate(FILENAME='/tmp/PMETS.xml')
#    print 'Validate errno: %s ,why: %s' % (errno,why)
#
#    XML_NewSchema,errno,why = updateSchemaLocation(FILENAME='/tmp/METS-RES.xml')
#    errno,why = writeToFile(XML_NewSchema,'/tmp/XML_NewSchema.xml')
#    print 'Write errno: %s ,why: %s' % (errno,why)



def main8():
#
#    ############################
#    # Get information from METS
    KB_filename = '/ESSArch/testdata/SIP/exempel/KB/KB_metsexample1_digprod_issue_20100428.xml'
    LDB_filename = '/ESSArch/testdata/SIP/exempel/LDB/i0001_METS.xml'
    R7_filename = '/ESSArch/testdata/SIP/exempel/R7/SWEIP_R7.xml'
    REDA_filename = '/ESSArch/testdata/SIP/exempel/REDA/REDA_METS.xml'
    SLL_filename = '/ESSArch/testdata/SIP/exempel/SLL/Q0000001_METS.xml'
    UNI_filename = '/ESSArch/testdata/SIP/exempel/Universitet_SLU_LiU/Q0000001_METS.xml'
    p_filename = '/ESSArch/testdata/SIP/Q0003670_Package_METS.xml'
    c_filename = '/ESSArch/testdata/SIP/Q0003670_Content_METS.xml'
    #c_filename = '/IngestPath/ESS00108_Content_METS.xml'
    #print 'getFileSizeFgrp001 Package',getFileSizeFgrp001(FILENAME=p_filename)
    #print 'getFileSizeFgrp001 Content',getFileSizeFgrp001(FILENAME=c_filename)
    #print 'getContentInfo Package',getContentInfo(FILENAME=p_filename)
    #print 'getContentInfo Content',getContentInfo(FILENAME=c_filename)
    ##print 'getAIPObjects Package',getAIPObjects(FILENAME=p_filename)
    #print 'getAIPObjects Content',getAIPObjects(FILENAME=c_filename)
    #print 'getTotalSize Package',getTotalSize(FILENAME=p_filename)
    #print 'getTotalSize Content',getTotalSize(FILENAME=c_filename)
    #print 'getPMETSInfo Package',getPMETSInfo(FILENAME=p_filename)
    #print 'getPMETSInfo Content',getPMETSInfo(FILENAME=c_filename)
    print '###############################################################################################################################'
    print 'getMETSFileList Package filename: %s' % c_filename
    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=c_filename)
    print res_info
    print 'res_info[2]: ',res_info[2]
    METS_agent_list = []
    for agent in res_info[2]:
        if not agent[3] == 'SOFTWARE':
            METS_agent_list.append(agent)
    METS_agent_list.append(['CREATOR',None, 'INDIVIDUAL', None, 'test_globen', []])
    METS_agent_list.append(['CREATOR',None, 'OTHER', 'SOFTWARE', 'ESSArch', ['VERSION=2.1.0']])
    print 'METS_agent_list: ',METS_agent_list
    
#    METS_agent_list.append(
    print 'date:',res_info[1][0]
    print 'agent:',res_info[2][0][3]

    print 'xlink_type: %s' % 'simple'
    print 'xlink_href: %s' % ''
    print 'ObjectIdentifierType: %s' % 'SE/ESS'
    P_objectIdentifierValue = res_info[0][1]
    print 'ObjectIdentifierValue: %s' % P_objectIdentifierValue
    print 'preservationLevelValue: %s' % 'full'
    print 'compositionLevel: %s' % '0'
    print 'formatName: %s' % 'tar'
    xml_PREMIS = createPremis(FILE=['simple','','SE/ESS',P_objectIdentifierValue,'full','0','tar','','bevarandesystemet',[]])
    if res_info[0][3] == 'SIP':
        print '#################### OK Package is a SIP'
    for agent in res_info[2]:
        if agent[0] == 'PRESERVATION' and \
           agent[1] == 'OTHER' and \
           agent[2] == 'SOFTWARE' and \
           agent[3] == 'ESSArch':
            note = csv.reader(agent[4], delimiter='=')
            print agent[4]
            for i in note:
                if i[0] == 'POLICYID':
                    print '###################### note: %s' % i[1]
    for a in res_a:
        if a[0] == 'fileSec' and \
           a[2] == 'fileGrp':
            print a
            F_objectIdentifierValue = a[8][5:]
            print 'ObjectIdentifierValue: %s' % F_objectIdentifierValue
            F_messageDigest = a[10]
            print 'messageDigest: %s' % F_messageDigest
            F_messageDigestAlgorithm = a[11]
            print 'messageDigestAlgorithm: %s' % F_messageDigestAlgorithm
            F_size = str(a[12])
            print 'size: %s' % F_size
            F_formatName = a[13]
            print 'METS_formatName: %s' % F_formatName
            F_formatName = ESSPGM.Check().MIMEtype2PREMISformat(a[13])
            print 'PREMIS_formatName: %s' % F_formatName
            xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/ESS',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_messageDigest,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/ESS',P_objectIdentifierValue]])])
        #xml_PREMIS = AddPremisEvent(xml_PREMIS,[('SE/ESS',str(uuid.uuid1()),'TIFF editering',F_eventDateTime,'Status: OK',F_eventOutcomeDetailNote,[['SE/RA',agentIdentifierValue]],[['SE/RA',F_objectIdentifierValue]])])
    for b in res_b[1]:
        print b
    xml_PREMIS = AddPremisAgent(xml_PREMIS,[('SE/ESS','ESSArch','ESSArch E-Arkiv','software')])
    errno,why = validate(xml_PREMIS)
    if errno:
        print 'errno: %s, why: %s' % (str(errno),str(why))
    #print etree.tostring(xml_PREMIS,encoding='UTF-8', xml_declaration=True, pretty_print=True)

#    print '###############################################################################################################################'
#    print 'getMETSFileList Content filename: %s' % c_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=c_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList KB filename: %s' % KB_filename
##    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=KB_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList KB filename: %s' % LDB_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=LDB_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList R7 filename: %s' % R7_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=R7_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList REDA filename: %s' % REDA_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=REDA_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList SLL filename: %s' % SLL_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=SLL_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b
#
#    print '###############################################################################################################################'
#    print 'getMETSFileList UNI filename: %s' % UNI_filename
#    res_info, res_a, res_b, error, why = getMETSFileList(FILENAME=UNI_filename)
#    print res_info
#    for a in res_a:
#        print a
#    for b in res_b[1]:
#        print b







    #print 'getFileSizePremis METS/PREMIS Package',getFileSizePremis(FILENAME=p_filename)
    #print 'getFileSizePremis METS/PREMIS Content',getFileSizePremis(FILENAME=c_filename)

#    print etree.tostring(xml2,encoding='UTF-8', xml_declaration=True, pretty_print=True)
#    XML_NewSchema,errno,why = updateSchemaLocation(FILENAME='/store/SIP/A0007600_Content_METS.xml')
#    errno,why = writeToFile(XML_NewSchema,'/tmp/XML_NewSchema.xml')
#    print 'Write errno: %s ,why: %s' % (errno,why)

def main9():
#
    tz=timezone.get_default_timezone()

    objectIdentifierValue = 'testobject'
    xml_PREMIS = createPremis(FILE=['simple','','SE/ESS',objectIdentifierValue,'full','0','tar','','bevarandesystemet',[]])
    #xml_PREMIS = createPremis(FILE=None)
    #xml_PREMIS = AddPremisFileObject(DOC=xml_PREMIS,FILES=[('simple','','SE/ESS',F_objectIdentifierValue,'',[],'0',[[F_messageDigestAlgorithm,F_messageDigest,'ESSArch']],F_size,F_formatName,'',[],[['simple','','AIP',P_objectIdentifierValue,'']],[['structural','is part of','SE/ESS',P_objectIdentifierValue]])])
    dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
    loc_dt_isoformat = dt.astimezone(tz).isoformat()
    eventDateTime = loc_dt_isoformat
    eventOutcomeDetailNote = 'test av event'
    agentIdentifierValue = 'ESSArch'
    objectIdentifierValue = 'test object 1'
    xml_PREMIS = AddPremisEvent(xml_PREMIS,[('SE/ESS',str(uuid.uuid1()),'TIFF editering',eventDateTime,'TIFF editering','Status: OK',eventOutcomeDetailNote,[['SE/ESS',agentIdentifierValue]],[['SE/ESS',objectIdentifierValue]])])
    xml_PREMIS = AddPremisAgent(xml_PREMIS,[('SE/ESS','ESSArch','ESSArch E-Arkiv','software')])
    errno,why = validate(xml_PREMIS)
    if errno:
        print 'errno: %s, why: %s' % (str(errno),str(why))
    print etree.tostring(xml_PREMIS,encoding='UTF-8', xml_declaration=True, pretty_print=True)

def main11():
    tz=timezone.get_default_timezone()
    dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
    loc_dt_isoformat = dt.astimezone(tz).isoformat()
    xml_METS = updatePackage(DOC=None,FILENAME='/kontroll/ingest/Q0020002/sip.xml',TYPE='AIP',CREATED=loc_dt_isoformat,metsDocumentID='Q0020002_Content_METS.xml')
    print etree.tostring(xml_METS,encoding='UTF-8', xml_declaration=True, pretty_print=True)

def main10():

    ############################
    # Create RES METS
    #xml2 = createMets('xxx123','AIC test',[['ARCHIVIST','ORGANIZATION','','Riksarkivet',[]],['CREATOR','ORGANIZATION','','Riksarkivet',[]],['CREATOR','INDIVIDUAL','','ESSArch_Marieberg',[]],['CREATOR','OTHER','SOFTWARE','ESSArch',['VERSION=2.0']]],[])
    xml2 = createMets('xxx123','AIC test',[],[],TYPE='AIC')
    xml2 = AddDataFiles(xml2,'AIP',FILES=[('A000123_000002.tar','223','2008-10-14T12:45:00+01:02','application/x-tar','','AIP Package','MD5','22345','URL','simple')])
    errno,why = writeToFile(xml2,'/tmp/AIC_METS.xml')
#    xml2 = AddDataFiles(xml2,'Datafiles',FILES=[(u'\xe5000001.tif'.encode('iso-8859-1'),'123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','MD5','12345','URL','simple')])
    #xml2 = AddDataFiles(xml2,'AIC',FILES=[(u'/hej/a-/b c\xe5000001.tif','123','2008-10-14T12:45:00+01:00','image/tiff','digiprovMD001','Datafile','MD5','12345','URL','simple')])
    #xml2 = AddDataFiles(xml2,'RA Information',FILES=[('00067990.res','123','2008-10-14T12:45:00+01:00','text/csv','techMD001','RA Information','MD5','32345','URL','simple')])

    #xml2 = AddDataFiles(xml2,'RES',[('0001.tif',1234,'2008-10-14T12:45:00+01:00','image/tiff')])
    #xml2 = AddDataFiles(xml2,'RES',[('0002.tif',1234,'2008-10-14T12:45:00+01:00','image/tiff')])
    #xml2 = AddContentFiles(xml2,'RES',[('000001_RES.res','222','2008-10-14T12:45:00+01:00')])
    #xml2 = AddContentFiles(xml2,'PREMISwrap',[(xml,'','')])
    #xml2 = AddContentFiles(xml2,'Content description',FILES=[('000001.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','42345','URL','simple')])
    #xml2 = AddContentFiles(xml2,'Content description',FILES=[('000002.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','52345','URL','simple')])
#    xml2 = AddContentEtree(xml2,[(xml_PREMIS,'PREMIS','')])
#    xml_PREMIS2,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_PREMIS.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#    xml2 = AddContentEtree(xml2,[(xml_PREMIS2,'PREMIS','')])
#    xml_ADDML,errno,why = parseFromFile('/store/test_born/Q0003675/Q0003675_ADDML.xml')
#    print 'Parse errno: %s ,why: %s' % (errno,why)
#    xml2 = AddContentEtree(xml2,[(xml_ADDML,'OTHER','ADDML')])
#    xml2 = AddContentFiles(xml2,'Content description',FILES=[('000003.RES','222','2008-10-14T12:45:00+01:00','text/xml','OTHER','RES','MD5','62345','URL','simple')])
#    #xml2 = AddContentEtree(xml2,[(xml,'OTHER','ADDML')])
    print 'Write errno: %s ,why: %s' % (errno,why)

    res,errno,why = updateFilesADMID(xml2)




if (__name__ == "__main__"):
    main4()
    #main()
    #main6()
    #main8()
    #main9()
    #main5()
    #main7()
    #main10()
    #main11()

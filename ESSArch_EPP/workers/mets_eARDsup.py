#!/usr/bin/env python
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
#
# Generated Wed Sep 12 13:21:13 2012 by generateDS.py version 2.7c.
#

import sys

import mets_eARD as supermod

etree_ = None
Verbose_import_ = False
(   XMLParser_import_none, XMLParser_import_lxml,
    XMLParser_import_elementtree
    ) = range(3)
XMLParser_import_library = None
try:
    # lxml
    from lxml import etree as etree_
    XMLParser_import_library = XMLParser_import_lxml
    if Verbose_import_:
        print("running with lxml.etree")
except ImportError:
    try:
        # cElementTree from Python 2.5+
        import xml.etree.cElementTree as etree_
        XMLParser_import_library = XMLParser_import_elementtree
        if Verbose_import_:
            print("running with cElementTree on Python 2.5+")
    except ImportError:
        try:
            # ElementTree from Python 2.5+
            import xml.etree.ElementTree as etree_
            XMLParser_import_library = XMLParser_import_elementtree
            if Verbose_import_:
                print("running with ElementTree on Python 2.5+")
        except ImportError:
            try:
                # normal cElementTree install
                import cElementTree as etree_
                XMLParser_import_library = XMLParser_import_elementtree
                if Verbose_import_:
                    print("running with cElementTree")
            except ImportError:
                try:
                    # normal ElementTree install
                    import elementtree.ElementTree as etree_
                    XMLParser_import_library = XMLParser_import_elementtree
                    if Verbose_import_:
                        print("running with ElementTree")
                except ImportError:
                    raise ImportError("Failed to import ElementTree from any known place")

def parsexml_(*args, **kwargs):
    if (XMLParser_import_library == XMLParser_import_lxml and
        'parser' not in kwargs):
        # Use the lxml ElementTree compatible parser so that, e.g.,
        #   we ignore comments.
        kwargs['parser'] = etree_.ETCompatXMLParser()
    doc = etree_.parse(*args, **kwargs)
    return doc

#
# Globals
#

ExternalEncoding = 'ascii'

#
# Data representation classes
#

class metsTypeSub(supermod.metsType):
    def __init__(self, PROFILE=None, LABEL=None, TYPE=None, ID=None, OBJID=None, metsHdr=None, dmdSec=None, amdSec=None, fileSec=None, structMap=None, structLink=None, behaviorSec=None, extensiontype_=None):
        super(metsTypeSub, self).__init__(PROFILE, LABEL, TYPE, ID, OBJID, metsHdr, dmdSec, amdSec, fileSec, structMap, structLink, behaviorSec, extensiontype_, )
supermod.metsType.subclass = metsTypeSub
# end class metsTypeSub


class amdSecTypeSub(supermod.amdSecType):
    def __init__(self, ID=None, techMD=None, rightsMD=None, sourceMD=None, digiprovMD=None):
        super(amdSecTypeSub, self).__init__(ID, techMD, rightsMD, sourceMD, digiprovMD, )
supermod.amdSecType.subclass = amdSecTypeSub
# end class amdSecTypeSub


class fileGrpTypeSub(supermod.fileGrpType):
    def __init__(self, VERSDATE=None, ADMID=None, ID=None, USE=None, fileGrp=None, file=None, extensiontype_=None):
        super(fileGrpTypeSub, self).__init__(VERSDATE, ADMID, ID, USE, fileGrp, file, extensiontype_, )
supermod.fileGrpType.subclass = fileGrpTypeSub
# end class fileGrpTypeSub


class structMapTypeSub(supermod.structMapType):
    def __init__(self, TYPE=None, ID=None, LABEL=None, div=None):
        super(structMapTypeSub, self).__init__(TYPE, ID, LABEL, div, )
supermod.structMapType.subclass = structMapTypeSub
# end class structMapTypeSub


class divTypeSub(supermod.divType):
    def __init__(self, ADMID=None, TYPE=None, LABEL=None, DMDID=None, ORDERLABEL=None, CONTENTIDS=None, label=None, ORDER=None, ID=None, mptr=None, fptr=None, div=None):
        super(divTypeSub, self).__init__(ADMID, TYPE, LABEL, DMDID, ORDERLABEL, CONTENTIDS, label, ORDER, ID, mptr, fptr, div, )
supermod.divType.subclass = divTypeSub
# end class divTypeSub


class parTypeSub(supermod.parType):
    def __init__(self, ID=None, area=None, seq=None):
        super(parTypeSub, self).__init__(ID, area, seq, )
supermod.parType.subclass = parTypeSub
# end class parTypeSub


class seqTypeSub(supermod.seqType):
    def __init__(self, ID=None, area=None, par=None):
        super(seqTypeSub, self).__init__(ID, area, par, )
supermod.seqType.subclass = seqTypeSub
# end class seqTypeSub


class areaTypeSub(supermod.areaType):
    def __init__(self, BEGIN=None, END=None, BETYPE=None, SHAPE=None, COORDS=None, EXTENT=None, CONTENTIDS=None, ADMID=None, ID=None, EXTTYPE=None, FILEID=None):
        super(areaTypeSub, self).__init__(BEGIN, END, BETYPE, SHAPE, COORDS, EXTENT, CONTENTIDS, ADMID, ID, EXTTYPE, FILEID, )
supermod.areaType.subclass = areaTypeSub
# end class areaTypeSub


class structLinkTypeSub(supermod.structLinkType):
    def __init__(self, ID=None, smLink=None, smLinkGrp=None, extensiontype_=None):
        super(structLinkTypeSub, self).__init__(ID, smLink, smLinkGrp, extensiontype_, )
supermod.structLinkType.subclass = structLinkTypeSub
# end class structLinkTypeSub


class behaviorSecTypeSub(supermod.behaviorSecType):
    def __init__(self, LABEL=None, ID=None, CREATED=None, behaviorSec=None, behavior=None):
        super(behaviorSecTypeSub, self).__init__(LABEL, ID, CREATED, behaviorSec, behavior, )
supermod.behaviorSecType.subclass = behaviorSecTypeSub
# end class behaviorSecTypeSub


class behaviorTypeSub(supermod.behaviorType):
    def __init__(self, ADMID=None, CREATED=None, STRUCTID=None, LABEL=None, GROUPID=None, BTYPE=None, ID=None, interfaceDef=None, mechanism=None):
        super(behaviorTypeSub, self).__init__(ADMID, CREATED, STRUCTID, LABEL, GROUPID, BTYPE, ID, interfaceDef, mechanism, )
supermod.behaviorType.subclass = behaviorTypeSub
# end class behaviorTypeSub


class objectTypeSub(supermod.objectType):
    def __init__(self, arcrole=None, title=None, OTHERLOCTYPE=None, show=None, actuate=None, LABEL=None, href=None, role=None, LOCTYPE=None, type_=None, ID=None):
        super(objectTypeSub, self).__init__(arcrole, title, OTHERLOCTYPE, show, actuate, LABEL, href, role, LOCTYPE, type_, ID, )
supermod.objectType.subclass = objectTypeSub
# end class objectTypeSub


class mdSecTypeSub(supermod.mdSecType):
    def __init__(self, STATUS=None, ADMID=None, CREATED=None, ID=None, GROUPID=None, mdRef=None, mdWrap=None):
        super(mdSecTypeSub, self).__init__(STATUS, ADMID, CREATED, ID, GROUPID, mdRef, mdWrap, )
supermod.mdSecType.subclass = mdSecTypeSub
# end class mdSecTypeSub


class fileTypeSub(supermod.fileType):
    def __init__(self, MIMETYPE=None, ADMID=None, END=None, CHECKSUMTYPE=None, SEQ=None, CREATED=None, CHECKSUM=None, USE=None, ID=None, DMDID=None, BEGIN=None, OWNERID=None, SIZE=None, GROUPID=None, BETYPE=None, FLocat=None, FContent=None, stream=None, transformFile=None, file=None):
        super(fileTypeSub, self).__init__(MIMETYPE, ADMID, END, CHECKSUMTYPE, SEQ, CREATED, CHECKSUM, USE, ID, DMDID, BEGIN, OWNERID, SIZE, GROUPID, BETYPE, FLocat, FContent, stream, transformFile, file, )
supermod.fileType.subclass = fileTypeSub
# end class fileTypeSub


class metsHdrTypeSub(supermod.metsHdrType):
    def __init__(self, CREATEDATE=None, RECORDSTATUS=None, ADMID=None, LASTMODDATE=None, ID=None, agent=None, altRecordID=None, metsDocumentID=None):
        super(metsHdrTypeSub, self).__init__(CREATEDATE, RECORDSTATUS, ADMID, LASTMODDATE, ID, agent, altRecordID, metsDocumentID, )
supermod.metsHdrType.subclass = metsHdrTypeSub
# end class metsHdrTypeSub


class agentTypeSub(supermod.agentType):
    def __init__(self, TYPE=None, OTHERTYPE=None, ROLE=None, ID=None, OTHERROLE=None, name=None, note=None):
        super(agentTypeSub, self).__init__(TYPE, OTHERTYPE, ROLE, ID, OTHERROLE, name, note, )
supermod.agentType.subclass = agentTypeSub
# end class agentTypeSub


class altRecordIDTypeSub(supermod.altRecordIDType):
    def __init__(self, TYPE=None, ID=None, valueOf_=None):
        super(altRecordIDTypeSub, self).__init__(TYPE, ID, valueOf_, )
supermod.altRecordIDType.subclass = altRecordIDTypeSub
# end class altRecordIDTypeSub


class metsDocumentIDTypeSub(supermod.metsDocumentIDType):
    def __init__(self, TYPE=None, ID=None, valueOf_=None):
        super(metsDocumentIDTypeSub, self).__init__(TYPE, ID, valueOf_, )
supermod.metsDocumentIDType.subclass = metsDocumentIDTypeSub
# end class metsDocumentIDTypeSub


class fileSecTypeSub(supermod.fileSecType):
    def __init__(self, ID=None, fileGrp=None):
        super(fileSecTypeSub, self).__init__(ID, fileGrp, )
supermod.fileSecType.subclass = fileSecTypeSub
# end class fileSecTypeSub


class fileGrpType1Sub(supermod.fileGrpType1):
    def __init__(self, VERSDATE=None, ADMID=None, ID=None, USE=None, fileGrp=None, file=None):
        super(fileGrpType1Sub, self).__init__(VERSDATE, ADMID, ID, USE, fileGrp, file, )
supermod.fileGrpType1.subclass = fileGrpType1Sub
# end class fileGrpType1Sub


class structLinkType1Sub(supermod.structLinkType1):
    def __init__(self, ID=None, smLink=None, smLinkGrp=None):
        super(structLinkType1Sub, self).__init__(ID, smLink, smLinkGrp, )
supermod.structLinkType1.subclass = structLinkType1Sub
# end class structLinkType1Sub


class mptrTypeSub(supermod.mptrType):
    def __init__(self, arcrole=None, show=None, OTHERLOCTYPE=None, title=None, actuate=None, href=None, role=None, LOCTYPE=None, CONTENTIDS=None, type_=None, ID=None):
        super(mptrTypeSub, self).__init__(arcrole, show, OTHERLOCTYPE, title, actuate, href, role, LOCTYPE, CONTENTIDS, type_, ID, )
supermod.mptrType.subclass = mptrTypeSub
# end class mptrTypeSub


class fptrTypeSub(supermod.fptrType):
    def __init__(self, CONTENTIDS=None, ID=None, FILEID=None, par=None, seq=None, area=None):
        super(fptrTypeSub, self).__init__(CONTENTIDS, ID, FILEID, par, seq, area, )
supermod.fptrType.subclass = fptrTypeSub
# end class fptrTypeSub


class smLinkTypeSub(supermod.smLinkType):
    def __init__(self, fromxx=None, show=None, title=None, actuate=None, to=None, arcrole=None, ID=None):
        super(smLinkTypeSub, self).__init__(fromxx, show, title, actuate, to, arcrole, ID, )
supermod.smLinkType.subclass = smLinkTypeSub
# end class smLinkTypeSub


class smLinkGrpTypeSub(supermod.smLinkGrpType):
    def __init__(self, role=None, title=None, ARCLINKORDER='unordered', ID=None, type_=None, smLocatorLink=None, smArcLink=None):
        super(smLinkGrpTypeSub, self).__init__(role, title, ARCLINKORDER, ID, type_, smLocatorLink, smArcLink, )
supermod.smLinkGrpType.subclass = smLinkGrpTypeSub
# end class smLinkGrpTypeSub


class smLocatorLinkTypeSub(supermod.smLocatorLinkType):
    def __init__(self, title=None, label=None, href=None, role=None, type_=None, ID=None):
        super(smLocatorLinkTypeSub, self).__init__(title, label, href, role, type_, ID, )
supermod.smLocatorLinkType.subclass = smLocatorLinkTypeSub
# end class smLocatorLinkTypeSub


class smArcLinkTypeSub(supermod.smArcLinkType):
    def __init__(self, ADMID=None, fromxx=None, title=None, show=None, actuate=None, ARCTYPE=None, to=None, arcrole=None, type_=None, ID=None):
        super(smArcLinkTypeSub, self).__init__(ADMID, fromxx, title, show, actuate, ARCTYPE, to, arcrole, type_, ID, )
supermod.smArcLinkType.subclass = smArcLinkTypeSub
# end class smArcLinkTypeSub


class mdRefTypeSub(supermod.mdRefType):
    def __init__(self, MIMETYPE=None, arcrole=None, XPTR=None, CHECKSUMTYPE=None, show=None, OTHERLOCTYPE=None, CHECKSUM=None, OTHERMDTYPE=None, title=None, actuate=None, MDTYPE=None, LABEL=None, href=None, role=None, LOCTYPE=None, MDTYPEVERSION=None, CREATED=None, type_=None, ID=None, SIZE=None):
        super(mdRefTypeSub, self).__init__(MIMETYPE, arcrole, XPTR, CHECKSUMTYPE, show, OTHERLOCTYPE, CHECKSUM, OTHERMDTYPE, title, actuate, MDTYPE, LABEL, href, role, LOCTYPE, MDTYPEVERSION, CREATED, type_, ID, SIZE, )
supermod.mdRefType.subclass = mdRefTypeSub
# end class mdRefTypeSub


class mdWrapTypeSub(supermod.mdWrapType):
    def __init__(self, MIMETYPE=None, CHECKSUMTYPE=None, CREATED=None, CHECKSUM=None, OTHERMDTYPE=None, MDTYPE=None, LABEL=None, MDTYPEVERSION=None, ID=None, SIZE=None, binData=None, xmlData=None):
        super(mdWrapTypeSub, self).__init__(MIMETYPE, CHECKSUMTYPE, CREATED, CHECKSUM, OTHERMDTYPE, MDTYPE, LABEL, MDTYPEVERSION, ID, SIZE, binData, xmlData, )
supermod.mdWrapType.subclass = mdWrapTypeSub
# end class mdWrapTypeSub


class xmlDataTypeSub(supermod.xmlDataType):
    def __init__(self, anytypeobjs_=None):
        super(xmlDataTypeSub, self).__init__(anytypeobjs_, )
supermod.xmlDataType.subclass = xmlDataTypeSub
# end class xmlDataTypeSub


class FLocatTypeSub(supermod.FLocatType):
    def __init__(self, arcrole=None, USE=None, title=None, OTHERLOCTYPE=None, show=None, actuate=None, href=None, role=None, LOCTYPE=None, type_=None, ID=None):
        super(FLocatTypeSub, self).__init__(arcrole, USE, title, OTHERLOCTYPE, show, actuate, href, role, LOCTYPE, type_, ID, )
supermod.FLocatType.subclass = FLocatTypeSub
# end class FLocatTypeSub


class FContentTypeSub(supermod.FContentType):
    def __init__(self, USE=None, ID=None, binData=None, xmlData=None):
        super(FContentTypeSub, self).__init__(USE, ID, binData, xmlData, )
supermod.FContentType.subclass = FContentTypeSub
# end class FContentTypeSub


class xmlDataType1Sub(supermod.xmlDataType1):
    def __init__(self, anytypeobjs_=None):
        super(xmlDataType1Sub, self).__init__(anytypeobjs_, )
supermod.xmlDataType1.subclass = xmlDataType1Sub
# end class xmlDataType1Sub


class streamTypeSub(supermod.streamType):
    def __init__(self, BEGIN=None, END=None, ADMID=None, BETYPE=None, streamType=None, DMDID=None, OWNERID=None, ID=None):
        super(streamTypeSub, self).__init__(BEGIN, END, ADMID, BETYPE, streamType, DMDID, OWNERID, ID, )
supermod.streamType.subclass = streamTypeSub
# end class streamTypeSub


class transformFileTypeSub(supermod.transformFileType):
    def __init__(self, TRANSFORMTYPE=None, TRANSFORMKEY=None, TRANSFORMBEHAVIOR=None, TRANSFORMALGORITHM=None, TRANSFORMORDER=None, ID=None):
        super(transformFileTypeSub, self).__init__(TRANSFORMTYPE, TRANSFORMKEY, TRANSFORMBEHAVIOR, TRANSFORMALGORITHM, TRANSFORMORDER, ID, )
supermod.transformFileType.subclass = transformFileTypeSub
# end class transformFileTypeSub


class metsSub(supermod.mets):
    def __init__(self, PROFILE=None, LABEL=None, TYPE=None, ID=None, OBJID=None, metsHdr=None, dmdSec=None, amdSec=None, fileSec=None, structMap=None, structLink=None, behaviorSec=None):
        super(metsSub, self).__init__(PROFILE, LABEL, TYPE, ID, OBJID, metsHdr, dmdSec, amdSec, fileSec, structMap, structLink, behaviorSec, )
supermod.mets.subclass = metsSub
# end class metsSub



def get_root_tag(node):
    tag = supermod.Tag_pattern_.match(node.tag).groups()[-1]
    rootClass = None
    if hasattr(supermod, tag):
        rootClass = getattr(supermod, tag)
    return tag, rootClass


def parse(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='',
        pretty_print=True)
    doc = None
    return rootObj


def parseString(inString):
    from StringIO import StringIO
    doc = parsexml_(StringIO(inString))
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('<?xml version="1.0" ?>\n')
    rootObj.export(sys.stdout, 0, name_=rootTag,
        namespacedef_='')
    return rootObj


def parseLiteral(inFilename):
    doc = parsexml_(inFilename)
    rootNode = doc.getroot()
    rootTag, rootClass = get_root_tag(rootNode)
    if rootClass is None:
        rootTag = 'mets'
        rootClass = supermod.mets
    rootObj = rootClass.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
    sys.stdout.write('#from mets_eARD import *\n\n')
    sys.stdout.write('import mets_eARD as model_\n\n')
    sys.stdout.write('rootObj = model_.mets(\n')
    rootObj.exportLiteral(sys.stdout, 0, name_="mets")
    sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()



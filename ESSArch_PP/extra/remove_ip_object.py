'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2017  ES Solutions AB

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

import django
django.setup()

from optparse import OptionParser
from essarch.models import ArchiveObject, eventIdentifier
from django.core.exceptions import ObjectDoesNotExist

def remove_ip_object(ObjectIdentifierValue, dryrun=False):
    if dryrun: 
        print 'Dry run remove of ObjectIdentifierValue: %s' % ObjectIdentifierValue
    try:        
        archiveobject_obj=ArchiveObject.objects.get(ObjectIdentifierValue=ObjectIdentifierValue)
    except ObjectDoesNotExist as e:
        print 'ArchiveObject not found for IP: %s' % (ObjectIdentifierValue)
        exit(1)
    aic_obj=archiveobject_obj.reluuid_set.get().AIC_UUID
    aic_obj_related_archiveobject_objs = aic_obj.archiveobjects.all()

    for storage_obj in archiveobject_obj.Storage_set.all():        
        print 'Remove storage: %s for archiveobject:: %s' % (storage_obj.id, archiveobject_obj.ObjectIdentifierValue)
        if not dryrun: storage_obj.delete()
        
    if len(aic_obj_related_archiveobject_objs) == 1:
        print 'Only one IP related to AIC, remove AIC: %s' % (aic_obj.ObjectIdentifierValue)
        if not dryrun: aic_obj.delete()

    archiveobjectdata_objs=archiveobject_obj.archiveobjectdata_set.all()
    for archiveobjectdata_obj in archiveobjectdata_objs:
        print 'Remove archiveobjectdata: (%s, %s) for IP: %s' % (archiveobjectdata_obj.id, archiveobjectdata_obj.label, archiveobject_obj.ObjectIdentifierValue)
        if not dryrun: archiveobjectdata_obj.delete()

    archiveobjectmetadata_objs=archiveobject_obj.archiveobjectmetadata_set.all()
    for archiveobjectmetadata_obj in archiveobjectmetadata_objs:
        print 'Remove archiveobjectmetadata: (%s) for IP: %s' % (archiveobjectmetadata_obj.id, archiveobject_obj.ObjectIdentifierValue)
        if not dryrun: archiveobjectmetadata_obj.delete()
        
    ObjectMetadata_obj=archiveobject_obj.ObjectMetadata
    if not ObjectMetadata_obj is None:
        print 'Remove ObjectMetadata: (%s, %s) for IP: %s' % (ObjectMetadata_obj.id, ObjectMetadata_obj.label, archiveobject_obj.ObjectIdentifierValue)
        if not dryrun: ObjectMetadata_obj.delete()
    
    for eventIdentifier_obj in eventIdentifier.objects.filter(linkingObjectIdentifierValue=ObjectIdentifierValue):
        print 'Remove log event: (%s, %s) for IP: %s' % (eventIdentifier_obj.id, eventIdentifier_obj.eventIdentifierValue, archiveobject_obj.ObjectIdentifierValue)
        if not dryrun: eventIdentifier_obj.delete()        

    print 'Remove IP: %s' % (archiveobject_obj.ObjectIdentifierValue)
    if not dryrun: archiveobject_obj.delete()

if __name__ == '__main__':
    ProcName = 'remove_ip_object'
    ProcVersion = __version__

    op = OptionParser(prog=ProcName,usage="usage: %prog [options] arg", version="%prog Version " + str(ProcVersion))
    op.add_option("--ObjectIdentifierValue", help="Remove ip object", dest="ObjectIdentifierValue", metavar="ObjectID")
    op.add_option("-t", "--DryRun", help="Only test run, does not remove any objects from database", action="store_true", dest="testflag", default=False)
    options, args = op.parse_args()

    optionflag = 1
    if options.ObjectIdentifierValue:
        optionflag = 0
    print 'dryflag: %s' % repr(options.testflag)

    if optionflag: op.error("incorrect options")
    
    remove_ip_object(options.ObjectIdentifierValue, options.testflag)
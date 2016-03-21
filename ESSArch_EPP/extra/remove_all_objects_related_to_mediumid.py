'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2016  ES Solutions AB

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
from Storage.models import storageMedium
from django.core.exceptions import ObjectDoesNotExist

import django
django.setup()

def remove_all_related_data_to_storagemediumid(storageMediumID, dryrun=False):
    if dryrun: 
        print 'Dry run remove of storagemedium: %s' % storageMediumID
    storageMedium_obj=storageMedium.objects.get(storageMediumID=storageMediumID)
    storage_objs=storageMedium_obj.storage_set.all()
    for storage_obj in storage_objs:
        archiveobject_obj=storage_obj.archiveobject
        aic_obj=archiveobject_obj.aic_set.get()
        aic_obj_related_archiveobject_objs = aic_obj.archiveobjects.all()
        
        # Only remove archiveobject if it do not exists on any other media
        if len(archiveobject_obj.Storage_set.all()) == 1:
            
            if len(aic_obj_related_archiveobject_objs) == 1:
                print 'Only one IP related to AIC, remove AIC: %s' % (aic_obj.ObjectUUID)
                if not dryrun: aic_obj.delete()
    
            archiveobjectdata_objs=archiveobject_obj.archiveobjectdata_set.all()
            for archiveobjectdata_obj in archiveobjectdata_objs:
                print 'Remove archiveobjectdata: %s for IP: %s' % (archiveobjectdata_obj, archiveobject_obj.ObjectUUID)
                if not dryrun: archiveobjectdata_obj.delete()
    
            archiveobjectmetadata_objs=archiveobject_obj.archiveobjectmetadata_set.all()
            for archiveobjectmetadata_obj in archiveobjectmetadata_objs:
                print 'Remove archiveobjectmetadata: %s for IP: %s' % (archiveobjectmetadata_obj, archiveobject_obj.ObjectUUID)
                if not dryrun: archiveobjectmetadata_obj.delete()
                
            ObjectMetadata_obj=archiveobject_obj.ObjectMetadata
            if not ObjectMetadata_obj is None:
                print 'Remove ObjectMetadata: %s for IP: %s' % (ObjectMetadata_obj.id, archiveobject_obj.ObjectUUID)
                if not dryrun: ObjectMetadata_obj.delete()
            
            #try:
            #    ArchiveObjectRel_obj=archiveobject_obj.reluuid_set.get()
            #    print 'Remove ArchiveObjectRel for IP: %s' % (archiveobject_obj.ObjectUUID)
            #    if not dryrun: ArchiveObjectRel_obj.delete()
            #except ObjectDoesNotExist as e:
            #    print '??? ArchiveObjectRel not found for IP: %s' % (archiveobject_obj.ObjectUUID)
            
            print 'Remove IP: %s' % (archiveobject_obj.ObjectUUID)
            if not dryrun: archiveobject_obj.delete()
        else:
            print 'Skip to remove IP: %s because of there are still copies of IP on other storagemedia' % archiveobject_obj.ObjectUUID
        
        print 'Remove storage: %s for storagemedia: %s' % (storage_obj.id, storageMedium_obj.storageMediumID)
        if not dryrun: storage_obj.delete()
    print 'Remove storagemedia: %s' % (storageMedium_obj.storageMediumID) 
    if not dryrun: storageMedium_obj.delete()

if __name__ == '__main__':
    ProcName = 'remove_all_related_data_to_storagemediumid'
    ProcVersion = __version__

    op = OptionParser(prog=ProcName,usage="usage: %prog [options] arg", version="%prog Version " + str(ProcVersion))
    op.add_option("--StorageMediaID", help="Remove all objects related to Storage Medium ID", dest="StorageMediaID", metavar="MediaID")
    op.add_option("-t", "--DryRun", help="Only test run, does not remove any objects from database", action="store_true", dest="testflag", default=False)
    options, args = op.parse_args()

    optionflag = 1
    if options.StorageMediaID:
        optionflag = 0
    print 'dryflag: %s' % repr(options.testflag)

    if optionflag: op.error("incorrect options")
    
    remove_all_related_data_to_storagemediumid(options.StorageMediaID, options.testflag)
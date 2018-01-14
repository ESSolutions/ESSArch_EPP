'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2017  ES Solutions AB

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
from Storage.models import storageMedium
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
import pytz
import ESSMSSQL
import datetime

def clear_packagename_for_all_objects_related_to_storagemediumid(storageMediumID, dryrun=False, allflag=False):
    ext_table='IngestObject' #'IngestObject'
    tz=timezone.get_default_timezone()
    if dryrun:
        print 'Dry run clear packagename for objects related to storagemedium: %s' % storageMediumID
    storageMedium_obj=storageMedium.objects.get(storageMediumID=storageMediumID)
    if allflag is True:
        storage_objs=storageMedium_obj.storage_set.all()
    else:
        storage_objs=storageMedium_obj.storage_set.filter(archiveobject__ObjectActive=1)  #(1, 'Active'), (2, 'Inactive')
    for storage_obj in storage_objs:
        archiveobject_obj=storage_obj.archiveobject
        print 'Clear packagename field for IP: %s' % (archiveobject_obj.ObjectIdentifierValue)
        if not dryrun:
            timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
            timestamp_dst = timestamp_utc.astimezone(tz)
            archiveobject_obj.ObjectPackageName = ''
            #archiveobject_obj.ObjectPackageName = '%s.tar' % archiveobject_obj.ObjectIdentifierValue
            archiveobject_obj.LocalDBdatetime=timestamp_utc
            #archiveobject_obj.LocalDBdatetime=archiveobject_obj.ExtDBdatetime
            if ext_table:
                archiveobject_obj.StatusProcess=0
                archiveobject_obj.StatusActivity=0
                archiveobject_obj.save(update_fields=['ObjectPackageName','LocalDBdatetime','StatusProcess','StatusActivity'])
            else:
                archiveobject_obj.save(update_fields=['ObjectPackageName','LocalDBdatetime'])
            if ext_table:
                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action(ext_table,'UPD',('ObjectPackageName','',
                                                                                 'LastEventDate',timestamp_dst.replace(tzinfo=None)),
                                                                                 ('ObjectGuid',archiveobject_obj.ObjectUUID))
                if ext_errno: 
                    print 'Problem to update AIS: %s, %s' % (ext_errno,ext_why)
                else:
                    archiveobject_obj.ExtDBdatetime=timestamp_utc
                    archiveobject_obj.save(update_fields=['ExtDBdatetime'])

if __name__ == '__main__':
    ProcName = 'clear_packagename_for_all_objects_related_to_storagemediumid'
    ProcVersion = __version__

    op = OptionParser(prog=ProcName,usage="usage: %prog [options] arg", version="%prog Version " + str(ProcVersion))
    op.add_option("--StorageMediaID", help="Clear packagename field for all objects related to Storage Medium ID", dest="StorageMediaID", metavar="MediaID")
    op.add_option("-t", "--DryRun", help="Only test run, does not change any objects in database", action="store_true", dest="testflag", default=False)
    op.add_option("-a", "--AllStatus", help="All objects (both inactive and active)", action="store_true", dest="allflag", default=False)
    options, args = op.parse_args()

    optionflag = 1
    if options.StorageMediaID:
        optionflag = 0
    print 'dryflag: %s' % repr(options.testflag)

    if optionflag: op.error("incorrect options")

    clear_packagename_for_all_objects_related_to_storagemediumid(options.StorageMediaID, options.testflag, options.allflag)
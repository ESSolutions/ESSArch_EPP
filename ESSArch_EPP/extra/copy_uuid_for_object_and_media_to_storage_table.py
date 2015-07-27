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

import django
django.setup()

# own models etc
from essarch.models import storageMedium, storage, ArchiveObject

def set_uuid_to_storage():

    storage_obj_list = storage.objects.filter(ObjectUUID__isnull=True).all()
    for storage_obj in storage_obj_list:
        ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue=storage_obj.ObjectIdentifierValue)
        print ip_obj.ObjectUUID
        storage_obj.ObjectUUID = ip_obj
        storage_obj.save()

    storage_obj_list = storage.objects.filter(storageMediumUUID__isnull=True).all()
    for storage_obj in storage_obj_list:
        medium_obj = storageMedium.objects.get(storageMediumID=storage_obj.storageMediumID)
        print medium_obj.storageMediumUUID
        storage_obj.storageMediumUUID = medium_obj
        storage_obj.save()

if __name__ == '__main__':
    set_uuid_to_storage()

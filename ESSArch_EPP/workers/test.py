#!/usr/bin/env /ESSArch/pd/python/bin/python
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

from essarch.models import ArchiveObject, storage
from django.db.models import Q

class Functions:
    def test(self):
        "Generate DIP for request in Accessqueue"
        pass

if __name__ == '__main__':
    s_term = 'disk'
    term = 'ESA'
    test2=Q(ObjectUUID__in = storage.objects.filter(storageMediumUUID__storageMediumID__startswith = term).values_list('ObjectUUID', flat=True))
    test_qs = ArchiveObject.objects.filter(StatusProcess=3000,PolicyId=1,storage__storageMediumUUID__storageMediumID__startswith = s_term).exclude(test2)
    object_list = test_qs.values('ObjectUUID','storage__storageMediumUUID__storageMediumID')
    print object_list

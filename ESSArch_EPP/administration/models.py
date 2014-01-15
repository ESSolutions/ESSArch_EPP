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
from django.db import models
from django.core.urlresolvers import reverse


#class Notes(models.Model):
#    title   = models.CharField(max_length=255,help_text='Ange en title')
#    FRESHMAN = 'FR'
#    SOPHOMORE = 'SO'
#    JUNIOR = 'JR'
#    SENIOR = 'SR'
#    YEAR_IN_SCHOOL_CHOICES = (
#        (FRESHMAN, 'Freshman'),
#        (SOPHOMORE, 'Sophomore'),
#        (JUNIOR, 'Junior'),
#        (SENIOR, 'Senior'),
#    )
#    content = models.CharField(max_length=2,help_text='Ange typ av content',choices=YEAR_IN_SCHOOL_CHOICES,default=FRESHMAN)
#    content2 = models.TextField(default='hej1232',help_text='help content2 xxxxyyytest123')
#    added_at = models.DateTimeField(auto_now_add=True) 
#    last_update = models.DateTimeField(auto_now=True)
#    last_update2 = models.DateTimeField(auto_now=True)
#
#    def get_absolute_url(self):
#        return reverse('notes_list')

#class permission(models.Model):
#    class Meta:
#        permissions = (
#            ("list", "list"),
#            ("create", "create"),
#            ("update", "update"),
#            ("delete", "delete"),
#        )

class robot_info(object):
    drives = 0
    slots = 0

class robot_drive(object):
    drive_id = 0
    slot_id = 0
    volume_id = ''
    status = ''
    
class robot_slot(object):
    slot_id = 0
    volume_id = ''
    volume_ver = ''
    status = ''
    
class robot_export(object):
    slot_id = 0
    volume_id = ''
    volume_ver = ''
    status = ''

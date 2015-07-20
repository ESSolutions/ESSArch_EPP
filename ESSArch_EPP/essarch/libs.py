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

from django.db.models import Q
from django.db import models
from django.db import transaction
from django.core.paginator import Paginator
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseBadRequest

from operator import or_

from eztables.views import DatatablesView
from eztables.forms import DatatablesForm

import os, stat, hashlib

#: SQLite unsupported field types for regex lookups
UNSUPPORTED_REGEX_FIELDS = (
    models.IntegerField,
    #models.BooleanField,
    #models.NullBooleanField,
    #models.FloatField,
    #models.DecimalField,
    models.DateTimeField,
)

RE_FORMATTED = re.compile(r'\{(\w+)\}')

#@transaction.commit_manually
#def flush_transaction():
#    """
#    Flush the current transaction so we don't read stale data
#
#    Use in long running processes to make sure fresh data is read from
#    the database.  This is a problem with MySQL and the default
#    transaction mode.  You can fix it by setting
#    "transaction-isolation = READ-COMMITTED" in my.cnf or by calling
#    this function at the appropriate moment
#    """
#    transaction.commit()
    
def get_real_field(model, field_name):
    '''
    Get the real field from a model given its name.

    Handle nested models recursively (aka. ``__`` lookups)
    '''
    parts = field_name.split('__')
    field = model._meta.get_field_by_name(parts[0])[0]
    if len(parts) == 1:
        return model._meta.get_field_by_name(field_name)[0]
    elif isinstance(field, models.ForeignKey):
        return get_real_field(field.rel.to, '__'.join(parts[1:]))
    elif isinstance(field, models.fields.related.ForeignObjectRel):
        return get_real_field(field.related_model,'__'.join(parts[1:]))
    else:
        raise Exception('Unhandled field: %s' % field_name)
    
def get_field_choices(obj, fields):
    '''
    Get the choices for fields.

    Handle nested models recursively (aka. ``__`` lookups)
    '''
    field_choices_dict = {}
    if obj:
        obj = obj[0]
        for db_field in fields:
            field = get_real_field(obj,db_field)
            field_choices = getattr(field,'choices',None)
            if field_choices:
                #print 'found choices: %s' % str(field.choices)
                field_choices_dict[db_field] = field_choices
    return field_choices_dict

def get_object_list_display(object_list, field_choices_dict):
    '''
    Get object_list_display
    '''
    object_list_display = []
    for obj in object_list:
        obj_dict_display = {'test':'hej'}
        for field in obj:
            if field in field_choices_dict:
                #print 'field: %s, key: %s' % (field, obj[field])
                #print 'field_choices_dict: %s' % str(field_choices_dict)
                try:
                    obj_dict_display[field] = dict(field_choices_dict[field])[obj[field]]
                except KeyError:
                    obj_dict_display[field] = obj[field]
            else:
                obj_dict_display[field] = obj[field]
        object_list_display.append(obj_dict_display)
    return object_list_display

def GetSize(path):
    """ Check size of file or directory """
    f_size = 0
    f_stat = os.stat(path)
    if stat.S_ISDIR(f_stat.st_mode):                 # It's a director
        for f_name in os.listdir(path):
            f_path = os.path.join(path,f_name)
            f_stat = os.stat(f_path)
            if stat.S_ISREG(f_stat.st_mode):                   # It's a file
                f_size += f_stat.st_size
            elif stat.S_ISDIR(f_stat.st_mode):                 # It's a directory
                f_size += GetSize(f_path)
    else:
        f_size += f_stat.st_size
    return f_size

def calcsum(filepath,checksumtype='MD5'):
    """Return checksum for a file."""
    if type(checksumtype) in [str,unicode]:
        checksumtype = checksumtype.lower()
    if checksumtype in ['md5',1]:
        h = hashlib.md5()
    elif checksumtype in ['sha256','sha-256',2]:
        h = hashlib.sha256()
    else:
        h = hashlib.md5()
    chunk = 1048576
    f = open(filepath, "rb")
    s = f.read(chunk)
    while s != "":
        h.update(s)
        s = f.read(chunk)
    f.close()
    return h.hexdigest()

class ESSArchSMError(Exception):
    def __init__(self, value):
        self.value = value
        #Exception.__init__(self, value)
        super(ESSArchSMError, self).__init__(value)
#    def __str__(self):
#        return repr(self.value)
    
class DatatablesView(DatatablesView):

    def process_dt_response(self, data):
        self.form = DatatablesForm(data)
        if self.form.is_valid():
            #flush_transaction()
            self.object_list = self.get_queryset().values(*self.get_db_fields())
            #print 'get_queryset: %s' % str(self.get_queryset)
            self.field_choices_dict = get_field_choices(self.get_queryset()[:1], self.get_db_fields())
            #field_choices_dict={}
            #print '####################################################################################################################'
            #print '###object_list: %s, type: %s' % (self.object_list, type(self.object_list))
            #self.object_list = get_object_list_display(self.object_list, field_choices_dict)
            #print '********************************************************************************************************************'
            #print '***object_list: %s, type: %s' % (self.object_list, type(self.object_list))
            #print 'object_list: %s' % str(object_list)
            #print 'field_choices_dict: %s' % str(field_choices_dict)
            #print 'object_list_display: %s' % str(object_list_display)
            #self.object_list = self.get_queryset().values(*self.get_db_fields())
            #self.object_list = self.object_list_display
            return self.render_to_response(self.form)
        else:
            return HttpResponseBadRequest()
    
    def get_page(self, form):
        '''Get the requested page'''
        page_size = form.cleaned_data['iDisplayLength']
        start_index = form.cleaned_data['iDisplayStart']
        if page_size == -1:
            #page_size = self.object_list.count()
            page_size = len(self.object_list)
            if page_size == 0: page_size = 1
        paginator = Paginator(self.object_list, page_size)
        num_page = (start_index / page_size) + 1
        return paginator.page(num_page)
    
    def can_regex(self, field):
        '''Test if a given field supports regex lookups'''
        from django.conf import settings
        if settings.DATABASES['default']['ENGINE'].endswith('sqlite3'):
            return not isinstance(get_real_field(self.model, field), UNSUPPORTED_REGEX_FIELDS)
        elif settings.DATABASES['default']['ENGINE'].endswith('mysql'):
            return not isinstance(get_real_field(self.model, field), UNSUPPORTED_REGEX_FIELDS)
        else:
            return True
    
    def global_search(self, queryset):
        '''Filter a queryset with global search'''
        search = self.dt_data['sSearch']
        if search:
            if self.dt_data['bRegex']:
                criterions = [Q(**{'%s__iregex' % field: search}) for field in self.get_db_fields() if self.can_regex(field)]
                if len(criterions) > 0:
                    search = reduce(or_, criterions)
                    queryset = queryset.filter(search)
            else:
                for term in search.split():
                    #criterions = (Q(**{'%s__icontains' % field: term}) for field in self.get_db_fields())
                    criterions = (Q(**{'%s__icontains' % field: term}) for field in self.get_db_fields() if self.can_regex(field))
                    search = reduce(or_, criterions)
                    #print search
                    queryset = queryset.filter(search)
        return queryset

    def render_to_response(self, form, **kwargs):
        '''Render Datatables expected JSON format'''
        page = self.get_page(form)
        #print 'page_type_object_list: %s' % type(page.object_list)
        page.object_list = get_object_list_display(page.object_list, self.field_choices_dict)
        data = {
            'iTotalRecords': page.paginator.count,
            'iTotalDisplayRecords': page.paginator.count,
            'sEcho': form.cleaned_data['sEcho'],
            'aaData': self.get_rows(page.object_list),
            #'aaData': self.get_rows(object_list),
        }
        return self.json_response(data)


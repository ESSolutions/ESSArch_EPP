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
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404, render
from django.db.models import Q
from django.db import models

from essarch.models import storageMedium, storageMediumTable, MediumType_CHOICES, MediumStatus_CHOICES, MediumLocationStatus_CHOICES, MediumFormat_CHOICES, MediumBlockSize_CHOICES, \
                           storage, robot, robotreq, robotReqQueueForm, ArchiveObject, ControlAreaQueue, ControlAreaForm_file2, \
                           MigrationQueue, MigrationReqType_CHOICES, ReqStatus_CHOICES, MigrationQueueForm, MigrationQueueFormUpdate
from configuration.models import Path, Parameter, ESSArchPolicy

from djcelery.models import TaskMeta

from administration.tasks import MigrationTask

from django.views.generic.detail import DetailView
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseUpdateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

from django.core.paginator import Paginator
from django.views.generic import View
from django.views.generic.list import MultipleObjectMixin
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest

from django_tables2 import RequestConfig
from eztables.views import DatatablesView, get_real_field
from eztables.forms import DatatablesForm

from operator import or_

import uuid, os.path as op, ESSPGM, ESSMD

from lxml import etree

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

from django.db import transaction

@transaction.commit_manually
def flush_transaction():
    """
    Flush the current transaction so we don't read stale data

    Use in long running processes to make sure fresh data is read from
    the database.  This is a problem with MySQL and the default
    transaction mode.  You can fix it by setting
    "transaction-isolation = READ-COMMITTED" in my.cnf or by calling
    this function at the appropriate moment
    """
    transaction.commit()

class storageMediumList(ListView):
    """
    List storageMedium
    """
    model = storageMedium
    template_name='administration/liststoragemedium.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(storageMediumList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(storageMediumList, self).get_context_data(**kwargs)
        context['label'] = 'List of storagemedium'
        context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        return context

class storageMediumDetail(DetailView):
    """
    storageMedium details
    """
    model = storageMedium
    template_name='administration/detail.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(storageMediumDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(storageMediumDetail, self).get_context_data(**kwargs)
        storageMediumID = context['object'].storageMediumID
        content_list = storage.objects.filter(storageMediumID=storageMediumID).order_by('id')
        context['content_list'] = content_list
        context['label'] = 'Detail information - storage medium'
        context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        context['MediumFormat_CHOICES'] = dict(MediumFormat_CHOICES)
        context['MediumBlockSize_CHOICES'] = dict(MediumBlockSize_CHOICES)
        return context

def storageMediumList2(request):
    """
    List storageMedium
    """
    model = storageMedium
    table = storageMediumTable(model.objects.all())
    RequestConfig(request).configure(table)
    template_name='administration/liststoragemedium2.html'
    context = {}
    context['table'] = table
    context['label'] = 'List of storagemedium'
    return render(request, template_name, context)

class storageMediumList3(TemplateView):
    template_name = 'administration/liststoragemedium3.html'

class storageMediumDatatablesView(DatatablesView):
    model = storageMedium
    fields = (
        "storageMediumID",
        "storageMedium",
        "storageMediumStatus",
        "storageMediumDate",
        "storageMediumLocation",
        "storageMediumLocationStatus",
        "storageMediumUsedCapacity",
        "storageMediumMounts",
    )
    def process_dt_response(self, data):
        self.form = DatatablesForm(data)
        if self.form.is_valid():
            #self.object_list = self.get_queryset().values(*self.get_db_fields())
            self.object_list = []
            for obj in self.get_queryset():
                obj_dict = {}
                for db_field in self.get_db_fields():
                    # We need to take special care here to allow get_FOO_display()
                    # methods on a model to be used if available.
                    field = obj._meta.get_field(db_field)
                    display = getattr(obj, 'get_%s_display' % db_field, None)
                    if field.choices and display:
                        value = display()
                    else:
                        value = getattr(obj, db_field, None)
                    obj_dict[db_field] = value
                self.object_list.append(obj_dict)
            return self.render_to_response(self.form)
        else:
            return HttpResponseBadRequest()
    
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
                    print search
                    queryset = queryset.filter(search)
        return queryset

class storageList(ListView):
    """
    List storage "content"
    """
    model = storage
    template_name='administration/liststorage.html'

    @method_decorator(permission_required('essarch.list_storage'))
    def dispatch(self, *args, **kwargs):
        return super(storageList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(storageList, self).get_context_data(**kwargs)
        context['label'] = 'List of storage content'
        return context
    
class robotList(ListView):
    model = robot
    template_name='administration/listrobot.html'
    
    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(robotList, self).get_context_data(**kwargs)
        context['label'] = 'List of robot content'
        context['admin_user'] = True
        return context

class robotReqCreate(CreateView):
    model = robotreq
    template_name='administration/create.html'
    form_class=robotReqQueueForm

    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(robotReqCreate, self).get_initial().copy()
        if 'storageMediumID' in self.kwargs:
            initial['t_id'] = self.kwargs['storageMediumID']
        if 'command' in self.kwargs:
            command = self.kwargs['command']
            if command == '1':
                initial['req_type'] = 'Mount'
                initial['work_uuid'] = 'Manual'
            elif command == '3':
                initial['req_type'] = 'F_Unmount'
        initial['job_prio'] = 1
        initial['status'] = 'pending'
        initial['user'] = self.request.user.username
        return initial

class robotInventory(DetailView):
    """
    Submit and View result from robot inventory
    """
    #model = ArchiveObject
    template_name='administration/result_detail.html'

    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotInventory, self).dispatch( *args, **kwargs)
    
    def get_object(self):
        return None

    def get_context_data(self, **kwargs):
        #context = super(robotInventory, self).get_context_data(**kwargs)
        context = {}
        ###############################################
        # robot inventory
        ###############################################
        # command=1 (robot inventory and do not fetch metadata form central database)
        # command=2 (robot inventory and fetch metadata form central database)
        # command=3 (robot inventory and fetch metadata form central database and Force set MediumLocaltion to IT_Mariberg)
        if 'command' in self.kwargs:
            command = self.kwargs['command']
        else:
            command = None

        if command == '1': 
            CentralDB = 0
            set_storageMediumLocation = ''
        elif command == '2':
            CentralDB = 1
            set_storageMediumLocation = ''
        elif command == '3':
            CentralDB = 1
            set_storageMediumLocation = 'IT_MARIEBERG'
        else:
            CentralDB = 0
            set_storageMediumLocation = ''

        status_code = ESSPGM.Robot().Inventory()
        if not status_code:
            status_code = ESSPGM.Robot().GetVolserDB(CentralDB=CentralDB, set_storageMediumLocation=set_storageMediumLocation)
        status_detail = [[],[]]
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context
    

class StorageMaintenance(TemplateView):
    template_name = 'administration/storagemaintenance.html'


def get_real_field_obj(model, field_name):
    '''
    Get the real field from a model given its name.

    Handle nested models recursively (aka. ``__`` lookups)
    '''
    parts = field_name.split('__')
    field = model._meta.get_field(parts[0])
    if len(parts) == 1:
        #return model._meta.get_field(field_name)
        return model, field_name, model._meta.get_field(field_name)
    elif isinstance(field, models.ForeignKey):
        return get_real_field_obj(field.rel.to, '__'.join(parts[1:]))
    #elif isinstance(field, models.related.RelatedObject):
    #    return get_real_field(field.field.rel.to, '__'.join(parts[1:]))
    else:
        raise Exception('Unhandled field: %s' % field_name)

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
    elif isinstance(field, models.related.RelatedObject):
        return None
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
                obj_dict_display[field] = dict(field_choices_dict[field])[obj[field]]
            else:
                obj_dict_display[field] = obj[field]
        object_list_display.append(obj_dict_display)
    return object_list_display

class StorageMaintenanceDatatablesView(DatatablesView):
    model = ArchiveObject
    fields = (
        'ObjectIdentifierValue',
        'ObjectUUID',
        'StatusProcess',
        'StatusActivity',
        'storage__storageMediumUUID__storageMediumID',
        'storage__contentLocationValue',
        
        'PolicyId__PolicyName',
        'PolicyId__PolicyID',
        'PolicyId__PolicyStat',
        
        '{PolicyId__sm_type_1} ({PolicyId__sm_1})',
        'PolicyId__sm_target_1',
        '{PolicyId__sm_type_2} ({PolicyId__sm_2})',
        'PolicyId__sm_target_2',
        '{PolicyId__sm_type_3} ({PolicyId__sm_3})',
        'PolicyId__sm_target_3',
        '{PolicyId__sm_type_4} ({PolicyId__sm_4})',
        'PolicyId__sm_target_4',
    )   

    def process_dt_response(self, data):
        self.form = DatatablesForm(data)
        if self.form.is_valid():
            flush_transaction()
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
            page_size = self.object_list.count()
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
                    print search
                    queryset = queryset.filter(search)
        return queryset

    def sort_col_4(self, direction):
        '''sort for col_5'''
        return ('%sstorage__storageMediumUUID__storageMediumID' % direction, '%sstorage__id' % direction)

    def sort_col_5(self, direction):
        '''sort for col_6'''
        return ('%sstorage__id' % direction, '%sstorage__storageMediumUUID__storageMediumID' % direction)
    
    def search_col_5(self, search, queryset):
        '''exclude filter for search terms'''
        for term in search.split():
            exclude_list = []
            #for x in storage.objects.filter(storageMediumUUID__storageMediumID__startswith = term, ObjectUUID__isnull=False).values_list('ObjectUUID', flat=True):
            for x in storage.objects.filter(storageMediumUUID__storageMediumID__startswith = term).values_list('ObjectUUID', flat=True):
                exclude_list.append(x)
            search2 = Q(ObjectUUID__in = exclude_list)
            queryset = queryset.exclude(search2)
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

class MigrateView(MultipleObjectMixin, View):
    '''
    MigrateView
    '''

    def post(self, request, *args, **kwargs):
        print request.POST
        q_dict = request.POST
        obj_list = q_dict.get('tableData',None)
        target_medium = q_dict.get('target',None)
        obj_list = obj_list.split('\r\n')[:-1]
        #print 'obj_list: %s' % str(obj_list)
        #print 'target_medium: %s' % target_medium
        EL_root = etree.Element('needcopies')    

        for obj in obj_list:
            EL_object = etree.SubElement(EL_root, 'object', attrib={'id':obj,
                                                                    'target':target_medium,
                                                                    })
        doc = etree.ElementTree(element=EL_root, file=None)
        ESSMD.writeToFile(doc,'/ESSArch/log/needcopies/needcopies.xml')

        data = {
            'iTotalRecords': 0,
            'iTotalDisplayRecords': 0,
            'sEcho': 'test123echo',
            'aaData': 'testdata',
        }
        #return self.process_dt_response(request.POST)
        return self.json_response(data)

    def get(self, request, *args, **kwargs):
        print request.GET
        #return self.process_dt_response(request.GET)

    def render_to_response(self, form, **kwargs):
        '''Render Datatables expected JSON format'''
        page = self.get_page(form)
        data = {
            'iTotalRecords': page.paginator.count,
            'iTotalDisplayRecords': page.paginator.count,
            'sEcho': form.cleaned_data['sEcho'],
            'aaData': self.get_rows(page.object_list),
        }
        return self.json_response(data)

    def json_response(self, data):
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            mimetype='application/json'
        )
    
class MigrationList(ListView):
    """
    List MigrationQueue
    """
    model = MigrationQueue
    template_name='administration/migreq_list.html'
    context_object_name='req_list'
    queryset=MigrationQueue.objects.filter(Status__lt=20)   # Status<20

    @method_decorator(permission_required('essarch.list_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MigrationList, self).get_context_data(**kwargs)
        context['label'] = 'List of migration requests'
        context['MigrationReqType_CHOICES'] = dict(MigrationReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class MigrationDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = MigrationQueue
    context_object_name='migration'
    template_name='administration/migreq_detail.html'

    @method_decorator(permission_required('essarch.list_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(MigrationDetail, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - migration requests'
        context['MigrationReqType_CHOICES'] = dict(MigrationReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class MigrationCreate(CreateView):
    model = MigrationQueue
    template_name = 'administration/migreq_create.html'
    form_class = MigrationQueueForm
    obj_list = None

    @method_decorator(permission_required('essarch.add_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationCreate, self).dispatch( *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            #print 'Form is valid!!!'
            #print request.POST
            obj_list = self.request.POST.get('ObjectIdentifierValue',None)
            if request.is_ajax():    
                self.obj_list = obj_list.split('\r\n')[:-1]
            else:
                self.obj_list = obj_list.split(' ')
            return self.form_valid(form)
        else:
            #print 'Form Not valid problem!!!'
            #print request.POST
            if request.is_ajax():
                return HttpResponseBadRequest()
            else:
                return self.form_invalid(form)
    
    def render_to_response2(self, context, **response_kwargs):
        #print 'render response!!!!'
        flag_json = 1
        if self.request.is_ajax():
            #print 'is_ajax!!!'           
            '''Render Datatables expected JSON format'''
            data = {
                'sEcho': 'test123echonew',
            }
            return self.json_response(data)
        else:
            return super(MigrationCreate, self).render_to_response( context, **response_kwargs) 

    def get_initial(self):
        initial = super(MigrationCreate, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = self.request.GET.get('ReqType',1)
        initial['ReqPurpose'] = self.request.GET.get('ReqPurpose') 
        #if initial['ReqType'] == 1:
        #    migration_path = Path.objects.get(entity='path_control').value
        #initial['Path'] = self.request.GET.get('Path', migration_path)
        #if 'ip_uuid' in self.kwargs:
        #    initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        
        self.object.pk = None 
        self.object.user = self.request.user.username
        self.object.ObjectIdentifierValue = self.obj_list
        self.object.ReqUUID = uuid.uuid1()
        self.object.save()
        req_pk = self.object.pk
        result = MigrationTask.delay_or_eager(obj_list=self.object.ObjectIdentifierValue, mig_pk=req_pk)
        task_id = result.task_id
        self.object.task_id = task_id
        self.object.save()
        if self.request.is_ajax():
            '''Render Datatables expected JSON format'''
            data = {
                'sEcho': 'OK',
                'req_pk': req_pk,
                'task_id': task_id,
            }
            return self.json_response(data)
        else:
            return super(MigrationCreate, self).form_valid(form)

    def json_response(self, data):
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            mimetype='application/json'
        )
        
class MigrationUpdate(UpdateView):
    model = MigrationQueue
    template_name='administration/migreq_update.html'
    form_class=MigrationQueueFormUpdate
    
    @method_decorator(permission_required('essarch.change_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationUpdate, self).dispatch( *args, **kwargs)

class MigrationDelete(DeleteView):
    model = MigrationQueue
    template_name='administration/migreq_delete.html'
    context_object_name='migration'
    success_url = reverse_lazy('migration_list')

    @method_decorator(permission_required('essarch.delete_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationDelete, self).dispatch( *args, **kwargs)
    
    
    
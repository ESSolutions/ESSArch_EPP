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
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import render
from django.db.models import Q
from operator import or_, and_

#from essarch.models import storageMedium, storageMediumTable, MediumType_CHOICES, MediumStatus_CHOICES, MediumLocationStatus_CHOICES, MediumFormat_CHOICES, MediumBlockSize_CHOICES, \
from essarch.models import storageMedium, MediumType_CHOICES, MediumStatus_CHOICES, MediumLocationStatus_CHOICES, MediumFormat_CHOICES, MediumBlockSize_CHOICES, \
                           storage, robot, robotQueue, robotQueueForm, robotQueueFormUpdate, RobotReqType_CHOICES, ArchiveObject, \
                           MigrationQueue, MigrationReqType_CHOICES, ReqStatus_CHOICES, MigrationQueueForm, MigrationQueueFormUpdate


from administration.tasks import MigrationTask, RobotInventoryTask

from django.views.generic.detail import DetailView
from django.views.generic import ListView, TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest

#from django_tables2 import RequestConfig

from essarch.libs import DatatablesView

import uuid, ESSPGM

class storageMediumList3(ListView):
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
    template_name='administration/storagemedium_detail.html'

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

class storageDatatablesView(DatatablesView):
    model = storage
    fields = (
        "id", 
        "ObjectIdentifierValue",
        "contentLocationValue",
    )
    def get_queryset(self):
        '''Apply search filter to QuerySet'''
        qs = super(DatatablesView, self).get_queryset()
        storageMediumID = self.request.GET.get('storageMediumID',None)
        if storageMediumID:
            qs = qs.filter(storageMediumID=storageMediumID)
        return qs

#def storageMediumList2(request):
#    """
#    List storageMedium
#    """
#    model = storageMedium
#    table = storageMediumTable(model.objects.all())
#    RequestConfig(request).configure(table)
#    template_name='administration/liststoragemedium2.html'
#    context = {}
#    context['table'] = table
#    context['label'] = 'List of storagemedium'
#    return render(request, template_name, context)

class storageMediumList(TemplateView):
    template_name = 'administration/storagemedium_list.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(storageMediumList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(storageMediumList, self).get_context_data(**kwargs)
        context['label'] = 'List of storagemedium'
        #context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        #context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        #context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        return context

class storageMediumDatatablesView(DatatablesView):
    model = storageMedium
    fields = (
        "id",
        "storageMediumID",
        "storageMedium",
        "storageMediumStatus",
        "storageMediumDate",
        "storageMediumLocation",
        "storageMediumLocationStatus",
        "storageMediumUsedCapacity",
        "storageMediumMounts",
    )
    
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
    template_name='administration/robot_list.html'
    
    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(robotList, self).get_context_data(**kwargs)
        context['label'] = 'List of robot content'
        context['admin_user'] = True
        context['robotreq_list'] = robotQueue.objects.filter(Q(Status__lt=20) | Q(Status=100))   # Status<20
        context['ReqType_CHOICES'] = dict(RobotReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class robotReqCreate(CreateView):
    model = robotQueue
    template_name='administration/robotreq_form.html'
    form_class=robotQueueForm

    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(robotReqCreate, self).get_initial().copy()
        if 'storageMediumID' in self.kwargs:
            initial['MediumID'] = self.kwargs['storageMediumID']
        if 'command' in self.kwargs:
            command = self.kwargs['command']
            if command == '1':
                initial['ReqType'] = 50
                initial['ReqUUID'] = 'Manual'
            elif command == '3':
                initial['ReqType'] = 52
                initial['ReqUUID'] = 'Manual'
            initial['Status'] = 0
        else:
            initial['ReqType'] = self.request.GET.get('ReqType',1)
            initial['ReqUUID'] = uuid.uuid1()
            initial['Status'] = 0
            initial['ReqPurpose'] = self.request.GET.get('ReqPurpose')
            initial['ais_flag'] = True
        initial['user'] = self.request.user.username
        return initial

    def form_valid(self, form):
        self.object = form.save(commit=False)
        
        #self.object.pk = None 
        #self.object.user = self.request.user.username
        #self.object.ObjectIdentifierValue = self.obj_list
        #self.object.ReqUUID = uuid.uuid1()
        ais_flag = form.cleaned_data.get('ais_flag',False)
        self.object.save()
        if not self.object.ReqType in [50,51,52]:
            req_pk = self.object.pk
            result = RobotInventoryTask.delay_or_eager(req_pk=req_pk,CentralDB=ais_flag)
            task_id = result.task_id
            self.object.task_id = task_id
            self.object.save()
        return super(robotReqCreate, self).form_valid(form)

class robotReqDetail(DetailView):
    """
    Detail View result
    """
    model = robotQueue
    context_object_name='req'
    template_name='administration/robotreq_detail.html'

    @method_decorator(permission_required('essarch.list_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(robotReqDetail, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - robot requests'
        context['ReqType_CHOICES'] = dict(RobotReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class robotReqUpdate(UpdateView):
    model = robotQueue
    template_name='administration/robotreq_update.html'
    form_class=robotQueueFormUpdate
    
    @method_decorator(permission_required('essarch.change_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqUpdate, self).dispatch( *args, **kwargs)

class robotReqDelete(DeleteView):
    model = robotQueue
    template_name='administration/robotreq_delete.html'
    context_object_name='req'
    success_url = reverse_lazy('admin_listrobot')

    @method_decorator(permission_required('essarch.delete_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqDelete, self).dispatch( *args, **kwargs)

class robotInventory(DetailView):
    """
    Submit and View result from robot inventory
    """
    #model = ArchiveObject
    template_name='administration/robotinventory_detail.html'

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
        if status_code == 0:
            status_code = 'OK'
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context
    

class StorageMaintenance(TemplateView):
    template_name = 'administration/storagemaintenance.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(StorageMaintenance, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StorageMaintenance, self).get_context_data(**kwargs)
        context['label'] = 'Storage maintenance'
        return context
    
class StorageMaintenanceDatatablesView(DatatablesView):
    model = ArchiveObject
    #queryset = ArchiveObject.objects.filter(StatusProcess=30001).all()
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
    
    
    
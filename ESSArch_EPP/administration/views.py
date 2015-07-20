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
from django.core.context_processors import request
from _elementtree import tostring
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
                           MigrationQueue, MigrationReqType_CHOICES, ReqStatus_CHOICES, MigrationQueueForm, MigrationQueueFormUpdate, DeactivateMediaForm

from configuration.models import sm, DefaultValue, ESSConfig, ESSArchPolicy

from administration.tasks import MigrationTask, RobotInventoryTask

from django.views.generic.detail import DetailView
from django.views.generic import ListView, TemplateView
from django.views.generic import View
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

from eztables.views import RE_FORMATTED


import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest

from django.utils import timezone

#from django_tables2 import RequestConfig

#from essarch.libs import DatatablesView, flush_transaction, DatatablesForm, get_field_choices, get_object_list_display
from essarch.libs import DatatablesView, DatatablesForm, get_field_choices, get_object_list_display

import uuid, ESSPGM, ESSMSSQL, logging, datetime, pytz

ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)

class storageMediumList3_old(ListView):
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
        context['label'] = 'ADMINISTRATION - List media information'
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
        context['label'] = 'ADMINISTRATION - List media information'
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
        "CreateDate",
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
        context['label'] = 'ADMINISTRATION - List media content'
        return context
    
class robotList(ListView):
    model = robot
    template_name='administration/robot_list.html'
    
    @method_decorator(permission_required('essarch.list_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(robotList, self).get_context_data(**kwargs)
        context['label'] = 'ADMINISTRATION - List robot information'
        context['admin_user'] = True
        context['robotreq_list'] = robotQueue.objects.filter(Q(Status__lt=20) | Q(Status=100))   # Status<20
        context['ReqType_CHOICES'] = dict(RobotReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class robotReqCreate(CreateView):
    model = robotQueue
    template_name='administration/robotreq_form.html'
    form_class=robotQueueForm

    @method_decorator(permission_required('essarch.add_robot'))
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

    @method_decorator(permission_required('essarch.list_robot'))
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
    
    @method_decorator(permission_required('essarch.change_robot'))
    def dispatch(self, *args, **kwargs):
        return super(robotReqUpdate, self).dispatch( *args, **kwargs)

class robotReqDelete(DeleteView):
    model = robotQueue
    template_name='administration/robotreq_delete.html'
    context_object_name='req'
    success_url = reverse_lazy('admin_listrobot')

    @method_decorator(permission_required('essarch.delete_robot'))
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
    

class StorageMigration(TemplateView):
    template_name = 'administration/storagemigration.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(StorageMigration, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(StorageMigration, self).get_context_data(**kwargs)
        context['label'] = 'ADMINISTRATION - Storage Migration'
        context['DefaultValue'] = dict(DefaultValue.objects.filter(entity__startswith='administration_storagemigration').values_list('entity','value'))
        #context['DefaultValueObject'] = DefaultValue.objects.filter(entity__startswith='administration_storagemaintenance').get_value_object()
        return context
    
    
            
class TargetPrePopulation(View):

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
    
        return super(TargetPrePopulation, self).dispatch( *args, **kwargs)
        
    def get_enabled_policies(self, *args, **kwargs):
        
        allPolicies = ESSArchPolicy.objects.all()
        enabled_policies = []
        policy_selection_list =[]
        for p in allPolicies: 
            if p.PolicyStat == 1:
                    enabled_policies.append(p)

        i = 0
        while (i < len(enabled_policies)):
            
            a = enabled_policies[i]

            Policy ={}
            Policy['PolicyID'] = a.PolicyID
            Policy['PolicyName'] =  a.PolicyName
            
            targetlist = []

            if a.sm_1 == True and 299 <a.sm_type_1 <400:
                        targetlist.append(a.sm_target_1)
            if a.sm_2 == True and 299 <a.sm_type_2 <400:
                        targetlist.append(a.sm_target_2)
            if a.sm_3 == True and 299 <a.sm_type_3 <400:
                        targetlist.append(a.sm_target_3)
            if a.sm_4 == True and 299 <a.sm_type_4 <400:
                        targetlist.append(a.sm_target_4)            
            Policy['targetlist'] = targetlist
            policy_selection_list.append(Policy)
            i = i +1
        
        return policy_selection_list  

    def json_response(self, request):
        
        data = self.get_enabled_policies()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            mimetype='application/json'
        )
    def get(self, request, *args, **kwargs):
        
        return self.json_response(request)  
    
    
    
class StorageMaintenance(TemplateView):
    template_name = 'administration/storagemaintenance.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(StorageMaintenance, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StorageMaintenance, self).get_context_data(**kwargs)
        context['label'] = 'ADMINISTRATION - Storage Maintenance'
        context['DefaultValue'] = dict(DefaultValue.objects.filter(entity__startswith='administration_storagemaintenance').values_list('entity','value'))
        #context['DefaultValueObject'] = DefaultValue.objects.filter(entity__startswith='administration_storagemaintenance').get_value_object()
        return context
     
class StorageMaintenanceDatatablesView(DatatablesView):
    model = ArchiveObject
    #queryset = ArchiveObject.objects.exclude(Q(storage__storageMediumUUID__storageMediumStatus = 0))
    #queryset = ArchiveObject.objects.exclude(storage__storageMediumUUID__storageMediumStatus = 0)
    #queryset = ArchiveObject.objects.extra(where=["NOT `storageMedium`.`storageMediumStatus` = %s"],params=['0'])
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
        
        #'storage__storageMediumUUID__storageMediumDate',
        'storage__storageMediumUUID__CreateDate',
        'storage__storageMediumUUID__storageMediumStatus',
    )   

    def process_dt_response(self, data):
        self.form = DatatablesForm(data)
        if self.form.is_valid():
            #flush_transaction()
            #self.object_list = self.get_queryset().extra(where=["NOT `storageMedium`.`storageMediumStatus` = %s"],params=['0']).values(*self.get_db_fields())
            self.object_list_with_writetapes = self.get_queryset().extra(where=["NOT `storageMedium`.`storageMediumStatus` = %s"],params=['0']).values(*self.get_db_fields())
            self.object_list = []
            for obj in self.object_list_with_writetapes:
                if not obj['storage__storageMediumUUID__storageMediumStatus'] == 20:
                    self.object_list.append(obj)
            
            #self.object_list = self.get_queryset().extra(where=["NOT `storageMedium`.`storageMediumStatus` IN (%s)"],params=['0',]).values(*self.get_db_fields())
            #self.object_list = self.get_queryset().extra(where=["NOT `storageMedium`.`storageMediumStatus` IN (%s,%s)"],params=['0','20']).values(*self.get_db_fields())
            #print 'self.object_list : %s' % self.object_list 
            self.field_choices_dict = get_field_choices(self.get_queryset()[:1], self.get_db_fields())
            return self.render_to_response(self.form)
        else:
            return HttpResponseBadRequest()

    def sort_col_4(self, direction):
        '''sort for col_5'''
        return ('%sstorage__storageMediumUUID__storageMediumID' % direction, '%sstorage__id' % direction)

    def sort_col_5(self, direction):
        '''sort for col_6'''
        return ('%sstorage__id' % direction, '%sstorage__storageMediumUUID__storageMediumID' % direction)

    def search_col_4(self, search, queryset):
        idx=4
        field = self.get_field(idx)
        fields = RE_FORMATTED.findall(field) if RE_FORMATTED.match(field) else [field]
        if not search.startswith('-'):
            if self.dt_data['bRegex_%s' % idx]:
                criterions = [Q(**{'%s__iregex' % field: search}) for field in fields if self.can_regex(field)]
                if len(criterions) > 0:
                    search = reduce(or_, criterions)
                    queryset = queryset.filter(search)
            else:
                for term in search.split():
                    criterions = (Q(**{'%s__icontains' % field: term}) for field in fields)
                    search = reduce(or_, criterions)
                    queryset = queryset.filter(search)
        return queryset

    def search_col_5(self, search, queryset):
        '''exclude filter for search terms'''
        #print 'search: %s' % search
        for term in search.split():
            #print 'term: %s' % term
            exclude_list = []
            if term.startswith('/'):
                #print 'term/: %s' % term
                #print 'exclude_list_before: %s' % exclude_list
                for x in storage.objects.filter(contentLocationValue = term, ObjectUUID__isnull=False).values_list('ObjectUUID', flat=True):
                    exclude_list.append(x)
                #print 'exclude_list_after: %s' % exclude_list
            else:
                for x in storage.objects.filter(storageMediumUUID__storageMediumID__startswith = term, ObjectUUID__isnull=False).values_list('ObjectUUID', flat=True):
                #for x in storage.objects.filter(storageMediumUUID__storageMediumID__startswith = term).values_list('ObjectUUID', flat=True):
                    exclude_list.append(x)
            search2 = Q(ObjectUUID__in = exclude_list)
            queryset = queryset.exclude(search2)
        return queryset

    def get_deactivate_list(self):
        logger = logging.getLogger('essarch.storagemaintenance')
        #
        # Create unique obj_list
        obj_list = []
        for obj in self.object_list_with_writetapes:
        #for obj in self.object_list:
            if not any(d['ObjectUUID'] == obj['ObjectUUID'] for d in obj_list):
                obj_list.append(obj)
        
        # Add sm_list(sm+storage) to obj_list 
        for num, obj in enumerate(obj_list):
            
            #Prepare storage method list
            sm_objs = []

            #current_mediumid_search = self.dt_data['sSearch_%s' % '4']
            current_mediumid_search = self.dt_data.get('sSearch_%s' % '4','xxx')
            logger.debug('col4 serach: %s' % current_mediumid_search)

            # Check whether the criteria for replacement of media target prefix is met
            if len(current_mediumid_search) == 8 and current_mediumid_search.startswith('-') and current_mediumid_search.__contains__('+'):
                media_target_replace_flag = 1
                # add corresponding new target medium prefix
                sm_obj = sm()
                sm_obj.id = 1
                sm_obj.status = 1
                sm_obj.type = 300
                sm_obj.target = current_mediumid_search[5:8]
                sm_objs.append(sm_obj)
                # add old target medium prefix
                sm_obj = sm()
                sm_obj.id = 2
                sm_obj.status = 0 # Set status to 0 for SM when items on this target medium is replaced
                sm_obj.type = 300
                sm_obj.target = current_mediumid_search[1:4]
                sm_objs.append(sm_obj)
            else:
                media_target_replace_flag = 0    
                for i in [1,2,3,4]:
                    sm_obj = sm()
                    sm_obj.id = i
                    sm_obj.status = obj['PolicyId__sm_%s' % i]
                    sm_obj.type = obj['PolicyId__sm_type_%s' % i]
                    #sm_obj.format = getattr(ep_obj,'sm_format_%s' % i)
                    #sm_obj.blocksize = getattr(ep_obj,'sm_blocksize_%s' % i)
                    #sm_obj.maxCapacity = getattr(ep_obj,'sm_maxCapacity_%s' % i)
                    #sm_obj.minChunkSize = getattr(ep_obj,'sm_minChunkSize_%s' % i)
                    #sm_obj.minContainerSize = getattr(ep_obj,'sm_minContainerSize_%s' % i)
                    #sm_obj.minCapacityWarning = getattr(ep_obj,'sm_minCapacityWarning_%s' % i)
                    sm_obj.target = obj['PolicyId__sm_target_%s' % i]
                    sm_objs.append(sm_obj)
                            
            sm_list = []
            if media_target_replace_flag:
                storage_list = []
                
            for sm_obj in sm_objs:
                storage_list = []
                if sm_obj.status == 1:
                    for d in self.object_list_with_writetapes:
                        if d['storage__storageMediumUUID__storageMediumID'] is not None:
                            if (sm_obj.type in range(300,330) and
                                d['storage__storageMediumUUID__storageMediumID'].startswith(sm_obj.target) and
                                d['ObjectUUID'] == obj['ObjectUUID']
                                ) or\
                                (media_target_replace_flag and sm_obj.type == 300 and
                                d['storage__storageMediumUUID__storageMediumID'].startswith(current_mediumid_search[1:4]) and
                                d['ObjectUUID'] == obj['ObjectUUID']
                                ) or\
                               (sm_obj.type == 200 and
                                d['storage__storageMediumUUID__storageMediumID'] == 'disk' and
                                d['ObjectUUID'] == obj['ObjectUUID']
                                ):
                                    storage_list.append({'storageMediumUUID__storageMediumID': d['storage__storageMediumUUID__storageMediumID'],
                                                         #'storageMediumUUID__storageMedium': sm_obj.type,
                                                         #'storageMediumUUID__storageMediumDate': d['storage__storageMediumUUID__storageMediumDate'],
                                                         'storageMediumUUID__CreateDate': d['storage__storageMediumUUID__CreateDate'],
                                                         'contentLocationValue': d['storage__contentLocationValue'],
                                                         'ObjectUUID__ObjectIdentifierValue': obj['ObjectIdentifierValue'],
                                                         'ObjectUUID__ObjectUUID': obj['ObjectUUID'],
                                                         })
                                    #print 'd - storage__storageMediumUUID__storageMediumID: %s' % d['storage__storageMediumUUID__storageMediumID']
                                    #print 'o - storage__storageMediumUUID__storageMediumID: %s' % obj['storage__storageMediumUUID__storageMediumID']
                    #print 'ObjectUUID: %s, target:%s , s_count:%s' % (obj['ObjectUUID'],sm_obj.target,len(storage_list))
                    sm_list.append({'id': sm_obj.id,
                                    'status': sm_obj.status,
                                    #'type': sm_obj.type,
                                    'target': sm_obj.target,
                                    'storage_list': storage_list})
                
            for x in sm_list:
                logger.debug('sm_list_x: %s' % repr(x))

            obj_list[num]['sm_list'] = sm_list
        
        # Create redundant storage list
        redundant_storage_list = {}
        for obj in obj_list:
            for sm_obj in obj['sm_list']:
                active_storage_obj = None
                if len(sm_obj['storage_list']) > 1:
                    #print '##################################################################################### %s, count:%s' % (sm_obj['storage_list'],len(sm_obj['storage_list']))
                    for storage_obj in sm_obj['storage_list']:
                        if active_storage_obj is None:
                            active_storage_obj = storage_obj
                        #elif storage_obj['storageMediumUUID__storageMediumDate'] > active_storage_obj['storageMediumUUID__storageMediumDate']:
                        elif storage_obj['storageMediumUUID__CreateDate'] > active_storage_obj['storageMediumUUID__CreateDate']:
                            active_storage_obj = storage_obj
                    for storage_obj in sm_obj['storage_list']:
                        #if storage_obj['storageMediumUUID__storageMediumDate'] < active_storage_obj['storageMediumUUID__storageMediumDate']:
                        if storage_obj['storageMediumUUID__CreateDate'] < active_storage_obj['storageMediumUUID__CreateDate']:
                            if not storage_obj['storageMediumUUID__storageMediumID'] in redundant_storage_list.keys():
                                redundant_storage_list[storage_obj['storageMediumUUID__storageMediumID']] = []
                            redundant_storage_list[storage_obj['storageMediumUUID__storageMediumID']].append(storage_obj)
        
        logger.debug('redundant_storage_list: %s' % repr(redundant_storage_list))

        # Create deactivate_media_list and need_to_migrate_dict
        deactivate_media_list = []
        need_to_migrate_list = []
        #need_to_migrate_dict = {}
        for storageMediumID in redundant_storage_list.keys():
            storage_list = storage.objects.exclude(storageMediumUUID__storageMediumStatus=0).filter(storageMediumUUID__storageMediumID=storageMediumID).values('storageMediumUUID__storageMediumID',
                                                                                                          #'storageMediumUUID__storageMedium',
                                                                                                          #'storageMediumUUID__storageMediumDate',
                                                                                                          'storageMediumUUID__CreateDate',
                                                                                                          'contentLocationValue',
                                                                                                          'ObjectUUID__ObjectIdentifierValue',
                                                                                                          'ObjectUUID__ObjectUUID',
                                                                                                          )
            storage_list2 = list(storage_list)
            for storage_values in storage_list:
                #print 'storage_list_len loop: %s' % len(storage_list)
                for redundant_storage_values in redundant_storage_list[storageMediumID]:
                    if storage_values == redundant_storage_values:
                        #print 'yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyfound ObjectUUID: %s, storageMediumID: %s, contentLocationValue: %s' % (redundant_storage_values['ObjectUUID__ObjectUUID'],storageMediumID,redundant_storage_values['contentLocationValue'])
                        #print 'storage_list2_len before: %s' % len(storage_list2)
                        #print 'storage_values: %s' % storage_values
                        if storage_values in storage_list2:
                            storage_list2.remove(storage_values)
                            #print 'remove %s' % storage_values
                        #else:
                            #print '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!not found!, skip remove %s' % storage_values
                        #print 'storage_list2_len after: %s' % len(storage_list2)
                        #pass
            if len(storage_list2) == 0:
                #deactivate_media_list.append([storageMediumID])
                deactivate_media_list.append(['','','','',storageMediumID,'','','','','','','','','','','',''])
            else:
                #need_to_migrate_dict[storageMediumID] = storage_list2
                for m in storage_list2:
                    tmp_list = []
                    keys = ['storageMediumUUID__storageMediumID',
                          #'storageMediumUUID__storageMedium',
                          #'storageMediumUUID__storageMediumDate',
                          'storageMediumUUID__CreateDate',
                          'contentLocationValue',
                          'ObjectUUID__ObjectIdentifierValue',
                          'ObjectUUID__ObjectUUID']
                    for key in keys:
                        tmp_list.append(m[key])
                    need_to_migrate_list.append(tmp_list)
                                               
        #print '#####################################obj_list: %s count: %s' % (obj_list,len(obj_list))
        #print '*************************************redundant_list: %s count: %s' % (redundant_storage_list,len(redundant_storage_list))
        #print '*************************************redundant_list: %s count: %s, storage_count: %s' % (redundant_storage_list,len(redundant_storage_list),len(redundant_storage_list['ESA001']))
        #deactivate_media_list.append(['ESA001'])
        #print 'deactivate_media_list: %s' % deactivate_media_list
        #print 'need_to_migrate_list: %s' % need_to_migrate_list
        return deactivate_media_list, need_to_migrate_list
        

    def render_to_response(self, form, **kwargs):
        '''Render Datatables expected JSON format'''
        page = self.get_page(form)
        #print 'page_type_object_list: %s' % type(page.object_list)
        page.object_list = get_object_list_display(page.object_list, self.field_choices_dict)
        deactivate_media_list, need_to_migrate_list = self.get_deactivate_list()
        data = {
            'iTotalRecords': page.paginator.count,
            'iTotalDisplayRecords': page.paginator.count,
            'sEcho': form.cleaned_data['sEcho'],
            'aaData': self.get_rows(page.object_list),
            'deactivate_media_list': deactivate_media_list,
            'need_to_migrate_list': need_to_migrate_list,
        }
        return self.json_response(data)

class DeactivateMedia(FormView):
    template_name = 'administration/migreq_create.html'
    form_class = DeactivateMediaForm
    success_url = '/'

    @method_decorator(permission_required('essarch.add_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(DeactivateMedia, self).dispatch( *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            if request.is_ajax():
                return HttpResponseBadRequest()
            else:
                return self.form_invalid(form)
    
    def form_valid(self, form):
        timestamp_utc = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        timestamp_dst = timestamp_utc.astimezone(timezone.get_default_timezone())
        logger = logging.getLogger('essarch.storagemaintenance')
        ReqPurpose = form.cleaned_data['ReqPurpose']
        if self.request.is_ajax():
            MediumList = []
            for o in json.loads(form.cleaned_data['MediumList']):
                MediumList.append(o[0])
        else:
            MediumList = form.cleaned_data['MediumList'].split(' ')
        #print 'MediumList: %s' % MediumList
        storageMedium_objs = storageMedium.objects.filter(storageMediumID__in=MediumList)
        #print len(storageMedium_objs)
        for storageMedium_obj in storageMedium_objs:
            storageMedium_obj.storageMediumStatus =  0
            storageMedium_obj.LocalDBdatetime = timestamp_utc
            storageMedium_obj.save(update_fields=['storageMediumStatus','LocalDBdatetime'])
            event_info = 'Setting mediumstatus to inactive for media: %s, ReqPurpose: %s' % (storageMedium_obj.storageMediumID,ReqPurpose)
            logger.info(event_info)
            ESSPGM.Events().create('2090','','Storage maintenance',__version__,'0',event_info,2,storageMediumID=storageMedium_obj.storageMediumID)
            if ExtDBupdate:
                ext_res,ext_errno,ext_why = ESSMSSQL.DB().action('storageMedium','UPD',('storageMediumStatus',storageMedium_obj.storageMediumStatus),
                                                                                                                                ('storageMediumID',storageMedium_obj.storageMediumID))
                if ext_errno: logger.error('Failed to update External DB: ' + str(storageMedium_obj.storageMediumID) + ' error: ' + str(ext_why))
                else:
                    storageMedium_obj.ExtDBdatetime = timestamp_utc
                    storageMedium_obj.save(update_fields=['ExtDBdatetime'])            
        if self.request.is_ajax():
            '''Render Datatables expected JSON format'''
            data = {
                'sEcho': 'OK',
            }
            return self.json_response(data)
        else:
            return super(DeactivateMedia, self).form_valid(form)

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
        context['label'] = 'ADMINISTRATION - Storage Migration  list'
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
        context['label'] = 'ADMINISTRATION - Storage Mainenance request'
        context['MigrationReqType_CHOICES'] = dict(MigrationReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class MigrationCreate(CreateView):
    model = MigrationQueue
    template_name = 'administration/migreq_create.html'
    form_class = MigrationQueueForm
    obj_list = None
    target_list = None
    copy_only_flag = None

    @method_decorator(permission_required('essarch.add_migrationqueue'))
    def dispatch(self, *args, **kwargs):
        return super(MigrationCreate, self).dispatch( *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handles POST requests, instantiating a form instance with the passed
        POST variables and then checked for validity.
        """
        logger = logging.getLogger('essarch.storagemaintenance')
        print("hit kom vi")
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():

            # Convert ObjectIdentifierValue to list
            obj_list = self.request.POST.get('ObjectIdentifierValue','')
            if request.is_ajax():
                self.obj_list = []
                try:
                    for o in json.loads(obj_list):
                        self.obj_list.append(o[1])
                except ValueError,detail:
                    logger.warning('Problem to parse json: %s, detail:%s' % (obj_list,detail))    
                #self.obj_list = obj_list.split('\r\n')[:-1]
                #print 'self.obj_list: %s' % self.obj_list
                #return HttpResponseBadRequest()
            else:
                self.obj_list = obj_list.split(' ')
            # Convert TargetMediumID to list and remove "+" ## Convert to checkbox answer.
            target_list = self.request.POST.get('TargetMediumID',None)
            self.target_list = target_list.split(' ')
            for c, target_item in enumerate(self.target_list):
                if target_item.startswith('+'):
                    self.target_list[c] = target_item[1:]

#            # Copy OnlyFlag       
#           self.copy_only_flag = self.request.POST.get('CopyOnlyFlag', None)
#           print 'copy_only_flag: %s %s' % (str(self.copy_only_flag), type(self.copy_only_flag))

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
        initial['CopyOnlyFlag'] = self.request.GET.get('CopyOnlyFlag')
        #if initial['ReqType'] == 1:
        #    migration_path = Path.objects.get(entity='path_control').value
        #initial['Path'] = self.request.GET.get('Path', migration_path)
        #if 'ip_uuid' in self.kwargs:
        #    initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        #print( self.object.CopyOnlyFlag)
        self.object.pk = None 
        self.object.user = self.request.user.username
        self.object.ObjectIdentifierValue = self.obj_list
        self.object.TargetMediumID = self.target_list
        self.object.ReqUUID = uuid.uuid1()
        #self.object.CopyOnlyFlag = self.copy_only_flag
        self.object.CopyOnlyFlag = form.cleaned_data.get('CopyOnlyFlag',False)
        print 'copy_only_flagrrr: %s %s' % (str(form.cleaned_data.get('CopyOnlyFlag',False)), type(form.cleaned_data.get('CopyOnlyFlag',False)))
        #print 'copy_only_flagrrr: %s %s' % (str(form.cleaned_data('CopyOnlyFlag',False)), type(form.cleaned_data('CopyOnlyFlag',False)))
        self.object.save()
        req_pk = self.object.pk
        print(self.object)
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

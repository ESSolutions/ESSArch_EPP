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
from django.db import utils
from operator import or_, and_

from essarch.models import ArchiveObject, robot, robotQueue, robotQueueForm, robotQueueFormUpdate, RobotReqType_CHOICES, \
                                        MigrationQueue, MigrationReqType_CHOICES, MigrationQueueForm, MigrationQueueFormUpdate, DeactivateMediaForm
                           
from Storage.models import storage, storageMedium, ReqStatus_CHOICES, MediumType_CHOICES, MediumStatus_CHOICES,\
                                        MediumLocationStatus_CHOICES, MediumFormat_CHOICES, MediumBlockSize_CHOICES

from configuration.models import sm, DefaultValue, ESSConfig, ArchivePolicy

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

from essarch.libs import DatatablesViewEss, DatatablesForm, get_field_choices, get_object_list_display

import uuid, ESSPGM, ESSMSSQL, logging, datetime, pytz

try:
    ExtDBupdate = int(ESSConfig.objects.get(Name='ExtDBupdate').Value)
except (ESSConfig.DoesNotExist, utils.ProgrammingError, utils.OperationalError) as e:
    ExtDBupdate = 0

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
        #content_list = storage.objects.filter(storagemedium__storageMediumID=storageMediumID).order_by('id')
        content_list = storage.objects.filter(storagemedium__storageMediumID=storageMediumID).extra(
                                                                     select={'contentLocationValue_int': 'CAST(contentLocationValue AS UNSIGNED)'}
                                                                     ).order_by('-contentLocationValue_int')
        context['content_list'] = content_list
        context['label'] = 'Detail information - storage medium'
        context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        context['MediumFormat_CHOICES'] = dict(MediumFormat_CHOICES)
        context['MediumBlockSize_CHOICES'] = dict(MediumBlockSize_CHOICES)
        return context

class storageDatatablesView(DatatablesViewEss):
    model = storage
    fields = (
        "archiveobject__ObjectIdentifierValue",
        "contentLocationValue",
    )

    def get_queryset(self):
        '''Apply search filter to QuerySet'''
        qs = super(storageDatatablesView, self).get_queryset()
        storageMediumID = self.request.GET.get('storageMediumID',None)
        if storageMediumID:
            qs = qs.filter(storagemedium__storageMediumID=storageMediumID)
        return qs

    def sort_col_qs_1(self, direction, queryset):
        '''sort for col_1'''
        queryset = queryset.extra(select={'contentLocationValue_int': 'CAST(`contentLocationValue` AS UNSIGNED)'})
        orders = ('%scontentLocationValue_int' % direction)
        return orders, queryset

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

class storageMediumDatatablesView(DatatablesViewEss):
    model = storageMedium
    fields = (
        "storageMediumUUID",
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

class StorageMigration(TemplateView):
    template_name = 'administration/storagemigration.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(StorageMigration, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(StorageMigration, self).get_context_data(**kwargs)
        context['label'] = 'ADMINISTRATION - Storage Migration'
        context['DefaultValue'] = dict(DefaultValue.objects.filter(entity__startswith='administration_storagemigration').values_list('entity','value'))
        return context

class StorageMigrationDatatablesView(DatatablesViewEss):
    model = ArchiveObject
    #queryset = ArchiveObject.objects.filter(StatusProcess=3000, StatusActivity=0).all()

    fields = (
        'ObjectIdentifierValue',
        'ObjectUUID',
        'StatusProcess',
        'StatusActivity',
        'ObjectActive',
        'Storage_set__storagemedium__storageMediumID',
        'Storage_set__contentLocationValue',     
        'PolicyId__PolicyName',
        'PolicyId__PolicyID',
        'PolicyId__PolicyStat', 
        'Storage_set__storagemedium__storagetarget__name',
        'Storage_set__storagemedium__storagetarget__target',

        'Storage_set__storagemedium__CreateDate',
        'Storage_set__storagemedium__storageMediumStatus',
    )   

    def process_dt_response(self, data):
        self.form = DatatablesForm(data)
        if self.form.is_valid():
            self.object_list_with_writetapes = self.get_queryset().extra(
                  where=["NOT `Storage_storagemedium`.`storageMediumStatus` = %s"],params=['0']).values(
                  *self.get_db_fields()).filter(StatusProcess=3000, StatusActivity=0)
            self.object_list = []
            for obj in self.object_list_with_writetapes:
                if not obj['Storage_set__storagemedium__storageMediumStatus'] == 20:
                    self.object_list.append(obj)
            self.field_choices_dict = get_field_choices(self.get_queryset()[:1], self.get_db_fields())
            return self.render_to_response(self.form)
        else:
            return HttpResponseBadRequest()

    def sort_col_qs_5(self, direction, queryset):
        '''sort for col_6'''
        queryset = queryset.extra(select={'contentLocationValue_int': 'CAST(`Storage_storage`.`contentLocationValue` AS UNSIGNED)'})
        orders = ('%sStorage_set__storagemedium__storageMediumID' % direction, '%scontentLocationValue_int' % direction)
        return orders, queryset

    def sort_col_qs_6(self, direction, queryset):
        '''sort for col_7'''
        queryset = queryset.extra(select={'contentLocationValue_int': 'CAST(`Storage_storage`.`contentLocationValue` AS UNSIGNED)'})
        orders = ('%scontentLocationValue_int' % direction, '%sStorage_set__storagemedium__storageMediumID' % direction)
        return orders, queryset

    def search_col_5(self, search, queryset):
        idx=5
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

    def search_col_6(self, search, queryset):
        '''exclude filter for search terms'''
        #print 'search: %s' % search
        for term in search.split():
            #print 'term: %s' % term
            exclude_list = []
            if term.startswith('/'):
                #print 'term/: %s' % term
                #print 'exclude_list_before: %s' % exclude_list
                for x in storage.objects.filter(contentLocationValue = term, archiveobject__isnull=False).values_list('archiveobject', flat=True):
                    exclude_list.append(x)
                #print 'exclude_list_after: %s' % exclude_list
            else:
                for x in storage.objects.filter(storagemedium__storageMediumID__startswith = term, archiveobject__isnull=False).values_list('archiveobject', flat=True):
                    exclude_list.append(x)
            search2 = Q(ObjectUUID__in = exclude_list)
            queryset = queryset.exclude(search2)
        return queryset
    
class TargetPrePopulation(View):

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(TargetPrePopulation, self).dispatch( *args, **kwargs)
        
    def get_enabled_policies(self, *args, **kwargs):
        policy_selection_list =[]
        ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1)
        for ArchivePolicy_obj in ArchivePolicy_objs:
            targetlist = []
            sm_objs = ArchivePolicy_obj.storagemethod_set.filter(status=1, type=300)
            for sm_obj in sm_objs:
                st_objs = sm_obj.storagetarget_set.filter(status__in=[1, 3])
                sm_targetdict = {}
                sm_write_target = ''
                sm_migrate_target = ''
                for st_obj in st_objs:
                    if not sm_write_target and st_obj.status==1:
                        if st_obj.target.status == 1:
                            target_obj = st_obj.target
                            sm_write_target=target_obj.target
                    elif not sm_migrate_target and st_obj.status==3:
                        if st_obj.target.status == 1:
                            target_obj = st_obj.target
                            sm_migrate_target=target_obj.target            
                sm_targetdict[sm_write_target] = sm_migrate_target
                targetlist.append(sm_targetdict)

            Policy ={}
            Policy['PolicyID'] = ArchivePolicy_obj.PolicyID
            Policy['PolicyName'] =  ArchivePolicy_obj.PolicyName
            Policy['targetlist'] = targetlist
            policy_selection_list.append(Policy)
        
        return policy_selection_list  

    def json_response(self, request):
        
        data = self.get_enabled_policies()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            content_type='application/json'
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

#import time     
#from memory_profiler import profile

class StorageMaintenanceDatatablesView(StorageMigrationDatatablesView):

#    @profile
    def get_deactivate_list(self):
        #start = time.time()
        #print '################# step 1 ###############################'
        logger = logging.getLogger('essarch.storagemaintenance')

        ObjectActive_filter = self.dt_data.get('sSearch_%s' % '4','')
        logger.debug('col4 serach: %s' % ObjectActive_filter)

        current_mediumid_search = self.dt_data.get('sSearch_%s' % '5','xxx')
        logger.debug('col5 serach: %s' % current_mediumid_search)

        policy_sm_objs_dict = {}

        obj_list = []
        obj_dict = {}
            
        #print '############ obj_dict len: %s' % len(obj_dict)

        # Check whether the criteria for replacement of media target prefix is met
        if len(current_mediumid_search) == 8 and current_mediumid_search.startswith('-') and current_mediumid_search.__contains__('+'):
            media_target_replace_flag = 1
        else:
            media_target_replace_flag = 0
            
        for obj in self.object_list_with_writetapes:
            try:
                obj_dict[obj['ObjectUUID']]
            except KeyError:
                obj_dict[obj['ObjectUUID']] = obj        

            ###############################
            # Prepare storage method list
            sm_objs = []

            # if replacement of media target prefix is met force sm_objs
            if media_target_replace_flag == 1:
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
                if not obj['PolicyId__PolicyID'] in policy_sm_objs_dict.keys():
                    ArchivePolicy_obj = ArchivePolicy.objects.get(PolicyID = obj['PolicyId__PolicyID'])
                    StorageMethod_objs = ArchivePolicy_obj.storagemethod_set.filter(status=1)
                    for StorageMethod_obj in StorageMethod_objs:
                        st_objs = StorageMethod_obj.storagetarget_set.filter(status=1)
                        if st_objs.count() == 1:
                            st_obj = st_objs[0]
                        elif st_objs.count() == 0:
                            logger.error('The storage method %s has no enabled target configured' % StorageMethod_obj.name)
                            continue
                        elif st_objs.count() > 1:
                            logger.error('The storage method %s has too many targets configured with the status enabled' % StorageMethod_obj.name)
                            continue
                        if st_obj.target.status == 1:
                            target_obj = st_obj.target
                        else:
                            logger.error('The target %s is disabled' % st_obj.target.name)
                            continue
                        sm_obj = sm()
                        sm_obj.id = StorageMethod_obj.id
                        sm_obj.status = st_obj.status
                        sm_obj.type = target_obj.type
                        sm_obj.target = target_obj.target
                        sm_objs.append(sm_obj)
                    policy_sm_objs_dict[obj['PolicyId__PolicyID']] = sm_objs
                else:
                    sm_objs = policy_sm_objs_dict[obj['PolicyId__PolicyID']]

            ###############################
            # Add storage_list to sm_objs
            if not 'sm_list' in obj_dict[obj['ObjectUUID']].keys():
                obj_dict[obj['ObjectUUID']]['sm_list'] = {}
                
            for sm_obj in sm_objs:
                if not sm_obj.id in obj_dict[obj['ObjectUUID']]['sm_list'].keys():
                    obj_dict[obj['ObjectUUID']]['sm_list'][sm_obj.id] = {'id': sm_obj.id,
                                    'status': sm_obj.status,
                                    #'type': sm_obj.type,
                                    'target': sm_obj.target,
                                    'storage_list': []}
                
                if sm_obj.status == 1: # StorageTarget_Status_CHOICES = (0, 'Disabled'), (1, 'Enabled'), (2, 'ReadOnly'), (3, 'Migrate')
                    if obj['Storage_set__storagemedium__storageMediumID'] is not None:
                        if (sm_obj.type in range(300,330) and
                            obj['Storage_set__storagemedium__storageMediumID'].startswith(sm_obj.target) and
                            obj['ObjectUUID'] == obj_dict[obj['ObjectUUID']]['ObjectUUID']
                            ) or\
                            (media_target_replace_flag and sm_obj.type == 300 and
                            obj['Storage_set__storagemedium__storageMediumID'].startswith(current_mediumid_search[1:4]) and
                            obj['ObjectUUID'] == obj_dict[obj['ObjectUUID']]['ObjectUUID']
                            ) or\
                           (sm_obj.type == 200 and
                            obj['Storage_set__storagemedium__storageMediumID'] == 'disk' and
                            obj['ObjectUUID'] == obj_dict[obj['ObjectUUID']]['ObjectUUID']
                            ):
                                obj_dict[obj['ObjectUUID']]['sm_list'][sm_obj.id]['storage_list'].append({
                                                     'storagemedium__storageMediumID': obj['Storage_set__storagemedium__storageMediumID'],
                                                     'storagemedium__CreateDate': obj['Storage_set__storagemedium__CreateDate'],
                                                     'contentLocationValue': obj['Storage_set__contentLocationValue'],
                                                     'archiveobject__ObjectIdentifierValue': obj_dict[obj['ObjectUUID']]['ObjectIdentifierValue'],
                                                     'archiveobject__ObjectUUID': obj_dict[obj['ObjectUUID']]['ObjectUUID'],
                                                     })
                                    #print 'd - storage__storageMediumUUID__storageMediumID: %s' % d['storage__storageMediumUUID__storageMediumID']
                                    #print 'o - storage__storageMediumUUID__storageMediumID: %s' % obj['storage__storageMediumUUID__storageMediumID']
                    #print 'ObjectUUID: %s, target:%s , s_count:%s' % (obj['ObjectUUID'],sm_obj.target,len(storage_list))
                
            for x in obj_dict[obj['ObjectUUID']]['sm_list'].values():
                logger.debug('sm_list_y: %s' % repr(x))

        #end = time.time()                
        #print '################# step 3 ###############################: %s' % (end - start)

        ###############################        
        # Create redundant storage list
        redundant_storage_list = {}
        newly_added_IP_storage_list = {} # We maybe want to use this list to exclude newly added IPs to storage....
        for obj in obj_dict.values():
            #print 'obj: %s' % repr(obj)
            #for sm_obj in obj['sm_list']:
                #print '##################################################################################### %s, count:%s' % (sm_obj['storage_list'],len(sm_obj['storage_list']))
            for sm_obj in obj['sm_list'].values():
                #print '##################################################################################### %s, count:%s' % (sm_obj['storage_list'],len(sm_obj['storage_list']))
                active_storage_obj = None
                if len(sm_obj['storage_list']) > 1:
                    #print '##################################################################################### %s, count:%s' % (sm_obj['storage_list'],len(sm_obj['storage_list']))
                    for storage_obj in sm_obj['storage_list']:
                        if active_storage_obj is None:
                            active_storage_obj = storage_obj
                        elif storage_obj['storagemedium__CreateDate'] > active_storage_obj['storagemedium__CreateDate']:
                            active_storage_obj = storage_obj
                    for storage_obj in sm_obj['storage_list']:
                        # Add the storage_obj with oldest storagemedium__CreateDate to redundant_storage_list
                        if storage_obj['storagemedium__CreateDate'] < active_storage_obj['storagemedium__CreateDate']:
                            if not storage_obj['storagemedium__storageMediumID'] in redundant_storage_list.keys():
                                redundant_storage_list[storage_obj['storagemedium__storageMediumID']] = []
                            redundant_storage_list[storage_obj['storagemedium__storageMediumID']].append(storage_obj)
                # if replacement of media target prefix is met and target prefix is current active media prefix, add this sm_obj as newly added IP that was not migrated
                elif media_target_replace_flag == 1 and len(sm_obj['storage_list']) == 1:
                    storage_obj = sm_obj['storage_list'][0]
                    if storage_obj['storagemedium__storageMediumID'].startswith(current_mediumid_search[5:8]):
                        if not storage_obj['storagemedium__storageMediumID'] in newly_added_IP_storage_list.keys():
                            newly_added_IP_storage_list[storage_obj['storagemedium__storageMediumID']] = []
                        newly_added_IP_storage_list[storage_obj['storagemedium__storageMediumID']].append(storage_obj)
        
        logger.debug('redundant_storage_list: %s' % repr(redundant_storage_list))
        logger.debug('newly_added_IP_storage_list: %s' % repr(newly_added_IP_storage_list))

        #print '################# step 4 ###############################'

        ###############################
        # Create deactivate_media_list and need_to_migrate_dict
        deactivate_media_list = []
        need_to_migrate_list = []
        #need_to_migrate_dict = {}
        for storageMediumID in redundant_storage_list.keys():
            if ObjectActive_filter:
                storage_list = storage.objects.exclude(storagemedium__storageMediumStatus=0).filter(storagemedium__storageMediumID=storageMediumID, archiveobject__ObjectActive=ObjectActive_filter).values('storagemedium__storageMediumID',
                                                                                                          'storagemedium__CreateDate',
                                                                                                          'contentLocationValue',
                                                                                                          'archiveobject__ObjectIdentifierValue',
                                                                                                          'archiveobject__ObjectUUID',
                                                                                                          )
            else:
                storage_list = storage.objects.exclude(storagemedium__storageMediumStatus=0).filter(storagemedium__storageMediumID=storageMediumID).values('storagemedium__storageMediumID',
                                                                                                          'storagemedium__CreateDate',
                                                                                                          'contentLocationValue',
                                                                                                          'archiveobject__ObjectIdentifierValue',
                                                                                                          'archiveobject__ObjectUUID',
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
                #for newly_added_IP_storage_values in newly_added_IP_storage_list[storageMediumID]:
                #    if storage_values == newly_added_IP_storage_values:
                #        if storage_values in storage_list2:
                #            storage_list2.remove(storage_values)                        
            if len(storage_list2) == 0:
                deactivate_media_list.append(['','','','',storageMediumID,'','','','','','','','','','','',''])
            else:
                #need_to_migrate_dict[storageMediumID] = storage_list2
                for m in storage_list2:
                    tmp_list = []
                    keys = ['storagemedium__storageMediumID',
                          'storagemedium__CreateDate',
                          'contentLocationValue',
                          'archiveobject__ObjectIdentifierValue',
                          'archiveobject__ObjectUUID']
                    for key in keys:
                        tmp_list.append(m[key])
                    need_to_migrate_list.append(tmp_list)
        
        #print '################# step 5 ###############################'                            
        
        #print '*************************************redundant_list: %s count: %s' % (redundant_storage_list,len(redundant_storage_list))
        #print '*************************************redundant_list: %s count: %s, storage_count: %s' % (redundant_storage_list,len(redundant_storage_list),len(redundant_storage_list['ESA001']))
        #deactivate_media_list.append(['ESA001'])
        #print 'deactivate_media_list: %s' % deactivate_media_list
        #print 'need_to_migrate_list: %s' % need_to_migrate_list
        return deactivate_media_list, need_to_migrate_list
        
    def render_to_response(self, form, **kwargs): #Paginator
        '''Render Datatables expected JSON format'''
        page = self.get_page(form)
        #print 'page_type_object_list: %s' % type(page.object_list)
        page.object_list = get_object_list_display(page.object_list, self.field_choices_dict)
        deactivate_media_list, need_to_migrate_list = self.get_deactivate_list()
        data = {
            'iTotalRecords': page.paginator.count,
            'iTotalDisplayRecords': page.paginator.count,
            'sEcho': form.cleaned_data['sEcho'],
            #'aaData': self.get_rows(page.object_list),
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
        
        robotMediumList = robot.objects.filter(t_id__in=MediumList)
        for media in robotMediumList:
            media.status = 'Inactive'
            media.save(update_fields=['status'])
            event_info_robot = 'Setting status to Inactive for media: %s, ReqPurpose: %s' % (media.t_id,ReqPurpose)
            logger.info(event_info_robot)
            
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
            content_type='application/json'
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
        #print 'copy_only_flagrrr: %s %s' % (str(form.cleaned_data.get('CopyOnlyFlag',False)), type(form.cleaned_data.get('CopyOnlyFlag',False)))
        #print 'copy_only_flagrrr: %s %s' % (str(form.cleaned_data('CopyOnlyFlag',False)), type(form.cleaned_data('CopyOnlyFlag',False)))
        self.object.save()
        req_pk = self.object.pk
        #print(self.object)
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
            content_type='application/json'
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
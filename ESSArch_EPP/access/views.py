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
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.http import HttpResponseRedirect

from essarch.models import AccessQueue, AccessQueueForm, AccessQueueFormUpdate, ArchiveObject, ArchiveObjectData, ArchiveObjectRel, PackageType_CHOICES, StatusProcess_CHOICES, ReqStatus_CHOICES, AccessReqType_CHOICES
from configuration.models import Path, DefaultValue, Parameter

from django.views.generic.detail import DetailView
from django.views.generic import ListView, TemplateView,View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest

from essarch.libs import DatatablesViewEss
import datetime, time

import uuid, os.path as op

class AccessListInfoView(View):

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessListInfoView, self).dispatch( *args, **kwargs)

    def get_access_listinfo(self, *args, **kwargs):
        AICs_to_access = ArchiveObject.objects.filter(StatusProcess=3000) #filter(Q(StatusProcess=3000) | Q(OAISPackageType=1))
        AIC_list = []
        for obj in AICs_to_access:
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID, UUID__StatusProcess=3000)
            if len(AIC_IPs_query) > 0:
                AIC = {}
                AIC['AIC_UUID'] =(str(obj.ObjectUUID))
                AIC_IPs = []
                for ip in AIC_IPs_query:
                    datainfo = ArchiveObjectData.objects.get(UUID=ip.UUID.ObjectUUID)
                    AIC_IP = {}
                    AIC_IP['id'] = ip.UUID.id
                    AIC_IP['ObjectUUID'] = str(ip.UUID.ObjectUUID)
                    AIC_IP['Archivist_organization'] = ip.UUID.EntryAgentIdentifierValue
                    AIC['Archivist_organization'] = ip.UUID.EntryAgentIdentifierValue
                    AIC_IP['Label'] = datainfo.label
                    AIC['Label'] = datainfo.label
                    AIC_IP['create_date'] = str(ip.UUID.EntryDate)[:10]
                    AIC['create_date'] = str(ip.UUID.EntryDate)[:10]
                    AIC_IP['Generation'] = ip.UUID.Generation
                    AIC_IP['startdate'] = str(datainfo.startdate)[:10]
                    AIC['startdate'] = str(datainfo.startdate)[:10]
                    AIC_IP['enddate'] = str(datainfo.enddate)[:10]
                    AIC['enddate'] = str(datainfo.enddate)[:10]
                    AIC_IP['Process'] = ip.UUID.StatusProcess
                    AIC_IP['Activity'] = ip.UUID.StatusActivity
                    AIC_IPs.append(AIC_IP)
                AIC['IPs'] = AIC_IPs
                AIC_list.append(AIC)
        return AIC_list

    def json_response(self, request):

        data = self.get_access_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):
        return self.json_response(request)

'''
class AccessListTemplateView(TemplateView):
    template_name = 'access/access_list.html'

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(AccessListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'ACCESS - List information packages'
        return context
'''

class AICCheckView(View):

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AICCheckView, self).dispatch( *args, **kwargs)

    def get_aic_check(self, *args, **kwargs):

        AICcheck = ArchiveObjectRel.objects.exists()
        #return AICcheck
        return AICcheck

    def json_response(self, request):

        data = self.get_aic_check()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):
        return self.json_response(request)

class ArchObjectList(TemplateView):
    #template_name = 'access/archiveobject_list.html'
    template_name = 'access/iplist.html'

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchObjectList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArchObjectList, self).get_context_data(**kwargs)
        context['label'] = 'ACCESS - List information packages'
        #context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        #context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        #context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        return context

class ArchObjectDatatablesView(DatatablesViewEss):
    model = ArchiveObject
    fields = (
        "id",
        "ObjectIdentifierValue",
        "Generation",    
        "EntryAgentIdentifierValue",
        "archiveobjectdata__label",
        "EntryDate",
        "archiveobjectdata__startdate",            
        "archiveobjectdata__enddate",            
        "OAISPackageType",
        "reluuid_set__AIC_UUID__ObjectIdentifierValue",
        #"reluuid_set__UUID__ObjectIdentifierValue",
        #"relaic_set__AIC_UUID__ObjectIdentifierValue",        
        "ObjectUUID",
        "StatusProcess",
        "StatusActivity",
    )

    def sort_col_9(self, direction):
        '''sort for col_9'''
        #return ('%sreluuid_set__AIC_UUID__ObjectIdentifierValue' % direction, '%sGeneration' % direction)
        #return ('%sid' % direction, '%sreluuid_set__AIC_UUID__ObjectIdentifierValue' % direction, '%sObjectUUID' % direction, '%sGeneration' % direction)
        #return ('%sGeneration' % direction, '%sreluuid_set__AIC_UUID__ObjectIdentifierValue' % direction, '%sObjectUUID' % direction )
        return ('%sid' % direction , '%sGeneration' % direction, '%sreluuid_set__AIC_UUID__ObjectIdentifierValue' % direction, '%sObjectUUID' % direction)

    def sort_col_9(self, direction):
        '''sort for col_10'''
        return ('%sid' % direction , '%sGeneration' % direction, '%sObjectUUID' % direction)
'''
class ArchObjectList2(ListView):
    """
    List ArchiveObject
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    #context_object_name='access_list'
    #queryset=ArchiveObject.objects.filter(StatusProcess=3000).order_by('id','Generation')
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=3000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchObjectList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArchObjectList, self).get_context_data(**kwargs)
        context['type'] = 'Access'
        context['label'] = 'ACCESS - List information packages'
        ip_list = []
        object_list = context['object_list']       
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=3000):
                ip_list.append(ip)
#                print '**********************ip_list:%s' % ip_list
#                print 'xxxxxxxxxxxxxxxxxxxxxx a:%s' % obj.ObjectUUID
#            #rel_obj_list = a.relaic_set.all().order_by('UUID__Generation')
#            rel_obj_list = a.reluuid_set.all()
#            #print 'rel_obj_list: %s' % rel_obj_list
#            if rel_obj_list:
#                #for rel_obj in a.relaic_set.all().order_by('UUID__Generation'):
#                for rel_obj in a.reluuid_set.all():
#                    #print 'rel_obj: %s' % rel_obj
#                    aic_obj = rel_obj.AIC_UUID
#                    ip_obj = rel_obj.UUID
#                    ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
#                    if ip_obj_data_list:
#                        ip_obj_data = ip_obj_data_list[0]
#                    else:
#                        ip_obj_data = None
#                    ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
#                    if ip_obj_metadata_list:
#                        ip_obj_metadata = ip_obj_metadata_list[0]
#                    else:
#                        ip_obj_metadata = None
#                    ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
#            else:
#                aic_obj = None
#                ip_obj = a
#                ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
#                if ip_obj_data_list:
#                    ip_obj_data = ip_obj_data_list[0]
#                else:
#                    ip_obj_data = None
#                ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
#                if ip_obj_metadata_list:
#                    ip_obj_metadata = ip_obj_metadata_list[0]
#                else:
#                    ip_obj_metadata = None
#                ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context
'''


class AccessList(ListView):
    """
    List AccessQueue
    """
    model = AccessQueue
    template_name='access/list.html'
    context_object_name='req_list'
    #queryset=AccessQueue.objects.filter(Status__lt=20)   # Status<20

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessList, self).get_context_data(**kwargs)
        context['label'] = 'ACCESS - List access request queue'
        context['AccessReqType_CHOICES'] = dict(AccessReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class AccessDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = AccessQueue
    context_object_name='access'
    template_name='access/detail.html'

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessDetail, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - access requests'
        context['AccessReqType_CHOICES'] = dict(AccessReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class AccessCreate(CreateView):
    model = AccessQueue
    template_name='access/create.html'
    form_class=AccessQueueForm

    @method_decorator(permission_required('essarch.add_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(AccessCreate, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        #initial['ReqType'] = self.request.GET.get('ReqType',4)
        default_ReqType = 5
        try:
            ReqType_obj = DefaultValue.objects.get(entity='access_new__ReqType')
        except DefaultValue.DoesNotExist:
            pass
        else:
            try:
                default_ReqType = int(ReqType_obj.value)
            except ValueError:
                pass
        initial['ReqType'] = self.request.GET.get('ReqType',default_ReqType)
        initial['ReqPurpose'] = self.request.GET.get('ReqPurpose') 
        if initial['ReqType'] == 5:
            access_path = Path.objects.get(entity='path_control').value
        else:
            path_work = Path.objects.get(entity='path_work').value
            access_path = op.join( op.join(path_work, self.request.user.username), 'access' )
        initial['Path'] = self.request.GET.get('Path', access_path)
        if 'ip_uuid' in self.kwargs:
            initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        return initial
    
    def get_context_data(self, **kwargs):
        context = super(AccessCreate, self).get_context_data(**kwargs)
        media_str = ''
        if 'ip_uuid' in self.kwargs:
            ip=ArchiveObject.objects.get(ObjectIdentifierValue=self.kwargs['ip_uuid'])
            media_list_tmp = ip.Storage_set.values_list('storagemedium__storageMediumID')
            media_list = [i[0] for i in media_list_tmp]
            media_str = ', '.join(media_list)
        context['media_list'] = media_str
        return context
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        num = 0
        for obj in form.instance.ObjectIdentifierValue.split():
            if form.instance.ReqType == 5 or form.instance.ReqType == '5':
                ip_obj = ArchiveObject.objects.get(ObjectIdentifierValue=obj)
                try:
                    aic_obj = ip_obj.reluuid_set.get().AIC_UUID
                except ObjectDoesNotExist: 
                    # if no AIC exists change ReqType to 3 and Path without AIC directory 
                    self.object.ReqType = 3
                    self.object.Path = form.instance.Path
                else:
                    self.object.Path = op.join(form.instance.Path, aic_obj.ObjectUUID)
            self.object.pk = None
            self.object.ObjectIdentifierValue = obj
            self.object.ReqUUID = uuid.uuid1()
            self.object.save()
            num += 1
        if num == 1:
            self.success_url = reverse_lazy('access_detail',kwargs={'pk': self.object.pk.hex})
        return super(AccessCreate, self).form_valid(form)
        
class AccessUpdate(UpdateView):
    model = AccessQueue
    template_name='access/update.html'
    form_class=AccessQueueFormUpdate
    
    @method_decorator(permission_required('essarch.change_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessUpdate, self).dispatch( *args, **kwargs)

class AccessDelete(DeleteView):
    model = AccessQueue
    template_name='access/delete.html'
    context_object_name='access'
    success_url = reverse_lazy('access_list')

    @method_decorator(permission_required('essarch.delete_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessDelete, self).dispatch( *args, **kwargs)

class AccessClearRequests(DeleteView):
    success_url = reverse_lazy('access_list')
    
    @method_decorator(permission_required('essarch.delete_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessClearRequests, self).dispatch( *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched objects and then
        redirects to the success URL.
        """
        self.object = None
        self.objects = AccessQueue.objects.filter(Status=20, user=self.request.user)
        self.objects.delete()
        return HttpResponseRedirect(self.success_url)
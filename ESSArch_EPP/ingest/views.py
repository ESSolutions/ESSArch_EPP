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
from django.shortcuts import get_object_or_404
from django.db.models import Q

from essarch.models import IngestQueue, IngestQueueForm, IngestQueueFormUpdate, ArchiveObject, \
                           ArchiveObjectData, ArchiveObjectRel, \
                           ArchiveObjectStatusForm, PackageType_CHOICES, StatusProcess_CHOICES, ReqStatus_CHOICES, IngestReqType_CHOICES

from django.views.generic import TemplateView, View
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseUpdateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required, login_required
from django.contrib.auth import authenticate
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse

import json
from django.core.serializers.json import DjangoJSONEncoder

import uuid, urlparse

class ArchObjectListUpdate(ListView, BaseUpdateView):
    model = ArchiveObject
    template_name='ingest/iplist_old.html'
    form_class=ArchiveObjectStatusForm
    queryset=ArchiveObject.objects.filter(Q(StatusProcess__lt=3000) | Q(OAISPackageType=1)).order_by('id','Generation')
    
    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchObjectListUpdate, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        context['object_list'] = self.get_queryset()
        context['type'] = 'Ingest'
        context['label'] = 'INGEST - List information packages'
        ip_list = []
        object_list = context['object_list']      
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess__lt=3000):
                # Create ip_form for ip_obj
                self.object = ip[1] # ip_obj
                ip_form_class = self.get_form_class()
                ip[2] = self.get_form(ip_form_class) # get form for ip_obj
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context
        
class IngestListInfoView(View):

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):    
        return super(IngestListInfoView, self).dispatch( *args, **kwargs)
        
    def get_ingest_listinfo(self, *args, **kwargs):
        AICs_in_ingestarea = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs_in_ingestarea:
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID, UUID__StatusProcess__lt=3000)
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
                    AIC_IP['create_date'] = ip.UUID.EntryDate
                    AIC['create_date'] = ip.UUID.EntryDate
                    AIC_IP['Generation'] = ip.UUID.Generation
                    AIC_IP['startdate'] = datainfo.startdate
                    AIC['startdate'] = datainfo.startdate
                    AIC_IP['enddate'] = datainfo.enddate
                    AIC['enddate'] = datainfo.enddate
                    AIC_IP['Process'] = ip.UUID.StatusProcess
                    AIC_IP['Activity'] = ip.UUID.StatusActivity
                    AIC_IPs.append(AIC_IP)
                AIC['IPs'] = AIC_IPs
                AIC_list.append(AIC)        
        return AIC_list
  
    def json_response(self, request):
        
        data = self.get_ingest_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class IngestIPListTemplateView(TemplateView):
    template_name = 'ingest/iplist.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestIPListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IngestIPListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'INGEST - List information packages'
        return context

class IngestList(ListView):
    """
    List IngestQueue
    """
    model = IngestQueue
    template_name='ingest/list.html'
    context_object_name='req_list'
    queryset=IngestQueue.objects.filter(Status__lt=20)   # Status<20

    @method_decorator(permission_required('essarch.list_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IngestList, self).get_context_data(**kwargs)
        context['label'] = 'INGEST - List ingest request queue'
        context['IngestReqType_CHOICES'] = dict(IngestReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class IngestDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = IngestQueue
    context_object_name='ingest'
    template_name='ingest/detail.html'

    @method_decorator(permission_required('essarch.list_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IngestDetail, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ingest requests'
        context['IngestReqType_CHOICES'] = dict(IngestReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class IngestCreate(CreateView):
    model = IngestQueue
    template_name='ingest/create.html'
    form_class=IngestQueueForm

    #@method_decorator(permission_required('essarch.add_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        username = self.request.GET.get('username', None)
        password = self.request.GET.get('password', None)
        if username and password:
            self.request.user = authenticate(username=username, password=password)
        if self.request.user is None:
            raise PermissionDenied
        if not self.request.user.has_perm('essarch.add_ingestqueue'):
            #raise PermissionDenied
            return redirect_to_login(self.request.get_full_path())
        return super(IngestCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(IngestCreate, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = self.request.GET.get('ReqType',1)
        qs = self.request.META.get('QUERY_STRING')
        try:
            initial['ReqPurpose'] = urlparse.parse_qs(qs).get('ReqPurpose',['Standard Approve'])[0].decode('utf-8')
        except UnicodeDecodeError:
            initial['ReqPurpose'] = urlparse.parse_qs(qs).get('ReqPurpose',['Standard Approve'])[0].decode('unicode-escape')
        initial['ObjectIdentifierValue'] = self.request.GET.get('ObjectIdentifierValue','')
        if 'ip_uuid' in self.kwargs:
            initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        self.autosubmit = self.request.GET.get('autosubmit', '0')
        self.raw = self.request.GET.get('raw', '0')
        return initial
    
    def form_invalid(self, form):
        if not form.is_valid():
            self.autosubmit = '0'
        return super(IngestCreate, self).form_invalid(form)
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        num = 0
        for obj in form.instance.ObjectIdentifierValue.split():
            self.object.pk = None
            self.object.ObjectIdentifierValue = obj
            self.object.ReqUUID = uuid.uuid1()
            self.object.save()
            num += 1
        if num == 1:
            self.success_url = reverse_lazy('ingest_detail',kwargs={'pk': self.object.pk})
        if self.autosubmit == '1' and self.raw == '1':
            #response = HttpResponse("Ingest request: %s for Object: %s Status: OK" % (self.object.ReqUUID, self.object.ObjectIdentifierValue), content_type="text/plain")
            response = HttpResponse("Ingest request: %s for Object: %s Status: OK" % (self.object.ReqUUID, self.object.ObjectIdentifierValue))
            return response
        return super(IngestCreate, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(IngestCreate, self).get_context_data(**kwargs)
        context['autosubmit'] = self.autosubmit
        return context
        
class IngestUpdate(UpdateView):
    model = IngestQueue
    template_name='ingest/update.html'
    form_class=IngestQueueFormUpdate
    
    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestUpdate, self).dispatch( *args, **kwargs)

class IngestDelete(DeleteView):
    model = IngestQueue
    template_name='ingest/delete.html'
    context_object_name='ingest'
    success_url = reverse_lazy('ingest_list')

    @method_decorator(permission_required('essarch.delete_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestDelete, self).dispatch( *args, **kwargs)

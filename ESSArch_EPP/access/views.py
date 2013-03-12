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

from essarch.models import AccessQueue, AccessQueueForm, AccessQueueFormUpdate, ArchiveObject, PackageType_CHOICES, StatusProcess_CHOICES, ReqStatus_CHOICES, AccessReqType_CHOICES
from configuration.models import Path, Parameter

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import uuid, os.path as op

class ArchObjectList(ListView):
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
        context['label'] = 'List of archived information packages'
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

class AccessList(ListView):
    """
    List AccessQueue
    """
    model = AccessQueue
    template_name='access/list.html'
    context_object_name='req_list'
    queryset=AccessQueue.objects.filter(Status__lt=20)   # Status<20

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessList, self).get_context_data(**kwargs)
        context['label'] = 'List of access requests'
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
        initial['ReqType'] = self.request.GET.get('ReqType',4)
        initial['ReqPurpose'] = self.request.GET.get('ReqPurpose')
        path_work = Path.objects.get(entity='path_work').value
        access_path = op.join( op.join(path_work, self.request.user.username), 'access' )
        initial['Path'] = self.request.GET.get('Path', access_path)
        if 'ip_uuid' in self.kwargs:
            initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        return initial
    
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
            self.success_url = reverse_lazy('access_detail',kwargs={'pk': self.object.pk})
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

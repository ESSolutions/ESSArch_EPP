from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404

from essarch.models import AccessQueue, AccessQueueForm, AccessQueueFormUpdate, ArchiveObject, PackageType_CHOICES
from configuration.models import Path, Parameter

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import uuid

class ArchObjectList(ListView):
    """
    List ArchiveObject
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    #context_object_name='access_list'
    queryset=ArchiveObject.objects.filter(StatusProcess=3000).order_by('id','Generation')

    @method_decorator(permission_required('access.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchObjectList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ArchObjectList, self).get_context_data(**kwargs)
        context['type'] = 'Access'
        context['label'] = 'List of archived information packages'
        ip_list = []
        a_list = context['object_list']
        for a in a_list:
            #for rel_obj in a.relaic_set.all().order_by('UUID__Generation'):
            rel_obj_list = a.reluuid_set.all()
            if rel_obj_list:
                for rel_obj in a.reluuid_set.all():
                    aic_obj = rel_obj.AIC_UUID
                    ip_obj = rel_obj.UUID
                    ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                    if ip_obj_data_list:
                        ip_obj_data = ip_obj_data_list[0]
                    else:
                        ip_obj_data = None
                    ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                    if ip_obj_metadata_list:
                        ip_obj_metadata = ip_obj_metadata_list[0]
                    else:
                        ip_obj_metadata = None
                    ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
            else:
                aic_obj = None
                ip_obj = a
                ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                if ip_obj_data_list:
                    ip_obj_data = ip_obj_data_list[0]
                else:
                    ip_obj_data = None
                ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                if ip_obj_metadata_list:
                    ip_obj_metadata = ip_obj_metadata_list[0]
                else:
                    ip_obj_metadata = None
                ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        return context

class AccessList(ListView):
    """
    List AccessQueue
    """
    model = AccessQueue
    template_name='access/list.html'
    context_object_name='req_list'
    queryset=AccessQueue.objects.filter(Status__lt=20)   # Status<20
    #queryset=AccessQueue.objects.filter(Status=20)   # Status<20
    #queryset=AccessQueue.objects.filter(Status__gt=20)   # Status<20

    @method_decorator(permission_required('access.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessList, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessList, self).get_context_data(**kwargs)
        context['label'] = 'List of access requests'
        return context

class AccessDetail(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = AccessQueue
    context_object_name='access'
    template_name='access/detail.html'

    @method_decorator(permission_required('access.detail_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(AccessDetail, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - access requests'
        return context

class AccessCreate(CreateView):
    model = AccessQueue
    template_name='access/create.html'
    form_class=AccessQueueForm

    @method_decorator(permission_required('access.add_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(AccessCreate, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqPurpose'] = self.request.GET.get('test')
        initial['Path'] = self.request.GET.get('Path')
        if 'ip_uuid' in self.kwargs:
            initial['ObjectIdentifierValue'] = self.kwargs['ip_uuid']
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        for obj in form.instance.ObjectIdentifierValue.split():
            self.object.pk = None
            self.object.ObjectIdentifierValue = obj
            self.object.ReqUUID = uuid.uuid1()
            self.object.save()
        return super(AccessCreate, self).form_valid(form)
        
class AccessUpdate(UpdateView):
    model = AccessQueue
    template_name='access/update.html'
    form_class=AccessQueueFormUpdate
    
    @method_decorator(permission_required('access.change_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessUpdate, self).dispatch( *args, **kwargs)

class AccessDelete(DeleteView):
    model = AccessQueue
    template_name='access/delete.html'
    context_object_name='access'
    success_url = reverse_lazy('access_list')

    @method_decorator(permission_required('access.delete_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AccessDelete, self).dispatch( *args, **kwargs)

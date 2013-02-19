from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404

from essarch.models import IngestQueue, IngestQueueForm, IngestQueueFormUpdate, ArchiveObject, \
                           ArchiveObjectStatusForm, PackageType_CHOICES, StatusProcess_CHOICES, ReqStatus_CHOICES, IngestReqType_CHOICES
from configuration.models import Path, Parameter

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseUpdateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import uuid

class ArchObjectListUpdate(ListView, BaseUpdateView):
    model = ArchiveObject
    template_name='archobject/list.html'
    form_class=ArchiveObjectStatusForm
    queryset=ArchiveObject.objects.filter(StatusProcess__lt=3000).order_by('id','Generation')
    
    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchObjectListUpdate, self).dispatch( *args, **kwargs)

    def get_initial(self):
        initial = super(ArchObjectListUpdate, self).get_initial().copy()
        initial['StatusActivity'] = self.object.StatusActivity
        return initial

    def get_context_data(self, **kwargs):
        context = super(ArchObjectListUpdate, self).get_context_data(**kwargs)
        context['type'] = 'Ingest'
        context['label'] = 'List of information packages in ingest'
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
                    # Create ip_form for ip_obj
                    self.object = ip_obj
                    ip_form_class = self.get_form_class()
                    ip_form = self.get_form(ip_form_class)
                    ip_list.append([aic_obj,ip_obj,ip_form,ip_obj_data,ip_obj_metadata])
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
                # Create ip_form for ip_obj
                self.object = ip_obj
                ip_form_class = self.get_form_class()
                ip_form = self.get_form(ip_form_class)
                ip_list.append([aic_obj,ip_obj,ip_form,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
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
        context['label'] = 'List of ingest requests'
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

    @method_decorator(permission_required('essarch.add_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(IngestCreate, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(IngestCreate, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = self.request.GET.get('ReqType',2)
        initial['ReqPurpose'] = self.request.GET.get('ReqPurpose')
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
            self.success_url = reverse_lazy('ingest_detail',kwargs={'pk': self.object.pk})
        return super(IngestCreate, self).form_valid(form)
        
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

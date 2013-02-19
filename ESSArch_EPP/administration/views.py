from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Q

from essarch.models import storageMedium, MediumType_CHOICES, MediumStatus_CHOICES, MediumLocationStatus_CHOICES, MediumFormat_CHOICES, MediumBlockSize_CHOICES, \
                           storage, robot, robotreq, robotReqQueueForm
from configuration.models import Path, Parameter

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseUpdateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import uuid, os.path as op, ESSPGM

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
    #context_object_name='access'
    template_name='administration/detail.html'

    @method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(storageMediumDetail, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(storageMediumDetail, self).get_context_data(**kwargs)
        storageMediumID = context['object'].storageMediumID
        content_list = storage.objects.filter(storageMediumID=storageMediumID).order_by('contentLocationValue')
        context['content_list'] = content_list
        context['label'] = 'Detail information - storage medium'
        context['MediumType_CHOICES'] = dict(MediumType_CHOICES)
        context['MediumStatus_CHOICES'] = dict(MediumStatus_CHOICES)
        context['MediumLocationStatus_CHOICES'] = dict(MediumLocationStatus_CHOICES)
        context['MediumFormat_CHOICES'] = dict(MediumFormat_CHOICES)
        context['MediumBlockSize_CHOICES'] = dict(MediumBlockSize_CHOICES)
        return context

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

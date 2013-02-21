from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404

from models import MyFile
from essarch.models import ArchiveObject, PackageType_CHOICES
from configuration.models import Path, Parameter
import essarch.ControlAreaFunc as ControlAreaFunc

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import ESSMD, os
from ESSPGM import Check as g_functions

class MyFileList(object):
    def __init__(self,filelist=None,source_path='',gate_path='',mets_obj=''):
        if filelist is None:
            filelist = []
        self.filelist = filelist
        self.PreIngestPath = source_path
        self.gate_path = gate_path
        self.mets_obj = mets_obj
    def get(self,ip_uuid = None):
        if os.path.isdir(self.PreIngestPath):
            for f in os.listdir(self.PreIngestPath): # /mottag
                if os.path.isdir(os.path.join(self.PreIngestPath, f)): #/mottag/cd or /mottag/usb
                    for ff in os.listdir(os.path.join(self.PreIngestPath, f)): # list cd or usb
                        if os.path.isdir(os.path.join(os.path.join(self.PreIngestPath, f), ff)): # ff = ip_uuid dir
                            ip = MyFile()
                            ObjectPath = os.path.join(os.path.join(self.PreIngestPath, f), ff)
                            mets_objpath = os.path.join(ObjectPath, self.mets_obj)
                            res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=mets_objpath)
                            ip.directory = ObjectPath
                            ip.media = f.upper()
                            ip.uuid = ''
                            if error == 0:
                                for agent in res_info[2]:
                                    if agent[0] == 'ARCHIVIST' and agent[2] == 'ORGANIZATION':
                                        ip.EntryAgentIdentifierValue = agent[4]
                                ip.label = res_info[0][0]
                                ip.createdate = res_info[1][0]
                                for altRecordID in res_info[3]:
                                    if altRecordID[0] == 'STARTDATE':
                                        ip.startdate = altRecordID[1]
                                    elif altRecordID[0] == 'ENDDATE':
                                        ip.enddate = altRecordID[1]
                                ip.iptype = res_info[0][3]
                                ip.state = 'Reception'
                                if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                                    ip.uuid = res_info[0][1][5:]
                                else:
                                    ip.uuid = res_info[0][1]
                            if ip_uuid is None:
                                self.filelist.append(ip)
                            elif ip.uuid == ip_uuid:
                                self.filelist = ip
                        elif os.path.isfile(os.path.join(os.path.join(self.PreIngestPath, f), ff)): # ff = file
                            ObjectPath = os.path.join(os.path.join(self.PreIngestPath, f), ff)
                            if ObjectPath[-4:].lower() == '.tar':
                                ObjectPackageName = ff
                                ip_uuid_test = ObjectPackageName[:-4]
                                logs_path = os.path.join( self.gate_path, 'logs' )
                                if os.path.isdir(logs_path):
                                    for g in os.listdir(logs_path):
                                        if os.path.isdir(os.path.join(logs_path, g)): #AIC dir
                                            if os.path.isdir( os.path.join( os.path.join( logs_path, g ), ip_uuid_test ) ): # ff = ip_uuid dir
                                                aic_path = os.path.join( logs_path, g )
                                                aic_uuid = os.path.split(aic_path)[1]
                                                ip = MyFile()
                                                mets_objpath = os.path.join(aic_path, self.mets_obj)
                                                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=mets_objpath)
                                                ip.directory = ObjectPath
                                                ip.media = f.upper()
                                                ip.uuid = ''
                                                if error == 0:
                                                    for agent in res_info[2]:
                                                        if agent[0] == 'ARCHIVIST' and agent[2] == 'ORGANIZATION':
                                                            ip.EntryAgentIdentifierValue = agent[4]
                                                    ip.label = res_info[0][0]
                                                    ip.createdate = res_info[1][0]
                                                    for altRecordID in res_info[3]:
                                                        if altRecordID[0] == 'STARTDATE':
                                                            ip.startdate = altRecordID[1]
                                                        elif altRecordID[0] == 'ENDDATE':
                                                            ip.enddate = altRecordID[1]
                                                    ip.iptype = res_info[0][3]
                                                    ip.state = 'Reception'
                                                    if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                                                        ip.uuid = res_info[0][1][5:]
                                                    else:
                                                        ip.uuid = res_info[0][1]
                                                    ip.aic_uuid = aic_uuid
                                                if ip_uuid is None:
                                                    self.filelist.append(ip)
                                                elif ip.uuid == ip_uuid:
                                                    self.filelist = ip
                                                
                                                    
        return self.filelist

    def __iter__(self):
        return iter(self.filelist)

    def __getitem__(self, key):
        return MyFileList(self.filelist[key])

class CheckinFromReceptionListView(ListView):
    """
    List reception area
    """
    #model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.all()
    source_path = Path.objects.get(entity='path_reception').value
    gate_path = Path.objects.get(entity='path_gate').value
    Pmets_obj = Parameter.objects.get(entity='package_descriptionfile').value

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromReceptionListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromReceptionListView, self).get_context_data(**kwargs)
        context['filelist'] = MyFileList(source_path = self.source_path, gate_path = self.gate_path, mets_obj = self.Pmets_obj).get()
        context['type'] = 'FromRec'
        context['label'] = 'Select which information package to checkin from reception'
        return context

class CheckinFromReception(DetailView):
    """
    Submit and View result from checkin from reception
    """
    #model = ArchiveObject
    template_name='controlarea/result_detail.html'
    source_path = Path.objects.get(entity='path_reception').value
    target_path = Path.objects.get(entity='path_control').value
    gate_path = Path.objects.get(entity='path_gate').value
    Pmets_obj = Parameter.objects.get(entity='package_descriptionfile').value

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromReception, self).dispatch( *args, **kwargs)

    def get_object(self):
        ip_uuid = self.kwargs['ip_uuid']
        return MyFileList(source_path = self.source_path, gate_path = self.gate_path, mets_obj = self.Pmets_obj).get(ip_uuid=ip_uuid)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromReception, self).get_context_data(**kwargs)
        objectpath = context['object'].directory
        ObjectIdentifierValue = context['object'].uuid
        status_code, status_detail = ControlAreaFunc.CheckInFromMottag(self.source_path, 
                                                                       self.target_path, 
                                                                       objectpath, 
                                                                       ObjectIdentifierValue,
                                                                       )
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context

class CheckoutToWorkListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(StatusProcess=5000).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWorkListView, self).get_context_data(**kwargs)
        context['type'] = 'ToWork'
        context['label'] = 'Select which information package to checkout to work area'
        ip_list = []
        a_list = context['object_list']
        for a in a_list:
            #for rel_obj in a.relaic_set.all().order_by('UUID__Generation'):
            for rel_obj in a.relaic_set.filter(UUID__StatusProcess=5000).order_by('UUID__Generation'):
            #for rel_obj in a.relaic_set.all():
            #for rel_obj in a.reluuid_set.all():
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
                ip_list.append([aic_obj,ip_obj,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        return context

class CheckoutToWork(DetailView):
    """
    Submit and View result from checkout to work area
    """
    model = ArchiveObject
    template_name='controlarea/result_detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWork, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWork, self).get_context_data(**kwargs)
        ip_obj = context['object']
        aic_obj = ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,ip_obj.ObjectUUID)
        source_path = Path.objects.get(entity='path_control').value
        target_path_tmp = Path.objects.get(entity='path_work').value
        target_path = os.path.join(target_path_tmp, self.request.user.username)
        a_uid = 503
        a_gid = 503
        a_mode = 0770
        status_code, status_detail = ControlAreaFunc.CheckOutToWork(source_path, 
                                                                    target_path, 
                                                                    objectpath, 
                                                                    a_uid, 
                                                                    a_gid, 
                                                                    a_mode,
                                                                    )
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context

class CheckinFromWorkListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(StatusProcess__gte=5000,StatusProcess__lte=5100).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromWorkListView, self).get_context_data(**kwargs)
        context['type'] = 'FromWork'
        context['label'] = 'Select which information package to checkin from work area'
        ip_list = []
        a_list = context['object_list']
        for a in a_list:
            #for rel_obj in a.relaic_set.all().order_by('UUID__Generation'):
            for rel_obj in a.relaic_set.filter(UUID__StatusProcess=5100).order_by('UUID__Generation'):
            #for rel_obj in a.reluuid_set.all():
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
                ip_list.append([aic_obj,ip_obj,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        return context

class CheckinFromWork(DetailView):
    """
    Submit and View result from checkin from work area
    """
    model = ArchiveObject
    template_name='controlarea/result_detail.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWork, self).dispatch( *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super(CheckinFromWork, self).get_context_data(**kwargs)
        ip_obj = context['object']
        aic_obj = ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,ip_obj.ObjectUUID)
        source_path_tmp = Path.objects.get(entity='path_work').value
        source_path = os.path.join(source_path_tmp, self.request.user.username)
        target_path = Path.objects.get(entity='path_control').value
        a_uid = 503
        a_gid = 503
        a_mode = 0770
        status_code, status_detail = ControlAreaFunc.CheckInFromWork(source_path, 
                                                                     target_path, 
                                                                     objectpath, 
                                                                     a_uid, 
                                                                     a_gid, 
                                                                     a_mode,
                                                                     )
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context

class DiffCheckListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(StatusProcess=5000).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheckListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiffCheckListView, self).get_context_data(**kwargs)
        context['type'] = 'DiffCheck'
        context['label'] = 'Select which information package to DiffCheck'
        ip_list = []
        a_list = context['object_list']
        for a in a_list:
            #for rel_obj in a.reluuid_set.all():
            for rel_obj in a.relaic_set.filter(UUID__StatusProcess=5000).order_by('UUID__Generation'):
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
                ip_list.append([aic_obj,ip_obj,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        return context

class DiffCheckWork(DetailView):
    """
    Submit and View result from diffcheck in work area
    """
    model = ArchiveObject
    template_name='controlarea/result_detail.html'
    target_path = Path.objects.get(entity='path_control').value
    Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
    
    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheckWork, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiffCheckWork, self).get_context_data(**kwargs)
        ip_obj = context['object']
        aic_obj = ip_obj.reluuid_set.get().AIC_UUID
        # Get IP_0 object
        ip_0_obj = aic_obj.relaic_set.filter(UUID__StatusProcess=5000).order_by('UUID__Generation')[:1].get().UUID
        AIC_ObjectPath = os.path.join(self.target_path, aic_obj.ObjectUUID)
        IP_ObjectPath = os.path.join(AIC_ObjectPath, ip_obj.ObjectUUID)
        #METS_ObjectPath = os.path.join(os.path.join(AIC_ObjectPath,ip_0_obj.ObjectUUID),'%s_Content_METS.xml' % ip_0_obj.ObjectUUID )
        METS_ObjectPath = os.path.join( os.path.join(AIC_ObjectPath,ip_0_obj.ObjectUUID), self.Cmets_obj )
        status_code, status_detail, res_list = g_functions().DiffCheck_IP(ObjectIdentifierValue=ip_obj.ObjectUUID,
                                                                          ObjectPath=IP_ObjectPath, 
                                                                          METS_ObjectPath=METS_ObjectPath,
                                                                          ) 
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context

class IngestIPListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(StatusProcess=5000).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(IngestIPListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IngestIPListView, self).get_context_data(**kwargs)
        context['type'] = 'ToIngest'
        context['label'] = 'Select which information package to preserve in archive'
        ip_list = []
        a_list = context['object_list']
        for a in a_list:
            for rel_obj in a.relaic_set.filter(UUID__StatusProcess=5000).order_by('UUID__Generation'):
            #for rel_obj in a.reluuid_set.all():
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
                ip_list.append([aic_obj,ip_obj,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        return context

class IngestIP(DetailView):
    """
    Submit and View result from ingest to ESSArch
    """
    model = ArchiveObject
    template_name='controlarea/result_detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(IngestIP, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(IngestIP, self).get_context_data(**kwargs)
        ip_obj = context['object']
        aic_obj = ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,ip_obj.ObjectUUID)
        source_path = Path.objects.get(entity='path_control').value
        target_path = Path.objects.get(entity='path_ingest').value
        #target_path = os.path.join(target_path_tmp, self.request.user.username)
        a_uid = 503
        a_gid = 503
        a_mode = 0770
        status_code, status_detail = ControlAreaFunc.IngestIP(source_path,
                                                            target_path, 
                                                            objectpath, 
                                                            a_uid, 
                                                            a_gid, 
                                                            a_mode,
                                                            )
        if status_code == 0:
            ip_obj.StatusProcess = 0
            ip_obj.save()
        context['status_code'] = status_code
        context['status_detail'] = status_detail
        return context


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

from models import MyFile, RequestFile
from django.db.models import Q
from essarch.models import ArchiveObject, PackageType_CHOICES, StatusProcess_CHOICES, \
                           ControlAreaQueue, ControlAreaForm, ControlAreaForm2, ControlAreaForm_reception, \
                           ControlAreaForm_CheckInFromWork, ControlAreaForm_CheckoutToWork, \
                           ControlAreaReqType_CHOICES, ReqStatus_CHOICES, ControlAreaForm_file, \
                           eventIdentifier, eventOutcome_CHOICES, IngestQueue
from configuration.models import Path, Parameter
import ControlAreaFunc

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import ESSMD, os, uuid
from ESSPGM import Check as g_functions
import ESSPGM, pytz, datetime, logging

logger = logging.getLogger('essarch.controlarea')

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
                                logger.warning('IP/directory: %s found in reception, this directory should not exists in reception, reception should only contain IP tarfiles.' % ObjectPath)
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
                                ip.state = '0'
                                ip.StatusProcess = 'Reception'
                                if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                                    ip.uuid = res_info[0][1][5:]
                                else:
                                    ip.uuid = res_info[0][1]
                            else:
                                logger.error('IP/directory: %s found in reception, this directory should not exists in reception, reception should only contain IP tarfiles. Problem to read metsfile: %s error: %s' % (ObjectPath,mets_objpath,str(why)))
                            if ip_uuid is None:
                                self.filelist.append(ip)
                            elif ip.uuid == ip_uuid:
                                self.filelist = ip
                        elif os.path.isfile(os.path.join(os.path.join(self.PreIngestPath, f), ff)): # ff = file
                            ObjectPath = os.path.join(os.path.join(self.PreIngestPath, f), ff)
                            if ObjectPath[-4:].lower() == '.tar':
                                ObjectPackageName = ff
                                ip_uuid_test = ObjectPackageName[:-4]
                                ip_uuid_test_flag = 0
                                #logger.info('IP: %s found in reception, start to check if an IP directory with name: "%s" exists in some AIC in "gate area"' % (ObjectPath, ip_uuid_test))
                                #TODO lobby in sweden and logs in Norway
                                #logs_path = os.path.join( self.gate_path, 'logs' )
                                logs_path = os.path.join( self.gate_path, 'lobby' )
                                if os.path.isdir(logs_path):
                                    for g in os.listdir(logs_path):
                                        if os.path.isdir(os.path.join(logs_path, g)): #AIC dir
                                            if os.path.isdir( os.path.join( os.path.join( logs_path, g ), ip_uuid_test ) ): # ff = ip_uuid dir
                                                ip_uuid_test_flag = 1                                            
                                                aic_path = os.path.join( logs_path, g )
                                                aic_uuid = os.path.split(aic_path)[1]
                                                ip = MyFile()
                                                mets_objpath = os.path.join(aic_path, self.mets_obj)
                                                res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=mets_objpath)
                                                ip.directory = ObjectPath
                                                ip.media = f.upper()
                                                ip.uuid = ''
                                                if error == 0:
                                                    logger.info('IP: %s found in reception and success to read metsfile: %s in "gate area"' % (ObjectPath, mets_objpath))
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
                                                    ip.state = '0'
                                                    ip.StatusProcess = 'Reception'
                                                    if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                                                        ip.uuid = res_info[0][1][5:]
                                                    else:
                                                        ip.uuid = res_info[0][1]
                                                    ip.aic_uuid = aic_uuid
                                                else:
                                                    logger.error('IP: %s found in reception, problem to read metsfile: %s in "gate area", error: %s' % (ObjectPath, mets_objpath, str(why)))
                                                if ip_uuid is None:
                                                    self.filelist.append(ip)
                                                elif ip.uuid == ip_uuid:
                                                    self.filelist = ip
                                    if ip_uuid_test_flag == 0:
                                        logger.error('IP: %s found in reception, IP directory with name: "%s" do not exists in any AIC in "gate area" (%s)' % (ObjectPath, ip_uuid_test, logs_path))       
                                else:
                                    logger.error('path: %s do not exists' % logs_path)                    
        return self.filelist

    def __iter__(self):
        return iter(self.filelist)

    def __getitem__(self, key):
        return MyFileList(self.filelist[key])

class RequestFileList(object):
    def __init__(self,reqlist=None,source_path=''):
        if reqlist is None:
            reqlist = []
        self.reqlist = reqlist
        self.source_path = os.path.join(source_path,u'exchange')
    def get(self):
        if os.path.isdir(self.source_path):
            for f in os.listdir(self.source_path): # gate_path/exchange
                #logger.info('type:%s, f:%s' % (type(f),f))
                #logger.info('type:%s, source_path:%s' % (type(self.source_path),self.source_path))
                #logger.info('defaultencoding: %s, filesystemencoding: %s' % (sys.getdefaultencoding(),sys.getfilesystemencoding()))
                if os.path.isdir(os.path.join(self.source_path, f)): # exchange ReqUUID directory
                    reqfilename = os.path.join(os.path.join(self.source_path, f),u'request.xml')
                    if os.path.isfile(reqfilename):
                        res_info,return_status_code,return_status_list = ControlAreaFunc.GetExchangeRequestFileContent(reqfilename)
                        if return_status_code == 0 and res_info:
                            req = RequestFile()
                            req.ReqUUID = res_info[0]
                            req.ReqType = res_info[1]
                            req.ReqPurpose = res_info[2]
                            req.user = res_info[3]
                            req.ObjectIdentifierValue = res_info[4]
                            req.posted = res_info[5]
                            req.filelist = res_info[6]
                            self.reqlist.append(req)                                                    
        return self.reqlist

    def __iter__(self):
        return iter(self.reqlist)

    def __getitem__(self, key):
        return RequestFileList(self.reqlist[key])

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

class CheckinFromReception(CreateView):
    """
    Create checkin request from reception
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm_reception
    source_path = Path.objects.get(entity='path_reception').value
    target_path = Path.objects.get(entity='path_control').value
    gate_path = Path.objects.get(entity='path_gate').value
    Pmets_obj = Parameter.objects.get(entity='package_descriptionfile').value

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromReception, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(CheckinFromReception, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 1
        initial['ReqPurpose'] = ''
        initial['POLICYID'] = 1
        initial['INFORMATIONCLASS'] = 1
        initial['DELIVERYTYPE'] = 'N/A'
        initial['DELIVERYSPECIFICATION'] = 'N/A'
        initial['allow_unknown_filetypes'] = True
        if 'ip_uuid' in self.kwargs:
            self.ip_obj = MyFileList(source_path = self.source_path, gate_path = self.gate_path, mets_obj = self.Pmets_obj).get(ip_uuid=self.kwargs['ip_uuid'])
            if self.ip_obj:
                initial['ObjectIdentifierValue'] = self.ip_obj.uuid
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        objectpath = self.ip_obj.directory
        ObjectIdentifierValue = form.instance.ObjectIdentifierValue
        altRecordID_list = []
        POLICYID = form.cleaned_data.get('POLICYID',None)
        if POLICYID:
            altRecordID_list.append(['POLICYID',POLICYID])
        INFORMATIONCLASS = form.cleaned_data.get('INFORMATIONCLASS',None)
        if INFORMATIONCLASS:
            altRecordID_list.append(['INFORMATIONCLASS',INFORMATIONCLASS])
        DELIVERYTYPE = form.cleaned_data.get('DELIVERYTYPE',None)
        if DELIVERYTYPE:
            altRecordID_list.append(['DELIVERYTYPE',DELIVERYTYPE])
        DELIVERYSPECIFICATION = form.cleaned_data.get('DELIVERYSPECIFICATION',None)
        if DELIVERYSPECIFICATION:
            altRecordID_list.append(['DELIVERYSPECIFICATION',DELIVERYSPECIFICATION])
        allow_unknown_filetypes = form.cleaned_data.get('allow_unknown_filetypes',False)
        status_code, status_detail = ControlAreaFunc.CheckInFromMottag(self.source_path, 
                                                                       self.target_path, 
                                                                       objectpath, 
                                                                       ObjectIdentifierValue,
                                                                       altRecordID_list=altRecordID_list,
                                                                       allow_unknown_filetypes=allow_unknown_filetypes,
                                                                       )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to CheckIn object: %s from reception, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                                form.cleaned_data.get('ReqUUID',None),
                                                                                                status_detail[1]
                                                                                                )
            ESSPGM.Events().create('30000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        else:
            self.object.Status=20
            event_info = 'Success to CheckIn object: %s from reception, ReqUUID: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                        form.cleaned_data.get('ReqUUID',None),
                                                                                        )
            ESSPGM.Events().create('30000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,ObjectIdentifierValue,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_checkinfromreceptionresult',kwargs={'pk': self.object.pk})
        return super(CheckinFromReception, self).form_valid(form)

class CheckinFromReceptionResult(DetailView):
    """
    View result from checkin from reception
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromReceptionResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromReceptionResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class CheckoutToWorkListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWorkListView, self).get_context_data(**kwargs)
        context['type'] = 'ToWork'
        context['label'] = 'Select which information package to checkout to work area'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5000,StatusActivity__in=[ 7, 8 ]):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class CheckoutToWork(CreateView):
    """
    Create checkout request to work area
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm_CheckoutToWork

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWork, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(CheckoutToWork, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 2
        initial['ReqPurpose'] = ''
        if 'pk' in self.kwargs:
            self.ip_obj = ArchiveObject.objects.get(pk=self.kwargs['pk'])
            initial['ObjectIdentifierValue'] = self.ip_obj.ObjectUUID
        initial['read_only_access'] = False
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,self.ip_obj.ObjectUUID)
        source_path = Path.objects.get(entity='path_control').value
        target_path_tmp = Path.objects.get(entity='path_work').value
        target_path = os.path.join(target_path_tmp, self.request.user.username)
        read_only_access = form.cleaned_data.get('read_only_access',False)
        a_uid = os.getuid()
        a_gid = os.getgid()
        a_mode = 0770
        status_code, status_detail = ControlAreaFunc.CheckOutToWork(source_path, 
                                                                    target_path, 
                                                                    objectpath, 
                                                                    a_uid, 
                                                                    a_gid, 
                                                                    a_mode,
                                                                    read_only_access,
                                                                    )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to CheckOut object: %s to workarea, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                              form.cleaned_data.get('ReqUUID',None),
                                                                                              status_detail[1]
                                                                                              )
            ESSPGM.Events().create('31000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        else:
            self.object.Status=20
            event_info = 'Success to CheckOut object: %s to workarea, ReqUUID: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                      form.cleaned_data.get('ReqUUID',None),
                                                                                      )
            ESSPGM.Events().create('31000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_checkouttoworkresult',kwargs={'pk': self.object.pk})
        return super(CheckoutToWork, self).form_valid(form)

class CheckoutToWorkResult(DetailView):
    """
    View result from checkout to work area
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWorkResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWorkResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class CheckinFromWorkListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5100) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromWorkListView, self).get_context_data(**kwargs)
        context['type'] = 'FromWork'
        context['label'] = 'Select which information package to checkin from work area'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5100):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class CheckinFromWork(CreateView):
    """
    Create checkin request from work area
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm_CheckInFromWork

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWork, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(CheckinFromWork, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 3
        initial['ReqPurpose'] = ''
        if 'pk' in self.kwargs:
            self.ip_obj = ArchiveObject.objects.get(pk=self.kwargs['pk'])
            initial['ObjectIdentifierValue'] = self.ip_obj.ObjectUUID
        initial['allow_unknown_filetypes'] = True
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,self.ip_obj.ObjectUUID)
        source_path_tmp = Path.objects.get(entity='path_work').value
        source_path = os.path.join(source_path_tmp, self.request.user.username)
        target_path = Path.objects.get(entity='path_control').value
        a_uid = os.getuid()
        a_gid = os.getgid()
        a_mode = 0770
        allow_unknown_filetypes = form.cleaned_data.get('allow_unknown_filetypes',False)
        status_code, status_detail = ControlAreaFunc.CheckInFromWork(source_path, 
                                                                     target_path, 
                                                                     objectpath, 
                                                                     a_uid, 
                                                                     a_gid, 
                                                                     a_mode,
                                                                     allow_unknown_filetypes,
                                                                     )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to CheckIn object: %s from workarea, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                               form.cleaned_data.get('ReqUUID',None),
                                                                                               status_detail[1]
                                                                                               )
            ESSPGM.Events().create('32000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        else:
            self.object.Status=20
            event_info = 'Success to CheckIn object: %s from workarea, ReqUUID: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                       form.cleaned_data.get('ReqUUID',None),
                                                                                       )
            ESSPGM.Events().create('32000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_checkinfromworkresult',kwargs={'pk': self.object.pk})
        return super(CheckinFromWork, self).form_valid(form)

class CheckinFromWorkResult(DetailView):
    """
    View result from checkin from work area
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWorkResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromWorkResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class CheckoutToGateFromWork(CreateView):
    """
    Create checkout request to gate from work
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm_file
    target_path = Path.objects.get(entity='path_gate').value
    source_path = Path.objects.get(entity='path_work').value
    
    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToGateFromWork, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(CheckoutToGateFromWork, self).get_initial()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 6
        initial['ReqPurpose'] = ''
        source_path = os.path.join(self.source_path, self.request.user.username)   
        filelist = []
        if os.path.exists(source_path):
            filetree = g_functions().GetFiletree(source_path)
            for file_item in filetree:
                filelist.append((file_item, file_item))
        self.form_class.FileSelect_CHOICES = filelist
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        filelist = form.cleaned_data.get('filename',[])
        ReqUUID = form.cleaned_data.get('ReqUUID',uuid.uuid1())
        target_path = os.path.join(self.target_path, 'exchange/%s' % ReqUUID)
        source_path = os.path.join(self.source_path, self.request.user.username)
        status_code, tmp_status_detail = ControlAreaFunc.CopyFilelist(source_path, target_path, filelist)
        if status_code:
            self.object.Status=100
        else:
            self.object.Status=20
        status_detail = [[],[]]
        req_filelist = []
        for item in tmp_status_detail[0]:
            event_info = '%s, ReqUUID: %s' % (item[0],form.cleaned_data.get('ReqUUID',None))
            ESSPGM.Events().create('35000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,item[1],linkingAgentIdentifierValue=self.request.user.username,
                                   )
            status_detail[0].append(item[0])
            req_filelist.append(item[1])
        for item in tmp_status_detail[1]:
            event_info = '%s, ReqUUID: %s' % (item[0],form.cleaned_data.get('ReqUUID',None))
            ESSPGM.Events().create('35000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,item[1],linkingAgentIdentifierValue=self.request.user.username,
                                   )
            status_detail[1].append(item[0])
            req_filelist.append(item[1])
        
        TimeZone = timezone.get_default_timezone_name()
        loc_timezone=pytz.timezone(TimeZone)
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
        self.object.posted = loc_dt_isoformat
        ControlAreaFunc.CreateExchangeRequestFile(ReqUUID = form.cleaned_data.get('ReqUUID'), 
                                                  ReqType = form.cleaned_data.get('ReqType'), 
                                                  ReqPurpose = form.cleaned_data.get('ReqPurpose'), 
                                                  user = form.cleaned_data.get('user'), 
                                                  ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue'), 
                                                  posted = loc_dt_isoformat, 
                                                  filelist = req_filelist, 
                                                  reqfilename = os.path.join(target_path,'request.xml'),
                                                  )
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_checkouttogatefromworkresult',kwargs={'pk': self.object.pk})
        return super(CheckoutToGateFromWork, self).form_valid(form)

class CheckoutToGateFromWorkResult(DetailView):
    """
    View result from checkout to gate area from work
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToGateFromWorkResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToGateFromWorkResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class CheckinFromGateToWork(CreateView):
    """
    Create checkin request from gate to work
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm_file
    target_path = Path.objects.get(entity='path_work').value
    source_path = Path.objects.get(entity='path_gate').value
    
    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromGateToWork, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(CheckinFromGateToWork, self).get_initial()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 7
        initial['ReqPurpose'] = ''
        source_path = os.path.join(self.source_path, 'exchange/%s' % self.request.user.username)   
        filelist = []
        if os.path.exists(source_path):
            filetree = g_functions().GetFiletree(source_path)
            for file_item in filetree:
                filelist.append((file_item, file_item))
        self.form_class.FileSelect_CHOICES = filelist
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        filelist = form.cleaned_data.get('filename',[])
        ReqUUID = form.cleaned_data.get('ReqUUID',uuid.uuid1())
        target_path = os.path.join(self.target_path, '%s/incoming/%s' % (self.request.user.username,ReqUUID))
        source_path = os.path.join(self.source_path, 'exchange/%s' % self.request.user.username)
        status_code, tmp_status_detail = ControlAreaFunc.CopyFilelist(source_path, target_path, filelist)
        if status_code:
            self.object.Status=100
        else:
            self.object.Status=20
        status_detail = [[],[]]
        req_filelist = []
        for item in tmp_status_detail[0]:
            event_info = '%s, ReqUUID: %s' % (item[0],form.cleaned_data.get('ReqUUID',None))
            ESSPGM.Events().create('35000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,item[1],linkingAgentIdentifierValue=self.request.user.username,
                                   )
            status_detail[0].append(item[0])
            req_filelist.append(item[1])
        for item in tmp_status_detail[1]:
            event_info = '%s, ReqUUID: %s' % (item[0],form.cleaned_data.get('ReqUUID',None))
            ESSPGM.Events().create('35000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,item[1],linkingAgentIdentifierValue=self.request.user.username,
                                   )
            status_detail[1].append(item[0])
            req_filelist.append(item[1])
        
        TimeZone = timezone.get_default_timezone_name()
        loc_timezone=pytz.timezone(TimeZone)
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
        self.object.posted = loc_dt_isoformat
        ControlAreaFunc.CreateExchangeRequestFile(ReqUUID = form.cleaned_data.get('ReqUUID'), 
                                                  ReqType = form.cleaned_data.get('ReqType'), 
                                                  ReqPurpose = form.cleaned_data.get('ReqPurpose'), 
                                                  user = form.cleaned_data.get('user'), 
                                                  ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue'), 
                                                  posted = loc_dt_isoformat, 
                                                  filelist = req_filelist, 
                                                  reqfilename = os.path.join(target_path,'request.xml'),
                                                  )
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_checkinfromgatetoworkresult',kwargs={'pk': self.object.pk})
        return super(CheckinFromGateToWork, self).form_valid(form)

class CheckinFromGateToWorkResult(DetailView):
    """
    View result from checkin from gate area to work
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromGateToWorkResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromGateToWorkResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class CheckinFromGateListView(ListView):
    """
    List gate "exchange" area
    """
    template_name='controlarea/reqlist.html'
    queryset=ArchiveObject.objects.all()
    gate_path = Path.objects.get(entity='path_gate').value

    @method_decorator(permission_required('controlarea.CheckinFromGate'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromGateListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromGateListView, self).get_context_data(**kwargs)
        context['req_list'] = RequestFileList(source_path = self.gate_path).get()
        context['type'] = 'FromGate'
        context['label'] = 'List exchange requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        return context

class DiffCheckListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheckListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiffCheckListView, self).get_context_data(**kwargs)
        context['type'] = 'DiffCheck'
        context['label'] = 'Select which information package to DiffCheck'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5000):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class DiffCheck(CreateView):
    """
    Create diffcheck request
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm2
    target_path = Path.objects.get(entity='path_control').value
    #Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheck, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(DiffCheck, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 4
        initial['ReqPurpose'] = ''
        if 'pk' in self.kwargs:
            self.ip_obj = ArchiveObject.objects.get(pk=self.kwargs['pk'])
            initial['ObjectIdentifierValue'] = self.ip_obj.ObjectUUID
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        logger.info('Start to DiffCheck object: %s' % self.ip_obj.ObjectUUID)
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        # Get IP_0 object
        ip_0_obj = aic_obj.relaic_set.filter(Q(UUID__StatusProcess=5000) | Q(UUID__StatusActivity__in=[ 7, 8 ])).order_by('UUID__Generation')[:1].get().UUID
        AIC_ObjectPath = os.path.join(self.target_path, aic_obj.ObjectUUID)
        IP_ObjectPath = os.path.join(AIC_ObjectPath, self.ip_obj.ObjectUUID)
        Cmets_obj = ip_0_obj.MetaObjectIdentifier
        if Cmets_obj == '':
            Cmets_obj = Parameter.objects.get(entity='content_descriptionfile').value
        METS_ObjectPath = os.path.join( os.path.join(AIC_ObjectPath,ip_0_obj.ObjectUUID), Cmets_obj )
        status_code, status_detail, res_list = g_functions().DiffCheck_IP(ObjectIdentifierValue=self.ip_obj.ObjectUUID,
                                                                          ObjectPath=IP_ObjectPath, 
                                                                          METS_ObjectPath=METS_ObjectPath,
                                                                          )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to DiffCheck object: %s, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                   form.cleaned_data.get('ReqUUID',None),
                                                                                   status_detail[1]
                                                                                   )
            ESSPGM.Events().create('33000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
            logger.error(event_info)
        else:
            self.object.Status=20
            status_summary = ''
            for st in status_detail[0]:
                if st.startswith('STATUS -'):
                    status_summary = st
            event_info = 'Success to DiffCheck object: %s, ReqUUID: %s, Result: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                       form.cleaned_data.get('ReqUUID',None),
                                                                                       status_summary
                                                                                       )
            ESSPGM.Events().create('33000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
            logger.info(event_info)
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_diffcheckresult',kwargs={'pk': self.object.pk})
        return super(DiffCheck, self).form_valid(form)

class DiffCheckResult(DetailView):
    """
    View result from diffcheck
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheckResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(DiffCheckResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context

class PreserveIPListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveIPListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PreserveIPListView, self).get_context_data(**kwargs)
        context['type'] = 'ToIngest'
        context['label'] = 'Select which information package to preserve in archive'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5000):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class PreserveIP(CreateView):
    """
    Create PreserveIP request
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm2

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveIP, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(PreserveIP, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 5
        initial['ReqPurpose'] = ''
        if 'pk' in self.kwargs:
            self.ip_obj = ArchiveObject.objects.get(pk=self.kwargs['pk'])
            initial['ObjectIdentifierValue'] = self.ip_obj.ObjectUUID
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,self.ip_obj.ObjectUUID)
        source_path = Path.objects.get(entity='path_control').value
        target_path = Path.objects.get(entity='path_ingest').value
        a_uid = os.getuid()
        a_gid = os.getgid()
        a_mode = 0770
        status_code, status_detail = ControlAreaFunc.PreserveIP(source_path,
                                                                target_path, 
                                                                objectpath, 
                                                                a_uid, 
                                                                a_gid, 
                                                                a_mode,
                                                                )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to PreserveIP object: %s, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                    form.cleaned_data.get('ReqUUID',None),
                                                                                    status_detail[1]
                                                                                    )
            ESSPGM.Events().create('34000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        else:
            self.object.Status=20
            IngestQueue_req = IngestQueue()
            IngestQueue_req.ReqUUID = form.cleaned_data.get('ReqUUID',None)
            IngestQueue_req.ReqType = 2
            IngestQueue_req.ReqPurpose = form.cleaned_data.get('ReqPurpose',None)
            IngestQueue_req.user = form.cleaned_data.get('user',None)
            IngestQueue_req.ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue',None)
            IngestQueue_req.Status = 0
            IngestQueue_req.save()
            event_info = 'Success to PreserveIP object: %s, ReqUUID: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                          form.cleaned_data.get('ReqUUID',None),
                                                                          )
            ESSPGM.Events().create('34000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )            
            # Update ip_obj with StatusProcess = 0 to enable ingest to discover new IP.
            self.ip_obj.StatusProcess = 0
            self.ip_obj.save()
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_preserveipresult',kwargs={'pk': self.object.pk})
        return super(PreserveIP, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(PreserveIP, self).get_context_data(**kwargs)
        context['type'] = 'PreserveIP'
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        ip_obj_list = ArchiveObject.objects.filter(reluuid_set__AIC_UUID=aic_obj).order_by('Generation')
        ip_uuid_list = []
        for ip_obj in ip_obj_list:
            ip_uuid_list.append(ip_obj.ObjectUUID)
        event_obj_list = eventIdentifier.objects.filter( linkingObjectIdentifierValue__in = ip_uuid_list ).order_by('linkingObjectIdentifierValue', 'eventDateTime')
        event_list1 = []
        event_list2 = []
        for event_obj in event_obj_list:
            linking_ip_obj = None
            for ip_obj in ip_obj_list:
                if ip_obj.ObjectUUID == event_obj.linkingObjectIdentifierValue:
                    linking_ip_obj = ip_obj
            if event_obj.linkingObjectIdentifierValue == self.ip_obj.ObjectUUID:                
                event_list1.append([event_obj,linking_ip_obj])
            else:
                event_list2.append([event_obj,linking_ip_obj])
        context['event_list1'] = event_list1
        context['event_list2'] = event_list2
        context['eventOutcome_CHOICES'] = dict(eventOutcome_CHOICES)
        return context

class PreserveIPResult(DetailView):
    """
    View result from PreserveIP
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveIPResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PreserveIPResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context
    
class ControlareaDeleteIPListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='archobject/list.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess__in=[5000,5100]) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(ControlareaDeleteIPListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ControlareaDeleteIPListView, self).get_context_data(**kwargs)
        context['type'] = 'ControlareaDeleteIP'
        context['label'] = 'Select which information package to delete in control/work area'
        ip_list = []
        object_list = context['object_list']
        aic_obj = None
        newest_gen = None
        for obj in object_list: 
            for ip in obj.get_ip_list( StatusProcess__in=[5000,5100] , StatusActivity__in=[ 7, 8 ] ):
                if not ip[0] == aic_obj:
                    Newest_object = ip[0].relaic_set.order_by('-UUID__Generation')[:1].get().UUID
                    newest_gen = Newest_object.Generation
                if not ip[1].StatusActivity in [ 7, 8 ] and ip[1].Generation in [0, newest_gen]:
                    pass
                else:
                    ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context

class ControlareaDeleteIP(CreateView):
    """
    Create delete IP request
    """
    model = ControlAreaQueue
    template_name='controlarea/create.html'
    form_class=ControlAreaForm2

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(ControlareaDeleteIP, self).dispatch( *args, **kwargs)
    
    def get_initial(self):
        initial = super(ControlareaDeleteIP, self).get_initial().copy()
        initial['ReqUUID'] = uuid.uuid1()
        initial['user'] = self.request.user.username
        initial['Status'] = 0
        initial['ReqType'] = 8
        initial['ReqPurpose'] = ''
        if 'pk' in self.kwargs:
            self.ip_obj = ArchiveObject.objects.get(pk=self.kwargs['pk'])
            initial['ObjectIdentifierValue'] = self.ip_obj.ObjectUUID
        return initial
    
    def form_valid(self, form):
        self.object = form.save(commit=True)
        aic_obj = self.ip_obj.reluuid_set.get().AIC_UUID
        objectpath = '%s/%s' % (aic_obj.ObjectUUID,self.ip_obj.ObjectUUID)
        source_path = Path.objects.get(entity='path_control').value
        target_path_tmp = Path.objects.get(entity='path_work').value
        target_path = os.path.join(target_path_tmp, self.request.user.username)
        status_code, status_detail = ControlAreaFunc.DeleteIP(source_path, 
                                                              target_path, 
                                                              objectpath, 
                                                              )
        if status_code:
            self.object.Status=100
            event_info = 'Failed to delete object: %s, ReqUUID: %s, why: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                                form.cleaned_data.get('ReqUUID',None),
                                                                                status_detail[1]
                                                                                )
            ESSPGM.Events().create('36000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'1',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
        else:
            self.object.Status=20
            event_info = 'Success to delete object: %s, ReqUUID: %s' % (form.cleaned_data.get('ObjectIdentifierValue',None),
                                                                        form.cleaned_data.get('ReqUUID',None),
                                                                        )
            ESSPGM.Events().create('36000',form.cleaned_data.get('ReqPurpose',''),'controlarea views',__version__,'0',
                                   event_info,0,self.ip_obj.ObjectUUID,linkingAgentIdentifierValue=self.request.user.username,
                                   )
            if self.ip_obj.StatusProcess in range(0,3001) and self.ip_obj.StatusActivity in [ 7, 8 ]:
                # ip_obj is archived update StatusActivity = 0
                self.ip_obj.StatusActivity = 0
                self.ip_obj.save()
            else:
                # Update ip_obj with StatusProcess = 9999 to mark as deleted.
                self.ip_obj.StatusProcess = 9999
                self.ip_obj.StatusActivity = 0
                self.ip_obj.ObjectActive = 0
                self.ip_obj.save()
        self.request.session['result_status_code'] = status_code
        self.request.session['result_status_detail'] = status_detail
        self.success_url = reverse_lazy('controlarea_deleteipresult',kwargs={'pk': self.object.pk})
        return super(ControlareaDeleteIP, self).form_valid(form)

class ControlareaDeleteIPResult(DetailView):
    """
    View result from delete IP
    """
    model = ControlAreaQueue
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(ControlareaDeleteIPResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ControlareaDeleteIPResult, self).get_context_data(**kwargs)
        context['label'] = 'Detail information - ControlArea requests'
        context['ControlAreaReqType_CHOICES'] = dict(ControlAreaReqType_CHOICES)
        context['ReqStatus_CHOICES'] = dict(ReqStatus_CHOICES)
        return context


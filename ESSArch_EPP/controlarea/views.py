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
from django.conf import settings

from models import MyFile, RequestFile
from django.db.models import Q
from django.db.models import Max
from essarch.models import ArchiveObject,ArchiveObjectData,ArchiveObjectRel, PackageType_CHOICES, StatusProcess_CHOICES, \
                           ControlAreaQueue, ControlAreaForm, ControlAreaForm2, ControlAreaForm_reception, \
                           ControlAreaForm_CheckInFromWork, ControlAreaForm_CheckoutToWork, \
                           ControlAreaReqType_CHOICES, ReqStatus_CHOICES, ControlAreaForm_file, \
                           eventIdentifier, eventOutcome_CHOICES, IngestQueue
from configuration.models import Path, Parameter, ArchivePolicy


from controlarea.tasks import CheckInFromMottagTask, CheckOutToWorkTask, CheckInFromWorkTask,\
							                DiffCheckTask, PreserveIPTask, CopyFilelistTask, DeleteIPTask,\
							                GetExchangeRequestFileContentTask, TestTask

from django.views.generic.detail import DetailView
from django.views.generic import ListView, TemplateView, View
from django.views.generic.edit import CreateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required

import json
import jsonpickle
from django.core.cache import cache
from operator import itemgetter, attrgetter, methodcaller
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseBadRequest
from djcelery.models import TaskMeta
from djcelery import views as celeryviews

import ESSMD, os, uuid
from ESSPGM import Check as g_functions
import ESSPGM, pytz, datetime, time, logging

logger = logging.getLogger('essarch.controlarea')

class MyFileList(object):
    def __init__(self,filelist=None,source_path='',path_gate_reception='',mets_obj=''):
        if filelist is None:
            filelist = []
        self.filelist = filelist
        #self.PreIngestPath = source_path
        self.path_gate_reception = path_gate_reception
        self.mets_obj = mets_obj
        self.source_path = source_path
        #print 'source_path', self.source_path
        #print 'gate', self.path_gate_reception
        #print 'mets', self.mets_obj

    def get(self,ip_uuid = None):

        #fil_lista = []
        ip_file = ''
        #ip_file_path = ''
        #ip_uuid = None

        # check for submit description
        # parse submit description file for ip uuid to get ip file
        # check if ip file exist in relative subfolders on gate
        # if ip file found on gate then exit else check on media
        # if not found at all exception exit

        # check for submit description and related ip file
        for dirname, dirnames, filenames in os.walk( self.path_gate_reception ):
            for f in filenames:
                ip_file = '' # clear
                # check for submit description
                if f == self.mets_obj:
                    submit_description_file = os.path.join(dirname, f)
                    #print '===== new IP ===='
                    #print 'submit desc exist', submit_description_file

                    # parse submit description file for ip uuid to get ip file
                    ip = MyFile()
                    res_info, res_files, res_struct, error, why = ESSMD.getMETSFileList(FILENAME=submit_description_file)
                    if error != 0:
                        #print 'could not read metsfile'
                        logger.error('Problem to read metsfile: %s at gate area, error: %s' % (submit_description_file, str(why)))
                        break
                    #else:
                        #print 'ok to read metsfile'
                    ip.uuid = ''
                    if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                        ip.uuid = res_info[0][1][5:]
                    else:
                        ip.uuid = res_info[0][1]
                    ip_tarfile = ip.uuid + '.tar'
                    ip_zipfile = ip.uuid + '.zip'

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
                            #        if res_info[0][1][:5] == 'UUID:' or res_info[0][1][:5] == 'RAID:':
                            #            ip.uuid = res_info[0][1][5:]
                            #        else:
                            #            ip.uuid = res_info[0][1]
                            #        ip.aic_uuid = aic_uuid

                    # check if ip file exist in relative subfolders on gate
                    for d, dn, f in os.walk( dirname ):
                        for ff in f:
                            if ff == ip_tarfile:
                                ip_file = os.path.join(d, ff)
                                #fil_lista.append(ip_file)
                                #print 'tar file found on gate:', ip_file
                                break
                            if ff == ip_zipfile:
                                ip_file = os.path.join(d, ff)
                                #fil_lista.append(ip_file)
                                #print 'zip file found on gate:', ip_file
                                break

                    # if ip file found on gate then exit else check on media
                    if ip_file:
                        aic_path = os.path.join( self.path_gate_reception, dirname )
                        aic_uuid = os.path.split(aic_path)[1]
                        ip.aic_uuid = aic_uuid
                        #ip = MyFile()
                        ip.directory = ip_file
                        ip.media = 'EFT'
                        #ip.uuid = ''
                        if ip_uuid is None:
                            self.filelist.append(ip)
                        elif ip.uuid == ip_uuid:
                            self.filelist = ip
                        #print '----- gate -----'
                        #print 'gate_aicpath', aic_path
                        #print 'gate_aicuuid', aic_uuid
                        #print 'gate_ipdir', ip.directory
                        #print 'gate_ipmedia', ip.media
                        #print 'gate_ipuuid', ip_uuid
                        #print 'gate_ip.uuid', ip.uuid
                        #print 'ip found at gate and success to read submit description'
                        logger.info('IP: %s found at gate and success to read submit description: %s' % (ip_file, submit_description_file))
                        break

                    else:
                        # check on media for ip file
                        for d, dn, f in os.walk( self.source_path ):
                            for ff in f:
                                if ff == ip_tarfile:
                                    ip_file = os.path.join(d, ff)
                                    #fil_lista.append(ip_file)
                                    #print 'tar file found on media:', ip_file
                                    aic_path = os.path.join( self.path_gate_reception, dirname )
                                    aic_uuid = os.path.split(aic_path)[1]
                                    ip.aic_uuid = aic_uuid
                                    #ip = MyFile()
                                    ip.directory = ip_file
                                    ip.media = os.path.split(d)[1].upper()
                                    #ip.uuid = ''
                                    if ip_uuid is None:
                                        self.filelist.append(ip)
                                    elif ip.uuid == ip_uuid:
                                        self.filelist = ip
                                    #print '---- media ----'
                                    #print 'media_aicpath', aic_path
                                    #print 'media_aicuuid', aic_uuid
                                    #print 'media_ipdir', ip.directory
                                    #print 'media_ipmedia', ip.media
                                    #print 'media_ipuuid', ip_uuid
                                    #print 'media_ip.uuid', ip.uuid
                                    #print 'ip found at media and success to read submit description'
                                    logger.info('IP: %s found at media and success to read submit description: %s' % (ip_file, submit_description_file))
                                    break

                    if not ip_file:
                        #print 'ip_file not found anywhere'
                        logger.error('IP: %s not found anywhere as stated in submit description: %s' % (ip_uuid, submit_description_file))

                    #fil_lista = ip_file
                    #fil_lista.append(ip_file_path)
                    #print 'submit_desc', submit_description_file
                    #print 'ip_file_path', ip_file_path

        #print '---- output ----'
        #print 'filelist', self.filelist
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
                         
                        filecontent = GetExchangeRequestFileContentTask.delay_or_fail(reqfilename)
                        filecontent_result = filecontent.get(timeout=30)
                        res_info = filecontent_result['res']
                        return_status_code = filecontent_result['status_code']
                        return_status_list = filecontent_result['status_list']
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
    model = ArchiveObject
    template_name='controlarea/fromrec.html'
    #template_name='archobject/list.html'
    queryset=ArchiveObject.objects.all()
    source_path = Path.objects.get(entity='path_reception').value
    path_gate_reception = Path.objects.get(entity='path_gate_reception').value
    Pmets_obj = Parameter.objects.get(entity='package_descriptionfile').value

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromReceptionListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromReceptionListView, self).get_context_data(**kwargs)
        originallist = MyFileList(source_path = self.source_path, path_gate_reception = self.path_gate_reception, mets_obj = self.Pmets_obj).get()
        context['filelist'] = sorted(originallist, key = attrgetter('EntryAgentIdentifierValue','label'))
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
    path_gate_reception = Path.objects.get(entity='path_gate').value
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
        ArchivePolicy_objs = ArchivePolicy.objects.filter(PolicyStat=1)
        if ArchivePolicy_objs:
            ArchivePolicy_obj = ArchivePolicy_objs[0]
            initial['POLICYID'] = ArchivePolicy_obj.PolicyID
            initial['INFORMATIONCLASS'] = ArchivePolicy_obj.INFORMATIONCLASS
        else:
            initial['POLICYID'] = 1
            initial['INFORMATIONCLASS'] = 1
        initial['DELIVERYTYPE'] = 'N/A'
        initial['DELIVERYSPECIFICATION'] = 'N/A'
        initial['allow_unknown_filetypes'] = True
        if 'ip_uuid' in self.kwargs:
            self.ip_obj = MyFileList(source_path = self.source_path, path_gate_reception = self.path_gate_reception, mets_obj = self.Pmets_obj).get(ip_uuid=self.kwargs['ip_uuid'])
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
        #status_code, status_detail = 
        ReqUUID = form.cleaned_data.get('ReqUUID',None)
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        ThisIPfromReception = CheckInFromMottagTask.delay_or_fail(source_path=self.source_path, 
                                                                target_path=self.target_path, 
                                                                Package=objectpath, 
                                                                ObjectIdentifierValue=ObjectIdentifierValue,
                                                                ReqUUID = ReqUUID,
                                                                ReqPurpose=ReqPurpose,
                                                                creator=None,
                                                                system=None,
                                                                version=None,
                                                                agent_list=[],
                                                                altRecordID_list=altRecordID_list,
                                                                allow_unknown_filetypes=allow_unknown_filetypes,
                                                                linkingAgentIdentifierValue=self.request.user.username
                                                                )
        '''if status_code:
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
        self.request.session['result_status_detail'] = status_detail'''
        taskid = ThisIPfromReception.task_id
        self.object.taskid = taskid
        self.object.save()
        self.success_url = '/controlarea/fromreceptionprogress/' + taskid
        return super(CheckinFromReception, self).form_valid(form)

class FromReceptionProgress(TemplateView):
    template_name = 'controlarea/fromreceptionprogress.html'

    @method_decorator(permission_required('controlarea.CheckinFromReception'))
    def dispatch(self, *args, **kwargs):
        return super(FromReceptionProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(FromReceptionProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context
'''class CheckinFromReceptionResult(DetailView):
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
        return context'''

'''class CheckoutToWorkListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='controlarea/towork.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWorkListView, self).get_context_data(**kwargs)
        #context['type'] = 'ToWork'
        context['label'] = 'Select which information package to checkout to work area'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5000,StatusActivity__in=[ 7, 8 ]):
                ip_list.append(ip)
               
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context'''

class ToWorkListInfoView(View):

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):    
        return super(ToWorkListInfoView, self).dispatch( *args, **kwargs)
        
    def get_towork_listinfo(self, *args, **kwargs):
        AICs_in_controlarea = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs_in_controlarea:
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(Q(UUID__StatusProcess=5000) | Q(UUID__StatusActivity=7))
            if len(AIC_IPs_query) > 0:
                AIC = {}           
                AIC_IPs = []
                for ip in AIC_IPs_query:
                        datainfo = ArchiveObjectData.objects.get(UUID=ip.UUID.ObjectUUID)
                        AIC['AIC_UUID'] =(str(obj.ObjectUUID))
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
                sortedAICs = sorted(AIC_list, key=itemgetter('Archivist_organization','Label'))   
        return sortedAICs

  
    def json_response(self, request):
        
        data = self.get_towork_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class ToWorkListTemplateView(TemplateView):
    template_name = 'controlarea/toworklist.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(ToWorkListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(ToWorkListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to checkout to work area'
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
        #status_code = None
            
        #toWork = TestTask.delay_or_fail(randomString = 'doWeGetAnyResult?')
        #toWork_result = toWork.get(timeout=180)
        #status_detail = [[toWork_result,'All is too well'],['All is well for now','Everything will only improve']]
        ObjectIdentifierValue=form.cleaned_data.get('ObjectIdentifierValue',None)
        ReqUUID=form.cleaned_data.get('ReqUUID',None)
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        linkingAgentIdentifierValue=self.request.user.username
        ThisIPtoWork = CheckOutToWorkTask.delay_or_fail(source_path=source_path, 
                                         target_path=target_path, 
                                         Package=objectpath, 
                                         a_uid=a_uid, 
                                         a_gid=a_gid, 
                                         a_mode=a_mode,
                                         read_only_access=read_only_access,
                                         ObjectIdentifierValue=ObjectIdentifierValue,
                                         ReqUUID=ReqUUID,
                                         ReqPurpose=ReqPurpose,
                                         linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                         )
        
       
        '''if status_code:
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
                                   )'''
                                   

        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        #return super(CheckoutToWork, self).form_valid(form)
        taskid = ThisIPtoWork.task_id
        self.object.taskid = taskid
        self.object.save()
        self.success_url = '/controlarea/toworkprogress/' + taskid
        # are you with me GIT?
        #self.success_url = self.get_success_url()
        return super(CheckoutToWork, self).form_valid(form)

class ToWorkProgress(TemplateView):
    template_name = 'controlarea/toworkprogress.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(ToWorkProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(ToWorkProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context

    '''def get_success_url(self):
    
        return '/taskinprogress/', {'label':'somelabel', 'taskid':1234 }'''
        


'''class CheckoutToWorkResult(DetailView):
    """
    View result for checkout to work
    """
    model = TaskMeta
    template_name='controlarea/detail.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToWorkResult, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckoutToWorkResult, self).get_context_data(**kwargs)
        context['label'] = 'CheckIn from Work'
        context['status'] = self.status
        context['result'] = self.result
        return context'''
'''class CheckoutToWorkResult(DetailView):
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
        return context'''

'''class CheckinFromWorkListView(ListView):
    """
    List control area AlteredTask
    """
    model = ArchiveObject
    template_name='controlarea/fromwork.html'
    #queryset=ArchiveObject.objects.filter(Q(StatusProcess=5100) | Q(OAISPackageType=1)).order_by('id','Generation')
    queryset=ArchiveObject.objects.filter(StatusProcess=5100).order_by('id','Generation')
    
    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromWorkListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(CheckinFromWorkListView, self).get_context_data(**kwargs)
        #context['type'] = 'FromWork'
        context['label'] = 'Select which information package to checkin from work area'
        ip_list = []
        aic_ip_list = []
        object_list = context['object_list']
        AIC_UUID_list = []
        aic_query = ArchiveObjectRel.objects.all()
        print aic_query
        for rel_obj in aic_query:
            AIC_UUID_UUID = [rel_obj.UUID.ObjectUUID,rel_obj.AIC_UUID.ObjectUUID]
            print AIC_UUID_UUID
            AIC_UUID_list.append(AIC_UUID_UUID)
        for obj in object_list:
            aic_ip_list.append(obj)
            for ip in obj.get_ip_list(StatusProcess=5100):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['aic_ip_list'] = aic_ip_list
        context['aic_uuid_list'] = AIC_UUID_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context'''

class FromWorkListInfoView(View):

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):    
        return super(FromWorkListInfoView, self).dispatch( *args, **kwargs)
        
    def get_fromwork_listinfo(self, *args, **kwargs):
        #AICs_in_workarea = ArchiveObject.objects.filter(StatusProcess=5000)
        AICs_in_workarea = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs_in_workarea:
            #AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(UUID__StatusProcess=5100)
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(Q(UUID__StatusProcess=5100) | Q(UUID__StatusActivity=8))
            if len(AIC_IPs_query) > 0:
                AIC = {}
                # AIC['AIC_UUID'] =(str(obj.ObjectUUID))            
                AIC_IPs = []
                for ip in AIC_IPs_query:
                        datainfo = ArchiveObjectData.objects.get(UUID=ip.UUID.ObjectUUID)
                        AIC['AIC_UUID'] =(str(obj.ObjectUUID))     
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
                sortedAICs = sorted(AIC_list, key=itemgetter('Archivist_organization','Label'))   
        return sortedAICs


  
    def json_response(self, request):
        
        data = self.get_fromwork_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class FromWorkListTemplateView(TemplateView):
    template_name = 'controlarea/fromworklist.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(FromWorkListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(FromWorkListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to checkin from work area'
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
        #status_code, status_detail = 
        ObjectIdentifierValue=form.cleaned_data.get('ObjectIdentifierValue',None)
        ReqUUID=form.cleaned_data.get('ReqUUID',None)
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        linkingAgentIdentifierValue=self.request.user.username
        ThisIPfromWork = CheckInFromWorkTask.delay_or_fail(source_path=source_path, 
                                          target_path=target_path, 
                                          Package=objectpath, 
                                          a_uid=a_uid, 
                                          a_gid=a_gid, 
                                          a_mode=a_mode,
                                          allow_unknown_filetypes=allow_unknown_filetypes,
                                          ObjectIdentifierValue=ObjectIdentifierValue,
                                          ReqUUID=ReqUUID,
                                          ReqPurpose=ReqPurpose,
                                          linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                          )
        '''if status_code:
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
                                   )'''
        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        #self.success_url = reverse_lazy('taskoverview')
        taskid = ThisIPfromWork.task_id
        self.object.taskid = taskid
        self.object.save()
        self.success_url = '/controlarea/fromworkprogress/' + taskid
        return super(CheckinFromWork, self).form_valid(form)

class FromWorkProgress(TemplateView):
    template_name = 'controlarea/fromworkprogress.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(FromWorkProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(FromWorkProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context
'''class CheckinFromWorkResult(DetailView):
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
        return context'''

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
        #status_code, tmp_status_detail = 
        ReqType = form.cleaned_data.get('ReqType')
        ReqPurpose = form.cleaned_data.get('ReqPurpose')
        user = form.cleaned_data.get('user')
        ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue')
        TimeZone = timezone.get_default_timezone_name()
        loc_timezone=pytz.timezone(TimeZone)
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        loc_dt_isoformat = dt.astimezone(loc_timezone).isoformat()
        #filelist = req_filelist
        reqfilename = os.path.join(target_path,'request.xml')
        linkingAgentIdentifierValue=self.request.user.username
        CopyFilelistTask_res = CopyFilelistTask.delay_or_fail(source_path = source_path,
                                        target_path = target_path,
                                        filelist = filelist,
                                        ReqUUID = ReqUUID, 
                                        ReqType = ReqType, 
                                        ReqPurpose = ReqPurpose, 
                                        user = user, 
                                        ObjectIdentifierValue = ObjectIdentifierValue, 
                                        posted = loc_dt_isoformat, 
                                        reqfilename=reqfilename,
                                        linkingAgentIdentifierValue=linkingAgentIdentifierValue
                                        )
        '''if status_code:
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
        CreateExchangeRequestFileTask.delay_or_fail(ReqUUID = form.cleaned_data.get('ReqUUID'), 
                                                  ReqType = form.cleaned_data.get('ReqType'), 
                                                  ReqPurpose = form.cleaned_data.get('ReqPurpose'), 
                                                  user = form.cleaned_data.get('user'), 
                                                  ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue'), 
                                                  posted = loc_dt_isoformat, 
                                                  filelist = req_filelist, 
                                                  reqfilename = os.path.join(target_path,'request.xml'),
                                                  )'''
        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        CopyFilelistTask_id = CopyFilelistTask_res.task_id
        self.object.taskid = CopyFilelistTask_id
        #print ('Task ID')
        #print (self.object.taskid)
        self.object.save()
        self.success_url = '/controlarea/checkouttogateprogress/' +  CopyFilelistTask_id
        return super(CheckoutToGateFromWork, self).form_valid(form)

'''class CheckoutToGateFromWorkResult(DetailView):
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
        return context'''

class CheckoutToGateProgress(TemplateView):
    template_name = 'controlarea/checkouttogateprogress.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckoutToGateProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CheckoutToGateProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
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
        #status_code, tmp_status_detail =  
        ReqType = form.cleaned_data.get('ReqType') 
        ReqPurpose = form.cleaned_data.get('ReqPurpose') 
        user = form.cleaned_data.get('user')
        ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue')
        TimeZone = timezone.get_default_timezone_name()
        loc_timezone=pytz.timezone(TimeZone)
        dt = datetime.datetime.utcnow().replace(microsecond=0,tzinfo=pytz.utc)
        posted = dt.astimezone(loc_timezone).isoformat()
        #filelist = req_filelist, 
        reqfilename = os.path.join(target_path,'request.xml')
        linkingAgentIdentifierValue=self.request.user.username        
        CopyFilelistTask_res = CopyFilelistTask.delay_or_fail(source_path=source_path,
                                        target_path=target_path,
                                        filelist=filelist,
                                        ReqUUID = ReqUUID, 
                                        ReqType = ReqType, 
                                        ReqPurpose = ReqPurpose, 
                                        user = user, 
                                        ObjectIdentifierValue = ObjectIdentifierValue, 
                                        posted = posted, 
                                        reqfilename = reqfilename,
                                        linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                                  )
        '''if status_code:
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
        CreateExchangeRequestFileTask.delay_or_fail(ReqUUID = form.cleaned_data.get('ReqUUID'), 
                                                  ReqType = form.cleaned_data.get('ReqType'), 
                                                  ReqPurpose = form.cleaned_data.get('ReqPurpose'), 
                                                  user = form.cleaned_data.get('user'), 
                                                  ObjectIdentifierValue = form.cleaned_data.get('ObjectIdentifierValue'), 
                                                  posted = loc_dt_isoformat, 
                                                  filelist = req_filelist, 
                                                  reqfilename = os.path.join(target_path,'request.xml'),
                                                  )'''
        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        CopyFilelistTask_id = CopyFilelistTask_res.task_id
        self.object.taskid = CopyFilelistTask_id
        #print ('Task ID')
        #print (self.object.taskid)
        self.object.save()
        self.success_url = '/controlarea/checkinfromgateprogress/' +  CopyFilelistTask_id
        return super(CheckinFromGateToWork, self).form_valid(form)

class CheckinFromGateProgress(TemplateView):
    template_name = 'controlarea/checkinfromgateprogress.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(CheckinFromGateProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(CheckinFromGateProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context

'''class CheckinFromGateToWorkResult(DetailView):
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
        return context'''

class DiffCheckListInfoView(View):

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):    
        return super(DiffCheckListInfoView, self).dispatch( *args, **kwargs)
        
    def get_diffcheck_listinfo(self, *args, **kwargs):
        AICs_in_controlarea = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs_in_controlarea:
            #AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID, UUID__StatusProcess=5000)
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(Q(UUID__StatusProcess=5000) | Q(UUID__StatusActivity=7))
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
                sortedAICs = sorted(AIC_list, key=itemgetter('Archivist_organization','Label'))   
        return sortedAICs
   

  
    def json_response(self, request):
        
        data = self.get_diffcheck_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class DiffCheckListTemplateView(TemplateView):
    template_name = 'controlarea/diffchecklist.html'

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(DiffCheckListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(DiffCheckListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to DiffCheck'
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
        ObjectIdentifierValue=form.cleaned_data.get('ObjectIdentifierValue')#self.ip_obj.ObjectUUID
        #print'ObjectIdentifierValue'
        #print ObjectIdentifierValue
        #print ObjectIdentifierValue[0]
        ObjectPath=IP_ObjectPath
        ReqUUID=form.cleaned_data.get('ReqUUID',None)
        linkingAgentIdentifierValue=self.request.user.username
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        self.object.save()
        IPtoDiffcheck = DiffCheckTask.delay_or_fail(ObjectIdentifierValue=ObjectIdentifierValue,
                                    ObjectPath=ObjectPath, 
                                    METS_ObjectPath=METS_ObjectPath,
                                    ReqUUID=ReqUUID,
                                    linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                    ReqPurpose=ReqPurpose,
                                    )

        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        diffchecktaskid = IPtoDiffcheck.task_id
        self.object.taskid = diffchecktaskid
        #print ('Task ID')
        #print (self.object.taskid)
        self.object.save()
        #self.success_url = reverse_lazy('taskoverview')
        #self.success_url = '/controlarea/diffcheckprogress/' + taskid
        self.success_url = '/controlarea/diffcheckprogress/' + diffchecktaskid
        return super(DiffCheck, self).form_valid(form)

class DiffcheckProgress(TemplateView):
    template_name = 'controlarea/diffcheckprogress.html'

    @method_decorator(permission_required('controlarea.CheckinFromWork'))
    def dispatch(self, *args, **kwargs):
        return super(DiffcheckProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(DiffcheckProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context
    
'''class DiffCheckResult(DetailView):
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
        return context'''

'''class PreserveIPListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='controlarea/preserveIP.html'
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=5000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveIPListView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(PreserveIPListView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to preserve in archive'
        ip_list = []
        object_list = context['object_list']
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=5000):
                ip_list.append(ip)
        context['ip_list'] = ip_list
        context['PackageType_CHOICES'] = dict(PackageType_CHOICES)
        context['StatusProcess_CHOICES'] = dict(StatusProcess_CHOICES)
        return context'''

class PreserveListInfoView(View):

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):    
        return super(PreserveListInfoView, self).dispatch( *args, **kwargs)
        
    def get_preserve_listinfo(self, *args, **kwargs):
        AICs_in_controlarea = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs_in_controlarea:
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(UUID__StatusProcess=5000)
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
                    AIC_IP['create_date'] = str( ip.UUID.EntryDate)[:10]
                    AIC['create_date'] =str( ip.UUID.EntryDate)[:10]
                    AIC_IP['Generation'] = str(ip.UUID.Generation)
                    AIC_IP['startdate'] = str(datainfo.startdate)[:10]
                    AIC['startdate'] = str(datainfo.startdate)[:10]
                    AIC_IP['enddate'] = str(datainfo.enddate)[:10]
                    AIC['enddate'] = str(datainfo.enddate)[:10]
                    AIC_IP['Process'] = ip.UUID.StatusProcess
                    AIC_IP['Activity'] = ip.UUID.StatusActivity
                    AIC_IPs.append(AIC_IP)
                AIC['IPs'] = AIC_IPs
                AIC_list.append(AIC)
                sortedAICs = sorted(AIC_list, key=itemgetter('Archivist_organization','Label'))   
        return sortedAICs  
   

  
    def json_response(self, request):
        
        data = self.get_preserve_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class PreserveTemplateView(TemplateView):
    template_name = 'controlarea/preserveIPlist.html'

    @method_decorator(permission_required('controlarea.DiffCheck'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(PreserveTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to preserve in archive'
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
        linkingAgentIdentifierValue = form.cleaned_data.get('user',None)
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        ObjectIdentifierValue=form.cleaned_data.get('ObjectIdentifierValue',None)
        ReqUUID=form.cleaned_data.get('ReqUUID',None)
        #status_code, status_detail = 
        IPtoPreserve = PreserveIPTask.delay_or_fail(source_path=source_path,
                                    target_path=target_path, 
                                    Package=objectpath, 
                                    a_uid=a_uid, 
                                    a_gid=a_gid, 
                                    a_mode=a_mode,
                                    linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                    ReqPurpose=ReqPurpose,
                                    ObjectIdentifierValue=ObjectIdentifierValue,
                                    ReqUUID=ReqUUID,
                                    )
        '''if status_code:
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
            self.ip_obj.save()'''
        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        taskid = IPtoPreserve.task_id
        self.object.taskid = taskid
        self.object.save()
        self.success_url = '/controlarea/preserveprogress/' + taskid
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

class PreserveProgress(TemplateView):
    template_name = 'controlarea/preserveprogress.html'

    @method_decorator(permission_required('controlarea.PreserveIP'))
    def dispatch(self, *args, **kwargs):
        return super(PreserveProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(PreserveProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context
'''class PreserveIPResult(DetailView):
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
        return context'''
    
'''class ControlareaDeleteIPListView(ListView):
    """
    List control area
    """
    model = ArchiveObject
    template_name='controlarea/controlareadeletelist.html'
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
        return context'''

class DeleteIPListInfoView(View):

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):    
        return super(DeleteIPListInfoView, self).dispatch( *args, **kwargs)
        
    def get_deleteip_listinfo(self, *args, **kwargs):
        AICs = ArchiveObject.objects.filter(OAISPackageType=1)
        AIC_list = []
        for obj in AICs:
            #AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(UUID__StatusProcess__in=[5000,5100])
            AIC_IPs_query = ArchiveObjectRel.objects.filter(AIC_UUID=obj.ObjectUUID).filter(Q(UUID__StatusProcess__in=[5000,5100]) | Q(UUID__StatusActivity__in=[ 7, 8 ])).order_by('UUID__Generation')
            if len(AIC_IPs_query)> 0:
                AIC = {}           
                AIC_IPs = []
                AIC['AIC_UUID'] =(str(obj.ObjectUUID)) 
                lastgeneration =  AIC_IPs_query.filter(UUID__StatusProcess__in=[5000,5100]).aggregate(Max('UUID__Generation')).values()[0]
                #print 'lastgeneration'
                #print lastgeneration
                excludelist = []
                for pp in AIC_IPs_query:
                    if pp.UUID.StatusProcess == 3000:
                        excludelist.append(pp) 
                    else:
                        if 0 < pp.UUID.Generation < lastgeneration:
                            excludelist.append(pp)
                for ip in excludelist:                   
                        datainfo = ArchiveObjectData.objects.get(UUID=ip.UUID.ObjectUUID)                    
                        AIC_IP = {}
                        AIC_IP['id'] = ip.UUID.id
                        AIC_IP['ObjectUUID'] = str(ip.UUID.ObjectUUID)
                        AIC_IP['Archivist_organization'] = ip.UUID.EntryAgentIdentifierValue
                        AIC['Archivist_organization'] = ip.UUID.EntryAgentIdentifierValue
                        AIC_IP['Label'] = datainfo.label
                        AIC['Label'] = datainfo.label
                        AIC_IP['create_date'] =str( ip.UUID.EntryDate)[:10]
                        AIC['create_date'] = str(ip.UUID.EntryDate)[:10]
                        AIC_IP['Generation'] = ip.UUID.Generation
                        AIC_IP['startdate'] = str(datainfo.startdate)[:10]
                        AIC['startdate'] = str(datainfo.startdate)[:10]
                        AIC_IP['enddate'] = str(datainfo.enddate)[:10]
                        AIC['enddate'] = str(datainfo.enddate)[:10]
                        AIC_IP['Process'] = ip.UUID.StatusProcess
                        AIC_IP['Activity'] = ip.UUID.StatusActivity
                        AIC_IPs.append(AIC_IP)
                if len(AIC_IPs) > 0:
                    AIC['IPs'] = AIC_IPs
                    AIC_list.append(AIC)
                sortedAICs = sorted(AIC_list, key=itemgetter('Archivist_organization','Label'))   
        return sortedAICs
 

  
    def json_response(self, request):
        
        data = self.get_deleteip_listinfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):        
        return self.json_response(request)

class DeleteIPListTemplateView(TemplateView):
    template_name = 'controlarea/controlareadeletelist.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(DeleteIPListTemplateView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(DeleteIPListTemplateView, self).get_context_data(**kwargs)
        context['label'] = 'Select which information package to delete in control/work area'
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
        #status_code, status_detail = 
        ObjectIdentifierValue=form.cleaned_data.get('ObjectIdentifierValue',None)
        ReqUUID=form.cleaned_data.get('ReqUUID',None)
        ReqPurpose=form.cleaned_data.get('ReqPurpose','')
        linkingAgentIdentifierValue=self.request.user.username
        Package=objectpath
        DeleteIP = DeleteIPTask.delay_or_fail(source_path=source_path, 
                                   target_path=target_path, 
                                   Package=Package,
                                   ObjectIdentifierValue=ObjectIdentifierValue,                        
                                   ReqUUID=ReqUUID,
                                   ReqPurpose=ReqPurpose,
                                   linkingAgentIdentifierValue=linkingAgentIdentifierValue,
                                   )
        '''if status_code:
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
                self.ip_obj.save()'''
        #self.request.session['result_status_code'] = status_code
        #self.request.session['result_status_detail'] = status_detail
        deletetaskid = DeleteIP.task_id
        self.success_url = '/controlarea/deleteprogress/' + deletetaskid
        return super(ControlareaDeleteIP, self).form_valid(form)

class DeleteProgress(TemplateView):
    template_name = 'controlarea/deleteprogress.html'

    @method_decorator(permission_required('controlarea.CheckoutToWork'))
    def dispatch(self, *args, **kwargs):
        return super(DeleteProgress, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(DeleteProgress, self).get_context_data(**kwargs)
        context['taskid'] = self.kwargs['taskid']
        return context
        
'''class ControlareaDeleteIPResult(DetailView):
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
        return context'''

class TasksInfo(View):

    
    def dispatch(self, *args, **kwargs):
    
        return super(TasksInfo, self).dispatch( *args, **kwargs)
        
    def getTaskInfo(self, *args, **kwargs):

        numberofdays = int(self.kwargs['days'])
        #print 'numberofdays'
        #print numberofdays

        enddate = datetime.datetime.now()
        #print 'enddate'
        #print enddate

        startdate = enddate - datetime.timedelta(days=numberofdays)
        #print 'startdate'
        #print startdate

        allTasks = TaskMeta.objects.filter(date_done__range=[startdate, enddate]).order_by('date_done').reverse()

        Tasks = {}
        FailedTasks = []
        PendingTasks = []
        ProgressTasks = []
        SuccessTasks = []
        for t in allTasks:
            Task = {
            'taskid': t.task_id,
            'status' : t.status,
            'result' : jsonpickle.encode(t.result)
            }
            if t.status == 'FAILURE':
                if ControlAreaQueue.objects.filter(taskid=t.task_id).exists():                    
                    taskinfo = ControlAreaQueue.objects.filter(taskid=t.task_id)
                    for s in taskinfo:
                        info = {}
                        info['reqpurpose'] = s.ReqPurpose
                        info['user'] = s.user
                        Task['info'] = json.dumps(info)                
                FailedTasks.append(Task)                
            elif t.status == 'PENDING':
                PendingTasks.append(Task)
            elif t.status == 'PROGRESS':                
                if ControlAreaQueue.objects.filter(taskid=t.task_id).exists():                    
                    taskinfo = ControlAreaQueue.objects.filter(taskid=t.task_id)
                    for s in taskinfo:
                        info = {}
                        info['reqpurpose'] = s.ReqPurpose
                        info['user'] = s.user
                        Task['info'] = json.dumps(info)
                        ProgressTasks.append(Task)
            elif t.status =='SUCCESS':
                if t.result is not None:
                        Task['datedone'] = str(t.date_done)[:10]
                        SuccessTasks.append(Task)                
        Tasks['FailedTasks'] = FailedTasks
        Tasks['PendingTasks'] = PendingTasks
        Tasks['ProgressTasks'] = ProgressTasks
        Tasks['SuccessTasks'] = SuccessTasks
        return Tasks

    def json_response(self, request):
        
        data = self.getTaskInfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):
        
        return self.json_response(request)

class TaskOverviewView(TemplateView):
    template_name = 'controlarea/taskoverview.html'

    #@method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(TaskOverviewView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(TaskOverviewView, self).get_context_data(**kwargs)
        return context

        
        
class ProgressTasksInfo(View):

    #@method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
    
        return super(ProgressTasksInfo, self).dispatch( *args, **kwargs)
        
    def getTaskInfo(self, *args, **kwargs):

        progressTasks = TaskMeta.objects.filter(status='PROGRESS')
        Tasks = []
        for t in progressTasks:
            progressinfo = ControlAreaQueue.objects.filter(taskid=t.task_id)
            for p in progressinfo:
                Task = {
                'user' : p.user,
                'reqpurpose': p.ReqPurpose,
                'status' : t.status,
                'result': json.dumps(t.result)
                }
                Tasks.append(Task)
        return Tasks

    def json_response(self, request):
        
        data = self.getTaskInfo()
        return HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder)
            #,mimetype='application/json'
        )

    def get(self, request, *args, **kwargs):
        
        return self.json_response(request)

class TestTaskView(TemplateView):
    template_name = 'controlarea/testtask.html'

    #@method_decorator(permission_required('essarch.list_storageMedium'))
    def dispatch(self, *args, **kwargs):
        return super(TestTaskView, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):

        context = super(TestTaskView, self).get_context_data(**kwargs)
        TestString = 'Teststring'
        if 'time' in self.kwargs:           
            timetorun = int(self.kwargs['time'])
        else:
            timetorun = 5
        logger.info('timetorun: %s' % timetorun)
        TestToSeeTasks = TestTask.delay_or_fail(TestString=TestString,timetorun=timetorun)
        context['task_id'] = TestToSeeTasks.task_id
        context['result'] = TestToSeeTasks.result
        return context
    
class TaskResult(View):

    
    def dispatch(self, *args, **kwargs):
    
        return super(TaskResult, self).dispatch( *args, **kwargs)
        
    def getTaskResult(self, *args, **kwargs):
        taskwrapper = {}
        task = {}
        thetaskid = self.kwargs['taskid']
        #print (thetaskid)
        
        kwargstest = TaskMeta.objects.filter(task_id=thetaskid).exists()
        #print (kwargstest)
        if kwargstest:
            #cache._cache.clear()
            thetask = TaskMeta.objects.filter(task_id=thetaskid)
            task['status'] = thetask[0].status
            task['result']  =  thetask[0].result
            task['id'] = thetaskid
        else:
            task['status'] = 'notaskfound'
            task['result'] = 'notaskfound'
            task['id'] = thetaskid
        taskwrapper['task'] = task
        finishedtask = jsonpickle.encode(taskwrapper)
        return finishedtask

    def json_response(self, request):
        
        data = self.getTaskResult()
        return HttpResponse(
            data
            #json.dumps(data, cls=DjangoJSONEncoder)
        )
    def get(self, request, *args, **kwargs):
        
        return self.json_response(request)

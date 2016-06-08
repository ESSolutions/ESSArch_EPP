'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2015  ES Solutions AB

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
try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
else:
    __version__ = epp.__version__

import os.path
import shutil
import sys
import traceback
import datetime
import uuid
from django.views.generic.base import TemplateView
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from configuration.models import (
                                  Path,
                                  Parameter,
                                  )
from api.models import (
                        TmpWorkareaUpload,
                        GateareaUpload,
                        )
from api.serializers import (
                        ArchiveObjectSerializer,
                        ArchiveObjectPlusAICPlusStorageNestedReadSerializer,
                        ArchiveObjectPlusAICPlusStorageNestedWriteSerializer,
                        AICObjectSerializer,
                        ArchivePolicySerializer,
                        ArchivePolicyNestedSerializer,
                        StorageMethodSerializer,
                        StorageTargetSerializer,
                        StorageTargetsSerializer,
                        storageMediumSerializer,
                        storageSerializer,
                        storageNestedReadSerializer,
                        storageNestedWriteSerializer,
                        IOQueueSerializer,
                        IOQueueNestedReadSerializer,
                        IOQueueNestedWriteSerializer,
                        ArchiveObjectRelSerializer,
                        ApplyStorageMethodTapeSerializer,
                        ApplyStorageMethodDiskSerializer,
                        MoveToAccessPathSerializer,
                        ProcessStepSerializer,
                        ProcessTaskSerializer,
                        ProcessStepNestedReadSerializer,
                        ArchiveObjectPlusAICPlusProcessNestedReadSerializer,
                        )
from essarch.models import (ArchiveObject, 
                            ArchiveObjectRel,
                            ProcessStep,
                            ProcessTask
                            )
from configuration.models import (ArchivePolicy,
                                                StorageMethod,
                                                StorageTarget,
                                                StorageTargets,
                                                )
from Storage.models import (storageMedium,
                                        storage,
                                        IOQueue,
                                        )
from rest_framework import viewsets, mixins, permissions, views
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
#from rest_framework.renderers import JSONRenderer
from celery.result import AsyncResult
from StorageMethodDisk.tasks import WriteStorageMethodDisk, ReadStorageMethodDisk
from StorageMethodTape.tasks import WriteStorageMethodTape, ReadStorageMethodTape
from Storage.tasks import MoveToAccessPath
from django.db.models import Q
from django import forms
from esscore.views.datatables import DatatableBaseView

class AICListView(TemplateView):
    template_name = 'api/aic_list.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AICListView, self).dispatch( *args, **kwargs)

class ArchiveObjectListView(TemplateView):
    template_name = 'api/ip_list.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(ArchiveObjectListView, self).dispatch( *args, **kwargs)

class ArchiveObject_dt_view(DatatableBaseView):
    qs =  ArchiveObject.objects.filter(
                               Q(OAISPackageType=1) | 
                               Q(OAISPackageType__in=[0,2], archiveobjects__isnull=True, aic_set__isnull=True)).distinct()
    columns = ['id', 'ObjectUUID', 
          'PolicyId.PolicyID', 'ObjectIdentifierValue',
          'ObjectPackageName', 'ObjectSize',
          'ObjectNumItems', 'ObjectMessageDigestAlgorithm',
          'ObjectMessageDigest', 'ObjectPath',
          'ObjectActive', 'MetaObjectIdentifier',
          'MetaObjectSize', 'CMetaMessageDigestAlgorithm',
          'CMetaMessageDigest', 'PMetaMessageDigestAlgorithm',
          'PMetaMessageDigest', 'DataObjectSize',
          'DataObjectNumItems', 'Status',
          'StatusActivity', 'StatusProcess',
          'LastEventDate', 'linkingAgentIdentifierValue',
          'CreateDate', 'CreateAgentIdentifierValue',
          'EntryDate', 'EntryAgentIdentifierValue',
          'OAISPackageType', 'preservationLevelValue',
          'DELIVERYTYPE', 'INFORMATIONCLASS',
          'Generation', 'LocalDBdatetime',
          'ExtDBdatetime', 'archiveobjects',
          'ObjectMetadata.label', 'ObjectMetadata.startdate',
          'ObjectMetadata.enddate']
    order_columns = ['id', 'ObjectIdentifierValue', 'EntryAgentIdentifierValue', 
                     'ObjectMetadata.label', 'EntryDate', 
                     'ObjectMetadata.startdate', 'ObjectMetadata.enddate', 
                     'OAISPackageType', 'Generation', 
                     'StatusProcess', 'StatusActivity']
    columns_archiveobjectdata_set = ['creator', 'label', 'startdate', 'enddate']
    #datetime_format = "%Y-%m-%d %H:%M"
    datetime_format = "%Y-%m-%d"

    def render_column(self, row, column):
        """ Renders a column on a row
        """
        if hasattr(row, 'get_%s_display' % column):
            # It's a choice field
            text = getattr(row, 'get_%s_display' % column)()
        else:
            try:
                text = getattr(row, column)
            except AttributeError:
                obj = row
                for part in column.split('.'):
                    if obj is None or hasattr(obj, 'all'):
                        break
                    if obj:
                        obj = getattr(obj, part)
                text = obj

        if text is None:
            text = self.none_string
        
        if hasattr(text,'all'):
            data = []
            if column == 'archiveobjects': 
                qs = self.filter_ip_queryset(text)
                qs = qs.order_by('Generation') # Sort order for related IPs to AIC
                columns = self.get_columns()
            elif column == 'columns_archiveobjectdata_set':
                qs = text.all()
                columns = self.columns_archiveobjectdata_set
            for item in qs:
                d={}
                for col in columns:
                    d[col]=self.render_column(item, col)
                data.append(d)
            text=data

        if column in ['Generation', 'StatusProcess']  and row.OAISPackageType == 1: # Remove field for AICs
            text = ''
        elif column == 'Generation' and row.OAISPackageType in [0, 2] and len(str(text))>0:
            text = 'IP_%s' % text
            
        if column == 'StatusActivity' and row.OAISPackageType != 1:
            enable_StatusActivity_selection = self._querydict.get('enable_StatusActivity_selection', None)
            if enable_StatusActivity_selection:
                if enable_StatusActivity_selection == 'true':
                    setactivity = 'setactivity(event,"%s")' % row.ObjectUUID
                    StatusActivityChoices = row._meta.get_field_by_name('StatusActivity')[0].choices
                    f = forms.ChoiceField(widget=forms.Select(attrs={'onchange':setactivity}), choices=StatusActivityChoices)
                    text = f.widget.render('selectstatusactivity', row.StatusActivity)
        elif column == 'StatusActivity': # Disable change of StatusActivity for AICs
            text = ''
        
        if column in ['EntryDate', 'ObjectMetadata.startdate', 'ObjectMetadata.enddate']:
            if type(text) is datetime.datetime:
                try:
                    res = text.strftime(self.datetime_format)
                except ValueError as e:
                    res = str(text)
                return res
        
        if text and hasattr(row, 'get_absolute_url') and self.absolute_url_link_flag:
            return '<a href="%s">%s</a>' % (row.get_absolute_url(), text)
        else:
            return text

    def filter_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            # get global search value
            search = self._querydict.get('search[value]', None)
            if search is not None:
                if not search.startswith('%ip'):
                    col_data = self.extract_datatables_column_data()
                    q = Q()
                    for col_no, col in enumerate(col_data):
                        # apply global search to all searchable columns
                        if search and col['searchable']:
                            #q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
                            if col['name']:
                                q |= Q(**{'{0}__icontains'.format(col['name'].replace('.', '__')): search})
                            else:
                                print 'WARNING - colums.name is not defined in datatables'
        
                        # column specific filter
                        if col['search.value']:
                            #qs = qs.filter(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): col['search.value']})
                            if col['name']:
                                qs = qs.filter(**{'{0}__icontains'.format(col['name'].replace('.', '__')): col['search.value']})
                            else:
                                print 'WARNING - colums.name is not defined in datatables'                    
                    qs = qs.filter(q)
                else:
                    search = search.strip('%ip')
                    #qs = qs.filter(archiveobjects__ObjectIdentifierValue__icontains=search)
                    col_data = self.extract_datatables_column_data()
                    q = Q()
                    for col_no, col in enumerate(col_data):
                        # apply global search to all searchable columns
                        if search and col['searchable']:
                            #q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
                            if col['name']:
                                q |= Q(**{'archiveobjects__{0}__icontains'.format(col['name'].replace('.', '__')): search})
                            else:
                                print 'WARNING - colums.name is not defined in datatables'
                    qs = qs.filter(q)
            #for x in qs:
                #print '###### Object: %s archiveobjects: %s' % (x.ObjectIdentifierValue, x.archiveobjects.count())
            qs = self.filter_extra_queryset(qs)
        return qs
    
    def filter_ip_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            ip_search_global = False
            if ip_search_global:
                # get global search value
                search = self._querydict.get('search[value]', None)
                if search is not None:
                    if search.startswith('%ip'):
                        search = search.strip('%ip')
                        col_data = self.extract_datatables_column_data()
                        q = Q()
                        for col_no, col in enumerate(col_data):
                            # apply global search to all searchable columns
                            if search and col['searchable']:
                                q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
            
                        qs = qs.filter(q)

            # IP specific filter
            archiveobjects__StatusProcess__lt = self._querydict.get('archiveobjects__StatusProcess__lt', None)
            archiveobjects__StatusProcess__in = self._querydict.get('archiveobjects__StatusProcess__in', None)
            archiveobjects__StatusActivity__in = self._querydict.get('archiveobjects__StatusActivity__in', None)
            archiveobjects__StatusProcess_or_StatusActivity__in = self._querydict.get('archiveobjects__StatusProcess_or_StatusActivity__in', None)
            archiveobjects__exclude_generation_0_and_latest = self._querydict.get('archiveobjects__exclude_generation_0_and_latest', None)
            if archiveobjects__StatusProcess__lt:
                qs = qs.filter(StatusProcess__lt = archiveobjects__StatusProcess__lt)
            if archiveobjects__StatusProcess__in:
                qs = qs.filter(StatusProcess__in = eval(archiveobjects__StatusProcess__in))
            if archiveobjects__StatusActivity__in:
                qs = qs.filter(StatusActivity__in = eval(archiveobjects__StatusActivity__in))
            if archiveobjects__StatusProcess_or_StatusActivity__in:
                StatusProcess__in, StatusActivity__in = eval(archiveobjects__StatusProcess_or_StatusActivity__in)
                qs = qs.filter(Q(StatusProcess__in = StatusProcess__in) | Q(StatusActivity__in = StatusActivity__in))
            if archiveobjects__exclude_generation_0_and_latest:
                if archiveobjects__exclude_generation_0_and_latest == 'true':
                    if qs.count() > 0:
                        qs2 =  ArchiveObject.objects.filter(
                                                            Q(OAISPackageType=1) | 
                                                            Q(OAISPackageType__in=[0,2], archiveobjects__isnull=True, aic_set__isnull=True)).distinct()
                        latest_generation = qs[0].aic_set.get().archiveobjects.order_by('-Generation')[:1].get()
                        qs = qs.exclude(StatusProcess__in=[5000,5100], Generation__in=[0,latest_generation.Generation])
                    else:
                        qs = qs.exclude(Generation=0)

        return qs
    
    def filter_extra_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            # Extra IP filter
            StatusProcess__lt = self._querydict.get('StatusProcess__lt', None)
            StatusProcess__in = self._querydict.get('StatusProcess__in', None)
            StatusActivity__in = self._querydict.get('StatusActivity__in', None)
            StatusProcess_or_StatusActivity__in = self._querydict.get('StatusProcess_or_StatusActivity__in', None)
            exclude_ip_without_aic = self._querydict.get('exclude_ip_without_aic', None)
            #exclude_aic_without_ips = self._querydict.get('exclude_aic_without_ips', None)
            ip_q = Q(OAISPackageType__in = [0, 2])
            if StatusProcess__lt:
                ip_q &= Q(StatusProcess__lt = StatusProcess__lt)
            if StatusProcess__in:
                ip_q &= Q(StatusProcess__in = eval(StatusProcess__in))
            if StatusActivity__in:
                ip_q &= Q(StatusActivity__in = eval(StatusActivity__in))
            if StatusProcess_or_StatusActivity__in:                
                StatusProcess__in, StatusActivity__in = eval(StatusProcess_or_StatusActivity__in)
                ip_q &= Q(Q(StatusProcess__in = StatusProcess__in) | Q(StatusActivity__in = StatusActivity__in))
            
            # Extra AIC filter
            archiveobjects__StatusProcess__lt = self._querydict.get('archiveobjects__StatusProcess__lt', None)
            archiveobjects__StatusProcess__in = self._querydict.get('archiveobjects__StatusProcess__in', None)
            archiveobjects__StatusActivity__in = self._querydict.get('archiveobjects__StatusActivity__in', None)
            archiveobjects__StatusProcess_or_StatusActivity__in = self._querydict.get('archiveobjects__StatusProcess_or_StatusActivity__in', None)
            aic_q = Q(OAISPackageType=1)
            if archiveobjects__StatusProcess__lt:
                aic_q &= Q(archiveobjects__StatusProcess__lt = archiveobjects__StatusProcess__lt)
            if archiveobjects__StatusProcess__in:
                aic_q &= Q(archiveobjects__StatusProcess__in = eval(archiveobjects__StatusProcess__in))
            if archiveobjects__StatusActivity__in:
                aic_q &= Q(archiveobjects__StatusActivity__in = eval(archiveobjects__StatusActivity__in))
            if archiveobjects__StatusProcess_or_StatusActivity__in:
                StatusProcess__in, StatusActivity__in = eval(archiveobjects__StatusProcess_or_StatusActivity__in)
                aic_q &= Q(Q(archiveobjects__StatusProcess__in = StatusProcess__in) | Q(archiveobjects__StatusActivity__in = StatusActivity__in))
            
            qs = qs.filter(Q(ip_q) | Q(aic_q))
            
            if exclude_ip_without_aic:
                if exclude_ip_without_aic == 'true':
                    qs = qs.exclude(OAISPackageType__in=[0,2], aic_set__isnull=True)

            #if exclude_aic_without_ips:
            #   if exclude_aic_without_ips == 'true':
            #        qs = qs.exclude(OAISPackageType=1, archiveobjects__isnull=True)

        return qs

    def prepare_results(self, qs):
        data = []
        exclude_aic_without_ips = self._querydict.get('exclude_aic_without_ips', None)
        for item in qs:
            d={}
            for column in self.get_columns():
                d[column]=self.render_column(item, column)
            if exclude_aic_without_ips:
                if exclude_aic_without_ips == 'true':
                    if d['OAISPackageType'] == 'AIC' and len(d['archiveobjects']) == 0: # Skip AICs with no IPs
                        pass
                    else:
                        data.append(d)
            else:
                data.append(d)
        return data

class TmpWorkareaUploadView(TemplateView):
    template_name = 'api/tmpworkarea_upload.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(TmpWorkareaUploadView, self).dispatch( *args, **kwargs)

class CreateTmpWorkareaUploadView(views.APIView, ChunkedUploadView):

    model = TmpWorkareaUpload
    field_name = 'the_file'
    permission_classes = (permissions.IsAuthenticated,)

class CreateTmpWorkareaUploadCompleteView(views.APIView, ChunkedUploadCompleteView):

    model = TmpWorkareaUpload
    permission_classes = (permissions.IsAuthenticated,)

    def on_completion(self, uploaded_file, request):
        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        #print dir(uploaded_file)
        #print 'filename: %s, type(file): %s' % (uploaded_file.name, type(uploaded_file.file))
        pass
    
    def move_to_destination(self, chunked_upload):
        """
        Move file to destination path and remove uploaded file from database
        """
        try:
            TmpWorkarea_upload_root =  Path.objects.get(entity='TmpWorkarea_upload_path').value
        except  Path.DoesNotExist as e:
            TmpWorkarea_upload_root = settings.MEDIA_ROOT
        
        tmp_file_path = chunked_upload.file.path
        dest_file_path = os.path.join(TmpWorkarea_upload_root, chunked_upload.filename)
        #print 'Move tmp_file_path: %s to dest_path: %s' % (tmp_file_path, dest_file_path)
        shutil.move(tmp_file_path, dest_file_path)
        chunked_upload.delete(delete_file=True)

    def get_response_data(self, chunked_upload, request):
        self.move_to_destination(chunked_upload)
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
                            (chunked_upload.filename, chunked_upload.offset))}

class CreateGateUploadView(views.APIView, ChunkedUploadView):

    model = GateareaUpload
    field_name = 'the_file'
    permission_classes = (permissions.IsAuthenticated,)

class CreateGateUploadCompleteView(views.APIView, ChunkedUploadCompleteView):

    model = GateareaUpload
    permission_classes = (permissions.IsAuthenticated,)

    def on_completion(self, uploaded_file, request):
        # Do something with the uploaded file. E.g.:
        # * Store the uploaded file on another model:
        # SomeModel.objects.create(user=request.user, file=uploaded_file)
        # * Pass it as an argument to a function:
        # function_that_process_file(uploaded_file)
        #print dir(uploaded_file)
        #print 'filename: %s, type(file): %s' % (uploaded_file.name, type(uploaded_file.file))
        pass

    def move_to_destination(self, chunked_upload, request):
        """
        Move file to destination path and remove uploaded file from database
        """
        try:            
            path_gate_reception = Path.objects.get(entity = 'path_gate_reception').value
            #Gatearea_upload_root =  Path.objects.get(entity='path_gate').value
        except  Path.DoesNotExist as e:
            path_gate_reception = settings.MEDIA_ROOT
            #Gatearea_upload_root = settings.MEDIA_ROOT

        # get or create IP and AIC structure
        path = request.POST.get('path', None)
        if path is None:
            print 'Missing parameter path in request'
        elif len(path.split('/')) == 2:
            path_items = path.split('/')
            aic_uuid = path_items[0]
            ip_uuid = path_items[1]
        else:
            print 'Path: %s is not identified' % repr(path)
            aic_uuid = str(uuid.uuid4())
            ip_uuid = str(uuid.uuid4())

        #aic_uuid = get_or_create_aic_uuid(gate_reception_path, ip_uuid)
        aic_rootpath = get_or_create_AICdirectory(path_gate_reception, aic_uuid)
        ip_rootpath = get_or_create_IPdirectory(aic_rootpath, ip_uuid )

        package_descriptionfile = Parameter.objects.get(entity ='package_descriptionfile').value
        ip_logfile = Parameter.objects.get(entity="ip_logfile").value
        path_reception = Path.objects.get(entity='path_reception').value
        copy_dest_file_path = None
        dest_file_path = None
        tmp_file_path = chunked_upload.file.path

        if chunked_upload.filename in [package_descriptionfile, '%s.xml' % ip_uuid]:
            dest_file_path = os.path.join(aic_rootpath, chunked_upload.filename)
        elif chunked_upload.filename in ['%s.tar' % ip_uuid]:
            dest_file_path = os.path.join(path_reception, chunked_upload.filename)
            copy_dest_file_path = os.path.join(os.path.join(ip_rootpath, 'content'), chunked_upload.filename)
        elif chunked_upload.filename in [ip_logfile, '%s_log.xml' % ip_uuid]:
            dest_file_path = os.path.join(ip_rootpath, chunked_upload.filename)

        if copy_dest_file_path:
            #print 'Copy tmp_file_path: %s to dest_path: %s' % (tmp_file_path, copy_dest_file_path)
            shutil.copy(tmp_file_path, copy_dest_file_path)

        if dest_file_path:
            #print 'Move tmp_file_path: %s to dest_path: %s' % (tmp_file_path, dest_file_path)
            shutil.move(tmp_file_path, dest_file_path)

        if dest_file_path or copy_dest_file_path:
            chunked_upload.delete(delete_file=True)

    def get_response_data(self, chunked_upload, request):
        self.move_to_destination(chunked_upload, request)
        return {'message': ("You successfully uploaded '%s' (%s bytes)!" %
                            (chunked_upload.filename, chunked_upload.offset))}

def get_or_create_aic_uuid(sourceroot, ip_uuid):
    """
    Get or create aic_uuid
    """
    # get or create AIC_UUID
    ip_rootpath_list = find_dirs(ip_uuid, sourceroot)
    if ip_rootpath_list:
        aicuuid = os.path.split(os.path.split(ip_rootpath_list[0])[0])[1]
    else:
        aicuuid = str(uuid.uuid4())
    return aicuuid

def find_dirs(name, path):
    result = []
    for root, dirs, files in os.walk(path):
        if name in dirs:
            result.append(os.path.join(root, name))
    return result

def get_or_create_AICdirectory(sourceroot, aicuuid):
    """
    Get or create AIC directory
    """
    # create AIC_UUID directory
    aicroot = os.path.join( sourceroot, aicuuid )
    if not os.path.exists(aicroot):
        os.makedirs( aicroot )
    return aicroot

def get_or_create_IPdirectory(sourceroot, ip_uuid):
    """
    Get or create IP directory
    """    
    site_profile = Parameter.objects.get(entity='site_profile').value
    zone = 'zone2'
    
    # prepare ip_directory_structure list
    ip_directory_structure = []
    ip_rootpath = os.path.join(sourceroot, ip_uuid)
    ip_directory_structure.append(ip_rootpath)
    ip_directory_structure.append(os.path.join(ip_rootpath, 'content'))
    if site_profile == "SE":
        ip_directory_structure.append(os.path.join(ip_rootpath, 'metadata'))
    elif site_profile == "NO":
        ip_directory_structure.append(os.path.join(ip_rootpath, 'descriptive_metadata'))
        ip_directory_structure.append(os.path.join(ip_rootpath, 'administrative_metadata'))
        if zone == 'zone2':
            ip_directory_structure.append(os.path.join(os.path.join(ip_rootpath, 'administrative_metadata'), 'repository_operations'))

    # create ip_directory_structure if not exists
    for ip_path in ip_directory_structure:
        if not os.path.exists(ip_path):
            os.makedirs(ip_path)
    return ip_rootpath

class TwentyResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 1000

class CreateListRetrieveViewSet(mixins.CreateModelMixin,
                                mixins.ListModelMixin,
                                mixins.RetrieveModelMixin,
                                viewsets.GenericViewSet):
    """
    A viewset that provides `retrieve`, `create`, and `list` actions.

    To use it, override the class and set the `.queryset` and
    `.serializer_class` attributes.
    """
    pass

class ArchiveObjectViewSet(mixins.UpdateModelMixin, CreateListRetrieveViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    
    s = requests.Session()
    s.auth = ('admin', 'admin')
    
    r = s.get('http://192.168.0.70:5001/api/archiveobjects/?PolicyId=test222&format=json')
    >>> r.json()
    [{u'ObjectSize': 1234, u'StatusProcess': 3000, u'StatusActivity': 0, u'ObjectUUID': u'11', 
    u'ObjectIdentifierValue': u'11', u'PolicyId': u'test222'}, {u'ObjectSize': 952320, 
    u'StatusProcess': 1999, u'StatusActivity': 0, u'ObjectUUID': u'4459bc18-b39d-11e4-945e-fa163e627d01', 
    u'ObjectIdentifierValue': u'4459bc18-b39d-11e4-945e-fa163e627d01', u'PolicyId': u'test222'}]

    r = s.post('http://192.168.0.70:5001/api/archiveobjects/', data={u'ObjectSize': 1234, 
                u'StatusProcess': 3000, u'StatusActivity': 0, u'ObjectUUID': u'33', u'ObjectIdentifierValue': u'33', 
                u'PolicyId': u'test222'})
    
    """
    queryset = ArchiveObject.objects.all()
    serializer_class = ArchiveObjectSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('ObjectIdentifierValue', 'ObjectUUID', 'PolicyId',
                     'StatusActivity', 'StatusProcess')
    lookup_field = 'ObjectUUID'
    lookup_value_regex = '[0-9a-f-]{36}'

class ArchiveObjectStorageViewSet(mixins.UpdateModelMixin, CreateListRetrieveViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` actions.
    """
    queryset = ArchiveObject.objects.all()
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('ObjectIdentifierValue', 'ObjectUUID', 'PolicyId')
    lookup_field = 'ObjectUUID'
    lookup_value_regex = '[0-9a-f-]{36}'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ArchiveObjectPlusAICPlusStorageNestedReadSerializer
        elif self.request.method in ['POST', 'PATCH', 'PUT']:
            return ArchiveObjectPlusAICPlusStorageNestedWriteSerializer
        else:
            return ArchiveObjectPlusAICPlusStorageNestedReadSerializer

class ArchiveObjectProcessViewSet(mixins.ListModelMixin, 
    mixins.RetrieveModelMixin, 
    viewsets.GenericViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` actions.
    """
    queryset = ArchiveObject.objects.all()
    queryset = queryset.exclude(processstep=None)
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('ObjectIdentifierValue', 'ObjectUUID', 'PolicyId')
    lookup_field = 'ObjectUUID'
    lookup_value_regex = '[0-9a-f-]{36}'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ArchiveObjectPlusAICPlusProcessNestedReadSerializer
        elif self.request.method in ['POST', 'PATCH', 'PUT']:
            return ArchiveObjectPlusAICPlusProcessNestedReadSerializer
            #return ArchiveObjectPlusAICPlusProcessNestedWriteSerializer
        else:
            return ArchiveObjectPlusAICPlusProcessNestedReadSerializer

class AICObjectViewSet(mixins.UpdateModelMixin, CreateListRetrieveViewSet):
#class AICObjectViewSet(viewsets.ModelViewSet):
    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    
    s = requests.Session()
    s.auth = ('admin', 'admin')
    
    r = s.get('http://192.168.0.70:5001/api/aicobjects/?StatusProcess=3000&archiveobjects__StatusProcess=3000&format=json')
    >>> r.json()
    [{u'ObjectSize': 1234, u'StatusProcess': 3000, u'StatusActivity': 0, u'ObjectUUID': u'11', 
    u'ObjectIdentifierValue': u'11', u'PolicyId': u'test222'}, {u'ObjectSize': 952320, 
    u'StatusProcess': 1999, u'StatusActivity': 0, u'ObjectUUID': u'4459bc18-b39d-11e4-945e-fa163e627d01', 
    u'ObjectIdentifierValue': u'4459bc18-b39d-11e4-945e-fa163e627d01', u'PolicyId': u'test222'}]

    r = s.post('http://192.168.0.70:5001/api/aicobjects/', json={u'ObjectSize': 1234, 
                u'StatusProcess': 3000, u'StatusActivity': 0, u'ObjectUUID': u'33', u'ObjectIdentifierValue': u'33', 
                u'PolicyId': u'test222'})
    
    """
    queryset = ArchiveObject.objects.filter(OAISPackageType=1)
    serializer_class = AICObjectSerializer
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = TwentyResultsSetPagination
    filter_fields = ('ObjectIdentifierValue', 'StatusProcess')
    lookup_field = 'ObjectUUID'
    lookup_value_regex = '[0-9a-f-]{36}'

class ArchiveObjectRelViewSet(CreateListRetrieveViewSet):
    queryset = ArchiveObjectRel.objects.all()
    serializer_class = ArchiveObjectRelSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('UUID', 'AIC_UUID')
    
class ArchivePolicyViewSet(CreateListRetrieveViewSet):

    queryset = ArchivePolicy.objects.all()
    serializer_class = ArchivePolicySerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'PolicyID', 'PolicyName', 'PolicyStat', 
                     'Mode', 'AIPType', 'INFORMATIONCLASS')

class ArchivePolicyNestedViewSet(ArchivePolicyViewSet):
    serializer_class = ArchivePolicyNestedSerializer

class StorageMethodViewSet(CreateListRetrieveViewSet):

    queryset = StorageMethod.objects.all()
    serializer_class = StorageMethodSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'name', 'status', 'type', 'archivepolicy')

class StorageTargetViewSet(CreateListRetrieveViewSet):

    queryset = StorageTarget.objects.all()
    serializer_class = StorageTargetSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'name', 'status', 'target', 'storagemethod')

class StorageTargetsViewSet(CreateListRetrieveViewSet):

    queryset = StorageTargets.objects.all()
    serializer_class = StorageTargetsSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'name', 'status', 'type', 'format', 'target')

class storageMediumViewSet(CreateListRetrieveViewSet):

    queryset = storageMedium.objects.all()
    serializer_class = storageMediumSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id',
                    'storageMediumUUID',
                    'storageMedium',
                    'storageMediumID',
                    'storageMediumDate',
                    'storageMediumLocation',
                    'storageMediumLocationStatus',
                    'storageMediumBlockSize',
                    'storageMediumUsedCapacity',
                    'storageMediumStatus',
                    'storageMediumFormat',
                    'storageMediumMounts',
                    'linkingAgentIdentifierValue',
                    'CreateDate',
                    'CreateAgentIdentifierValue',
                    'storagetarget')

class storageViewSet(CreateListRetrieveViewSet):

    queryset = storage.objects.all()
    serializer_class = storageSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'contentLocationType', 'contentLocationValue', 
                     'archiveobject', 'storagemedium')

class storageNestedViewSet(storageViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return storageNestedReadSerializer
        elif self.request.method in ['POST', 'PATCH', 'PUT']:
            return storageNestedWriteSerializer
        else:
            return storageSerializer

class ProcessStepViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, CreateListRetrieveViewSet):

    queryset = ProcessStep.objects.all()
    serializer_class = ProcessStepSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id',
                    'name',
                    'type',
                    'user',
                    'result',
                    'status',
                    'posted',
                    'progress',
                    'archiveobject',
                    'hidden')

class ProcessTaskViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, CreateListRetrieveViewSet):

    queryset = ProcessTask.objects.all()
    serializer_class = ProcessTaskSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id', 'name', 'task_id', 'status', 'result', 
                  'date_done', 'traceback', 'hidden',
                  'meta', 'progress', 'processstep')

class ProcessStepNestedViewSet(ProcessStepViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return ProcessStepNestedReadSerializer
        elif self.request.method in ['POST', 'PATCH', 'PUT']:
            return ProcessStepNestedReadSerializer
            #return ProcessStepNestedWriteSerializer
        else:
            return ProcessStepNestedReadSerializer

class IOQueueViewSet(mixins.DestroyModelMixin, mixins.UpdateModelMixin, CreateListRetrieveViewSet):

    queryset = IOQueue.objects.all()
    serializer_class = IOQueueSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('id',
                    'ReqType',
                    'ReqPurpose',
                    'user',
                    'ObjectPath',
                    'WriteSize',
                    'result',
                    'Status',
                    'task_id',
                    'posted',
                    'archiveobject',
                    'storagemethod',
                    'storagemethodtarget',
                    'storagetarget',
                    'storagemedium',
                    'storage',
                    'accessqueue',
                    'remote_status',
                    'transfer_task_id')

class IOQueueNestedViewSet(IOQueueViewSet):
    def get_serializer_class(self):
        if self.request.method == 'GET':
            return IOQueueNestedReadSerializer
        elif self.request.method in ['POST', 'PATCH', 'PUT']:
            return IOQueueNestedWriteSerializer
        else:
            return IOQueueSerializer

class WriteStorageMethodTapeApplyViewSet(viewsets.ViewSet):    
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplyStorageMethodTapeSerializer

    def list(self, request):
        return Response({})
    
    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        return Response({
            "task_id": pk,
            "state": result.state,
            "result": repr(result.result),
            "traceback": result.traceback, 
        })

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            try:
                ArchiveObject_objs_ObjectUUID_list = serializer.validated_data['ArchiveObject_objs_ObjectUUID_list']
                IOQueue_objs_id_list = serializer.validated_data['IOQueue_objs_id_list']
                queue = serializer.validated_data['queue']
                ArchiveObject.objects.filter(
                                             ObjectUUID__in = ArchiveObject_objs_ObjectUUID_list,
                                             ).update(StatusActivity=5)
                result = WriteStorageMethodTape().apply_async((IOQueue_objs_id_list,), queue=queue)
                return Response({"task_id": result.task_id, "state": "ok"}, status=201)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))
                return Response({"state": 'fail', "error": msg}, status=420)
        else:
            return Response({"state": 'not valid'}, status=400)

    '''
    def update(self, request, pk=None):
        pass

    def partial_update(self, request, pk=None):
        pass

    def destroy(self, request, pk=None):
        pass

    def metadata(self, request):
        ret = super(WriteStorageMethodTapeApply, self).metadata(request)

        ret['parameters'] = {
            "page": {
                "type": "integer",
                "description": "The page number",
                "required": False
            },
            "region_id": {
                "type": "integer",
                "description": "The region ID to filter the results",
                "required": False
            }
        }

        return ret
    '''

class WriteStorageMethodDiskApplyViewSet(viewsets.ViewSet):    
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplyStorageMethodDiskSerializer

    def list(self, request):
        return Response({})
    
    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        return Response({
            "task_id": pk,
            "state": result.state,
            "result": repr(result.result),
            "traceback": result.traceback, 
        })

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            try:
                ArchiveObject_obj_ObjectUUID = serializer.validated_data['ArchiveObject_obj_ObjectUUID']
                IOQueue_obj_id = serializer.validated_data['IOQueue_obj_id']
                queue = serializer.validated_data['queue']
                ArchiveObject.objects.filter(
                                             ObjectUUID = ArchiveObject_obj_ObjectUUID,
                                             ).update(StatusActivity=5)
                result = WriteStorageMethodDisk().apply_async((IOQueue_obj_id,), queue=queue)
                return Response({"task_id": result.task_id, "state": "ok"}, status=201)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))
                return Response({"state": 'fail', "error": msg}, status=420)
        else:
            return Response({"state": 'not valid'}, status=400)

class ReadStorageMethodTapeApplyViewSet(viewsets.ViewSet):    
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplyStorageMethodTapeSerializer

    def list(self, request):
        return Response({})
    
    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        data = {
            "task_id": pk,
            "state": result.state,
            "result": repr(result.result),
            "traceback": result.traceback}        
        return Response(data)

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            try:
                ArchiveObject_objs_ObjectUUID_list = serializer.validated_data['ArchiveObject_objs_ObjectUUID_list']
                IOQueue_objs_id_list = serializer.validated_data['IOQueue_objs_id_list']
                queue = serializer.validated_data['queue']
                ArchiveObject.objects.filter(
                                             ObjectUUID__in = ArchiveObject_objs_ObjectUUID_list,
                                             ).update(StatusActivity=5)
                result = ReadStorageMethodTape().apply_async((IOQueue_objs_id_list,), queue=queue)
                return Response({"task_id": result.task_id, "state": "ok"}, status=201)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))
                return Response({"state": 'fail', "error": msg}, status=420)
        else:
            return Response({"state": 'not valid'}, status=400)

class ReadStorageMethodDiskApplyViewSet(viewsets.ViewSet):    
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ApplyStorageMethodDiskSerializer

    def list(self, request):
        return Response({})
    
    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        return Response({
            "task_id": pk,
            "state": result.state,
            "result": repr(result.result),
            "traceback": result.traceback, 
        })

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            try:
                ArchiveObject_obj_ObjectUUID = serializer.validated_data['ArchiveObject_obj_ObjectUUID']
                IOQueue_obj_id = serializer.validated_data['IOQueue_obj_id']
                queue = serializer.validated_data['queue']
                ArchiveObject.objects.filter(
                                             ObjectUUID = ArchiveObject_obj_ObjectUUID,
                                             ).update(StatusActivity=5)
                result = ReadStorageMethodDisk().apply_async((IOQueue_obj_id,), queue=queue)
                return Response({"task_id": result.task_id, "state": "ok"}, status=201)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))
                return Response({"state": 'fail', "error": msg}, status=420)
        else:
            return Response({"state": 'not valid'}, status=400)

class MoveToAccessPathViewSet(viewsets.ViewSet):    
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = MoveToAccessPathSerializer

    def list(self, request):
        return Response({})
    
    def retrieve(self, request, pk=None):
        result = AsyncResult(pk)
        return Response({
            "task_id": pk,
            "state": result.state,
            "result": repr(result.result),
            "traceback": result.traceback,
        })

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid(raise_exception=True):
            try:
                filename_list = serializer.validated_data['filename_list']
                IOQueue_obj_id = serializer.validated_data['IOQueue_obj_id']
                queue = serializer.validated_data['queue']
                result = MoveToAccessPath().apply_async((IOQueue_obj_id, filename_list), queue=queue)
                return Response({"task_id": result.task_id, "state": "ok"}, status=201)
            except Exception as e:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                msg = 'Unknown error, error: %s trace: %s' % (e, repr(traceback.format_tb(exc_traceback)))
                return Response({"state": 'fail', "error": msg}, status=420)
        else:
            return Response({"state": 'not valid'}, status=400)
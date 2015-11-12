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
from django.views.generic.base import TemplateView
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from chunked_upload.views import ChunkedUploadView, ChunkedUploadCompleteView
from chunked_upload.exceptions import ChunkedUploadError
from chunked_upload.response import Response
from configuration.models import Path
from api.models import TmpWorkareaUpload
from api.serializers import (
                        ArchiveObjectSerializer,
                        ArchiveObjectNestedSerializer,
                        AICObjectSerializer,
                        ArchivePolicySerializer,
                        ArchivePolicyNestedSerializer,
                        StorageMethodSerializer,
                        StorageTargetSerializer,
                        StorageTargetsSerializer,
                        storageMediumSerializer,
                        storageSerializer,
                        storageNestedSerializer,
                        IOQueueSerializer,
                        IOQueueNestedSerializer,
                        ArchiveObjectRelSerializer,
                        )
from essarch.models import ArchiveObject, ArchiveObjectRel
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
from rest_framework.pagination import PageNumberPagination

class AICListView(TemplateView):
    template_name = 'api/aic_list.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(AICListView, self).dispatch( *args, **kwargs)

class TmpWorkareaUploadView(TemplateView):
    template_name = 'api/tmpworkarea_upload.html'

    @method_decorator(permission_required('essarch.change_ingestqueue'))
    def dispatch(self, *args, **kwargs):
        return super(TmpWorkareaUploadView, self).dispatch( *args, **kwargs)

class CreateTmpWorkareaUploadView(views.APIView, ChunkedUploadView):

    model = TmpWorkareaUpload
    field_name = 'the_file'
    permission_classes = (permissions.IsAuthenticated,)
    '''
    def get(self, request, *args, **kwargs):
        request.META["CSRF_COOKIE_USED"] = True
        return HttpResponse('hej')

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests.
        """
        print 'HTTP_X_FILE_NAME: %s' % request.META.get("HTTP_X_FILE_NAME", '--')
        print 'HTTP_TRANSFER_ENCODING: %s' % request.META.get('HTTP_TRANSFER_ENCODING', '--')
        print 'CONTENT_TYPE: %s' % request.META['CONTENT_TYPE']
        print 'HTTP_CONTENT_RANGE: %s' % request.META.get('HTTP_CONTENT_RANGE', '--')
        if hasattr(request, 'data'):
            try:
                print 'data keys: %s' % request.data.keys()
            except:
                print 'data: %s' % request.data
        else:
            print 'request.data does not exists'
        if hasattr(request, 'FILES'):
            try:
                print 'FILES keys: %s' % request.FILES.keys()
            except:
                print 'FILES: %s' % request.FILES
        else:
            print 'request.FILES does not exists'
        if hasattr(request, 'session'):
            try:
                print 'session keys: %s' % request.session.keys()
            except:
                print 'session: %s' % request.session
        else:
            print 'request.session does not exists'
            
        try:
            self.check_permissions(request)
            return self._post(request, *args, **kwargs)
        except ChunkedUploadError as error:
            return Response(error.data, status=error.status_code)
        '''

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
    #serializer_class = ArchiveObjectNestedSerializer
    serializer_class = ArchiveObjectSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filter_fields = ('ObjectIdentifierValue', 'ObjectUUID', 'PolicyId')
    lookup_field = 'ObjectUUID'
    lookup_value_regex = '[0-9a-f-]{36}'

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
    serializer_class = storageNestedSerializer

class IOQueueViewSet(CreateListRetrieveViewSet):

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
                    'remote_target',
                    'remote_status',
                    'transfer_taks_id')

class IOQueueNestedViewSet(IOQueueViewSet):
    serializer_class = IOQueueNestedSerializer

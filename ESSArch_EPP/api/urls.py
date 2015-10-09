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

from django.conf.urls import patterns, url, include
from rest_framework.routers import DefaultRouter

from api.views import TmpWorkareaUploadView, \
                    CreateTmpWorkareaUploadView, \
                    CreateTmpWorkareaUploadCompleteView, \
                    ArchiveObjectViewSet, \
                    AICObjectViewSet, \
                    ArchivePolicyViewSet,\
                    StorageMethodViewSet,\
                    StorageTargetViewSet,\
                    StorageTargetsViewSet,\
                    storageMediumViewSet,\
                    storageViewSet,\
                    IOQueueViewSet

# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'archiveobjects', ArchiveObjectViewSet)
router.register(r'aicobjects', AICObjectViewSet)
router.register(r'archivepolicy', ArchivePolicyViewSet)
router.register(r'storagemethod', StorageMethodViewSet)
router.register(r'storagetarget', StorageTargetViewSet)
router.register(r'storagetargets', StorageTargetsViewSet)
router.register(r'storagemedium', storageMediumViewSet)
router.register(r'storage', storageViewSet)
router.register(r'ioqueue', IOQueueViewSet)

urlpatterns = patterns('',
    url(r'^', include(router.urls)),
    url(r'^tmpworkarea_upload', TmpWorkareaUploadView.as_view(), name='chunked_upload'),
    url(r'^create_tmpworkarea_upload/?$', CreateTmpWorkareaUploadView.as_view(), name='api_chunked_upload'),
    url(r'^create_tmpworkarea_upload_complete/?$', CreateTmpWorkareaUploadCompleteView.as_view(), name='api_chunked_upload_complete'),
)

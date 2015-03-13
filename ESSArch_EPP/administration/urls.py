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
from django.conf.urls import patterns, url
from views import (
    storageMediumList, 
    storageMediumDatatablesView,
    storageMediumDetail,
    storageDatatablesView,  
    #storageMediumList2, 
    #storageMediumList3,  
    storageList, 
    robotList, 
    robotReqCreate,
    robotReqDetail,
    robotReqUpdate,  
    robotReqDelete,
    robotInventory, 
    StorageMigration,
    TargetPrePopulation,
    StorageMaintenance,
    StorageMaintenanceDatatablesView,
    MigrationList,
    MigrationDetail,
    MigrationCreate,
    MigrationUpdate,
    MigrationDelete,
    DeactivateMedia,
)

#import views

urlpatterns = patterns('',   
    url(r'^liststoragemedium/$', storageMediumList.as_view(),name='admin_liststoragemedium'),
    url(r'^storagemediumdt$', storageMediumDatatablesView.as_view(), name='storagemedium-dt'),
    url(r'^detailstoragemedium/(?P<pk>\d+)/$', storageMediumDetail.as_view(), name='admin_detailstoragemedium'),
    url(r'^storagedt$', storageDatatablesView.as_view(), name='storage-dt'),
    #url(r'^liststoragemedium2/$', storageMediumList2,name='admin_liststoragemedium2'),
    #url(r'^liststoragemedium3$', storageMediumList3.as_view(), name='admin_liststoragemedium3'),
    url(r'^liststorage/$', storageList.as_view(),name='admin_liststorage'),
    url(r'^listrobot/$', robotList.as_view(),name='admin_listrobot'),
    url(r'^newrobotreq/$', robotReqCreate.as_view(), name='admin_robotreq_create'),
    url(r'^newrobotreq/(?P<storageMediumID>[^&]*)/(?P<command>\d+)/$', robotReqCreate.as_view(), name='admin_robotreq_create_mediumid'),
    url(r'^robotreqdetail/(?P<pk>\d+)/$', robotReqDetail.as_view(), name='robotreq_detail'),
    url(r'^robotrequpdate/(?P<pk>\d+)/$', robotReqUpdate.as_view(), name='robotreq_update'),
    url(r'^robotreqdelete/(?P<pk>\d+)/$', robotReqDelete.as_view(), name='robotreq_delete'),
    url(r'^robotinventory/(?P<command>\d+)/$', robotInventory.as_view(), name='admin_create_robotinventory'),
    url(r'^storagemigration$', StorageMigration.as_view(), name='admin_storagemigration'),
    url(r'^migrationtarget$', TargetPrePopulation.as_view(), name='admin_migrationtarget'),
    url(r'^storagemaintenancedt$', StorageMaintenanceDatatablesView.as_view(), name='storagemaintenance-dt'),
    url(r'^storagemaintenance$', StorageMaintenance.as_view(), name='admin_storagemaintenance'),
    url(r'^migreqlist/$', MigrationList.as_view(), name='migration_list'),
    url(r'^migreqnew$', MigrationCreate.as_view(), name='migration_create_parameter'),
    url(r'^migreqnew/$', MigrationCreate.as_view(), name='migration_create'),
    url(r'^migreqnew/(?P<ip_uuid>[^&]*)/$', MigrationCreate.as_view(), name='migration_create_ip_uuid'),
    url(r'^migredetail/(?P<pk>\d+)/$', MigrationDetail.as_view(), name='migration_detail'),
    url(r'^migrequpdate/(?P<pk>\d+)/$', MigrationUpdate.as_view(), name='migration_update'),
    url(r'^migreqdelete/(?P<pk>\d+)/$', MigrationDelete.as_view(), name='migration_delete'),  
    url(r'^deactivatemediacreate/$', DeactivateMedia.as_view(), name='deactivatemedia_create'),
)
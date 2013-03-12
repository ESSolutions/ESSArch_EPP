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
from django.conf.urls.defaults import *
from views import storageMediumList, storageMediumDetail, storageList, robotList, robotReqCreate, robotInventory

#import views

urlpatterns = patterns('',   
    url(r'^liststoragemedium/$', storageMediumList.as_view(),name='admin_liststoragemedium'),
    url(r'^detailstoragemedium/(?P<pk>\d+)/$', storageMediumDetail.as_view(), name='admin_detailstoragemedium'),
    url(r'^liststorage/$', storageList.as_view(),name='admin_liststorage'),
    url(r'^listrobot/$', robotList.as_view(),name='admin_listrobot'),
    url(r'^newrobotreq/(?P<storageMediumID>[^&]*)/(?P<command>\d+)/$', robotReqCreate.as_view(), name='admin_create_robotreq'),
    url(r'^robotinventory/(?P<command>\d+)/$', robotInventory.as_view(), name='admin_create_robotinventory'),
)
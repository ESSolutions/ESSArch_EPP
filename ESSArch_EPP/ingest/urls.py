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
from views import IngestList, IngestDetail, IngestCreate, IngestUpdate, IngestDelete, ArchObjectListUpdate

#import views

urlpatterns = patterns('',   
    url(r'^listobj/$', ArchObjectListUpdate.as_view(),name='ingest_listobj'),
    url(r'^listobjupd/(?P<pk>\d+)/$', ArchObjectListUpdate.as_view(),name='ingest_listobjupd'),
    url(r'^list/$', IngestList.as_view(),name='ingest_list'),
    url(r'^detail/(?P<pk>\d+)/$', IngestDetail.as_view(), name='ingest_detail'),
    url(r'^new$', IngestCreate.as_view(), name='ingest_create_parameter'),
    url(r'^new/$', IngestCreate.as_view(), name='ingest_create'),
    url(r'^new/(?P<ip_uuid>[^&]*)/$', IngestCreate.as_view(), name='ingest_create_ip_uuid'),
    url(r'^update/(?P<pk>\d+)/$', IngestUpdate.as_view(), name='ingest_update'),
    url(r'^delete/(?P<pk>\d+)/$', IngestDelete.as_view(), name='ingest_delete'),  
)
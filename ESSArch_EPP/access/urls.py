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
from views import AccessList, AccessDetail, AccessCreate ,AccessUpdate, AccessDelete, ArchObjectList, ArchObjectDatatablesView

#import views

urlpatterns = patterns('',   
    url(r'^listobj/$', ArchObjectList.as_view(),name='access_listobj'),
    url(r'^archobjectdt$', ArchObjectDatatablesView.as_view(), name='archobject-dt'),
    url(r'^list/$', AccessList.as_view(),name='access_list'),
    url(r'^detail/(?P<pk>\d+)/$', AccessDetail.as_view(), name='access_detail'),
    url(r'^new$', AccessCreate.as_view(), name='access_create_parameter'),
    url(r'^new/$', AccessCreate.as_view(), name='access_create'),
    url(r'^new/(?P<ip_uuid>[^&]*)/$', AccessCreate.as_view(), name='access_create_ip_uuid'),
    url(r'^update/(?P<pk>\d+)/$', AccessUpdate.as_view(), name='access_update'),
    url(r'^delete/(?P<pk>\d+)/$', AccessDelete.as_view(), name='access_delete'),  
)
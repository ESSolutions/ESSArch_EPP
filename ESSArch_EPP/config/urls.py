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

from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Standard URLS:
    #url(r'^$', 'configuration.views.index', name='home'),
    url(r'^$', 'monitoring.views.sysstat', name='home'),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login' ),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'} ),
    url(r'^admin/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'} ),
    url(r'^changepassword$', 'configuration.views.change_password'),
    
    # URLS to include:
    url(r'^configuration/', include('configuration.urls')),
    url(r'^controlarea/', include('controlarea.urls')),
    url(r'^access/', include('access.urls')),
    url(r'^ingest/', include('ingest.urls')),
    url(r'^administration/', include('administration.urls')),
    url(r'^reports/', include('reports.urls')),
    url(r'^admin/', include('logfileviewer.admin_urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^js/', include('djangojs.urls')),
    url(r'^task/', include('djcelery.urls')),
    url(r'^monitoring/', include('monitoring.urls')),
    url(r'^api/', include('api.urls')),

    # StorageLogistics_ws URLS:
    url(r'^webservice/StorageLogisticsService$', "storagelogistics.views.dispatch"),
)

'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB, Henrik Ek

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
#from django.conf.urls.defaults import patterns, url
from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView

from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from books.models import Publisher

urlpatterns = patterns('',
    # Configuration URLS:
    url(r'^$', 'configuration.views.index', name='home'),
    url(r'^logout$', 'configuration.views.logout_view'),
    url(r'^changepassword$', 'configuration.views.change_password'),
    #url(r'^configuration/parameters$', 'configuration.views.parameters'),
    #url(r'^configuration/parameters/(?P<username>\w+)$', 'configuration.views.userparameters'),


    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login' ),

    # StorageLogistics_ws URLS:
    url(r'^webservice/StorageLogisticsService$', "storagelogistics.views.dispatch"),

    # grappelli admin
    #(r'^grappelli/', include('grappelli.urls')),
    (r'^publishers/$', ListView.as_view(
        model=Publisher,
    )),
)

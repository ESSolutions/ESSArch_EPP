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

urlpatterns = patterns('',
    url(r'^changepassword$', 'configuration.views.change_password'),
    url(r'^install_defaultschemas$', 'configuration.views.installdefaultschemaprofiles'),
    url(r'^install_defaultparameters$', 'configuration.views.installdefaultparameters'),
    url(r'^install_defaultusers$', 'configuration.views.createdefaultusers'),
    #url(r'^parameters$', 'configuration.views.parameters'),
    #url(r'^parameters/(?P<username>\w+)$', 'configuration.views.userparameters'),
)
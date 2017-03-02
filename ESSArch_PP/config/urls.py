"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

from django.conf.urls import include, url
from django.contrib import admin
from django.contrib.auth import views as auth_views

from rest_framework import routers

from ESSArch_Core.auth.views import (
    GroupViewSet,
    PermissionViewSet,
    UserViewSet,
)

from ESSArch_Core.configuration.views import (
    AgentViewSet,
    ArchivePolicyViewSet,
    EventTypeViewSet,
    ParameterViewSet,
    PathViewSet,
    SysInfoView,
)

from ip.views import (
    EventIPViewSet,
    InformationPackageViewSet,
    InformationPackageReceptionViewSet,
)

from tags.views import TagViewSet

admin.site.site_header = 'ESSArch Preservation Platform Administration'
admin.site.site_title = 'ESSArch Preservation Platform Administration'

router = routers.DefaultRouter()
router.register(r'agents', AgentViewSet)
router.register(r'archive_policies', ArchivePolicyViewSet)
router.register(r'event-types', EventTypeViewSet)
router.register(r'events', EventIPViewSet)
router.register(r'groups', GroupViewSet)
router.register(r'information-packages', InformationPackageViewSet)
router.register(r'ip-reception', InformationPackageReceptionViewSet, base_name="ip-reception")
router.register(r'parameters', ParameterViewSet)
router.register(r'paths', PathViewSet)
router.register(r'permissions', PermissionViewSet)
router.register(r'tags', TagViewSet)
router.register(r'users', UserViewSet)

urlpatterns = [
    url(r'^', include('frontend.urls'), name='home'),
    url(r'^accounts/changepassword', auth_views.password_change, {'post_change_redirect': '/'}),
    url(r'^accounts/login/$', auth_views.login),
    url(r'^admin/', admin.site.urls),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include(router.urls)),
    url(r'^api/sysinfo/', SysInfoView.as_view()),
    url(r'^rest-auth/', include('rest_auth.urls')),
    url(r'^rest-auth/registration/', include('rest_auth.registration.urls')),
]

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

from django.db.models import Q

import django_filters

from ESSArch_Core.filters import ListFilter

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    InformationPackage,
)


class InformationPackageFilter(django_filters.FilterSet):
    package_type = ListFilter(name='package_type')
    state = ListFilter(name='State', method='filter_state')

    def filter_state(self, queryset, name, value):
        value_list = value.split(u',')

        return queryset.filter(
            Q(State__in=value_list) |
            Q(information_packages__State__in=value_list)
        )

    class Meta:
        model = InformationPackage
        fields = ['package_type', 'state']


class ArchivalInstitutionFilter(django_filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalInstitution
        fields = ('ip_state',)


class ArchivistOrganizationFilter(django_filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivistOrganization
        fields = ('ip_state',)


class ArchivalTypeFilter(django_filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalType
        fields = ('ip_state',)


class ArchivalLocationFilter(django_filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalLocation
        fields = ('ip_state',)

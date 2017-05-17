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

from django_filters import rest_framework as filters

from ESSArch_Core.filters import ListFilter

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    InformationPackage,
)


class InformationPackageFilter(filters.FilterSet):
    archival_institution = ListFilter(name="ArchivalInstitution__name", method='filter_fields')
    archivist_organization = ListFilter(name='ArchivistOrganization__name', method='filter_fields')
    archival_type = ListFilter(name='ArchivalType__name', method='filter_fields')
    archival_location = ListFilter(name='ArchivalLocation__name', method='filter_fields')
    package_type = ListFilter(name='package_type')
    state = ListFilter(name='State', method='filter_fields_in_list')
    object_identifier_value = ListFilter(name='ObjectIdentifierValue', method='filter_fields')
    label = ListFilter(name='Label', method='filter_fields')
    responsible = ListFilter(name='Responsible__username', method='filter_fields')
    create_date = ListFilter(name='CreateDate', method='filter_fields')
    object_size = ListFilter(name='object_size', method='filter_fields')
    start_date = ListFilter(name='Startdate', method='filter_fields')
    end_date = ListFilter(name='Enddate', method='filter_fields')
    archived = filters.BooleanFilter()
    cached = filters.BooleanFilter()

    def filter_fields(self, queryset, name, value):
        view_type = self.data.get('view_type', 'aic')

        if view_type == 'aic':
            return queryset.filter(
                **{'information_packages__%s__icontains' % name: value}
            ).distinct()
        elif view_type == 'ip':
            return queryset.filter(
                Q(
                    Q(**{'%s__icontains' % name: value}) |
                    Q(**{'aic__information_packages__%s__icontains' % name: value})
                ), generation=0
            ).distinct()

        return queryset.filter(
            **{'%s__icontains' % name: value}
        ).distinct()

    def filter_fields_in_list(self, queryset, name, value):
        value_list = value.split(u',')
        view_type = self.data.get('view_type', 'aic')

        if view_type == 'aic':
            return queryset.filter(
                **{'information_packages__%s__in' % name: value_list}
            ).distinct()
        elif view_type == 'ip':
            return queryset.filter(
                Q(
                    Q(**{'%s__in' % name: value_list}) |
                    Q(**{'aic__information_packages__%s__in' % name: value_list})
                ), generation=0
            ).distinct()

        return queryset.filter(
            **{'%s__in' % name: value_list}
        ).distinct()

    class Meta:
        model = InformationPackage
        fields = ['package_type', 'state', 'label','object_identifier_value',
        'responsible', 'create_date','object_size', 'start_date', 'end_date',
        'archival_institution', 'archivist_organization']


class ArchivalInstitutionFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalInstitution
        fields = ('ip_state',)


class ArchivistOrganizationFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivistOrganization
        fields = ('ip_state',)


class ArchivalTypeFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalType
        fields = ('ip_state',)


class ArchivalLocationFilter(filters.FilterSet):
    ip_state = ListFilter(name='information_packages__State', distinct=True)

    class Meta:
        model = ArchivalLocation
        fields = ('ip_state',)

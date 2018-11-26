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
from rest_framework import exceptions
from rest_framework.filters import SearchFilter

from ESSArch_Core.filters import ListFilter
from ESSArch_Core.ip.filters import InformationPackageFilter as InformationPackageFilterCore
from ESSArch_Core.ip.models import InformationPackage, Workarea

ip_search_fields = (
    'object_identifier_value', 'label', 'responsible__first_name',
    'responsible__last_name', 'responsible__username', 'state',
    'submission_agreement__name', 'start_date', 'end_date', 'aic__object_identifier_value',
)

def get_ip_search_fields(nested=True):
    if not nested:
        return ip_search_fields

    with_extra_fields = ip_search_fields

    for field in ip_search_fields:
        with_extra_fields += ('aic__information_packages__%s' % field, 'information_packages__%s' % field)

    return with_extra_fields


class InformationPackageFilter(InformationPackageFilterCore):
    search_filter = SearchFilter()

    package_type = ListFilter(field_name='package_type')
    package_type_name_exclude = filters.CharFilter(field_name='Package Type Name', method='filter_package_type_name')
    search = filters.CharFilter(method='filter_search')

    def filter_search(self, queryset, name, value):
        class DummyView(object):
            search_fields = get_ip_search_fields(nested=False)
        return self.search_filter.filter_queryset(self.request, queryset, DummyView)

    def filter_package_type_name(self, queryset, name, value):
        for package_type_id, package_type_name in InformationPackage.PACKAGE_TYPE_CHOICES:
            if package_type_name.lower() == value.lower():
                return queryset.exclude(package_type=package_type_id)
        return queryset.none()

    class Meta:
        model = InformationPackage
        fields = InformationPackageFilterCore.Meta.fields + ['archived', 'cached', 'package_type',
                                                             'package_type_name_exclude']


class WorkareaFilter(InformationPackageFilter):
    type = ListFilter(field_name='workareas__type', method='filter_workarea')

    def filter_workarea(self, queryset, name, value):
        workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

        try:
            workarea_type = workarea_type_reverse[value]
        except KeyError:
            raise exceptions.ParseError('Workarea of type "%s" does not exist' % value)

        return self.filterset_fields(queryset, name, workarea_type)

    class Meta:
        model = InformationPackage
        fields = InformationPackageFilter.Meta.fields + ['type']

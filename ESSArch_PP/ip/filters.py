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

from rest_framework import exceptions

from ESSArch_Core.api.filters import ListFilter
from ESSArch_Core.ip.filters import InformationPackageFilter
from ESSArch_Core.ip.models import InformationPackage, Workarea


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

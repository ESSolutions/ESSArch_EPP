"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Core
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

from django.contrib import admin
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect

from nested_inline.admin import NestedModelAdmin

from ESSArch_Core.configuration.models import ArchivePolicy

from storage.admin import StorageMethodInline


csrf_protect_m = method_decorator(csrf_protect)


class ArchivePolicyAdmin(NestedModelAdmin):
    """
    ArchivePolicy
    """
    model = ArchivePolicy
    list_display = ('policy_name', 'policy_id', 'policy_stat', 'ais_project_name', 'ais_project_id', 'mode')
    fieldsets = (
        (None, {
            'fields': (
                'policy_stat',
                'policy_name',
                'policy_id',
                'ais_project_name',
                'ais_project_id',
                'mode',
                'checksum_algorithm',
                'ip_type',
                'preingest_metadata',
                'ingest_metadata',
                'information_class',
                'ingest_path',
                'cache_storage',
                'wait_for_approval',
                'validate_checksum',
                'validate_xml',
                'ingest_delete',
                'index',
                'receive_extract_sip',
                'cache_extracted_size',
                'cache_package_size',
                'cache_extracted_age',
                'cache_package_age',
            )
        }),
    )
    inlines = [StorageMethodInline]

    @csrf_protect_m
    @transaction.atomic
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = self.admin_site.each_context(request)
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    @csrf_protect_m
    @transaction.atomic
    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = self.admin_site.each_context(request)
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)


admin.site.register(ArchivePolicy, ArchivePolicyAdmin)

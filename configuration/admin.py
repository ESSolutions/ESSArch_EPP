#!/usr/bin/env /ESSArch/python27/bin/python
# -*- coding: UTF-8 -*-
'''
    ESSArch Tools - ESSArch is an Electronic Preservation Platform
    Copyright (C) 2005-2013  ES Solutions AB

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

from configuration.models import LogEvent, Parameter, SchemaProfile, Path, IPParameter
from django.contrib import admin

# Logevents
class LogEventAdmin( admin.ModelAdmin ):
    list_display = ( 'eventDetail', 'eventType' )
    search_fields = ( 'eventDetail', )
        
admin.site.register( LogEvent, LogEventAdmin )
 
# XML schemas and namespaces
class SchemaProfileAdmin( admin.ModelAdmin ):
    list_display = ( 'entity', 'value' )
    search_fields = ( 'entity', )
    readonly_fields = ('entity',)
    fields = ('entity', 'value')
    
admin.site.register(SchemaProfile, SchemaProfileAdmin)

# Parameters
class ParameterAdmin( admin.ModelAdmin ):
    list_display = ( 'entity', 'value' )
    search_fields = ( 'entity', )
    readonly_fields = ('entity',)
    fields = ('entity', 'value')

admin.site.register(Parameter, ParameterAdmin)

# Paths
class PathAdmin( admin.ModelAdmin ):
    list_display = ( 'entity', 'value' )
    search_fields = ( 'entity', )
    readonly_fields = ('entity',)
    fields = ('entity', 'value')

admin.site.register(Path, PathAdmin)

# General metadata for information package
class IPParameterAdmin( admin.ModelAdmin ):
    list_display = ( 'type', 'label', 'createdate', 'recordstatus', 'deliverytype' )
    search_fields = ( 'type', )
    readonly_fields = ('objid',)
    list_filter = ('type', 'label')
    fieldsets = (
                (None,{
                   'classes': ('wide'),
                   'fields': (
                              'label',
                              'type',
                              'objid',
                              'createdate',
                              'recordstatus',
                              'deliverytype'
                              )}),
                ('General metadata for information package',{
                   'classes': ('collapse','wide'),
                   'fields': (
                              'deliveryspecification',
                              'submissionagreement',
                              'previoussubmissionagreement',
                              'datasubmissionsession',
                              'packagenumber',
                              'referencecode',
                              'previousreferencecode',
                              'appraisal',
                              'accessrestrict',
                              'archivist_organization',
                              'archivist_organization_id',
                              'archivist_organization_software',
                              'archivist_organization_software_id',
                              'creator_organization',
                              'creator_organization_id',
                              'creator_individual',
                              'creator_individual_details',
                              'creator_software',
                              'creator_software_id',
                              'editor_organization',
                              'editor_organization_id',
                              'preservation_organization',
                              'preservation_organization_id',
                              'preservation_organization_software',
                              'preservation_organization_software_id'
                              )}),
                ('Additional metadata for information package',{
                   'classes': ('collapse', 'wide'),
                   'fields': (
                              'startdate',
                              'enddate',
                              'aic_id',
                              'informationclass',
                              'projectname',
                              'policyid',
                              'receipt_email'
                              )}),
                #('Reference metadata for files in information package',{
                #   'classes': ('collapse', 'wide'),
                #   'fields': (
                #              'file_id',
                #              'file_name',
                #              'file_createdate',
                #              'file_mime_type',
                #              'file_format',
                #              'file_format_size',
                #              'file_type',
                #              'file_checksum',
                #              'file_checksum_type',
                #              'file_transform_type',
                #              'file_transform_key'
                #              )}),
                )

admin.site.register(IPParameter, IPParameterAdmin)



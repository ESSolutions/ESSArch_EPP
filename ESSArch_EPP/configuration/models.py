#!/usr/bin/env /ESSArch/python27/bin/python
# -*- coding: UTF-8 -*-
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

from django.db import models
from django.contrib import admin
from picklefield.fields import PickledObjectField

import datetime
import sys
import uuid

# Logevents
class LogEvent(models.Model):
    eventType   = models.IntegerField( default=0, unique=True )
    eventDetail = models.CharField( max_length = 255 )

    class Meta:
        ordering = ['eventType']
        permissions = (
                       ("Can_view_log_menu", "Can_view_log_menu"),
                       )

    def __unicode__(self):
        # create a unicode representation of this object
        return self.eventDetail

    def populate_from_form(self, form):
        # pull out all fields from a form and use them to set
        # the values of this object.
        for field in LogEvent._meta.fields:
            if field.name in form.cleaned_data:
                setattr( self, field.name, form.cleaned_data[field.name] )

    def get_value_array(self):
        # make an associative array of all fields  mapping the field
        # name to the current value of the field
        return { field.name: field.value_to_string(self) 
                 for field in LogEvent._meta.fields }


# Parameters
class Parameter(models.Model):
    entity      = models.CharField( max_length = 255, unique=True )
    value       = models.CharField( max_length = 255 )
    
    class Meta:
        ordering = ["entity"]

    def __unicode__(self):
        # create a unicode representation of this object
        return self.entity
    
    def get_value_array(self):
        # make an associative array of all fields  mapping the field
        # name to the current value of the field
        return { field.name: field.value_to_string(self) 
                 for field in Parameter._meta.fields }


# Paths
class Path(models.Model):
    entity  = models.CharField( max_length = 255, unique=True )
    value   = models.CharField( max_length = 255 )

    class Meta:
        ordering = ["entity"]

 
# XML schemas and namespaces
class SchemaProfile(models.Model):
    entity      = models.CharField( max_length = 255, unique=True )
    value       = models.CharField( max_length = 255 )
    
    class Meta:
        ordering = ["entity"]
        verbose_name = 'XML schema'
    

# General metadata for information package
# Additional metadata for information package
# Reference metadata for files in information package
class IPParameter(models.Model):
    objid                                   = models.CharField( max_length = 255, unique=True   ) # General metadata for information package
    label                                   = models.CharField( max_length = 255 )
    type                                    = models.CharField( max_length = 255 )
    createdate                              = models.CharField( max_length = 255 )
    recordstatus                            = models.CharField( max_length = 255 )
    deliverytype                            = models.CharField( max_length = 255 )
    deliveryspecification                   = models.CharField( max_length = 255 )
    submissionagreement                     = models.CharField( max_length = 255 )
    previoussubmissionagreement             = models.CharField( max_length = 255 )
    datasubmissionsession                   = models.CharField( max_length = 255 )
    packagenumber                           = models.CharField( max_length = 255 )
    referencecode                           = models.CharField( max_length = 255 )
    previousreferencecode                   = models.CharField( max_length = 255 )
    appraisal                               = models.CharField( max_length = 255 )
    accessrestrict                          = models.CharField( max_length = 255 )
    archivist_organization                  = models.CharField( max_length = 255 )
    archivist_organization_id               = models.CharField( max_length = 255 )
    archivist_organization_software         = models.CharField( max_length = 255 )
    archivist_organization_software_id      = models.CharField( max_length = 255 )
    creator_organization                    = models.CharField( max_length = 255 )
    creator_organization_id                 = models.CharField( max_length = 255 )
    creator_individual                      = models.CharField( max_length = 255 )
    creator_individual_details              = models.CharField( max_length = 255 )    
    creator_software                        = models.CharField( max_length = 255 )
    creator_software_id                     = models.CharField( max_length = 255 )
    editor_organization                     = models.CharField( max_length = 255 )
    editor_organization_id                  = models.CharField( max_length = 255 )
    preservation_organization               = models.CharField( max_length = 255 )
    preservation_organization_id            = models.CharField( max_length = 255 )
    preservation_organization_software      = models.CharField( max_length = 255 )
    preservation_organization_software_id   = models.CharField( max_length = 255 )
    startdate                               = models.CharField( max_length = 255 ) # Additional metadata for information package
    enddate                                 = models.CharField( max_length = 255 )
    aic_id                                  = models.CharField( max_length = 255 )
    informationclass                        = models.CharField( max_length = 255 )
    projectname                             = models.CharField( max_length = 255 )
    policyid                                = models.IntegerField( default=0 )
    receipt_email                           = models.CharField( max_length = 255 )
    file_id                                 = models.CharField( max_length = 255 ) # Reference metadata for files in information package 
    file_name                               = models.CharField( max_length = 255 )
    file_createdate                         = models.CharField( max_length = 255 )
    file_mime_type                          = models.CharField( max_length = 255 )
    file_format                             = models.CharField( max_length = 255 )
    file_format_size                        = models.CharField( max_length = 255 )
    file_type                               = models.CharField( max_length = 255 )
    file_checksum                           = models.CharField( max_length = 255 )
    file_checksum_type                      = models.CharField( max_length = 255 )
    file_transform_type                     = models.CharField( max_length = 255 )
    file_transform_key                      = models.CharField( max_length = 255 )

    class Meta:
        ordering = ['type']
        verbose_name = 'Default values for IP parameter'
        
    def __unicode__(self):
        # create a unicode representation of this object
        return self.type

    def populate_from_form(self, form):
        # pull out all fields from a form and use them to set
        # the values of this object.
        for field in IPParameter._meta.fields:
            if field.name in form.cleaned_data:
                setattr( self, field.name, form.cleaned_data[field.name] )

    def get_value_array(self):
        # make an associative array of all fields  mapping the field
        # name to the current value of the field
        return { field.name: field.value_to_string(self) 
                 for field in IPParameter._meta.fields }

enabled_disabled_CHOICES = (
    (0, 'Disabled'),
    (1, 'Enabled'),
)

StorageTarget_Status_CHOICES = (
    (0, 'Disabled'),
    (1, 'Enabled'),
    (2, 'ReadOnly'),
    (3, 'Migrate'),
)

Mode_Policy_CHOICES = (
    (0, 'Master'),
    (2, 'AIS'),
)

WaitProjectApprobal_Policy_CHOICES = (
    (0, 'No'),
    (2, 'IngestRequest'),
)

ChecksumAlgorithm_CHOICES = (
    (1, 'MD5'),
    (2, 'SHA-256'),
)

AIPType_Policy_CHOICES = (
    (1, 'TAR'),
)

PreIngestMetadata_Policy_CHOICES = (
    (0, 'Disabled'),
    (1, 'RES'),
)

IngestMetadata_Policy_CHOICES = (
    (1, 'METS'),
    (4, 'METS (eArd)'),
)

INFORMATIONCLASS_Policy_CHOICES = (
    (0, '0'),
    (1, '1'),
    (2, '2'),
    (3, '3'),
    (4, '4'),
)

MediumType_CHOICES = (
    (200, 'DISK'),
    (300, 'TAPE'),
    (301, 'IBM-LTO1'),
    (302, 'IBM-LTO2'),
    (303, 'IBM-LTO3'),
    (304, 'IBM-LTO4'),
    (305, 'IBM-LTO5'),
    (306, 'IBM-LTO6'),
    (325, 'HP-LTO5'),
    (326, 'HP-LTO6'),
    (400, 'CAS'),
    (401, 'HDFS'),
    (402, 'HDFS-REST'),
)

MediumFormat_CHOICES = (
    (102, '102 (Media label)'),
    (103, '103 (AIC support)'),
)

MediumBlockSize_CHOICES = (
    (128, '64K'),
    (256, '128K'),
    (512, '256K'),
    (1024, '512K'),
    (2048, '1024K'),
)

minChunkSize_CHOICES = (
    (0, 'Disabled'),
    (1000000, '1 MByte'),
    (1073741824, '1 GByte'),
    (53687091201, '5 GByte'),
    (10737418240, '10 GByte'),
    (107374182400, '100 GByte'),
)

minContainerSize_CHOICES = (
    (0, 'Disabled'),
)

class ESSArchPolicy(models.Model):
    PolicyName          = models.CharField('Policy Name', max_length=255)
    PolicyID            = models.IntegerField('Policy ID', unique=True)
    PolicyStat          = models.IntegerField('Policy Status', choices=enabled_disabled_CHOICES, default=0)
    AISProjectName      = models.CharField('AIS Policy Name', max_length=255, blank=True)
    AISProjectID        = models.CharField('AIS Policy ID', max_length=255, blank=True)
    Mode                = models.IntegerField(choices=Mode_Policy_CHOICES, default=0)
    WaitProjectApproval = models.IntegerField('Wait for approval', choices=WaitProjectApprobal_Policy_CHOICES, default=2)
    ChecksumAlgorithm   = models.IntegerField('Checksum algorithm', choices=ChecksumAlgorithm_CHOICES,default=1)
    ValidateChecksum    = models.IntegerField('Validate checksum', choices=enabled_disabled_CHOICES,default=1)
    ValidateXML         = models.IntegerField('Validate XML', choices=enabled_disabled_CHOICES,default=1)
    ManualControll      = models.IntegerField('Manual Control', choices=enabled_disabled_CHOICES,default=0)
    AIPType             = models.IntegerField('AIP type', choices=AIPType_Policy_CHOICES,default=1)
    AIPpath             = models.CharField('Temp work directory', max_length=255,default='/ESSArch/work')
    PreIngestMetadata   = models.IntegerField('Pre ingest metadata',choices=PreIngestMetadata_Policy_CHOICES,default=0)
    IngestMetadata      = models.IntegerField('Ingest metadata', choices=IngestMetadata_Policy_CHOICES,default=4)
    INFORMATIONCLASS    = models.IntegerField('Information class', choices=INFORMATIONCLASS_Policy_CHOICES, default=0)
    IngestPath          = models.CharField('Ingest directory', max_length=255,default='/ESSArch/ingest')
    IngestDelete        = models.IntegerField('Delete SIP after success to create AIP', choices=enabled_disabled_CHOICES,default=1)
    sm_1                = models.IntegerField('Storage method', choices=enabled_disabled_CHOICES,default=0)
    sm_type_1           = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    sm_format_1         = models.IntegerField('Format', choices=MediumFormat_CHOICES,default=103)
    sm_blocksize_1      = models.BigIntegerField('BlockSize (tape)', choices=MediumBlockSize_CHOICES,default=1024)
    sm_maxCapacity_1    = models.BigIntegerField('Max capacity (0=Disabled)', default=0)
    sm_minChunkSize_1   = models.BigIntegerField('Min chunk size', choices=minChunkSize_CHOICES, default=0)
    sm_minContainerSize_1   = models.BigIntegerField('Min container size (0=Disabled)', choices=minContainerSize_CHOICES, default=0)
    sm_minCapacityWarning_1 = models.BigIntegerField('Min capacity warning (0=Disabled)', default=0)
    sm_target_1         = models.CharField('Target (path or barcodeprefix)', max_length=255,blank=True)
    sm_2                = models.IntegerField('Storage method', choices=enabled_disabled_CHOICES,default=0)
    sm_type_2           = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    sm_format_2         = models.IntegerField('Format', choices=MediumFormat_CHOICES,default=103)
    sm_blocksize_2      = models.BigIntegerField('BlockSize (tape)', choices=MediumBlockSize_CHOICES,default=1024)
    sm_maxCapacity_2    = models.BigIntegerField('Max capacity (0=Disabled)', default=0)
    sm_minChunkSize_2   = models.BigIntegerField('Min chunk size', choices=minChunkSize_CHOICES, default=0)
    sm_minContainerSize_2   = models.BigIntegerField('Min container size (0=Disabled)', choices=minContainerSize_CHOICES, default=0)
    sm_minCapacityWarning_2 = models.BigIntegerField('Min capacity warning (0=Disabled)', default=0)
    sm_target_2         = models.CharField('Target (path or barcodeprefix)', max_length=255,blank=True)
    sm_3                = models.IntegerField('Storage method', choices=enabled_disabled_CHOICES,default=0)
    sm_type_3           = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    sm_format_3         = models.IntegerField('Format', choices=MediumFormat_CHOICES,default=103)
    sm_blocksize_3      = models.BigIntegerField('BlockSize (tape)', choices=MediumBlockSize_CHOICES,default=1024)
    sm_maxCapacity_3    = models.BigIntegerField('Max capacity (0=Disabled)', default=0)
    sm_minChunkSize_3   = models.BigIntegerField('Min chunk size', choices=minChunkSize_CHOICES, default=0)
    sm_minContainerSize_3   = models.BigIntegerField('Min container size (0=Disabled)', choices=minContainerSize_CHOICES, default=0)
    sm_minCapacityWarning_3 = models.BigIntegerField('Min capacity warning (0=Disabled)', default=0)
    sm_target_3         = models.CharField('Target (path or barcodeprefix)', max_length=255,blank=True)
    sm_4                = models.IntegerField('Storage method', choices=enabled_disabled_CHOICES,default=0)
    sm_type_4           = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    sm_format_4         = models.IntegerField('Format', choices=MediumFormat_CHOICES,default=103)
    sm_blocksize_4      = models.BigIntegerField('BlockSize (tape)', choices=MediumBlockSize_CHOICES,default=1024)
    sm_maxCapacity_4    = models.BigIntegerField('Max capacity (0=Disabled)', default=0)
    sm_minChunkSize_4   = models.BigIntegerField('Min chunk size', choices=minChunkSize_CHOICES, default=0)
    sm_minContainerSize_4   = models.BigIntegerField('Min container size (0=Disabled)', choices=minContainerSize_CHOICES, default=0)
    sm_minCapacityWarning_4 = models.BigIntegerField('Min capacity warning (0=Disabled)', default=0)
    sm_target_4         = models.CharField('Target (path or barcodeprefix)', max_length=255,blank=True)
    class Meta:
        db_table = 'ESSArchPolicy'
        verbose_name = 'Archive policy'

class ArchivePolicy(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    #PolicyID = models.UUIDField(default=uuid.uuid4, unique=True)
    PolicyID = models.CharField('Policy ID', max_length=32, unique=True)
    PolicyName = models.CharField('Policy Name', max_length=255)
    PolicyStat = models.IntegerField('Policy Status', choices=enabled_disabled_CHOICES, default=0)
    AISProjectName = models.CharField('AIS Policy Name', max_length=255, blank=True)
    AISProjectID = models.CharField('AIS Policy ID', max_length=255, blank=True)
    Mode = models.IntegerField(choices=Mode_Policy_CHOICES, default=0)
    WaitProjectApproval = models.IntegerField('Wait for approval', choices=WaitProjectApprobal_Policy_CHOICES, default=2)
    ChecksumAlgorithm = models.IntegerField('Checksum algorithm', choices=ChecksumAlgorithm_CHOICES,default=1)
    ValidateChecksum = models.IntegerField('Validate checksum', choices=enabled_disabled_CHOICES,default=1)
    ValidateXML = models.IntegerField('Validate XML', choices=enabled_disabled_CHOICES,default=1)
    ManualControll = models.IntegerField('Manual Control', choices=enabled_disabled_CHOICES,default=0)
    AIPType = models.IntegerField('AIP type', choices=AIPType_Policy_CHOICES,default=1)
    AIPpath = models.CharField('Temp work directory', max_length=255,default='/ESSArch/work')
    PreIngestMetadata = models.IntegerField('Pre ingest metadata',choices=PreIngestMetadata_Policy_CHOICES,default=0)
    IngestMetadata = models.IntegerField('Ingest metadata', choices=IngestMetadata_Policy_CHOICES,default=4)
    INFORMATIONCLASS = models.IntegerField('Information class', choices=INFORMATIONCLASS_Policy_CHOICES, default=0)
    IngestPath = models.CharField('Ingest directory', max_length=255,default='/ESSArch/ingest')
    IngestDelete = models.IntegerField('Delete SIP after success to create AIP', choices=enabled_disabled_CHOICES,default=1)

    def __unicode__(self):
        if len(self.PolicyName): return self.PolicyName
        else: return unicode(self.PolicyID)

class StorageMethod(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Name', max_length=255, blank=True)
    status = models.IntegerField('Storage method status', choices=enabled_disabled_CHOICES,default=0)
    type = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    archivepolicy = models.ForeignKey('ArchivePolicy')

    def __unicode__(self):
        if len(self.name): return self.name
        else: return unicode(self.id)

class StorageTarget(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Name', max_length=255, blank=True)
    status = models.IntegerField('Storage target status', choices=StorageTarget_Status_CHOICES,default=0)
    target = models.ForeignKey('StorageTargets')
    storagemethod = models.ForeignKey('StorageMethod')
    class Meta:
        verbose_name = 'Target'
        
    def __unicode__(self):
        if len(self.name): return self.name
        else: return unicode(self.id)

class StorageTargets(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField('Name', max_length=255, unique=True)
    status = models.IntegerField('Storage target status', choices=enabled_disabled_CHOICES,default=1)
    type = models.IntegerField('Type', choices=MediumType_CHOICES,default=200)
    format = models.IntegerField('Format', choices=MediumFormat_CHOICES,default=103)
    blocksize = models.BigIntegerField('BlockSize (tape)', choices=MediumBlockSize_CHOICES,default=1024)
    maxCapacity = models.BigIntegerField('Max capacity (0=Disabled)', default=0)
    minChunkSize = models.BigIntegerField('Min chunk size', choices=minChunkSize_CHOICES, default=0)
    minContainerSize = models.BigIntegerField('Min container size (0=Disabled)', choices=minContainerSize_CHOICES, default=0)
    minCapacityWarning = models.BigIntegerField('Min capacity warning (0=Disabled)', default=0)
    target = models.CharField('Target (URL, path or barcodeprefix)', max_length=255)
    class Meta:
        verbose_name = 'Storage Target'

    def __unicode__(self):
        if len(self.name): return self.name
        else: return unicode(self.id)

class sm(object):
    id                  = 0
    type                = 200
    format              = 103
    blocksize           = 1024
    maxCapacity         = 0
    minChunkSize        = 0
    minContainerSize    = 0
    minCapacityWarning  = 0
    target              = ''

class ESSConfig(models.Model):
    Name = models.CharField(max_length=255)
    Value = models.CharField(max_length=255,blank=True)
    Status = models.CharField(max_length=10,blank=True)
    class Meta:
        db_table = 'ESSConfig'
        verbose_name = 'Parameter (core)'

class ESSProc(models.Model):
    Name = models.CharField(max_length=255)
    Path = models.CharField(max_length=255)
    LogFile = models.CharField(max_length=255)
    expected_pids = models.IntegerField(default=1)
    Time = models.CharField(max_length=4)
    Status = models.CharField(max_length=10)
    Run = models.CharField(max_length=10)
    PID = models.IntegerField()
    child_pids = PickledObjectField(null=True)
    Pause = models.IntegerField()
    checked = models.DateTimeField(default='2014-01-01 00:01')
    alarm = models.IntegerField(default=0)
    class Meta:
        db_table = 'ESSProc'
        verbose_name = 'Worker processes (core)'
        
# Default value
class DefaultValueQuerySet(models.query.QuerySet):
    def get_value_object(self):
        class Struct:
            def __init__(self, **entries):
                self.__dict__.update(entries)
        return Struct(**dict(self.values_list('entity','value')))

class DefaultValueManager(models.Manager):
    def get_query_set(self):
        return DefaultValueQuerySet(self.model)

    def __getattr__(self, attr, *args):
        if attr.startswith("_"): # or at least "__"
            raise AttributeError
        return getattr(self.get_query_set(), attr, *args) 

class DefaultValue(models.Model):
    entity      = models.CharField( max_length = 255, unique=True )
    value       = models.CharField( max_length = 255 )
    objects     = DefaultValueManager()
    
    class Meta:
        ordering = ["entity"]
        verbose_name = 'Default value'
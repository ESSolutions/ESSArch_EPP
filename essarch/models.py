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
from django.db import models

# Create your models here.
class permission(models.Model):
    class Meta:
        permissions = (
            ("ESSArch_Marieberg", "site Marieberg"),
            ("ESSArch_MKC", "site MKC"),
            ("ESSArch_SVAR", "site SVAR"),
            ("ESSArch_HLA", "site HLA"),
            ("ESSArch_Globen", "site Globen"),
            ("ESSArch_RA-OSLO", "site Oslo"),
            ("essadministrate", "ESSArch admin "),
            ("essaccess", "ESSArch access"),
            ("essingest", "ESSArch ingest"),
            ("infoclass_0", "Information Class 0"),
            ("infoclass_1", "Information Class 1"),
            ("infoclass_2", "Information Class 2"),
            ("infoclass_3", "Information Class 3"),
            ("infoclass_4", "Information Class 4"),
        )

class ArchiveObject(models.Model):
    ObjectUUID = models.CharField(max_length=36, unique=True)
    PolicyId = models.IntegerField()
    ObjectIdentifierValue = models.CharField(max_length=255, unique=True)
    ObjectPackageName = models.CharField(max_length=255)
    ObjectSize = models.BigIntegerField()
    ObjectNumItems = models.IntegerField()
    ObjectMessageDigestAlgorithm = models.IntegerField()
    ObjectMessageDigest = models.CharField(max_length=128)
    ObjectPath = models.CharField(max_length=255)
    ObjectActive = models.IntegerField()
    MetaObjectIdentifier = models.CharField(max_length=255)
    MetaObjectSize = models.BigIntegerField()
    CMetaMessageDigestAlgorithm = models.IntegerField()
    CMetaMessageDigest = models.CharField(max_length=128)
    PMetaMessageDigestAlgorithm = models.IntegerField()
    PMetaMessageDigest = models.CharField(max_length=128)
    DataObjectSize = models.BigIntegerField()
    DataObjectNumItems = models.IntegerField()
    Status = models.IntegerField()
    StatusActivity = models.IntegerField()
    StatusProcess = models.IntegerField()
    LastEventDate = models.DateTimeField()
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    CreateDate = models.DateTimeField()
    CreateAgentIdentifierValue = models.CharField(max_length=45)
    EntryDate = models.DateTimeField()
    EntryAgentIdentifierValue = models.CharField(max_length=45)
    OAISPackageType = models.IntegerField()
    preservationLevelValue = models.IntegerField()
    DELIVERYTYPE = models.CharField(max_length=255)
    INFORMATIONCLASS = models.IntegerField()
    Generation = models.IntegerField()
    LocalDBdatetime = models.DateTimeField()
    ExtDBdatetime = models.DateTimeField()
    class Meta:
        db_table = 'IngestObject'

class ArchiveObjectData(models.Model):
    #UUID = models.CharField(max_length=36)
    UUID = models.ForeignKey(ArchiveObject, db_column='UUID', to_field='ObjectUUID')
    Creator = models.CharField(max_length=255)
    System = models.CharField(max_length=255)
    Version = models.CharField(max_length=255)
    class Meta:
        db_table = 'Object_data'

class ArchiveObjectMetadata(models.Model):
    #ObjectUUID = models.CharField(max_length=36)
    ObjectUUID = models.ForeignKey(ArchiveObject, db_column='ObjectUUID', to_field='ObjectUUID')
    ObjectIdentifierValue = models.CharField(max_length=255)
    ObjectMetadataType = models.IntegerField()
    ObjectMetadataServer = models.IntegerField()
    ObjectMetadataURL = models.CharField(max_length=255)
    ObjectMetadataBLOB = models.TextField()
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    LocalDBdatetime = models.DateTimeField()
    ExtDBdatetime = models.DateTimeField()
    class Meta:
        db_table = 'IngestObjectMetadata'

class ArchiveObjectRel(models.Model):
    #AIC_UUID = models.CharField(max_length=36)
    AIC_UUID = models.ForeignKey(ArchiveObject, db_column='AIC_UUID', related_name='relaic_set', to_field='ObjectUUID')
    #UUID = models.CharField(max_length=36)
    UUID = models.ForeignKey(ArchiveObject, db_column='UUID', related_name='reluuid_set', to_field='ObjectUUID')
    class Meta:
        db_table = 'Object_rel'

class agentIdentifier(models.Model):
    agentIdentifierValue = models.CharField(max_length=45)
    agentName = models.CharField(max_length=45)
    agentType = models.IntegerField()
    class Meta:
        db_table = 'agentIdentifier'

class eventIdentifier(models.Model):
    eventIdentifierValue = models.CharField(max_length=36, unique=True)
    eventType = models.IntegerField()
    eventDateTime = models.DateTimeField()
    eventDetail = models.CharField(max_length=255)
    eventApplication = models.CharField(max_length=50)
    eventVersion = models.CharField(max_length=45)
    eventOutcome = models.IntegerField()
    eventOutcomeDetailNote = models.CharField(max_length=255)
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    linkingObjectIdentifierValue = models.CharField(max_length=255)
    class Meta:
        db_table = 'eventIdentifier'

class eventType_codes(models.Model):
    code = models.IntegerField()
    desc_sv = models.CharField(max_length=100)
    desc_en = models.CharField(max_length=100)
    localDB = models.IntegerField()
    externalDB = models.IntegerField()
    class Meta:
        db_table = 'eventType_codes'

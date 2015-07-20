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
from django.core.exceptions import ObjectDoesNotExist
from configuration.models import StorageMethod, StorageTarget, StorageTargets
from essarch.models import ArchiveObject
from picklefield.fields import PickledObjectField
import uuid

IOReqType_CHOICES = (
    (10, 'Write to tape'),
    (15, 'Write to disk'),
    (20, 'Read from tape'),
    (25, 'Read from disk'),
    (41, 'Write to HDFS'),
    (42, 'Read from HDFS'),
    (43, 'Write to HDFS-REST'),
    (44, 'Read from HDFS-REST'),
)

ReqStatus_CHOICES = (
    (0, 'Pending'),
    (2, 'Initiate'),
    (5, 'Progress'),
    (20, 'Success'),
    (100, 'FAIL'),
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

MediumStatus_CHOICES = (
    (0, 'Inactive'),
    (20, 'Write'),
    (30, 'Full'),
    (100, 'FAIL'),
)

MediumLocationStatus_CHOICES = (
    (10, '10'),
    (20, '20'),
    (30, '30'),
    (40, '40'),
    (50, 'Robot'),
)

class storageMedium(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    storageMediumUUID = models.CharField(max_length=36, unique=True)
    storageMedium = models.IntegerField(choices=MediumType_CHOICES)
    storageMediumID = models.CharField(max_length=255, unique=True)
    storageMediumDate = models.DateTimeField()
    storageMediumLocation = models.CharField(max_length=255)
    storageMediumLocationStatus = models.IntegerField(choices=MediumLocationStatus_CHOICES)
    storageMediumBlockSize = models.IntegerField()
    storageMediumUsedCapacity = models.BigIntegerField()
    storageMediumStatus = models.IntegerField(choices=MediumStatus_CHOICES)
    storageMediumFormat = models.IntegerField(choices=MediumFormat_CHOICES)
    storageMediumMounts = models.IntegerField()
    linkingAgentIdentifierValue = models.CharField(max_length=255)
    CreateDate  = models.DateTimeField(null=True)
    CreateAgentIdentifierValue = models.CharField(max_length=255)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    storagetarget = models.ForeignKey(StorageTargets)
    class Meta:
        permissions = (
            ("list_storageMedium", "Can list storageMedium"),
        )

    def __unicode__(self):
        if len(self.storageMediumID): return self.storageMediumID
        else: return unicode(self.id)
        
class storage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contentLocationType = models.IntegerField(choices=MediumType_CHOICES)
    contentLocationValue = models.CharField(max_length=255)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    archiveobject = models.ForeignKey(ArchiveObject, related_name='Storage_set', to_field='ObjectUUID')
    storagemedium = models.ForeignKey(storageMedium)
    class Meta:
        permissions = (
            ("list_storage", "Can list storage"),
        )

    def __unicode__(self):
        try:
            storageMediumID = self.storagemedium.storageMediumID
        except ObjectDoesNotExist:
            storageMediumID = 'unknown media'
        try:
            ObjectIdentifierValue = self.archiveobject.ObjectIdentifierValue
        except ObjectDoesNotExist:
            storageMediumID = 'unknown object'
        name = '%s @ %s' % (ObjectIdentifierValue, storageMediumID)
        return name


class IOQueue(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ReqType = models.IntegerField(choices=IOReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255, blank=True)
    user = models.CharField(max_length=45)
    ObjectPath = models.CharField(max_length=256, blank=True)
    WriteSize = models.BigIntegerField(null=True, blank=True)
    result = PickledObjectField(blank=True)
    Status = models.IntegerField(blank=True, default=0, choices=ReqStatus_CHOICES)
    task_id = models.CharField(max_length=36,blank=True)
    posted = models.DateTimeField(auto_now_add=True)
    archiveobject = models.ForeignKey(ArchiveObject, to_field='ObjectUUID', blank=True, null=True)
    storagemethod = models.ForeignKey(StorageMethod, blank=True, null=True)
    storagemethodtarget = models.ForeignKey(StorageTarget, blank=True, null=True)
    storagetarget = models.ForeignKey(StorageTargets, blank=True, null=True)
    storagemedium = models.ForeignKey(storageMedium, blank=True, null=True)
    storage = models.ForeignKey(storage, blank=True, null=True)
    class Meta:
        permissions = (
            ("list_IOQueue", "Can list IOQueue"),
        )
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
from django import forms
from django.utils.safestring import mark_safe
from django.forms.util import flatatt
from django.core.urlresolvers import reverse

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

StatusActivity_CHOICES = (
    (0, 'OK'),
    (1, 'New object'),
    (2, 'Receive'),
    (3, 'Checking'),
    (4, 'Need of assistance'),
    (5, 'Progress'),
    (6, 'Pending writes'),
    (100, 'FAIL'),
)

StatusProcess_CHOICES = (
    (0, 'Receive new object'),
    (5, 'The object is ready to remodel'),
    (9, 'New object stable'),
    (10, "Object don't exist in AIS"),
    (11, "Object don't have any projectcode in AIS"),
    (12, "Object don't have any local policy"),
    (13, "Object already have an AIP!"),
    (14, "Object is not active!"),
    (19, 'Object got a policy'),
    (20, "Object not updated from AIS"),
    (21, 'Object not accepted in AIS'),
    (24, 'Object accepted in AIS'),
    (25, 'SIP validate'),
    (26, 'SIP validate failed'),
    (29, 'SIP validate OK'),
    (30, 'Create AIP package'),
    (31, 'AIP create failed'),
    (39, 'AIP created OK'),
    (40, 'Create packge checksum'),
    (49, 'AIP checksum created OK'),
    (50, 'AIP validate'),
    (51, 'AIP validate failed'),
    (59, 'AIP validate OK'),
    (60, 'Try to remove IngestObject'),
    (61, 'Failed to remove IngestObject'),
    (69, 'Remove OK of IngestObject'),
    (1000, 'Write AIP to longterm storage'),
    (1001, 'Fail to write AIP'),
    (1002, 'No empty media available'),
    (1003, 'Problem to mount media'),
    (1004, 'Failed to verify tape after full write'),
    (1999, 'Write AIP OK'),
    (2000, 'Try to remove temp AIP object'),
    (2001, 'Failed to remove temp AIP object'),
    (2009, 'Remove temp AIP object OK'),
    (3000, 'Archived'),
    (5000, 'ControlArea'),
    (5100, 'WorkArea'),
)

PackageType_CHOICES = (
    (0, 'SIP'),
    (1, 'AIC'),
    (2, 'AIP'),
    (3, 'AIU'),
    (4, 'DIP'),
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
    StatusActivity = models.IntegerField(choices=StatusActivity_CHOICES)
    StatusProcess = models.IntegerField(choices=StatusProcess_CHOICES)
    LastEventDate = models.DateTimeField()
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    CreateDate = models.DateTimeField()
    CreateAgentIdentifierValue = models.CharField(max_length=45)
    EntryDate = models.DateTimeField()
    EntryAgentIdentifierValue = models.CharField(max_length=45)
    OAISPackageType = models.IntegerField(choices=PackageType_CHOICES)
    preservationLevelValue = models.IntegerField()
    DELIVERYTYPE = models.CharField(max_length=255)
    INFORMATIONCLASS = models.IntegerField()
    Generation = models.IntegerField()
    LocalDBdatetime = models.DateTimeField()
    ExtDBdatetime = models.DateTimeField()
    class Meta:
        db_table = 'IngestObject'
    def get_absolute_url(self):
        return reverse('ingest_listobj')

class ArchiveObjectStatusForm(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model=ArchiveObject
        exclude=('ObjectUUID','PolicyId','ObjectIdentifierValue','ObjectPackageName','ObjectSize','ObjectNumItems','ObjectMessageDigestAlgorithm','ObjectMessageDigest',
                 'ObjectPath','ObjectActive','MetaObjectIdentifier','MetaObjectSize','CMetaMessageDigestAlgorithm','CMetaMessageDigest','PMetaMessageDigestAlgorithm',
                 'PMetaMessageDigest','DataObjectSize','DataObjectNumItems','Status','StatusProcess','LastEventDate','linkingAgentIdentifierValue','CreateDate',
                 'CreateAgentIdentifierValue','EntryDate','EntryAgentIdentifierValue','OAISPackageType','preservationLevelValue','DELIVERYTYPE','INFORMATIONCLASS',
                 'Generation','LocalDBdatetime','ExtDBdatetime')
        widgets = {'StatusActivity': forms.Select(attrs={'onchange':'submit()'}),}    

class ArchiveObjectData(models.Model):
    #UUID = models.CharField(max_length=36)
    UUID = models.ForeignKey(ArchiveObject, db_column='UUID', to_field='ObjectUUID')
    creator = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    startdate = models.DateTimeField()
    enddate = models.DateTimeField()
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

ReqStatus_CHOICES = (
    (0, 'Pending'),
    (5, 'Progress'),
    (20, 'Success'),
    (100, 'FAIL'),
)

AccessReqType_CHOICES = (
    (3, 'Generate DIP (package)'),
    (4, 'Generate DIP (package extracted)'),
    (1, 'Generate DIP (package & package extracted)'),
    (2, 'Verify StorageMedium'),
)

class AccessQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(choices=AccessReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = models.CharField(max_length=255, blank=True)
    storageMediumID = models.CharField(max_length=45, blank=True)
    Status = models.IntegerField(blank=True, default=0, choices=ReqStatus_CHOICES)
    Path = models.CharField(max_length=255)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'AccessQueue'
    def get_absolute_url(self):
        return reverse('access_list')

class PlainText(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs)
        if not value=='' and hasattr(self, 'choices'):
            value_label = dict(self.choices)[value]
        else:
            value_label = value
        return mark_safe(u'<input type="hidden" name="%s" %s value="%s" />%s' % (name,flatatt(final_attrs),value,value_label))

class AccessQueueForm(forms.ModelForm):
    required_css_class = 'required'
    #ReqUUID = forms.CharField(label='ReqUUID', widget = forms.TextInput(attrs={'readonly':'readonly'}))
    ReqUUID = forms.CharField(label='ReqUUID', widget = PlainText())
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = forms.CheckboxInput(attrs={'disabled':'disabled'}))
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = forms.Select(attrs={'disabled':'disabled'}))
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = PlainText())
    ObjectIdentifierValue = forms.CharField(widget=forms.Textarea())
    Status = forms.IntegerField(widget = forms.HiddenInput())
    user = forms.CharField(label='User', widget = PlainText())
#    def clean_Path(self):
#        data = self.cleaned_data['Path']
#        print data
#        if not data == 'hej0077':
#            raise forms.ValidationError("Wrong Path2222")
#        return data
#    def clean(self):
#        cleaned_data = super(AccessQueueForm, self).clean()
#        Path = cleaned_data.get('Path')
#        if not Path == 'hej007':
#            msg = u"Wrong path!"
#            self._errors["Path"] = self.error_class([msg])
#        del cleaned_data['Path']
#        print 'dir cleaned_data: %s' % dir(cleaned_data)
#        print 'cleaned_data: %s' % cleaned_data
#        return cleaned_data

    class Meta:
        model=AccessQueue   
        exclude=('password',)    

class AccessQueueFormUpdate(AccessQueueForm):
    Status = forms.ChoiceField(choices=ReqStatus_CHOICES)

IngestReqType_CHOICES = (
    (1, 'Ingest request'),
    (2, 'Ingest request without AIS'),
)

class IngestQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(choices=IngestReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = models.CharField(max_length=255, blank=True)
    Status = models.IntegerField(blank=True, default=0, choices=ReqStatus_CHOICES)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'ReqIngestQueue'
    def get_absolute_url(self):
        return reverse('ingest_list')
    
class IngestQueueForm(forms.ModelForm):
    required_css_class = 'required'
    ReqUUID = forms.CharField(label='ReqUUID', widget = PlainText())
    ObjectIdentifierValue = forms.CharField(widget=forms.Textarea())
    Status = forms.IntegerField(widget = forms.HiddenInput())
    user = forms.CharField(label='User', widget = PlainText())
    class Meta:
        model=IngestQueue   
        exclude=('password',)    

class IngestQueueFormUpdate(IngestQueueForm):
    Status = forms.ChoiceField(choices=ReqStatus_CHOICES)
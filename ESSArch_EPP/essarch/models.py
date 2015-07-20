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
from celery.worker.strategy import default
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
from django.db import models
from django import forms
from django.utils.safestring import mark_safe
from django.forms.utils import flatatt
from django.core.urlresolvers import reverse
from django.conf import settings
from configuration.models import ESSArchPolicy, ArchivePolicy
#import django_tables2 as tables
#from django_tables2.utils import A
from djcelery.models import TaskMeta
from picklefield.fields import PickledObjectField
from essarch.fields import BigAutoField

###########################################################################
#
# ESSArch permission model
#
class permission(models.Model):
    class Meta:
        permissions = (
            #("ESSArch_Marieberg", "site Marieberg"),
            #("ESSArch_MKC", "site MKC"),
            #("ESSArch_SVAR", "site SVAR"),
            #("ESSArch_HLA", "site HLA"),
            #("ESSArch_Globen", "site Globen"),
            #("ESSArch_RA-OSLO", "site Oslo"),
            ("essadministrate", "ESSArch admin "),
            ("essaccess", "ESSArch access"),
            ("essingest", "ESSArch ingest"),
            ("infoclass_0", "Information Class 0"),
            ("infoclass_1", "Information Class 1"),
            ("infoclass_2", "Information Class 2"),
            ("infoclass_3", "Information Class 3"),
            ("infoclass_4", "Information Class 4"),
        )

###########################################################################
#
# Custom widgets
#
class PlainText(forms.TextInput):
    def render(self, name, value, attrs=None):
        if value is None:
            value = ''
        final_attrs = self.build_attrs(attrs)
        if not value=='' and hasattr(self, 'choices'):
            try:
                value = int(value)
            except:
                value_label = value
            else:
                value_label = dict(self.choices)[value]
        else:
            value_label = value
        return mark_safe(u'<input type="hidden" name="%s" %s value="%s" />%s' % (name,flatatt(final_attrs),value,value_label))

class MultiSelectWidget(forms.SelectMultiple):
    #css_class = 'multiselect'
    class Media:
        css = {
            'all': (
                #settings.STATIC_URL + 'js/jquery.uix.multiselect/css/common.css',
                #settings.STATIC_URL + 'jquery-ui-1.10.3/themes/base/jquery-ui.css',
                settings.STATIC_URL + 'jquery.uix.multiselect/css/jquery.uix.multiselect.css',
            )
        }
        js = (
            #settings.STATIC_URL + 'jquery-1.10.2.min.js',
            #settings.STATIC_URL + 'jquery-ui-1.10.3/ui/minified/jquery-ui.min.js',
            settings.STATIC_URL + 'jquery.uix.multiselect/js/jquery.uix.multiselect.js',
        )

    #def add_css_class(self, attrs):
    #    attrs = attrs or {}
    #    if 'class' in attrs:
    #        attrs['class'] += " %s" % self.css_class
    #    else:
    #        attrs['class'] = self.css_class
    #    return attrs

    def __init__(self, language=None, attrs=None):
        self.language = language or settings.LANGUAGE_CODE[:2]
        #attrs = self.add_css_class(attrs)
        super(MultiSelectWidget, self).__init__(attrs=attrs)

    def render(self, name, value, attrs=None):
        rendered = super(MultiSelectWidget, self).render(name, value, attrs)
        return rendered + mark_safe(u'''<script type="text/javascript">
           $(document).ready(function afterReady() {
                var elem = $('#id_%(name)s');
                elem.multiselect();
            });
            </script>''' % {'name':name})

###########################################################################
#
# Choices for models and forms
#
StatusActivity_CHOICES = (
    (0, 'OK'),
    (1, 'New object'),
    (2, 'Receive'),
    (3, 'Checking'),
    (4, 'Need of assistance'),
    (5, 'Progress'),
    (6, 'Pending writes'),
    (7, 'ControlArea'),
    (8, 'WorkArea'),
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
    (9999, 'Deleted'),
)

PackageType_CHOICES = (
    (0, 'SIP'),
    (1, 'AIC'),
    (2, 'AIP'),
    (3, 'AIU'),
    (4, 'DIP'),
)

ReqStatus_CHOICES = (
    (0, 'Pending'),
    (2, 'Initiate'),
    (5, 'Progress'),
    (20, 'Success'),
    (100, 'FAIL'),
)

ControlAreaReqType_CHOICES = (
    (1, 'CheckIn from Reception'),
    (2, 'CheckOut to Workarea'),
    (3, 'CheckIn from Workarea'),
    (4, 'DiffCheck'),
    (5, 'Preserve Information Package'),
    (6, 'CheckOut to Gatearea from WorkArea'),
    (7, 'CheckIn from Gatearea to WorkArea'),
    (8, 'Delete IP in control/work area'),
)

AccessReqType_CHOICES = (
    (3, 'Generate DIP (package)'),
    (4, 'Generate DIP (package extracted)'),
    (1, 'Generate DIP (package & package extracted)'),
    (2, 'Verify StorageMedium'),
    (5, 'Get AIP to ControlArea'),
)

IngestReqType_CHOICES = (
    (1, 'Ingest request'),
    (2, 'Ingest request without AIS'),
)

MigrationReqType_CHOICES = (
    (1, 'Copy IP to new storage'),
)

RobotReqType_CHOICES = (
    (50, 'Mount tape'),
    (51, 'Unmount tape'),
    (52, 'Unmount tape (force)'),
    (1, 'Robot inventory'),
)

#RobotReqStatus_CHOICES = (
#    ('0', 'Pending'),
#    ('5', 'Progress'),
#    ('20', 'Success'),
#    ('100', 'FAIL'),
#    ('pending', 'Mount/Unmount Pending'),
#    ('mounting', 'Mount/Unmount Progress'),
#)

MediumType_CHOICES = (
    (200, 'DISK'),
    (301, 'IBM-LTO1'),
    (302, 'IBM-LTO2'),
    (303, 'IBM-LTO3'),
    (304, 'IBM-LTO4'),
    (305, 'IBM-LTO5'),
    (306, 'IBM-LTO6'),
    (325, 'HP-LTO5'),
    (326, 'HP-LTO6'),
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

MediumBlockSize_CHOICES = (
    (128, '64K'),
    (256, '128K'),
    (512, '256K'),
    (1024, '512K'),
    (2048, '1024K'),
)

eventOutcome_CHOICES = (
    (0, 'OK'),
    (1, 'Failed'),
)

###########################################################################
#
# General models and forms
#
class ArchiveObject(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    ObjectUUID = models.CharField(max_length=36, unique=True)
    #PolicyId = models.IntegerField(null=True)
    #PolicyId = models.ForeignKey(ESSArchPolicy, db_column='PolicyId', to_field='PolicyID', default=0)
    PolicyId = models.ForeignKey(ArchivePolicy, db_column='PolicyId', to_field='PolicyID', default=0)
    ObjectIdentifierValue = models.CharField(max_length=255, unique=True)
    ObjectPackageName = models.CharField(max_length=255)
    ObjectSize = models.BigIntegerField(null=True)
    ObjectNumItems = models.IntegerField(null=True)
    ObjectMessageDigestAlgorithm = models.IntegerField(null=True)
    ObjectMessageDigest = models.CharField(max_length=128)
    ObjectPath = models.CharField(max_length=255)
    ObjectActive = models.IntegerField(null=True)
    MetaObjectIdentifier = models.CharField(max_length=255)
    MetaObjectSize = models.BigIntegerField(null=True)
    CMetaMessageDigestAlgorithm = models.IntegerField(null=True)
    CMetaMessageDigest = models.CharField(max_length=128)
    PMetaMessageDigestAlgorithm = models.IntegerField(null=True)
    PMetaMessageDigest = models.CharField(max_length=128)
    DataObjectSize = models.BigIntegerField(null=True)
    DataObjectNumItems = models.IntegerField(null=True)
    Status = models.IntegerField(null=True)
    StatusActivity = models.IntegerField(null=True, choices=StatusActivity_CHOICES)
    StatusProcess = models.IntegerField(null=True, choices=StatusProcess_CHOICES)
    LastEventDate = models.DateTimeField(null=True)
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    CreateDate = models.DateTimeField(null=True)
    CreateAgentIdentifierValue = models.CharField(max_length=45)
    EntryDate = models.DateTimeField(null=True)
    EntryAgentIdentifierValue = models.CharField(max_length=45)
    OAISPackageType = models.IntegerField(null=True,choices=PackageType_CHOICES)
    preservationLevelValue = models.IntegerField(null=True)
    DELIVERYTYPE = models.CharField(max_length=255)
    INFORMATIONCLASS = models.IntegerField(null=True)
    Generation = models.IntegerField(null=True)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    class Meta:
        db_table = 'IngestObject'
    def __unicode__(self):
        return self.ObjectIdentifierValue
    def get_absolute_url(self):
        return reverse('ingest_listobj')
    def get_ip_list(self,StatusProcess=None,StatusProcess__lt=None,StatusProcess__in=None,StatusActivity__in=None):
        ip_list = []
        # Try to get an list of IP objects related to AIC object "IP_Object"
        ip_obj_list = ArchiveObject.objects.filter(reluuid_set__AIC_UUID=self).order_by('Generation')
        if StatusProcess__in and StatusActivity__in:
            ip_obj_list = ip_obj_list.filter(models.Q(StatusProcess__in=StatusProcess__in) | models.Q(StatusActivity__in=StatusActivity__in))
        elif StatusProcess and StatusActivity__in:
            ip_obj_list = ip_obj_list.filter(models.Q(StatusProcess=StatusProcess) | models.Q(StatusActivity__in=StatusActivity__in))
        elif StatusProcess:
            ip_obj_list = ip_obj_list.filter(StatusProcess=StatusProcess)
        if StatusProcess__lt:
            ip_obj_list = ip_obj_list.filter(StatusProcess__lt=StatusProcess__lt)
        if ip_obj_list:
            aic_obj = self
            for ip_obj in ip_obj_list:
                if not ip_obj.OAISPackageType == 1:
                    ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                    if ip_obj_data_list:
                        ip_obj_data = ip_obj_data_list[0]
                    else:
                        ip_obj_data = None
                    ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                    if ip_obj_metadata_list:
                        ip_obj_metadata = ip_obj_metadata_list[0]
                    else:
                        ip_obj_metadata = None
                    ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
        # Check if object "IP_Object" has an AIC, if not "IP_Object" can be an IP object without AIC.
        elif not ArchiveObject.objects.filter(relaic_set__UUID=self).exists():
            aic_obj = None
            if not self.OAISPackageType == 1:
                ip_obj = self
                ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                if ip_obj_data_list:
                    ip_obj_data = ip_obj_data_list[0]
                else:
                    ip_obj_data = None
                ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                if ip_obj_metadata_list:
                    ip_obj_metadata = ip_obj_metadata_list[0]
                else:
                    ip_obj_metadata = None
                ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
                
        return ip_list

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
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    UUID = models.ForeignKey(ArchiveObject, db_column='UUID', to_field='ObjectUUID')
    creator = models.CharField(max_length=255)
    label = models.CharField(max_length=255)
    startdate = models.DateTimeField(null=True)
    enddate = models.DateTimeField(null=True)
    class Meta:
        db_table = 'Object_data'

class ArchiveObjectMetadata(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    ObjectUUID = models.ForeignKey(ArchiveObject, db_column='ObjectUUID', to_field='ObjectUUID')
    ObjectIdentifierValue = models.CharField(max_length=255)
    ObjectMetadataType = models.IntegerField(null=True)
    ObjectMetadataServer = models.IntegerField(null=True)
    ObjectMetadataURL = models.CharField(max_length=255)
    ObjectMetadataBLOB = models.TextField()
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    class Meta:
        db_table = 'IngestObjectMetadata'

class ArchiveObjectRel(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    AIC_UUID = models.ForeignKey(ArchiveObject, db_column='AIC_UUID', related_name='relaic_set', to_field='ObjectUUID')
    UUID = models.ForeignKey(ArchiveObject, db_column='UUID', related_name='reluuid_set', to_field='ObjectUUID')
    class Meta:
        db_table = 'Object_rel'

class agentIdentifier(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    agentIdentifierValue = models.CharField(max_length=45)
    agentName = models.CharField(max_length=45)
    agentType = models.IntegerField(null=True)
    class Meta:
        db_table = 'agentIdentifier'

class eventIdentifier(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    eventIdentifierValue = models.CharField(max_length=36, unique=True)
    eventType = models.IntegerField(null=True)
    eventDateTime = models.DateTimeField(null=True)
    eventDetail = models.CharField(max_length=255)
    eventApplication = models.CharField(max_length=50)
    eventVersion = models.CharField(max_length=45)
    eventOutcome = models.IntegerField(null=True)
    eventOutcomeDetailNote = models.CharField(max_length=255)
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    linkingObjectIdentifierValue = models.CharField(max_length=255)
    class Meta:
        db_table = 'eventIdentifier'

class eventType_codes(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    code = models.IntegerField(null=True)
    desc_sv = models.CharField(max_length=100)
    desc_en = models.CharField(max_length=100)
    localDB = models.IntegerField(null=True)
    externalDB = models.IntegerField(null=True)
    class Meta:
        db_table = 'eventType_codes'

class IOqueue(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    cmd = models.IntegerField(null=True)
    cmdprio = models.IntegerField(null=True)
    work_uuid = models.CharField(max_length=36)
    ObjectIdentifierValue = models.CharField(max_length=255)
    ObjectMessageDigest = models.CharField(max_length=128)
    ObjectPath = models.CharField(max_length=255)
    storageMedium = models.IntegerField(null=True)
    storageMediumID = models.CharField(max_length=45)
    sm_list = models.CharField(max_length=255)
    storageMediumBlockSize = models.IntegerField(null=True)
    storageMediumFormat = models.IntegerField(null=True)
    contentLocationValue = models.IntegerField(null=True)
    storageMediumLocation = models.CharField(max_length=45)
    t_prefix = models.CharField(max_length=6)
    WriteSize = models.BigIntegerField(null=True)
    date_created = models.DateTimeField(null=True)
    Status = models.IntegerField(null=True)
    class Meta:
        db_table = 'IOqueue'

class ESSReg001(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    ObjectUUID = models.ForeignKey(ArchiveObject, db_column='ObjectUUID', to_field='ObjectUUID')
    i000 = models.IntegerField(null=True)
    i001 = models.IntegerField(null=True)
    i002 = models.IntegerField(null=True)
    i003 = models.IntegerField(null=True)
    i004 = models.IntegerField(null=True)
    i005 = models.IntegerField(null=True)
    i006 = models.IntegerField(null=True)
    i007 = models.IntegerField(null=True)
    i008 = models.IntegerField(null=True)
    i009 = models.IntegerField(null=True)
    i010 = models.IntegerField(null=True)
    i011 = models.IntegerField(null=True)
    i012 = models.IntegerField(null=True)
    i013 = models.IntegerField(null=True)
    i014 = models.IntegerField(null=True)
    i015 = models.IntegerField(null=True)
    i016 = models.IntegerField(null=True)
    i017 = models.IntegerField(null=True)
    i018 = models.IntegerField(null=True)
    i019 = models.IntegerField(null=True)
    s000 = models.CharField(max_length=255)
    s001 = models.CharField(max_length=255)
    s002 = models.CharField(max_length=255)
    s003 = models.CharField(max_length=255)
    s004 = models.CharField(max_length=255)
    s005 = models.CharField(max_length=255)
    s006 = models.CharField(max_length=255)
    s007 = models.CharField(max_length=255)
    s008 = models.CharField(max_length=255)
    s009 = models.CharField(max_length=255)
    s010 = models.CharField(max_length=255)
    s011 = models.CharField(max_length=255)
    s012 = models.CharField(max_length=255)
    s013 = models.CharField(max_length=255)
    s014 = models.CharField(max_length=255)
    s015 = models.CharField(max_length=255)
    s016 = models.CharField(max_length=255)
    s017 = models.CharField(max_length=255)
    s018 = models.CharField(max_length=255)
    s019 = models.CharField(max_length=255)
    class Meta:
        db_table = 'ESSReg001'

###########################################################################
#
# Controlarea models and forms
#
class ControlAreaQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(null=True, choices=ControlAreaReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = models.CharField(max_length=255, blank=True)
    Status = models.IntegerField(null=True, blank=True, default=0, choices=ReqStatus_CHOICES)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'ReqControlAreaQueue'
    
class ControlAreaForm(forms.ModelForm):
    required_css_class = 'required'
    ReqUUID = forms.CharField(label='ReqUUID', widget = PlainText())
    ObjectIdentifierValue = forms.CharField(label='ObjectIdentifierValue', widget=PlainText())
    Status = forms.IntegerField(widget = forms.HiddenInput())
    user = forms.CharField(label='User', widget = PlainText())
    class Meta:
        model=ControlAreaQueue   
        exclude=('password',)

class ControlAreaForm2(ControlAreaForm):
    ReqType = forms.ChoiceField(label='ReqType',choices=ControlAreaReqType_CHOICES, widget = PlainText())

class ControlAreaForm_CheckoutToWork(ControlAreaForm2):
    read_only_access = forms.BooleanField(label='Read only access',help_text='Do not create a new IP generation',required=False)

class ControlAreaForm_CheckInFromWork(ControlAreaForm2):
    allow_unknown_filetypes = forms.BooleanField(label='Allow unknown filetypes',required=False)

class ControlAreaForm_file(ControlAreaForm2):
    ObjectIdentifierValue = forms.CharField(label='ObjectIdentifierValue',required=False, widget = forms.HiddenInput())
    FileSelect_CHOICES = () 
    filename = forms.MultipleChoiceField(choices=FileSelect_CHOICES, widget=forms.CheckboxSelectMultiple())
    def __init__(self, *args, **kwargs):    
        super(ControlAreaForm_file, self ).__init__(*args, **kwargs)
        if self.FileSelect_CHOICES:
            self.fields['filename'].choices = self.FileSelect_CHOICES

class ControlAreaForm_file2(ControlAreaForm2):
    ObjectIdentifierValue = forms.CharField(label='ObjectIdentifierValue',required=False, widget = forms.HiddenInput())
    FileSelect_CHOICES = () 
    filename = forms.MultipleChoiceField(choices=FileSelect_CHOICES, widget=MultiSelectWidget())
    def __init__(self, *args, **kwargs):    
        super(ControlAreaForm_file2, self ).__init__(*args, **kwargs)
        if self.FileSelect_CHOICES:
            self.fields['filename'].choices = self.FileSelect_CHOICES

class ControlAreaForm_reception(ControlAreaForm2):
    POLICYID = forms.CharField(label='Archive Policy ID', widget = PlainText())
    INFORMATIONCLASS = forms.CharField(label='Information Class', widget = PlainText())
    DELIVERYTYPE = forms.CharField(label='DELIVERYTYPE', widget = PlainText())
    DELIVERYSPECIFICATION = forms.CharField(label='DELIVERYSPECIFICATION', widget = PlainText())
    allow_unknown_filetypes = forms.BooleanField(label='Allow unknown filetypes',required=False)
    
###########################################################################
#
# Access models and forms
#
class AccessQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(null=True, choices=AccessReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = models.CharField(max_length=255, blank=True)
    storageMediumID = models.CharField(max_length=45, blank=True)
    Status = models.IntegerField(null=True, blank=True, default=0, choices=ReqStatus_CHOICES)
    Path = models.CharField(max_length=255)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'AccessQueue'
        permissions = (                    
            ("list_accessqueue", "Can list access queue"),
        )
    def get_absolute_url(self):
        return reverse('access_list')

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

###########################################################################
#
# Ingest models and forms
#
class IngestQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(null=True, choices=IngestReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = models.CharField(max_length=255, blank=True)
    Status = models.IntegerField(null=True, blank=True, default=0, choices=ReqStatus_CHOICES)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'ReqIngestQueue'
        permissions = (
            ("list_ingestqueue", "Can list ingest queue"),
        )
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

###########################################################################
#
# Administration models and forms
#
class storageMedium(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    storageMediumUUID = models.CharField(max_length=36, unique=True)
    storageMedium = models.IntegerField(null=True, choices=MediumType_CHOICES)
    storageMediumID = models.CharField(max_length=45, unique=True)
    storageMediumDate = models.DateTimeField(null=True)
    storageMediumLocation = models.CharField(max_length=45)
    storageMediumLocationStatus = models.IntegerField(null=True, choices=MediumLocationStatus_CHOICES)
    storageMediumBlockSize = models.IntegerField(null=True)
    storageMediumUsedCapacity = models.BigIntegerField(null=True)
    storageMediumStatus = models.IntegerField(null=True, choices=MediumStatus_CHOICES)
    storageMediumFormat = models.IntegerField(null=True, choices=MediumFormat_CHOICES)
    storageMediumMounts = models.IntegerField(null=True)
    linkingAgentIdentifierValue = models.CharField(max_length=45)
    CreateDate  = models.DateTimeField(null=True)
    CreateAgentIdentifierValue = models.CharField(max_length=45)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    class Meta:
        db_table = 'storageMedium'
        permissions = (
            ("list_storageMedium", "Can list storageMedium"),
        )

#class storageMediumTable(tables.Table):
#    storageMediumUUID = tables.CheckBoxColumn()
#    storageMediumID = tables.LinkColumn('admin_detailstoragemedium',args=[A('pk')],verbose_name="ID")
#    storageMedium = tables.Column(verbose_name="Type")
#    storageMediumStatus = tables.Column(verbose_name="Status")
#    storageMediumDate =  tables.Column(verbose_name="LastUpdate")
#    storageMediumLocation = tables.Column(verbose_name="Location")
#    storageMediumLocationStatus = tables.Column(verbose_name="Location Status")
#    storageMediumUsedCapacity = tables.Column(verbose_name="Used Capacity")
#    storageMediumMounts = tables.Column(verbose_name="Used")
# 
#    class Meta:
#        model = storageMedium
#        attrs = {"class": "paleblue"}
#        fields = ("storageMediumUUID","storageMediumID","storageMedium","storageMediumStatus","storageMediumDate","storageMediumLocation","storageMediumLocationStatus","storageMediumUsedCapacity","storageMediumMounts")

        
class storage(models.Model):
    #id = models.AutoField(big=True,primary_key=True)
    id = BigAutoField(primary_key=True)
    contentLocation = models.BigIntegerField(null=True)
    ObjectUUID = models.ForeignKey(ArchiveObject, db_column='ObjectUUID', to_field='ObjectUUID', null=True)
    ObjectIdentifierValue = models.CharField(max_length=255)
    contentLocationType = models.IntegerField(null=True)
    contentLocationValue = models.CharField(max_length=45)
    storageMediumUUID = models.ForeignKey(storageMedium, db_column='storageMediumUUID', to_field='storageMediumUUID', null=True)
    storageMediumID = models.CharField(max_length=45)
    LocalDBdatetime = models.DateTimeField(null=True)
    ExtDBdatetime = models.DateTimeField(null=True)
    class Meta:
        db_table = 'storage'
        permissions = (
            ("list_storage", "Can list storage"),
        )
        
class robot(models.Model):
    slot_id = models.IntegerField(null=True)
    drive_id = models.IntegerField(null=True)
    status = models.CharField(max_length=45)
    t_id = models.CharField(max_length=6)
    class Meta:
        db_table = 'robot'
        permissions = (
            ("list_robot", "Can list robot"),
        )
        
class robotdrives(models.Model):
    drive_id = models.IntegerField(null=True)
    t_id = models.CharField(max_length=6)
    slot_id = models.IntegerField(null=True)
    status = models.CharField(max_length=10)
    num_mounts = models.IntegerField(null=True)
    drive_dev = models.CharField(max_length=15)
    drive_type = models.CharField(max_length=15)
    drive_serial = models.CharField(max_length=20)
    drive_firmware = models.CharField(max_length=20)
    drive_lock = models.CharField(max_length=36)
    IdleTime = models.IntegerField(null=True)
    class Meta:
        db_table = 'robotdrives'

class robotie(models.Model):
    slot_id = models.IntegerField(null=True)
    drive_id = models.IntegerField(null=True)
    status = models.CharField(max_length=10)
    t_id = models.CharField(max_length=6)
    class Meta:
        db_table = 'robotie'

#class robotreq(models.Model):
#    job_prio = models.IntegerField(null=True, blank=True)
#    status = models.CharField(max_length=10, choices=RobotReqStatus_CHOICES)
#    #req_type = models.CharField(max_length=10,blank=True, choices=RobotReqType_CHOICES)
#    req_type = models.CharField(max_length=10, choices=RobotReqType_CHOICES)
#    #req_type = models.CharField(choices=RobotReqType_CHOICES)
#    t_id = models.CharField(max_length=6,blank=True)
#    work_uuid = models.CharField(max_length=36,blank=True)
#    user = models.CharField(max_length=255,blank=True)
#    ReqPurpose = models.CharField(max_length=255)
#    class Meta:
#        db_table = 'robotreq'
#    def get_absolute_url(self):
#        return reverse('admin_listrobot')
#        
#class robotReqQueueForm(forms.ModelForm):
#    required_css_class = 'required'
#    work_uuid = forms.CharField(label='ReqUUID', required=False, widget = PlainText())
#    t_id = forms.CharField(label='MediumID', required=False, widget = PlainText())
#    status = forms.CharField(label='Status', widget = forms.HiddenInput())
#    user = forms.CharField(label='User', widget = PlainText())
#    class Meta:
#        model=robotreq
#        fields = ['work_uuid', 'req_type', 'ReqPurpose', 'user', 'status', 't_id']
#        exclude=('job_prio',)
#
#class robotReqQueueFormUpdate(robotReqQueueForm):
#    status = forms.ChoiceField(label='Status', choices=RobotReqStatus_CHOICES)

class robotQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(null=True, choices=RobotReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    MediumID = models.CharField(max_length=45,blank=True)
    Status = models.IntegerField(null=True, blank=True, default=0, choices=ReqStatus_CHOICES)
    task_id = models.CharField(max_length=36,blank=True)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'robotQueue'
        permissions = (                    
            ("list_robotqueue", "Can list robot queue"),
        )
    def get_absolute_url(self):
        return reverse('admin_listrobot')

class robotQueueForm(forms.ModelForm):
    required_css_class = 'required'
    ReqUUID = forms.CharField(label='ReqUUID', widget = PlainText())
    Status = forms.IntegerField(widget = forms.HiddenInput())
    user = forms.CharField(label='User', widget = PlainText())
    task_id = forms.CharField(required = False, widget = PlainText())
    ais_flag = forms.BooleanField(label='Update related objects from AIS',required=False)

    class Meta:
        model=robotQueue   
        exclude=('password',)    

class robotQueueFormUpdate(robotQueueForm):
    Status = forms.ChoiceField(choices=ReqStatus_CHOICES)  
        
###########################################################################
#
# Migration models and forms
#
class MigrationQueue(models.Model):     
    ReqUUID = models.CharField(max_length=36)
    ReqType = models.IntegerField(null=True, choices=MigrationReqType_CHOICES)
    ReqPurpose = models.CharField(max_length=255)
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=45,blank=True)
    ObjectIdentifierValue = PickledObjectField()
    TargetMediumID = PickledObjectField()
    Status = models.IntegerField(null=True, blank=True, default=0, choices=ReqStatus_CHOICES)
    Path = models.CharField(max_length=255)
    CopyPath = models.CharField(max_length=255,blank=True)
    CopyOnlyFlag =  models.BooleanField(default = False)
    task_id = models.CharField(max_length=36,blank=True)
    #task_id = models.ForeignKey(TaskMeta, db_column='task_id', to_field='task_id', null=True, blank=True)
    posted = models.DateTimeField(auto_now_add=True)
    class Meta:
        db_table = 'MigrationQueue'
        permissions = (                    
            ("list_migrationqueue", "Can list migration queue"),
        )
    def get_absolute_url(self):
        return reverse('migration_list')

class MigrationQueueForm(forms.ModelForm):
    required_css_class = 'required'
    #ReqUUID = forms.CharField(label='ReqUUID', widget = forms.TextInput(attrs={'readonly':'readonly'}))
    ReqUUID = forms.CharField(label='ReqUUID', widget = PlainText())
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = forms.CheckboxInput(attrs={'disabled':'disabled'}))
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = forms.Select(attrs={'disabled':'disabled'}))
    #ReqType = forms.ChoiceField(label='ReqType', choices=ReqType_CHOICES , widget = PlainText())
    ObjectIdentifierValue = forms.CharField(widget=forms.Textarea())
    TargetMediumID = forms.CharField(widget=forms.Textarea())
    CopyOnlyFlag = forms.BooleanField(widget=forms.CheckboxInput(), required=False,initial=False)
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
        model=MigrationQueue   
        exclude=('password',)    

class MigrationQueueFormUpdate(MigrationQueueForm):
    Status = forms.ChoiceField(choices=ReqStatus_CHOICES)

class DeactivateMediaForm(forms.Form):
    ReqPurpose = forms.CharField(max_length=255)
    MediumList = forms.CharField(widget=forms.Textarea())
    class Meta:
        model=MigrationQueue 

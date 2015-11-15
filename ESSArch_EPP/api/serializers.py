'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2015  ES Solutions AB

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
try:
    import ESSArch_EPP as epp
except ImportError:
    __version__ = '2'
else:
    __version__ = epp.__version__
    
from rest_framework import (serializers,
                                         relations,
                                         validators,
                                         )
#import rest_framework_filters as rest_filters
import django_filters
from django.db.models import fields
from essarch.models import (ArchiveObject,
                                        ArchiveObjectRel,
                                        ArchiveObjectData,
                                        ArchiveObjectMetadata,
                                        )
from configuration.models import (ArchivePolicy,
                                                StorageMethod,
                                                StorageTarget,
                                                StorageTargets,
                                                )
from Storage.models import (storageMedium,
                                        storage,
                                        IOQueue,
                                        )

class StorageTargetsSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=StorageTargets.objects.all())])    
    class Meta:
        model = StorageTargets
        fields = ('id', 'name', 'status', 'type', 'format', 'blocksize', 'maxCapacity', 
                  'minChunkSize', 'minContainerSize', 'minCapacityWarning', 'target')

class StorageTargetSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=StorageTarget.objects.all())])
    class Meta:
        model = StorageTarget
        fields = ('id', 'name', 'status', 'target', 'storagemethod')
    
class StorageTargetNestedSerializer(StorageTargetSerializer):
    target = StorageTargetsSerializer()
    class Meta:
        model = StorageTarget
        fields = ('id', 'name', 'status', 'target')

class StorageMethodSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=StorageMethod.objects.all())])
    class Meta:
        model = StorageMethod
        fields = ['id', 'name', 'status', 'type', 'archivepolicy']

class StorageMethodNestedSerializer(StorageMethodSerializer):
    storagetarget_set =  StorageTargetNestedSerializer(many=True)
    class Meta:
        model = StorageMethod
        fields = ['id', 'name', 'status', 'type', 'storagetarget_set']

class ArchivePolicySerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=ArchivePolicy.objects.all())])
    class Meta:
        model = ArchivePolicy
        fields = ['id', 'PolicyID', 'PolicyName', 'PolicyStat', 
                  'AISProjectName', 'AISProjectID', 'Mode', 
                  'WaitProjectApproval', 'ChecksumAlgorithm', 'ValidateChecksum',
                  'ChecksumAlgorithm', 'ValidateXML', 'ManualControll', 
                  'AIPType', 'AIPpath', 'PreIngestMetadata', 
                  'IngestMetadata', 'INFORMATIONCLASS', 'IngestPath',
                  'IngestDelete']

class ArchivePolicyNestedSerializer(ArchivePolicySerializer):
    storagemethod_set =  StorageMethodNestedSerializer(many=True)
    class Meta:
        model = ArchivePolicy
        fields = ArchivePolicySerializer.Meta.fields + ['storagemethod_set',]

class ArchiveObjectDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchiveObjectData
        fields = ('creator', 'label', 'startdate', 'enddate')
        
class ArchiveObjectMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchiveObjectMetadata
        fields = ('ObjectMetadataType', 
                  'ObjectMetadataServer', 
                  'ObjectMetadataURL')

class ArchiveObjectSerializer(serializers.ModelSerializer):
    PolicyId = relations.SlugRelatedField(label='PolicyId', 
                                          slug_field='PolicyID', 
                                          queryset=ArchivePolicy.objects.all(), 
                                          required=False,
                                          )
    class Meta:
        model = ArchiveObject
        fields = ['ObjectUUID', 
                  'PolicyId', 'ObjectIdentifierValue',
                  'ObjectPackageName', 'ObjectSize',
                  'ObjectNumItems', 'ObjectMessageDigestAlgorithm',
                  'ObjectMessageDigest', 'ObjectPath',
                  'ObjectActive', 'MetaObjectIdentifier',
                  'MetaObjectSize', 'CMetaMessageDigestAlgorithm',
                  'CMetaMessageDigest', 'PMetaMessageDigestAlgorithm',
                  'PMetaMessageDigest', 'DataObjectSize',
                  'DataObjectNumItems', 'Status',
                  'StatusActivity', 'StatusProcess',
                  'LastEventDate', 'linkingAgentIdentifierValue',
                  'CreateDate', 'CreateAgentIdentifierValue',
                  'EntryDate', 'EntryAgentIdentifierValue',
                  'OAISPackageType', 'preservationLevelValue',
                  'DELIVERYTYPE', 'INFORMATIONCLASS',
                  'Generation', 'LocalDBdatetime',
                  'ExtDBdatetime']

class ArchiveObjectNestedSerializer(ArchiveObjectSerializer):
    archiveobjectdata_set =  ArchiveObjectDataSerializer(many=True)
    archiveobjectmetadata_set =  ArchiveObjectMetadataSerializer(many=True)
    class Meta:
        model = ArchiveObject
        fields = ArchiveObjectSerializer.Meta.fields + ['archiveobjectdata_set',
                                'archiveobjectmetadata_set']
    
    def create(self, validated_data):
        #print 'validated_data: %s' % repr(validated_data)
        archiveobjectdata_set_data = validated_data.pop('archiveobjectdata_set')
        archiveobjectmetadata_set_data = validated_data.pop('archiveobjectmetadata_set')
        ArchiveObject_obj = ArchiveObject.objects.create(**validated_data)
        for archiveobjectdata_data in archiveobjectdata_set_data:
            ArchiveObjectData.objects.create(UUID=ArchiveObject_obj, **archiveobjectdata_data)
        for archiveobjectmetadata_data in archiveobjectmetadata_set_data:
            ArchiveObjectMetadata.objects.create(ObjectUUID=ArchiveObject_obj, **archiveobjectmetadata_data)
        return ArchiveObject_obj

class ArchiveObjectPlusAICNestedSerializer(ArchiveObjectNestedSerializer):
    PolicyId = ArchivePolicyNestedSerializer()
    aic_set = ArchiveObjectNestedSerializer(many=True)
    class Meta:
        model = ArchiveObject
        fields = ArchiveObjectNestedSerializer.Meta.fields + ['aic_set']

class IPFilter(django_filters.FilterSet):
    archiveobjects__ObjectIdentifierValue = django_filters.CharFilter(name='ObjectIdentifierValue')
    archiveobjects__ObjectUUID = django_filters.CharFilter(name='ObjectUUID')
    archiveobjects__PolicyId = django_filters.CharFilter(name='PolicyId')
    archiveobjects__StatusProcess = django_filters.NumberFilter(name='StatusProcess')
    archiveobjects__StatusProcess__lt = django_filters.NumberFilter(name='StatusProcess', lookup_type='lt')
    class Meta:
        model = ArchiveObjectRel
        fields = ['archiveobjects__ObjectIdentifierValue', 
                  'archiveobjects__ObjectUUID', 
                  'archiveobjects__PolicyId',
                  'archiveobjects__StatusProcess',
                  'archiveobjects__StatusProcess__lt']
        
class Filtered_archiveobjects__IP_ListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        data = IPFilter(self.context['request'].GET, queryset=data)
        return super(Filtered_archiveobjects__IP_ListSerializer, self).to_representation(data)

class ArchiveObjectIDNestedSerializer(ArchiveObjectNestedSerializer):
    class Meta:
        model = ArchiveObject
        list_serializer_class = Filtered_archiveobjects__IP_ListSerializer
        fields = ArchiveObjectNestedSerializer.Meta.fields + ['id']

class AICObjectSerializer(serializers.ModelSerializer):
    archiveobjects = ArchiveObjectIDNestedSerializer(many=True)
    class Meta:
        model = ArchiveObject
        fields = ('ObjectUUID','ObjectIdentifierValue', 'StatusActivity', 
                  'StatusProcess', 'archiveobjects',)

    def create(self, validated_data):
        #print 'validated_data: %s' % repr(validated_data)
        archiveobjects_data = validated_data.pop('archiveobjects')
        AIC_ArchiveObject_obj = ArchiveObject.objects.create(**validated_data)
        for ip_data in archiveobjects_data:
            archiveobjectdata_set_data = ip_data.pop('archiveobjectdata_set')
            archiveobjectmetadata_set_data = ip_data.pop('archiveobjectmetadata_set')
            IP_ArchiveObject_obj = ArchiveObject.objects.create(**ip_data) 
            for archiveobjectdata_data in archiveobjectdata_set_data:
                ArchiveObjectData.objects.get_or_create(UUID=IP_ArchiveObject_obj, **archiveobjectdata_data)
            for archiveobjectmetadata_data in archiveobjectmetadata_set_data:
                ArchiveObjectMetadata.objects.get_or_create(ObjectUUID=IP_ArchiveObject_obj, **archiveobjectmetadata_data)
            ArchiveObjectRel_obj = ArchiveObjectRel.objects.create(UUID = IP_ArchiveObject_obj,
                                                                                            AIC_UUID = AIC_ArchiveObject_obj)
        
        return AIC_ArchiveObject_obj

    def update(self, instance, validated_data):
        #print 'validated_data: %s' % repr(validated_data)
        archiveobjects_data = validated_data.pop('archiveobjects')
        instance.StatusProcess = validated_data.get('StatusProcess', instance.StatusProcess)
        instance.StatusActivity = validated_data.get('StatusActivity', instance.StatusActivity)
        
        return instance

class ArchiveObjectRelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchiveObjectRel
        fields = ('UUID', 'AIC_UUID')
       
class storageMediumSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=storageMedium.objects.all())])
    class Meta:
        model = storageMedium
        fields = ['id',
                    'storageMediumUUID',
                    'storageMedium',
                    'storageMediumID',
                    'storageMediumDate',
                    'storageMediumLocation',
                    'storageMediumLocationStatus',
                    'storageMediumBlockSize',
                    'storageMediumUsedCapacity',
                    'storageMediumStatus',
                    'storageMediumFormat',
                    'storageMediumMounts',
                    'linkingAgentIdentifierValue',
                    'CreateDate',
                    'CreateAgentIdentifierValue',
                    'LocalDBdatetime',
                    'ExtDBdatetime',
                    'storagetarget']

class storageMediumNoValidateNestedSerializer(storageMediumSerializer):
    id = serializers.UUIDField(read_only=False, validators=[])
    storageMediumUUID = serializers.CharField(label='storageMediumUUID', max_length=36, validators=[])
    storageMediumID = serializers.CharField(label='storageMediumUUID', max_length=255, validators=[])
    class Meta:
        model = storageMedium
        fields = storageMediumSerializer.Meta.fields

class storageSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=storage.objects.all())])
    class Meta:
        model = storage
        fields = ['id', 'contentLocationType', 'contentLocationValue', 
                  'archiveobject', 'storagemedium']

class storageNestedSerializer(storageSerializer):
    storagemedium = storageMediumNoValidateNestedSerializer()
    class Meta:
        model = storage
        fields = storageSerializer.Meta.fields

    def create(self, validated_data):
        #print 'validated_data: %s' % repr(validated_data)
        storagemedium_data = validated_data.pop('storagemedium')
        storageMedium_obj, created = storageMedium.objects.update_or_create(
                                                                   id=storagemedium_data['id'], 
                                                                   defaults=storagemedium_data)
        storage_obj = storage.objects.create(storagemedium=storageMedium_obj, **validated_data)
        return storage_obj

class IOQueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = IOQueue
        fields = ('id',
                    'ReqType',
                    'ReqPurpose',
                    'user',
                    'ObjectPath',
                    'WriteSize',
                    'result',
                    'Status',
                    'task_id',
                    'posted',
                    'archiveobject',
                    'storagemethod',
                    'storagemethodtarget',
                    'storagetarget',
                    'storagemedium',
                    'storage',
                    'accessqueue',
                    'remote_status',
                    'transfer_task_id')

class IOQueueNestedReadSerializer(IOQueueSerializer):
    archiveobject = ArchiveObjectPlusAICNestedSerializer()
    
    class Meta:
        model = IOQueue
        fields = IOQueueSerializer.Meta.fields


class IOQueueNestedWriteSerializer(IOQueueSerializer):
    id = serializers.UUIDField(read_only=False, validators=[validators.UniqueValidator(queryset=IOQueue.objects.all())])
    archiveobject = serializers.CharField(validators=[])
    storagemethodtarget = serializers.UUIDField(validators=[])
    
    class Meta:
        model = IOQueue
        fields = IOQueueSerializer.Meta.fields

    def create(self, validated_data):
        #print 'validated_data: %s' % repr(validated_data)
        ip_data = eval(validated_data.pop('archiveobject'))
        
        #Create or Update ArchivePolicy
        PolicyId_data = ip_data.pop('PolicyId')
        storagemethod_set_data = PolicyId_data.pop('storagemethod_set')
        ArchivePolicy_obj, created = ArchivePolicy.objects.update_or_create(
                                                                   PolicyID=PolicyId_data['PolicyID'], 
                                                                   defaults=PolicyId_data)
        for storagemethod_data in storagemethod_set_data:
            storagetarget_set_data = storagemethod_data.pop('storagetarget_set')
            storagemethod_data['archivepolicy'] = ArchivePolicy_obj
            StorageMethod_obj, created = StorageMethod.objects.update_or_create(
                                                                       id=storagemethod_data['id'], 
                                                                       defaults=storagemethod_data)
            for storagetarget_data in storagetarget_set_data:
                target_data = storagetarget_data.pop('target')
                target_obj, created = StorageTargets.objects.update_or_create(
                                                                     id=target_data['id'],
                                                                     defaults=target_data)
                storagetarget_data['target'] = target_obj
                storagetarget_data['storagemethod'] = StorageMethod_obj
                StorageTarget_obj, created = StorageTarget.objects.update_or_create(
                                                                           id=storagetarget_data['id'],
                                                                           defaults=storagetarget_data)
        # Create IP
        archiveobjectdata_set_data = ip_data.pop('archiveobjectdata_set')
        archiveobjectmetadata_set_data = ip_data.pop('archiveobjectmetadata_set')
        aic_data = ip_data.pop('aic_set')[0]
        ip_data['PolicyId'] = ArchivePolicy_obj
        IP_ArchiveObject_obj, ip_created = ArchiveObject.objects.get_or_create(
                                                                   ObjectUUID=ip_data['ObjectUUID'], 
                                                                   defaults=ip_data) 
        for archiveobjectdata_data in archiveobjectdata_set_data:
            ArchiveObjectData.objects.get_or_create(UUID=IP_ArchiveObject_obj, **archiveobjectdata_data)
        for archiveobjectmetadata_data in archiveobjectmetadata_set_data:
            ArchiveObjectMetadata.objects.get_or_create(ObjectUUID=IP_ArchiveObject_obj, **archiveobjectmetadata_data)
        
        # Create AIC
        archiveobjectdata_set_data = aic_data.pop('archiveobjectdata_set')
        archiveobjectmetadata_set_data = aic_data.pop('archiveobjectmetadata_set')
        aic_data['PolicyId'] = ArchivePolicy_obj
        AIC_ArchiveObject_obj, created = ArchiveObject.objects.get_or_create(
                                                                             ObjectUUID=aic_data['ObjectUUID'], 
                                                                             defaults=aic_data) 
        for archiveobjectdata_data in archiveobjectdata_set_data:
            ArchiveObjectData.objects.get_or_create(UUID=AIC_ArchiveObject_obj, **archiveobjectdata_data)
        for archiveobjectmetadata_data in archiveobjectmetadata_set_data:
            ArchiveObjectMetadata.objects.get_or_create(ObjectUUID=AIC_ArchiveObject_obj, **archiveobjectmetadata_data)
        
        # Create relation between IP and AIC
        if ip_created: 
            ArchiveObjectRel_obj = ArchiveObjectRel.objects.create(UUID = IP_ArchiveObject_obj,
                                                                                        AIC_UUID = AIC_ArchiveObject_obj)
        
        StorageTarget_obj = StorageTarget.objects.get(id=validated_data.pop('storagemethodtarget'))
        # Create IOQueue object
        IOQueue_obj = IOQueue.objects.create(archiveobject=IP_ArchiveObject_obj, 
                                             storagemethodtarget=StorageTarget_obj, 
                                             **validated_data)
        return IOQueue_obj

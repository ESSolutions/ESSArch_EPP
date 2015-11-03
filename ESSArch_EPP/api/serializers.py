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
    
from rest_framework import serializers, \
                                         relations
#import rest_framework_filters as rest_filters
import django_filters
from essarch.models import ArchiveObject, \
                                        ArchiveObjectRel, \
                                        ArchiveObjectData, \
                                        ArchiveObjectMetadata
from configuration.models import ArchivePolicy, \
                                                StorageMethod, \
                                                StorageTarget,\
                                                StorageTargets
from Storage.models import storageMedium, \
                                        storage, \
                                        IOQueue

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
                                          required=False)
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

class IPFilter(django_filters.FilterSet):
    archiveobjects__ObjectIdentifierValue = django_filters.CharFilter(name='ObjectIdentifierValue')
    archiveobjects__ObjectUUID = django_filters.CharFilter(name='ObjectUUID')
    archiveobjects__PolicyId = django_filters.CharFilter(name='PolicyId')
    archiveobjects__StatusProcess = django_filters.CharFilter(name='StatusProcess')
    class Meta:
        model = ArchiveObjectRel
        fields = ['archiveobjects__ObjectIdentifierValue', 
                  'archiveobjects__ObjectUUID', 
                  'archiveobjects__PolicyId',
                  'archiveobjects__StatusProcess']

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
        ArchiveObject_obj = ArchiveObject.objects.create(**validated_data)
        for ip_data in archiveobjects_data:
            archiveobjectdata_set_data = ip_data.pop('archiveobjectdata_set')
            archiveobjectmetadata_set_data = ip_data.pop('archiveobjectmetadata_set')
            IP_ArchiveObject_obj = ArchiveObject.objects.create(**ip_data)
            for archiveobjectdata_data in archiveobjectdata_set_data:
                ArchiveObjectData.objects.create(UUID=IP_ArchiveObject_obj, **archiveobjectdata_data)
            for archiveobjectmetadata_data in archiveobjectmetadata_set_data:
                ArchiveObjectMetadata.objects.create(ObjectUUID=IP_ArchiveObject_obj, **archiveobjectmetadata_data)
            ArchiveObjectRel_obj = ArchiveObjectRel.objects.create(UUID = IP_ArchiveObject_obj,
                                                                                            AIC_UUID = ArchiveObject_obj)
        return ArchiveObject_obj
    
class ArchivePolicySerializer(serializers.ModelSerializer):
        class Meta:
                model = ArchivePolicy

class StorageMethodSerializer(serializers.ModelSerializer):
        class Meta:
                model = StorageMethod

class StorageTargetSerializer(serializers.ModelSerializer):
        class Meta:
                model = StorageTarget

class StorageTargetsSerializer(serializers.ModelSerializer):
        class Meta:
                model = StorageTargets

class storageMediumSerializer(serializers.ModelSerializer):
        class Meta:
                model = storageMedium

class storageSerializer(serializers.ModelSerializer):
        class Meta:
                model = storage

class IOQueueSerializer(serializers.ModelSerializer):
        class Meta:
                model = IOQueue

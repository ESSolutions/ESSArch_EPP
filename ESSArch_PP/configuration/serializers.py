import uuid

from rest_framework import serializers

from ESSArch_Core.configuration.models import ArchivePolicy
from ESSArch_Core.configuration.serializers import ArchivePolicySerializer as CoreArchivePolicySerializer

from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

from ESSArch_Core.storage.models import StorageMethod, StorageTarget, StorageMethodTargetRelation

class ArchivePolicyNestedSerializer(CoreArchivePolicySerializer):
    class Meta:
        model = ArchivePolicy
        fields = (
            "id", "index", "cache_extracted_size",
            "cache_package_size", "cache_extracted_age",
            "cache_package_age", "policy_id", "policy_name",
            "policy_stat", "ais_project_name", "ais_project_id",
            "mode", "wait_for_approval", "checksum_algorithm",
            "validate_checksum", "validate_xml", "ip_type",
            "preingest_metadata", "ingest_metadata",
            "information_class", "ingest_delete",
            "receive_extract_sip", "cache_storage", "ingest_path",
        )
        extra_kwargs = {
            'id': {
                'validators': [],
            },
            'policy_id': {
                'validators': [],
            },
        }


class StorageTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageTarget
        fields = (
            'url', 'id', 'name', 'status', 'type', 'default_block_size', 'default_format', 'min_chunk_size',
            'min_capacity_warning', 'max_capacity', 'remote_server', 'master_server', 'target'
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'default': uuid.uuid4,
            },
            'name': {
                'validators': [],
            },
        }


class StorageMethodTargetRelationSerializer(serializers.HyperlinkedModelSerializer):
    storage_method = serializers.UUIDField(format='hex_verbose', source='storage_method.id', validators=[])
    storage_target = StorageTargetSerializer()

    class Meta:
        model = StorageMethodTargetRelation
        fields = (
            'url', 'id', 'name', 'status', 'storage_target', 'storage_method',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
                'default': uuid.uuid4,
            },
        }


class StorageMethodSerializer(DynamicHyperlinkedModelSerializer):
    archive_policy = ArchivePolicyNestedSerializer()
    targets = serializers.PrimaryKeyRelatedField(pk_field=serializers.UUIDField(format='hex_verbose'), many=True, read_only=True)
    storage_method_target_relations = StorageMethodTargetRelationSerializer(validators=[], many=True)

    class Meta:
        model = StorageMethod
        fields = (
            'url', 'id', 'name', 'status', 'type', 'archive_policy', 'targets',
            'storage_method_target_relations',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
                'default': uuid.uuid4,
            },
        }


class ArchivePolicySerializer(CoreArchivePolicySerializer):
    storage_methods = StorageMethodSerializer(many=True)

    class Meta:
        model = ArchivePolicy
        fields = CoreArchivePolicySerializer.Meta.fields
        extra_kwargs = {
            'id': {
                'validators': [],
            },
            'policy_id': {
                'validators': [],
            },
        }

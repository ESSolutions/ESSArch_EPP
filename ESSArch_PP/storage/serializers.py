from rest_framework import serializers

from ESSArch_Core.storage.models import (
    StorageMedium,
    StorageObject,
    StorageTarget,
)


class StorageObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageObject
        fields = (
            'url', 'id', 'content_location_type', 'content_location_value', 'last_changed_local',
            'last_changed_external', 'ip', 'storage_medium'
        )


class StorageMediumSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageMedium
        fields = (
            'url', 'id', 'medium_id', 'status', 'location', 'location_status', 'block_size', 'format',
            'used_capacity', 'number_of_mounts', 'create_date', 'agent', 'storage_target'
        )


class StorageTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageTarget
        fields = (
            'url', 'id', 'name', 'status', 'type', 'default_block_size', 'default_format', 'min_chunk_size',
            'min_capacity_warning', 'max_capacity', 'remote_server', 'master_server', 'target'
        )

from rest_framework import serializers

from ESSArch_Core.storage.models import (
    IOQueue,
    StorageMedium,
    StorageMethod,
    StorageMethodTargetRelation,
    StorageObject,
    StorageTarget,
)


class IOQueueSerializer(serializers.HyperlinkedModelSerializer):
    result = serializers.ModelField(model_field=IOQueue()._meta.get_field('result'), read_only=False)

    class Meta:
        model = IOQueue
        fields = (
            'url', 'id', 'req_type', 'req_purpose', 'user', 'object_path',
            'write_size', 'result', 'status', 'task_id', 'posted',
            'ip', 'storage_method', 'storage_method_target',
            'storage_target', 'storage_medium', 'storage_object', 'access_queue',
            'remote_status', 'transfer_task_id'
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


class StorageMethodSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageMethod
        fields = (
            'url', 'id', 'name', 'status', 'type', 'archive_policy', 'targets',
        )


class StorageMethodTargetRelationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageMethodTargetRelation
        fields = (
            'url', 'id', 'name', 'status', 'storage_target', 'storage_method',
        )


class StorageTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageTarget
        fields = (
            'url', 'id', 'name', 'status', 'type', 'default_block_size', 'default_format', 'min_chunk_size',
            'min_capacity_warning', 'max_capacity', 'remote_server', 'master_server', 'target'
        )

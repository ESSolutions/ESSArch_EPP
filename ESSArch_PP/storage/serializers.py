from rest_framework import serializers

from ip.serializers import InformationPackageSerializer

from ESSArch_Core.auth.serializers import UserSerializer

from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

from ESSArch_Core.storage.models import medium_status_CHOICES

from ESSArch_Core.storage.models import (
    IOQueue,
    Robot,
    RobotQueue,
    StorageMedium,
    StorageMethod,
    StorageMethodTargetRelation,
    StorageObject,
    StorageTarget,
    TapeDrive,
    TapeSlot,
)


class IOQueueSerializer(serializers.HyperlinkedModelSerializer):
    result = serializers.ModelField(model_field=IOQueue()._meta.get_field('result'), read_only=False)

    class Meta:
        model = IOQueue
        fields = (
            'url', 'id', 'req_type', 'req_purpose', 'user', 'object_path',
            'write_size', 'result', 'status', 'task_id', 'posted',
            'ip', 'storage_method_target', 'storage_medium', 'storage_object', 'access_queue',
            'remote_status', 'transfer_task_id'
        )

class StorageObjectReadSerializer(serializers.HyperlinkedModelSerializer):
    ip = InformationPackageSerializer()
    class Meta:
        model = StorageObject
        fields = (
            'url', 'id', 'content_location_type', 'content_location_value', 'last_changed_local',
            'last_changed_external', 'ip', 'storage_medium'
        )

class StorageObjectWriteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageObject
        fields = (
            'url', 'id', 'content_location_type', 'content_location_value', 'last_changed_local',
            'last_changed_external', 'ip', 'storage_medium'
        )

class StorageTargetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageTarget
        fields = (
            'url', 'id', 'name', 'status', 'type', 'default_block_size', 'default_format', 'min_chunk_size',
            'min_capacity_warning', 'max_capacity', 'remote_server', 'master_server', 'target'
        )

class StorageMediumReadSerializer(serializers.HyperlinkedModelSerializer):
    storage_target = StorageTargetSerializer(read_only=True)
    class Meta:
        model = StorageMedium
        fields = (
            'url', 'id', 'medium_id', 'status', 'location', 'location_status', 'block_size', 'format',
            'used_capacity', 'num_of_mounts', 'create_date', 'agent', 'storage_target', 'tape_slot', 'tape_drive',
        )

class StorageMediumWriteSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageMedium
        fields = (
            'url', 'id', 'medium_id', 'status', 'location', 'location_status', 'block_size',
            'format', 'used_capacity', 'num_of_mounts', 'create_date', 'agent', 'storage_target', 'tape_slot', 'tape_drive'
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

class RobotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Robot
        fields = (
            'url','id', 'label', 'device', 'online',
        )

class TapeSlotSerializer(serializers.HyperlinkedModelSerializer):
    status = serializers.SerializerMethodField()
    def get_status(self, obj):
        if hasattr(obj, 'storage_medium'):
            return obj.storage_medium.get_status_display()
        return 'empty'

    class Meta:
        model = TapeSlot
        fields = (
            'url','id', 'slot_id', 'medium_id', 'robot', 'status'
        )

class TapeDriveSerializer(serializers.HyperlinkedModelSerializer):
    storage_medium = serializers.HyperlinkedRelatedField(
        queryset=StorageMedium.objects.all(),
        view_name='storagemedium-detail',
        allow_null=True
    )
    status = serializers.SerializerMethodField()
    def get_status(self, obj):
        if hasattr(obj, 'storage_medium'):        
            return obj.storage_medium.get_status_display()
        return 'empty'

    class Meta:
        model = TapeDrive
        fields = (
            'url', 'id', 'device', 'io_queue_entry', 'num_of_mounts', 'idle_time', 'robot', 'status', 'storage_medium',
        )

class RobotQueueSerializer(serializers.HyperlinkedModelSerializer):
    io_queue_entry = IOQueueSerializer(read_only=True)
    robot = RobotSerializer(read_only=True)
    storage_medium = StorageMediumReadSerializer(read_only=True)
    user = UserSerializer(read_only=True, fields=['url', 'id', 'username', 'first_name', 'last_name'])

    class Meta:
        model = RobotQueue
        fields = (
            'url', 'id', 'user', 'posted', 'robot', 'io_queue_entry',
            'storage_medium', 'req_type', 'status'
        )

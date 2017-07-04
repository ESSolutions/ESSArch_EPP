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

    req_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_req_type(self, obj):
        return obj.get_req_type_display()

    def get_status(self, obj):
        return obj.get_status_display()

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

class StorageMediumReadSerializer(DynamicHyperlinkedModelSerializer):
    storage_target = StorageTargetSerializer(read_only=True)

    location_status = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_location_status(self, obj):
        return obj.get_location_status_display()

    def get_status(self, obj):
        return obj.get_status_display()

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
    storage_medium = StorageMediumReadSerializer(fields=[
        'url', 'id', 'tape_drive', 'status', 'used_capacity',
        'num_of_mounts', 'create_date',
    ])
    locked = serializers.SerializerMethodField()
    mounted = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_locked(self, obj):
        if hasattr(obj, 'storage_medium') and obj.storage_medium.tape_drive is not None:
            return obj.storage_medium.tape_drive.locked
        return False

    def get_mounted(self, obj):
        return hasattr(obj, 'storage_medium') and obj.storage_medium.tape_drive is not None

    def get_status(self, obj):
        if hasattr(obj, 'storage_medium'):
            if obj.storage_medium.tape_drive:
                drive = obj.storage_medium.tape_drive
                return 'Mounted in drive %s (%s)' % (drive.pk, drive.device)
            return obj.storage_medium.get_status_display()
        return 'empty'

    class Meta:
        model = TapeSlot
        fields = (
            'url','id', 'slot_id', 'medium_id', 'robot', 'status', 'locked', 'mounted', 'storage_medium',
        )

class TapeDriveSerializer(serializers.HyperlinkedModelSerializer):
    storage_medium = StorageMediumReadSerializer()
    status = serializers.SerializerMethodField()
    def get_status(self, obj):
        if hasattr(obj, 'storage_medium'):        
            return obj.storage_medium.get_status_display()
        return 'empty'

    class Meta:
        model = TapeDrive
        fields = (
            'url', 'id', 'device', 'io_queue_entry', 'num_of_mounts', 'idle_time', 'robot', 'status', 'storage_medium',
            'locked', 'last_change',
        )

class RobotQueueSerializer(serializers.HyperlinkedModelSerializer):
    io_queue_entry = IOQueueSerializer(read_only=True)
    robot = RobotSerializer(read_only=True)
    storage_medium = StorageMediumReadSerializer(read_only=True)
    user = UserSerializer(read_only=True, fields=['url', 'id', 'username', 'first_name', 'last_name'])
    req_type = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_req_type(self, obj):
        return obj.get_req_type_display()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = RobotQueue
        fields = (
            'url', 'id', 'user', 'posted', 'robot', 'io_queue_entry',
            'storage_medium', 'req_type', 'status'
        )

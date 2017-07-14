from django.contrib.auth import get_user_model

from rest_framework import serializers, validators

from ESSArch_Core.auth.serializers import UserSerializer

from ESSArch_Core.configuration.models import ArchivePolicy, Path

from ESSArch_Core.ip.models import InformationPackage

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

from ip.serializers import InformationPackageDetailSerializer

class StorageObjectSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = StorageObject
        fields = (
            'url', 'id', 'content_location_type', 'content_location_value', 'last_changed_local',
            'last_changed_external', 'ip', 'storage_medium'
        )


class StorageMediumSerializer(DynamicHyperlinkedModelSerializer):
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


class RobotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Robot
        fields = (
            'url','id', 'label', 'device', 'online',
        )

class TapeSlotSerializer(serializers.HyperlinkedModelSerializer):
    storage_medium = StorageMediumSerializer(fields=[
        'url', 'id', 'tape_drive', 'status', 'used_capacity',
        'num_of_mounts', 'create_date',
    ])
    locked = serializers.SerializerMethodField()
    mounted = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    def get_locked(self, obj):
        if hasattr(obj, 'storage_medium') and obj.storage_medium.tape_drive is not None:
            return obj.storage_medium.tape_drive.locked
        return False

    def get_mounted(self, obj):
        return hasattr(obj, 'storage_medium') and obj.storage_medium.tape_drive is not None

    class Meta:
        model = TapeSlot
        fields = (
            'url','id', 'slot_id', 'medium_id', 'robot', 'status', 'locked', 'mounted', 'storage_medium',
        )

class TapeDriveSerializer(serializers.HyperlinkedModelSerializer):
    storage_medium = StorageMediumSerializer(read_only=True)
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return obj.get_status_display()

    class Meta:
        model = TapeDrive
        fields = (
            'url', 'id', 'drive_id', 'device', 'io_queue_entry', 'num_of_mounts', 'idle_time', 'robot', 'status', 'storage_medium',
            'locked', 'last_change',
        )


class IOQueueSerializer(DynamicHyperlinkedModelSerializer):
    ip = InformationPackageDetailSerializer()
    result = serializers.ModelField(model_field=IOQueue()._meta.get_field('result'), read_only=False)
    user = UserSerializer()
    storage_method_target = serializers.PrimaryKeyRelatedField(pk_field=serializers.UUIDField(format='hex_verbose'), allow_null=True, queryset=StorageMethodTargetRelation.objects.all())

    req_type_display = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()

    def get_req_type_display(self, obj):
        return obj.get_req_type_display()

    def get_status_display(self, obj):
        return obj.get_status_display()

    class Meta:
        model = IOQueue
        fields = (
            'url', 'id', 'req_type', 'req_type_display', 'req_purpose', 'user', 'object_path',
            'write_size', 'result', 'status', 'status_display', 'task_id', 'posted',
            'ip', 'storage_method_target', 'storage_medium', 'storage_object', 'access_queue',
            'remote_status', 'transfer_task_id'
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [validators.UniqueValidator(queryset=IOQueue.objects.all())],
            },
        }


class IOQueueWriteSerializer(IOQueueSerializer):
    storage_method_target = serializers.UUIDField(required=True)
    storage_medium = serializers.UUIDField(allow_null=True, required=False)

    def create(self, validated_data):
        ip_data = validated_data.pop('ip')
        aic_data = ip_data.pop('aic')
        policy_data = ip_data.pop('policy')
        storage_method_set_data = policy_data.pop('storage_methods')

        cache_storage_data = policy_data.pop('cache_storage')
        ingest_path_data = policy_data.pop('ingest_path')

        cache_storage = Path.objects.get_or_create(entity=cache_storage_data['entity'], defaults=cache_storage_data)
        ingest_path = Path.objects.get_or_create(entity=ingest_path_data['entity'], defaults=ingest_path_data)

        policy_data['cache_storage'], _ = cache_storage
        policy_data['ingest_path'], _ = ingest_path

        policy, _ = ArchivePolicy.objects.update_or_create(policy_id=policy_data['policy_id'],
                                                           defaults=policy_data)

        for storage_method_data in storage_method_set_data:
            storage_method_target_set_data = storage_method_data.pop('storage_method_target_relations')
            storage_method_data['archive_policy'] = policy
            storage_method, _ = StorageMethod.objects.update_or_create(id=storage_method_data['id'],
                                                                       defaults=storage_method_data)

            for storage_method_target_data in storage_method_target_set_data:
                storage_target_data = storage_method_target_data.pop('storage_target')
                storage_target, _ = StorageTarget.objects.update_or_create(id=storage_target_data['id'],
                                                                           defaults=storage_target_data)
                storage_method_target_data['storage_method'] = storage_method
                storage_method_target_data['storage_target'] = storage_target
                storage_method_target, _ = StorageMethodTargetRelation.objects.update_or_create(
                                                                            id=storage_method_target_data['id'],
                                                                            defaults=storage_method_target_data)

        aic, _ = InformationPackage.objects.get_or_create(id=aic_data['id'], defaults=aic_data)

        ip_data['aic'] = aic
        ip_data['policy'] = policy
        ip, _ = InformationPackage.objects.get_or_create(id=ip_data['id'], defaults=ip_data)

        storage_method_target = StorageMethodTargetRelation.objects.get(id=validated_data.pop('storage_method_target'))

        try:
            storage_medium_data = validated_data.pop('storage_medium')

            if storage_medium_data is not None:
                storage_medium = StorageMedium.objects.get(id=storage_medium_data['id'])
            else:
                storage_medium = None
        except KeyError, StorageMedium.DoesNotExist:
            storage_medium = None

        user = None
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            user = request.user
        else:
            user = get_user_model.objects.get(username="system")

        validated_data['user'] = user
        validated_data['status'] = -1

        return IOQueue.objects.create(ip=ip, storage_method_target=storage_method_target,
                                      storage_medium=storage_medium, **validated_data)


class RobotQueueSerializer(serializers.HyperlinkedModelSerializer):
    io_queue_entry = IOQueueSerializer(read_only=True)
    robot = RobotSerializer(read_only=True)
    storage_medium = StorageMediumSerializer(read_only=True)
    user = UserSerializer(read_only=True)
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

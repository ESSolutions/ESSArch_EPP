"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets, filters

from rest_framework_extensions.mixins import NestedViewSetMixin

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

from storage.serializers import (
    IOQueueSerializer,
    RobotSerializer,
    RobotQueueSerializer,
    StorageMethodSerializer,
    StorageMethodTargetRelationSerializer,
    StorageObjectReadSerializer,
    StorageObjectWriteSerializer,
    StorageMediumReadSerializer,
    StorageMediumWriteSerializer,
    StorageTargetSerializer,
    TapeDriveSerializer,
    TapeSlotSerializer,
)

class IOQueueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for IO queues
    """
    queryset = IOQueue.objects.all()
    serializer_class = IOQueueSerializer


class StorageMediumViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage medium
    """
    queryset = StorageMedium.objects.all()
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'id', 'medium_id', 'status', 'location', 'location_status', 'used_capacity', 'create_date',
    )
    search_fields = (
        'id', 'medium_id', 'status', 'location', 'location_status', 'used_capacity', 'create_date',
    )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StorageMediumReadSerializer
        return StorageMediumWriteSerializer

class StorageMethodViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage method
    """
    queryset = StorageMethod.objects.all()
    serializer_class = StorageMethodSerializer

class StorageMethodTargetRelationViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage method target relation
    """
    queryset = StorageMethodTargetRelation.objects.all()
    serializer_class = StorageMethodTargetRelationSerializer

class StorageObjectViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint for storage object
    """
    queryset = StorageObject.objects.all()

    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'ip__object_identifier_value', 'content_location_value',
    )

    search_fields = (
        'ip__object_identifier_value', 'content_location_value',
    )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return StorageObjectReadSerializer
        return StorageObjectWriteSerializer

class StorageTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage target
    """
    queryset = StorageTarget.objects.all()
    serializer_class = StorageTargetSerializer

class RobotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for robot
    """
    queryset = Robot.objects.all()
    serializer_class = RobotSerializer
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'id', 'label', 'device', 'online',
    )

    search_fields = (
        'id', 'label', 'device', 'online',
    )

class RobotQueueViewSet(viewsets.ModelViewSet):
    """
    API endpoint for robot
    """
    queryset = RobotQueue.objects.all()
    serializer_class = RobotQueueSerializer
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'id', 'user', 'posted', 'robot', 'io_queue_entry',
        'storage_medium', 'req_type', 'status',
    )

    search_fields = (
        'id', 'user', 'posted', 'robot', 'io_queue_entry',
        'storage_medium', 'req_type', 'status',
    )

class TapeDriveViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TapeDrive
    """
    queryset = TapeDrive.objects.all()
    serializer_class = TapeDriveSerializer
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'id', 'device', 'num_of_mounts', 'idle_time',
    )
    search_fields = (
        'id', 'device', 'num_of_mounts', 'idle_time',
    )

class TapeSlotViewSet(viewsets.ModelViewSet):
    """
    API endpoint for TapeSlot
    """
    queryset = TapeSlot.objects.all()
    serializer_class = TapeSlotSerializer
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'id', 'slot_id', 'medium_id',
    )
    search_fields = (
        'id', 'slot_id', 'medium_id',

    )

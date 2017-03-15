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

from rest_framework import viewsets

from ESSArch_Core.storage.models import IOQueue, StorageMedium, StorageMethod, StorageMethodTargetRelation, StorageObject, StorageTarget

from storage.serializers import IOQueueSerializer, StorageMethodSerializer, StorageMethodTargetRelationSerializer, StorageObjectSerializer, StorageMediumSerializer, StorageTargetSerializer


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
    serializer_class = StorageMediumSerializer


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


class StorageObjectViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage object
    """
    queryset = StorageObject.objects.all()
    serializer_class = StorageObjectSerializer


class StorageTargetViewSet(viewsets.ModelViewSet):
    """
    API endpoint for storage target
    """
    queryset = StorageTarget.objects.all()
    serializer_class = StorageTargetSerializer

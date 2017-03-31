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

import datetime
import itertools
import pytz

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask

from ESSArch_Core.WorkflowEngine.permissions import (
    CanUndo,
    CanRetry,
)

from workflow.serializers import (
    ProcessStepSerializer,
    ProcessStepChildrenSerializer,
    ProcessTaskSerializer,
    ProcessTaskDetailSerializer
)


class ProcessStepViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows steps to be viewed or edited.
    """
    queryset = ProcessStep.objects.all()
    serializer_class = ProcessStepSerializer


    @detail_route(methods=['get'], url_path='children')
    def children(self, request, pk=None):
        step = self.get_object()
        child_steps = step.child_steps.all()
        tasks = step.tasks.filter(hidden=False).select_related('responsible')
        queryset = sorted(
            itertools.chain(child_steps, tasks),
            key=lambda instance: instance.time_started or
            datetime.datetime(datetime.MAXYEAR, 1, 1, 1, 1, 1, 1, pytz.UTC)
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializers = ProcessStepChildrenSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializers.data)
        serializers = ProcessStepChildrenSerializer(queryset, many=True, context={'request': request})
        return Response(serializers.data)

    @detail_route(methods=['get'], url_path='child-steps')
    def child_steps(self, request, pk=None):
        step = self.get_object()
        child_steps = step.child_steps.all()
        page = self.paginate_queryset(child_steps)
        if page is not None:
            serializers = ProcessStepSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializers.data)
        serializers = ProcessStepSerializer(child_steps, many=True, context={'request': request})
        return Response(serializers.data)

    @detail_route(methods=['get'])
    def tasks(self, request, pk=None):
        step = self.get_object()
        tasks = step.tasks.filter(hidden=False).select_related('responsible')
        page = self.paginate_queryset(tasks)
        if page is not None:
            serializers = ProcessTaskSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializers.data)
        serializers = ProcessTaskSerializer(tasks, many=True, context={'request': request})
        return Response(serializers.data)

    @detail_route(methods=['post'], permission_classes=[CanUndo])
    def undo(self, request, pk=None):
        self.get_object().undo()
        return Response({'status': 'undoing step'})

    @detail_route(methods=['post'], url_path='undo-failed', permission_classes=[CanUndo])
    def undo_failed(self, request, pk=None):
        self.get_object().undo(only_failed=True)
        return Response({'status': 'undoing failed tasks in step'})

    @detail_route(methods=['post'], permission_classes=[CanRetry])
    def retry(self, request, pk=None):
        self.get_object().retry()
        return Response({'status': 'retrying step'})

    @detail_route(methods=['post'])
    def resume(self, request, pk=None):
        self.get_object().resume()
        return Response({'status': 'resuming step'})


class ProcessTaskViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tasks to be viewed or edited.
    """
    queryset = ProcessTask.objects.select_related('responsible').all()
    serializer_class = ProcessTaskSerializer

    def get_serializer_class(self):
        if self.action == 'list':
            return ProcessTaskSerializer

        return ProcessTaskDetailSerializer

    @detail_route(methods=['post'], permission_classes=[CanUndo])
    def undo(self, request, pk=None):
        self.get_object().undo()
        return Response({'status': 'undoing task'})

    @detail_route(methods=['post'], permission_classes=[CanRetry])
    def retry(self, request, pk=None):
        self.get_object().retry()
        return Response({'status': 'retries task'})

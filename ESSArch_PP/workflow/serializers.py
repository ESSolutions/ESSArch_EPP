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

from rest_framework import serializers

from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask


class ProcessStepSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ProcessStep
        fields = (
            'url', 'id', 'name', 'result', 'type', 'user', 'parallel',
            'status', 'progress', 'undone', 'time_created', 'parent_step',
            'parent_step_pos', 'information_package',
        )
        read_only_fields = (
            'status', 'progress', 'time_created', 'time_done', 'undone',
        )


class ProcessTaskSerializer(serializers.HyperlinkedModelSerializer):
    responsible = serializers.SlugRelatedField(
        slug_field='username', read_only=True
    )

    class Meta:
        model = ProcessTask
        fields = (
            'url', 'id', 'name', 'status', 'progress',
            'processstep', 'processstep_pos', 'time_started',
            'time_done', 'undone', 'undo_type', 'retried',
            'responsible', 'hidden',
        )

        read_only_fields = (
            'status', 'progress', 'time_started', 'time_done', 'undone',
            'undo_type', 'retried', 'hidden',
        )


class ProcessTaskDetailSerializer(ProcessTaskSerializer):
    params = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    def get_params(self, obj):
        return dict((str(k), str(v)) for k, v in obj.params.iteritems())

    def get_result(self, obj):
        return str(obj.result)

    class Meta:
        model = ProcessTaskSerializer.Meta.model
        fields = ProcessTaskSerializer.Meta.fields + (
            'params', 'result', 'traceback', 'exception',
        )
        read_only_fields = ProcessTaskSerializer.Meta.read_only_fields + (
            'params', 'result', 'traceback', 'exception',
        )

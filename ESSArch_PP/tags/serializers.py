from django.utils.translation import ugettext as _
from rest_framework import serializers

from ESSArch_Core.tags.models import (
    Agent,
    AgentIdentifier,
    AgentName,
    AgentNote,
    AgentPlace,
    AgentType,
    MainAgentType,
    Structure,
    Topography,
)


class AgentIdentifierSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentIdentifier
        fields = ('id', 'identifier', 'type',)


class AgentNameSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentName
        fields = ('id', 'main', 'part', 'description', 'type', 'start_date', 'end_date', 'certainty',)


class AgentNoteSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentNote
        fields = ('id', 'text', 'type', 'create_date', 'revise_date',)


class TopographySerializer(serializers.ModelSerializer):
    class Meta:
        model = Topography
        fields = (
            'id',
            'name',
            'alt_name',
            'type',
            'main_category',
            'sub_category',
            'reference_code',
            'start_year',
            'end_year',
            'lng',
            'lat',
        )


class AgentPlaceSerializer(serializers.ModelSerializer):
    topography = TopographySerializer()
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentPlace
        fields = ('id', 'topography', 'type', 'description', 'start_date', 'end_date')


class MainAgentTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MainAgentType
        fields = ('id', 'name',)


class AgentTypeSerializer(serializers.ModelSerializer):
    main_type = MainAgentTypeSerializer()

    class Meta:
        model = AgentType
        fields = ('id', 'main_type', 'sub_type', 'cpf',)


class AgentSerializer(serializers.ModelSerializer):
    identifiers = AgentIdentifierSerializer(many=True)
    names = AgentNameSerializer(many=True)
    notes = AgentNoteSerializer(many=True)
    places = AgentPlaceSerializer(source='agentplace_set', many=True)
    type = AgentTypeSerializer()

    class Meta:
        model = Agent
        fields = (
            'id',
            'names',
            'notes',
            'type',
            'identifiers',
            'places',
            'level_of_detail',
            'record_status',
            'script',
            'language',
            'mandates',
            'create_date',
            'revise_date',
            'start_date',
            'end_date',
        )


class SearchSerializer(serializers.Serializer):
    index = serializers.ChoiceField(choices=['archive', 'component'], default='component')
    name = serializers.CharField()
    type = serializers.CharField()
    reference_code = serializers.CharField()
    structure = serializers.PrimaryKeyRelatedField(required=False, queryset=Structure.objects.all())
    archive = serializers.CharField(required=False)
    parent = serializers.CharField(required=False)
    structure_unit = serializers.CharField(required=False)
    archive_creator = serializers.CharField(required=False)
    archive_responsible = serializers.CharField(required=False)

    def validate(self, data):
        if data['index'] == 'archive' and 'structure' not in data:
            raise serializers.ValidationError({'structure': [_('This field is required.')]})

        if data['index'] != 'archive':
            if 'parent' not in data and 'structure_unit' not in data:
                raise serializers.ValidationError('parent or structure_unit required')

            if 'structure_unit' in data and 'archive' not in data:
                raise serializers.ValidationError({'archive': [_('This field is required.')]})

        return data

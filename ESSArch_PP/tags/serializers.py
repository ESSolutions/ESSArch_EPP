from django.utils.translation import ugettext as _
from rest_framework import serializers

from ESSArch_Core.tags.models import (
    Agent,
    AgentIdentifier,
    AgentName,
    AgentNote,
    AgentPlace,
    AgentRelation,
    AgentTagLink,
    AgentType,
    MainAgentType,
    Structure,
    SourcesOfAuthority,
    Topography,
)

from ESSArch_Core.tags.serializers import TagVersionNestedSerializer


class AgentIdentifierSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentIdentifier
        fields = ('id', 'identifier', 'type',)


class AgentNameSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentName
        fields = ('main', 'part', 'description', 'type', 'start_date', 'end_date', 'certainty',)


class AgentNoteSerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentNote
        fields = ('text', 'type', 'create_date', 'revise_date',)


class SourcesOfAuthoritySerializer(serializers.ModelSerializer):
    type = serializers.CharField(source='type.name')

    class Meta:
        model = SourcesOfAuthority
        fields = ('id', 'name', 'description', 'type', 'href', 'start_date', 'end_date',)


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


class RelatedAgentSerializer(serializers.ModelSerializer):
    names = AgentNameSerializer(many=True)
    type = AgentTypeSerializer()

    class Meta:
        model = Agent
        fields = ('id', 'names', 'type',)


class AgentRelationSerializer(serializers.ModelSerializer):
    agent = RelatedAgentSerializer(source='agent_b')
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentRelation
        fields = ('type', 'description', 'start_date', 'end_date', 'agent',)


class AgentArchiveLinkSerializer(serializers.ModelSerializer):
    archive = TagVersionNestedSerializer(source='tag')
    type = serializers.CharField(source='type.name')

    class Meta:
        model = AgentTagLink
        fields = ('archive', 'type', 'description', 'start_date', 'end_date',)


class AgentSerializer(serializers.ModelSerializer):
    identifiers = AgentIdentifierSerializer(many=True)
    names = AgentNameSerializer(many=True)
    notes = AgentNoteSerializer(many=True)
    places = AgentPlaceSerializer(source='agentplace_set', many=True)
    type = AgentTypeSerializer()
    mandates = SourcesOfAuthoritySerializer(many=True)
    related_agents = AgentRelationSerializer(source='agent_relations_a', many=True)

    class Meta:
        model = Agent
        fields = (
            'id',
            'names',
            'notes',
            'type',
            'identifiers',
            'places',
            'mandates',
            'level_of_detail',
            'record_status',
            'script',
            'language',
            'mandates',
            'related_agents',
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

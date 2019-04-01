from django.db import transaction
from django.utils.translation import ugettext as _
from rest_framework import serializers

from ESSArch_Core.agents.models import Agent, AgentTagLink, AgentTagLinkRelationType
from ESSArch_Core.auth.fields import CurrentUsernameDefault
from ESSArch_Core.tags.documents import Archive, Component
from ESSArch_Core.tags.models import Search, Structure, StructureUnit, Tag, TagStructure, TagVersion, TagVersionType


class ComponentWriteSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=TagVersionType.objects.filter(archive_type=False))
    reference_code = serializers.CharField()
    parent = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=TagVersion.objects.filter(type__archive_type=False),
    )
    structure = serializers.PrimaryKeyRelatedField(required=False, queryset=Structure.objects.filter(template=False))
    structure_unit = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=StructureUnit.objects.filter(structure__template=False),
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        with transaction.atomic():
            structure_unit = validated_data.pop('structure_unit', None)
            parent = validated_data.pop('parent', None)
            structure = validated_data.pop('structure', None)

            tag = Tag.objects.create()
            tag_structure = TagStructure(tag=tag)

            if structure_unit is not None:
                tag_structure.structure_unit = structure_unit
                tag_structure.structure = structure_unit.structure

                archive_structure = TagStructure.objects.get(structure=structure_unit.structure).get_root()
                tag_structure.parent = archive_structure

                tag_structure.save()

            else:
                if structure is None:
                    parent_structure = parent.get_active_structure()
                else:
                    parent_structure = parent.get_structures(structure).get()

                tag_structure.parent = parent_structure
                tag_structure.structure = parent_structure.structure

            tag_structure.save()

            tag_version = TagVersion.objects.create(
                tag=tag, elastic_index='component', **validated_data,
            )
            tag.current_version=tag_version
            tag.save()

            for agent_link in AgentTagLink.objects.filter(tag=tag_version):
                AgentTagLink.objects.create(tag=tag_version, agent=agent_link.agent, type=agent_link.type)

        doc = Component.from_obj(tag_version)
        doc.save()

        return tag

    def validate(self, data):
        if 'parent' not in data and 'structure_unit' not in data:
            raise serializers.ValidationError('parent or structure_unit required')

        if data.get('start_date') and data.get('end_date') and \
           data.get('start_date') > data.get('end_date'):

            raise serializers.ValidationError(_("end date must occur after start date"))

        return data


class ArchiveWriteSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.PrimaryKeyRelatedField(queryset=TagVersionType.objects.filter(archive_type=True))
    structure = serializers.PrimaryKeyRelatedField(queryset=Structure.objects.filter(template=True))
    archive_creator = serializers.PrimaryKeyRelatedField(queryset=Agent.objects.all())
    description = serializers.CharField(required=False)
    reference_code = serializers.CharField()
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)

    def create(self, validated_data):
        with transaction.atomic():
            agent = validated_data.pop('archive_creator')

            structure = validated_data.pop('structure')
            new_structure = structure.create_template_instance()

            tag = Tag.objects.create()
            TagStructure.objects.create(tag=tag, structure=new_structure)
            tag_version = TagVersion.objects.create(
                tag=tag, elastic_index='archive', **validated_data,
            )
            tag.current_version=tag_version
            tag.save()

            org = self.context['request'].user.user_profile.current_organization
            org.add_object(tag_version)

            tag_link_type, _ = AgentTagLinkRelationType.objects.get_or_create(name='creator')
            AgentTagLink.objects.create(agent=agent, tag=tag_version, type=tag_link_type)

        doc = Archive.from_obj(tag_version)
        doc.save()

        return tag

    def validate(self, data):
        if data.get('start_date') and data.get('end_date') and \
           data.get('start_date') > data.get('end_date'):

            raise serializers.ValidationError(_("end date must occur after start date"))

        return data


class StoredSearchSerializer(serializers.ModelSerializer):
    user = serializers.CharField(read_only=True, default=CurrentUsernameDefault())
    query = serializers.JSONField()

    def create(self, validated_data):
        if 'user' not in validated_data:
            validated_data['user'] = self.context['request'].user
        return super().create(validated_data)

    class Meta:
        model = Search
        fields = ('id', 'name', 'user', 'query',)

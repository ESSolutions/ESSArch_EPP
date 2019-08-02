from django.db import transaction
from django.utils.translation import ugettext as _
from django.utils import timezone
from rest_framework import serializers

from ESSArch_Core.agents.models import Agent, AgentTagLink, AgentTagLinkRelationType
from ESSArch_Core.auth.fields import CurrentUsernameDefault
from ESSArch_Core.tags.documents import Archive, Component
from ESSArch_Core.tags.models import (
    Search,
    Structure,
    StructureUnit,
    Tag,
    TagStructure,
    TagVersion,
    TagVersionType,
    Location,
    NodeNote,
    NodeIdentifier,
)
from ESSArch_Core.tags.serializers import (
    NodeNoteSerializer,
    NodeNoteWriteSerializer,
    NodeIdentifierSerializer,
    NodeIdentifierWriteSerializer,
)


class ComponentWriteSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(required=False)
    type = serializers.PrimaryKeyRelatedField(queryset=TagVersionType.objects.filter(archive_type=False))
    reference_code = serializers.CharField()
    parent = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=TagVersion.objects.filter(type__archive_type=False),
    )
    location = serializers.PrimaryKeyRelatedField(queryset=Location.objects.all(), allow_null=True)
    structure = serializers.PrimaryKeyRelatedField(
        required=False, queryset=Structure.objects.filter(is_template=False))
    structure_unit = serializers.PrimaryKeyRelatedField(
        required=False,
        queryset=StructureUnit.objects.filter(structure__is_template=False),
    )
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    custom_fields = serializers.JSONField(required=False)
    notes = NodeNoteWriteSerializer(many=True, required=False)
    identifiers = NodeIdentifierWriteSerializer(many=True, required=False)

    @staticmethod
    def create_notes(tag_version, notes_data):
        NodeNote.objects.bulk_create([
            NodeNote(tag_version=tag_version, **note)
            for note in notes_data
        ])

    @staticmethod
    def create_identifiers(tag_version, identifiers_data):
        NodeIdentifier.objects.bulk_create([
            NodeIdentifier(tag_version=tag_version, **identifier)
            for identifier in identifiers_data
        ])

    def create(self, validated_data):
        with transaction.atomic():
            structure_unit = validated_data.pop('structure_unit', None)
            parent = validated_data.pop('parent', None)
            structure = validated_data.pop('structure', None)
            notes_data = validated_data.pop('notes', None)
            identifiers_data = validated_data.pop('identifiers', [])

            tag = Tag.objects.create()
            tag_structure = TagStructure(tag=tag)

            if structure_unit is not None:
                tag_structure.structure_unit = structure_unit
                tag_structure.structure = structure_unit.structure

                archive_structure = TagStructure.objects.filter(structure=structure_unit.structure).first().get_root()
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
            tag.current_version = tag_version
            tag.save()

            for agent_link in AgentTagLink.objects.filter(tag=tag_version):
                AgentTagLink.objects.create(tag=tag_version, agent=agent_link.agent, type=agent_link.type)

            tag_structure.refresh_from_db()
            structure_unit = tag_structure.get_ancestors(
                include_self=True
            ).filter(structure_unit__isnull=False).get().structure_unit
            related_units = structure_unit.related_structure_units.filter(
                structure__is_template=False
            ).exclude(
                structure=tag_structure.structure
            )

            for related in related_units:
                new_unit = related if tag_structure.structure_unit is not None else None
                tag_structure.copy_to_new_structure(related.structure, new_unit=new_unit)

            self.create_identifiers(self, identifiers_data)
            self.create_notes(self, notes_data)

        doc = Component.from_obj(tag_version)
        doc.save()

        return tag

    def update(self, instance, validated_data):
        structure_unit = validated_data.pop('structure_unit', None)
        parent = validated_data.pop('parent', None)
        structure = validated_data.pop('structure', None)
        notes_data = validated_data.pop('notes', None)
        identifiers_data = validated_data.pop('identifiers', [])

        if identifiers_data is not None:
            NodeIdentifier.objects.filter(tag_version=instance).delete()
            self.create_identifiers(instance, identifiers_data)


        if notes_data is not None:
            NodeNote.objects.filter(tag_version=instance).delete()
            for note in notes_data:
                note.setdefault('create_date', timezone.now())
            self.create_notes(instance, notes_data)

        if structure is not None:
            tag = instance.tag
            tag_structure = TagStructure.objects.get(tag=tag, structure=structure)

            if structure_unit is not None:
                tag_structure.structure_unit = structure_unit
                archive_structure = tag_structure.get_root()
                tag_structure.parent = archive_structure
                tag_structure.save()

            if parent is not None:
                parent_structure = parent.get_structures(structure).get()
                tag_structure.parent = parent_structure
                tag_structure.structure_unit = None
                tag_structure.save()

        TagVersion.objects.filter(pk=instance.pk).update(**validated_data)
        instance.refresh_from_db()

        doc = Component.from_obj(instance)
        doc.save()

        return instance

    def validate(self, data):
        if not self.instance and 'parent' not in data and 'structure_unit' not in data:
            raise serializers.ValidationError('parent or structure_unit required')

        if data.get('start_date') and data.get('end_date') and \
           data.get('start_date') > data.get('end_date'):

            raise serializers.ValidationError(_("end date must occur after start date"))

        return data


class ArchiveWriteSerializer(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.PrimaryKeyRelatedField(queryset=TagVersionType.objects.filter(archive_type=True))
    structures = serializers.PrimaryKeyRelatedField(
        queryset=Structure.objects.filter(is_template=True, published=True), many=True)
    archive_creator = serializers.PrimaryKeyRelatedField(queryset=Agent.objects.all())
    description = serializers.CharField(required=False)
    reference_code = serializers.CharField()
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    custom_fields = serializers.JSONField(required=False)
    notes = NodeNoteWriteSerializer(many=True, required=False)
    identifiers = NodeIdentifierWriteSerializer(many=True, required=False)

    @staticmethod
    def create_notes(tag_version, notes_data):
        NodeNote.objects.bulk_create([
            NodeNote(tag_version=tag_version, **note)
            for note in notes_data
        ])

    @staticmethod
    def create_identifiers(tag_version, identifiers_data):
        NodeIdentifier.objects.bulk_create([
            NodeIdentifier(tag_version=tag_version, **identifier)
            for identifier in identifiers_data
        ])

    def create(self, validated_data):
        with transaction.atomic():
            agent = validated_data.pop('archive_creator')
            structures = validated_data.pop('structures')
            notes_data = validated_data.pop('notes', None)
            identifiers_data = validated_data.pop('identifiers', [])

            tag = Tag.objects.create()
            tag_version = TagVersion.objects.create(
                tag=tag, elastic_index='archive', **validated_data,
            )
            tag.current_version = tag_version
            tag.save()

            for structure in structures:
                structure.create_template_instance(tag)

            org = self.context['request'].user.user_profile.current_organization
            org.add_object(tag)
            org.add_object(tag_version)

            tag_link_type, _ = AgentTagLinkRelationType.objects.get_or_create(name='creator')
            AgentTagLink.objects.create(agent=agent, tag=tag_version, type=tag_link_type)
            self.create_identifiers(self, identifiers_data)
            self.create_notes(self, notes_data)

        doc = Archive.from_obj(tag_version)
        doc.save()

        return tag

    def update(self, instance, validated_data):
        structures = validated_data.pop('structures', [])
        notes_data = validated_data.pop('notes', None)
        identifiers_data = validated_data.pop('identifiers', [])

        if identifiers_data is not None:
            NodeIdentifier.objects.filter(tag_version=instance).delete()
            self.create_identifiers(instance, identifiers_data)


        if notes_data is not None:
            NodeNote.objects.filter(tag_version=instance).delete()
            for note in notes_data:
                note.setdefault('create_date', timezone.now())
            self.create_notes(instance, notes_data)

        with transaction.atomic():
            for structure in structures:
                if not TagStructure.objects.filter(tag=instance.tag, structure__template=structure).exists():
                    structure.create_template_instance(instance.tag)

            TagVersion.objects.filter(pk=instance.pk).update(**validated_data)
            instance.refresh_from_db()

        doc = Archive.from_obj(instance)
        doc.save()

        return instance

    def validate_structures(self, structures):
        if not len(structures):
            raise serializers.ValidationError(_("At least one structure is required"))

        if self.instance:
            existing_structures = Structure.objects.filter(tagstructure__tag=self.instance.tag)

            for existing_structure in existing_structures:
                if existing_structure.template not in structures:
                    raise serializers.ValidationError(_("Structures cannot be deleted from archives"))

        return structures

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

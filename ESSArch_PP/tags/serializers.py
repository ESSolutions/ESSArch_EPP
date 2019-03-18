from django.utils.translation import ugettext as _
from rest_framework import serializers

from ESSArch_Core.auth.fields import CurrentUsernameDefault
from ESSArch_Core.tags.models import Search, Structure


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

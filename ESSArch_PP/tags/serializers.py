from rest_framework import serializers


class SearchSerializer(serializers.Serializer):
    index = serializers.ChoiceField(choices=['archive', 'component'])
    name = serializers.CharField()
    type = serializers.CharField()
    structure = serializers.CharField(required=False)
    parent = serializers.CharField(required=False)
    parent_index = serializers.ChoiceField(choices=['archive', 'component'], required=False)

    def validate(self, data):
        if data.get('parent') is None and data.get('structure') is None:
            raise serializers.ValidationError("parent or structure is required")
        return data

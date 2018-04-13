from rest_framework import serializers


class SearchSerializer(serializers.Serializer):
    index = serializers.ChoiceField(choices=['archive', 'component'])
    name = serializers.CharField()
    type = serializers.CharField()
    parent = serializers.CharField(required=False)
    parent_index = serializers.ChoiceField(choices=['archive', 'component'], required=False)

from rest_framework import serializers


class SearchSerializer(serializers.Serializer):
    index = serializers.ChoiceField(choices=['archive', 'component'])
    name = serializers.CharField()
    type = serializers.CharField()
    reference_code = serializers.CharField()
    structure = serializers.CharField(required=True)
    parent = serializers.CharField(required=False)

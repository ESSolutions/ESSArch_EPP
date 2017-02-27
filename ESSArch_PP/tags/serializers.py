from rest_framework import serializers

from ESSArch_Core.ip.models import InformationPackage
from ESSArch_Core.tags.models import Tag


class NestedTagSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Tag
        fields = ('url', 'id', 'name', 'desc',)


class TagSerializer(serializers.HyperlinkedModelSerializer):
    children = NestedTagSerializer(many=True, read_only=True)
    information_packages = serializers.HyperlinkedRelatedField(
        many=True,
        queryset=InformationPackage.objects.all(),
        view_name='informationpackage-detail'
    )

    class Meta:
        model = Tag
        fields = ('url', 'id', 'name', 'desc', 'children', 'parent', 'information_packages',)

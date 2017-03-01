from rest_framework import serializers

from ESSArch_Core.ip.models import InformationPackage


class InformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = InformationPackage
        fields = ('url', 'id', 'Label', 'ObjectIdentifierValue',)


class InformationPackageDetailSerializer(InformationPackageSerializer):
    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags',
        )

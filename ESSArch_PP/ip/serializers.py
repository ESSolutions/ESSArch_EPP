from rest_framework import serializers

from ESSArch_Core.ip.models import InformationPackage


class InformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)

    class Meta:
        model = InformationPackage
        fields = ('url', 'id', 'Label', 'ObjectIdentifierValue', 'package_type')


class InformationPackageDetailSerializer(InformationPackageSerializer):
    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags',
        )

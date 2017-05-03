from rest_framework import serializers

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    EventIP,
    InformationPackage,
)

from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

class ArchivalInstitutionSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalInstitution
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivistOrganizationSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivistOrganization
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivalTypeSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalType
        fields = ('url', 'id', 'name', 'information_packages',)


class ArchivalLocationSerializer(DynamicHyperlinkedModelSerializer):
    class Meta:
        model = ArchivalLocation
        fields = ('url', 'id', 'name', 'information_packages',)


class EventIPSerializer(serializers.HyperlinkedModelSerializer):
    eventDetail = serializers.SlugRelatedField(slug_field='eventDetail', source='eventType', read_only=True)

    class Meta:
        model = EventIP
        fields = (
                'url', 'id', 'eventType', 'eventDateTime', 'eventDetail',
                'eventVersion', 'eventOutcome',
                'eventOutcomeDetailNote', 'linkingAgentIdentifierValue',
                'linkingObjectIdentifierValue',
        )

class NestedInformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)

    ArchivalInstitution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivistOrganization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivalType = ArchivalTypeSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivalLocation = ArchivalLocationSerializer(
        fields=['url', 'id', 'name']
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'Label', 'ObjectIdentifierValue',
            'package_type', 'Responsible', 'CreateDate',
            'entry_date', 'State', 'status', 'step_state',
            'aic', 'generation', 'ArchivalInstitution',
            'ArchivistOrganization', 'ArchivalType', 'ArchivalLocation',
        )

class InformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = NestedInformationPackageSerializer(
        many=True,
        read_only=True,
        source='related_ips'
    )

    ArchivalInstitution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivistOrganization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivalType = ArchivalTypeSerializer(
        fields=['url', 'id', 'name']
    )
    ArchivalLocation = ArchivalLocationSerializer(
        fields=['url', 'id', 'name']
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'Label', 'ObjectIdentifierValue', 'package_type',
            'Responsible', 'CreateDate', 'entry_date', 'State', 'status',
            'step_state', 'aic', 'information_packages', 'generation',
            'ArchivalInstitution', 'ArchivistOrganization', 'ArchivalType',
            'ArchivalLocation',
        )


class InformationPackageDetailSerializer(InformationPackageSerializer):
    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags',
        )

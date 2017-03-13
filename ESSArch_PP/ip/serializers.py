from rest_framework import serializers

from ESSArch_Core.ip.models import EventIP, InformationPackage


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


class InformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='informationpackage-detail',
        source='related_ips'
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'Label', 'ObjectIdentifierValue',
            'package_type', 'Responsible', 'CreateDate',
            'entry_date', 'State', 'status', 'step_state',
            'aic', 'information_packages', 'generation',
        )


class InformationPackageDetailSerializer(InformationPackageSerializer):
    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags',
        )

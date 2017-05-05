from rest_framework import exceptions, serializers

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    EventIP,
    InformationPackage,
    Workarea,
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
    information_packages = serializers.SerializerMethodField()

    def get_information_packages(self, obj):
        request = self.context['request']
        view_type = request.query_params.get('view_type', 'aic')
        state = request.query_params.get('state', '').split(u',')

        related = obj.related_ips().filter(State__in=state)

        ips = NestedInformationPackageSerializer(
            related, many=True, context={'request': request}
        )
        return ips.data

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

class WorkareaSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = serializers.SerializerMethodField()

    """
    def get_information_packages(self, obj):
        request = self.context['request']
        related = obj.related_ips().filter()

        try:
            workarea_type = request.query_params['type'].lower()
            workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

            try:
                related = related.filter(
                    workareas__user=request.user,
                    workareas__type=workarea_type_reverse[workarea_type]
                )
            except KeyError:
                raise exceptions.ParseError('Workarea of type "%s" does not exist' % workarea_type)
        except KeyError:
            related = related.filter(
                workareas__user=request.user,
            )


        ips = NestedInformationPackageSerializer(
            related, many=True, context={'request': request}
        )
        return ips.data
    """

    def get_information_packages(self, obj):
        related = obj.related_ips()
        request = self.context['request']

        try:
            query_wtype = request.query_params['type'].lower()
        except KeyError:
            related = related.filter(
                workareas__user=request.user,
            )
        else:
            workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

            try:
                workarea_type = workarea_type_reverse[query_wtype]
            except KeyError:
                raise exceptions.ParseError('Workarea of type "%s" does not exist' % query_wtype)

            related = related.filter(
                workareas__user=request.user,
                workareas__type=workarea_type
            )

        state = request.query_params.get('state', '').split(u',')

        ips = NestedInformationPackageSerializer(
            related, many=True, context={'request': request}
        )

        return ips.data

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

from rest_framework import exceptions, filters, serializers

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    EventIP,
    InformationPackage,
    Order,
    Workarea,
)

from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

from ip.filters import InformationPackageFilter

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
            'archived', 'cached', 'aic', 'generation', 'ArchivalInstitution',
            'ArchivistOrganization', 'ArchivalType', 'ArchivalLocation',
        )

class InformationPackageSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = serializers.SerializerMethodField()

    def get_information_packages(self, obj):
        request = self.context['request']
        view = self.context.get('view')
        view_type = request.query_params.get('view_type', 'aic')

        related = obj.related_ips()

        qp = request.query_params.copy()
        qp.__setitem__('view_type', 'self')

        related = InformationPackageFilter(qp, queryset=related).qs

        search_filter = filters.SearchFilter()

        # do not need to check on IPs related to the related IPs
        view.search_fields = [
            s for s in view.search_fields
            if not s.startswith('aic__information_packages__') and
            not s.startswith('information_packages__')
        ]
        related = search_filter.filter_queryset(request, related, view)

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
            'step_state', 'archived', 'cached', 'aic', 'information_packages',
            'generation', 'ArchivalInstitution', 'ArchivistOrganization',
            'ArchivalType', 'ArchivalLocation',
        )

class WorkareaSerializer(serializers.HyperlinkedModelSerializer):
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = serializers.SerializerMethodField()

    def get_information_packages(self, obj):
        related = obj.related_ips()
        request = self.context['request']
        view = self.context.get('view')
        view_type = request.query_params.get('view_type', 'aic')

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

        qp = request.query_params.copy()
        qp.__setitem__('view_type', 'self')

        related = InformationPackageFilter(qp, queryset=related).qs

        search_filter = filters.SearchFilter()

        # do not need to check on IPs related to the related IPs
        view.search_fields = [
            s for s in view.search_fields
            if not s.startswith('aic__information_packages__') and
            not s.startswith('information_packages__')
        ]
        related = search_filter.filter_queryset(request, related, view)

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


class OrderSerializer(serializers.HyperlinkedModelSerializer):
    responsible = serializers.HyperlinkedRelatedField(
        view_name='user-detail', read_only=True,
        default=serializers.CurrentUserDefault()
    )
    information_packages = serializers.HyperlinkedRelatedField(
        many=True, required=False, view_name='informationpackage-detail',
        queryset=InformationPackage.objects.filter(
            package_type=InformationPackage.DIP
        )
    )

    class Meta:
        model = Order
        fields = (
            'url', 'id', 'label', 'responsible', 'information_packages',
        )

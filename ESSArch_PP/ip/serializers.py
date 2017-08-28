from _version import get_versions

from rest_framework import exceptions, filters, serializers

from ESSArch_Core.configuration.models import EventType

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

from ESSArch_Core.auth.serializers import UserSerializer
from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer

from configuration.serializers import ArchivePolicySerializer
from ip.filters import InformationPackageFilter

VERSION = get_versions()['version']

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
    user = UserSerializer(read_only=True, source='linkingAgentIdentifierValue', default=serializers.CurrentUserDefault())
    information_package = serializers.PrimaryKeyRelatedField(required=False, allow_null=True, queryset=InformationPackage.objects.all(), source='linkingObjectIdentifierValue',)
    eventType = serializers.PrimaryKeyRelatedField(queryset=EventType.objects.all())
    eventDetail = serializers.SlugRelatedField(slug_field='eventDetail', source='eventType', read_only=True)

    class Meta:
        model = EventIP
        fields = (
                'url', 'id', 'eventType', 'eventDateTime', 'eventDetail',
                'eventVersion', 'eventOutcome',
                'eventOutcomeDetailNote', 'user',
                'information_package',
        )
        extra_kwargs = {
            'eventVersion': {
                'default': VERSION
            }
        }


class InformationPackageSerializer(DynamicHyperlinkedModelSerializer):
    responsible = UserSerializer(read_only=True)
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)

    archival_institution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archivist_organization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_type = ArchivalTypeSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_location = ArchivalLocationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value',
            'package_type', 'responsible', 'create_date',
            'entry_date', 'state', 'status', 'step_state',
            'archived', 'cached', 'aic', 'generation', 'archival_institution',
            'archivist_organization', 'archival_type', 'archival_location',
            'policy', 'message_digest', 'message_digest_algorithm',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class NestedInformationPackageSerializer(DynamicHyperlinkedModelSerializer):
    responsible = UserSerializer(read_only=True)
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    information_packages = serializers.SerializerMethodField()

    def get_information_packages(self, obj):
        request = self.context['request']
        view = self.context.get('view')

        if view is None or not hasattr(view, 'search_fields'):
            return obj.related_ips()

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

        ips = InformationPackageSerializer(
            related, many=True, context={'request': request}
        )
        return ips.data

    archival_institution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archivist_organization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_type = ArchivalTypeSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_location = ArchivalLocationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'package_type',
            'responsible', 'create_date', 'entry_date', 'state', 'status',
            'step_state', 'archived', 'cached', 'aic', 'information_packages',
            'generation', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'policy', 'message_digest',
            'message_digest_algorithm', 'submission_agreement',
            'submission_agreement_locked'
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


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

        ips = InformationPackageSerializer(
            related, many=True, context={'request': request}
        )
        return ips.data

    archival_institution = ArchivalInstitutionSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archivist_organization = ArchivistOrganizationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_type = ArchivalTypeSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )
    archival_location = ArchivalLocationSerializer(
        fields=['url', 'id', 'name'],
        read_only=True,
    )

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'package_type',
            'responsible', 'create_date', 'entry_date', 'state', 'status',
            'step_state', 'archived', 'cached', 'aic', 'information_packages',
            'generation', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'policy', 'message_digest',
            'message_digest_algorithm',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class InformationPackageAICSerializer(DynamicHyperlinkedModelSerializer):
    information_packages = InformationPackageSerializer(read_only=True, many=True)
    package_type = serializers.ChoiceField(choices=((1, 'AIC'),))

    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = (
            'id', 'label', 'object_identifier_value',
            'package_type', 'responsible', 'create_date',
            'entry_date', 'information_packages',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


class InformationPackageDetailSerializer(InformationPackageSerializer):
    aic = InformationPackageAICSerializer(omit=['information_packages'])
    policy = ArchivePolicySerializer()

    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'tags', 'submission_agreement', 'submission_agreement_locked',
        )
        extra_kwargs = {
            'id': {
                'read_only': False,
                'validators': [],
            },
            'object_identifier_value': {
                'read_only': False,
                'validators': [],
            },
        }


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

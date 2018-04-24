from guardian.shortcuts import get_perms
from rest_framework import filters, serializers

from ESSArch_Core.auth.serializers import UserSerializer
from ESSArch_Core.ip.models import (ArchivalInstitution, ArchivalLocation,
                                    ArchivalType, ArchivistOrganization,
                                    InformationPackage, Order)
from ESSArch_Core.ip.serializers import WorkareaSerializer
from ESSArch_Core.profiles.models import SubmissionAgreement
from ESSArch_Core.serializers import DynamicHyperlinkedModelSerializer
from _version import get_versions
from configuration.serializers import ArchivePolicySerializer

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


class InformationPackageSerializer(serializers.ModelSerializer):
    responsible = UserSerializer(read_only=True)
    package_type = serializers.ChoiceField(choices=InformationPackage.PACKAGE_TYPE_CHOICES)
    package_type_display = serializers.SerializerMethodField()
    workarea = serializers.SerializerMethodField()
    aic = serializers.PrimaryKeyRelatedField(queryset=InformationPackage.objects.all())
    first_generation = serializers.SerializerMethodField()
    last_generation = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

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

    def get_package_type_display(self, obj):
        return obj.get_package_type_display()

    def get_first_generation(self, obj):
        if hasattr(obj, 'first_generation'):
            return obj.first_generation

        return obj.is_first_generation()

    def get_last_generation(self, obj):
        if hasattr(obj, 'last_generation'):
            return obj.last_generation

        return obj.is_last_generation()

    def get_permissions(self, obj):
        checker = self.context.get('perm_checker')

        if checker is not None:
            return checker.get_perms(obj)

        request = self.context.get('request')
        if hasattr(request, 'user'):
            return get_perms(request.user, obj)

        return []

    def get_workarea(self, obj):
        try:
            workareas = obj.prefetched_workareas
        except AttributeError:
            request = self.context.get('request')
            see_all = request.user.has_perm('ip.see_all_in_workspaces')
            workareas = obj.workareas.all()

            if not see_all:
                workareas = workareas.filter(user=request.user)

        return WorkareaSerializer(workareas, many=True, context=self.context).data


    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'object_size',
            'package_type', 'package_type_display', 'responsible', 'create_date',
            'entry_date', 'state', 'status', 'step_state',
            'archived', 'cached', 'aic', 'generation', 'archival_institution',
            'archivist_organization', 'archival_type', 'archival_location',
            'policy', 'message_digest', 'message_digest_algorithm',
            'content_mets_create_date', 'content_mets_size', 'content_mets_digest_algorithm', 'content_mets_digest',
            'package_mets_create_date', 'package_mets_size', 'package_mets_digest_algorithm', 'package_mets_digest',
            'workarea', 'first_generation', 'last_generation', 'start_date', 'end_date',
            'permissions', 'appraisal_date',
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
    package_type_display = serializers.SerializerMethodField()
    information_packages = serializers.SerializerMethodField()
    aic = serializers.PrimaryKeyRelatedField(queryset=InformationPackage.objects.all())
    submission_agreement = serializers.PrimaryKeyRelatedField(queryset=SubmissionAgreement.objects.all())
    workarea = serializers.SerializerMethodField()
    first_generation = serializers.SerializerMethodField()
    last_generation = serializers.SerializerMethodField()
    new_version_in_progress = serializers.SerializerMethodField()
    permissions = serializers.SerializerMethodField()

    search_filter = filters.SearchFilter()

    def get_package_type_display(self, obj):
        return obj.get_package_type_display()

    def get_permissions(self, obj):
        checker = self.context.get('perm_checker')

        if checker is not None:
            return checker.get_perms(obj)

        request = self.context.get('request')
        if hasattr(request, 'user'):
            return get_perms(request.user, obj)

        return []

    def get_information_packages(self, obj):
        request = self.context['request']
        return InformationPackageSerializer(obj.related_ips(), many=True, context={'request': request, 'perm_checker': self.context.get('perm_checker')}).data

    def get_workarea(self, obj):
        try:
            workareas = obj.prefetched_workareas
        except AttributeError:
            request = self.context.get('request')
            see_all = request.user.has_perm('ip.see_all_in_workspaces')
            workareas = obj.workareas.all()

            if not see_all:
                workareas = workareas.filter(user=request.user)

        return WorkareaSerializer(workareas, many=True, context=self.context).data

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

    def get_first_generation(self, obj):
        if hasattr(obj, 'first_generation'):
            return obj.first_generation

        return obj.is_first_generation()

    def get_last_generation(self, obj):
        if hasattr(obj, 'last_generation'):
            return obj.last_generation

        return obj.is_last_generation()

    def get_new_version_in_progress(self, obj):
        new = obj.new_version_in_progress()
        if new is None:
            return None
        return WorkareaSerializer(new, context=self.context).data

    class Meta:
        model = InformationPackage
        fields = (
            'url', 'id', 'label', 'object_identifier_value', 'package_type', 'package_type_display',
            'responsible', 'create_date', 'entry_date', 'state', 'status',
            'step_state', 'archived', 'cached', 'aic', 'information_packages',
            'generation', 'archival_institution', 'archivist_organization',
            'archival_type', 'archival_location', 'policy', 'message_digest',
            'message_digest_algorithm', 'submission_agreement',
            'submission_agreement_locked', 'workarea', 'object_size',
            'first_generation', 'last_generation', 'start_date', 'end_date',
            'new_version_in_progress', 'appraisal_date', 'permissions',
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
            'entry_date', 'information_packages', 'appraisal_date',
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
    submission_agreement = serializers.PrimaryKeyRelatedField(queryset=SubmissionAgreement.objects.all())

    class Meta:
        model = InformationPackageSerializer.Meta.model
        fields = InformationPackageSerializer.Meta.fields + (
            'submission_agreement', 'submission_agreement_locked',
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
    responsible = UserSerializer(read_only=True,
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

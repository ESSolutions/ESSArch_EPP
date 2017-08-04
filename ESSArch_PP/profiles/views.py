"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Tools for Producer (ETP)
    Copyright (C) 2005-2017 ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program. If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
"""

import os

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Prefetch

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import exceptions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ESSArch_Core.configuration.models import (
    Path,
)

from ESSArch_Core.essxml.ProfileMaker.models import extensionPackage, templatePackage

from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalLocation,
    ArchivalType,
    EventIP,
    InformationPackage,
)

from ESSArch_Core.ip.permissions import (
    CanLockSA,
)

from ESSArch_Core.WorkflowEngine.models import (
    ProcessStep,
    ProcessTask,
)

from ESSArch_Core.profiles.serializers import (
    ProfileSerializer,
    ProfileSASerializer,
    ProfileIPSerializer,
    SubmissionAgreementSerializer
)

from ESSArch_Core.profiles.models import (
    SubmissionAgreement,
    Profile,
    ProfileSA,
    ProfileIP,
)

from profiles.serializers import ProfileMakerTemplateSerializer, ProfileMakerExtensionSerializer

from rest_framework import viewsets


class SubmissionAgreementViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows submission agreements to be viewed or edited.
    """
    queryset = SubmissionAgreement.objects.all().prefetch_related(
        Prefetch('profilesa_set', to_attr='profiles')
    )
    serializer_class = SubmissionAgreementSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('published',)

    @detail_route(methods=['post'])
    def publish(self, request, pk=None):
        SubmissionAgreement.objects.filter(pk=pk).update(published=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @detail_route(methods=['post'], url_path='include-type')
    def include_type(self, request, pk=None):
        sa = SubmissionAgreement.objects.get(pk=pk)
        ptype = request.data["type"]

        setattr(sa, "include_profile_%s" % ptype, True)
        sa.save()

        return Response({
            'status': 'Including profile type %s in SA %s' % (ptype, sa)
        })

    @detail_route(methods=['post'], url_path='exclude-type')
    def exclude_type(self, request, pk=None):
        sa = SubmissionAgreement.objects.get(pk=pk)
        ptype = request.data["type"]

        setattr(sa, "include_profile_%s" % ptype, False)
        sa.save()

        return Response({
            'status': 'Excluding profile type %s in SA %s' % (ptype, sa)
        })

    @detail_route(methods=['post'])
    def save(self, request, pk=None):
        if not request.user.has_perm('profiles.create_new_sa_generation'):
            raise exceptions.PermissionDenied

        sa = self.get_object()

        try:
            new_name = request.data["new_name"]
        except KeyError:
            new_name = ''

        if not new_name:
            return Response(
                {'status': 'No name specified'},
                status=status.HTTP_400_BAD_REQUEST
            )

        new_data = request.data.get("data", {})

        changed_data = False

        for field in sa.template:
            if field.get('templateOptions', {}).get('required', False):
                if not new_data.get(field['key'], None):
                    return Response(
                        {"status': 'missing required field '%s'" % field['key']},
                        status=status.HTTP_400_BAD_REQUEST
                    )

        for k, v in new_data.iteritems():
            if v != getattr(sa, k):
                changed_data = True
                break

        if not changed_data:
            return Response({'status': 'no changes, not saving'}, status=status.HTTP_400_BAD_REQUEST)

        new_sa = sa.copy(new_data=new_data, new_name=new_name,)
        serializer = SubmissionAgreementSerializer(
            new_sa, context={'request': request}
        )
        return Response(serializer.data)

    @detail_route(methods=["post"])
    def lock(self, request, pk=None):
        sa = self.get_object()
        ip_id = request.data.get("ip")

        try:
            ip = InformationPackage.objects.get(
                pk=ip_id
            )
        except InformationPackage.DoesNotExist:
            return Response(
                {'status': 'Information Package with id %s does not exist' % ip_id},
                status=status.HTTP_404_NOT_FOUND
            )

        permission = CanLockSA()
        if not permission.has_object_permission(request, self, ip):
            self.permission_denied(
                request, message=getattr(permission, 'message', None)
            )

        if ip.submission_agreement_locked:
            raise exceptions.ParseError('IP already has a locked SA')

        if ip.submission_agreement == sa:
            ip.submission_agreement_locked = True

            if sa.archivist_organization:
                arch, _ = ArchivistOrganization.objects.get_or_create(
                    name=sa.archivist_organization
                )
                ip.archivist_organization = arch

            ip.save()

            return Response({'status': 'locking submission_agreement'})
        elif ip.submission_agreement is None:
            return Response(
                {'status': 'No SA connected to IP'},
                status=status.HTTP_400_BAD_REQUEST
            )
        else:
            return Response(
                {'status': 'This SA is not connected to the selected IP'},
                status=status.HTTP_400_BAD_REQUEST
            )

class ProfileSAViewSet(viewsets.ModelViewSet):
    queryset = ProfileSA.objects.all()
    serializer_class = ProfileSASerializer


class ProfileIPViewSet(viewsets.ModelViewSet):
    queryset = ProfileIP.objects.all()
    serializer_class = ProfileIPSerializer


class ProfileViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows profiles to be viewed or edited.
    """
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    def get_queryset(self):
        queryset = Profile.objects.all()
        profile_type = self.request.query_params.get('type', None)

        if profile_type is not None:
            queryset = queryset.filter(profile_type=profile_type)

        return queryset

    @detail_route(methods=['post'])
    def save(self, request, pk=None):
        profile = Profile.objects.get(pk=pk)
        new_data = request.data.get("specification_data", {})
        new_structure = request.data.get("structure", {})

        changed_data = (profile.specification_data.keys().sort() == new_data.keys().sort() and
                        profile.specification_data != new_data)

        changed_structure = profile.structure != new_structure

        if (changed_data or changed_structure):
            try:
                new_profile = profile.copy(
                    specification_data=new_data,
                    new_name=request.data["new_name"],
                    structure=new_structure,
                )
            except ValidationError as e:
                return Response(e.message, status=status.HTTP_400_BAD_REQUEST)

            serializer = ProfileSerializer(
                new_profile, context={'request': request}
            )
            return Response(serializer.data)

        return Response({'status': 'no changes, not saving'}, status=status.HTTP_400_BAD_REQUEST)

    @detail_route(methods=["post"])
    def lock(self, request, pk=None):
        profile = self.get_object()

        try:
            profile.clean()
        except ValidationError as e:
            return Response({'status': repr(e)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ip_id = request.data["information_package"]
        except KeyError:
            raise exceptions.ParseError(detail='information_package parameter missing')

        try:
            ip = InformationPackage.objects.get(
                pk=ip_id
            )
        except InformationPackage.DoesNotExist:
            return Response(
                {'status': 'Information Package with id %s does not exist' % ip_id},
                status=status.HTTP_404_NOT_FOUND
            )

        if not (ip.submission_agreement and ip.submission_agreement_locked):
            return Response(
                {'status': 'IP needs a locked SA before locking profile'},
                status=status.HTTP_400_BAD_REQUEST
            )

        profile_ip, _ = ProfileIP.objects.get_or_create(profile=profile, ip=ip)

        if profile_ip.LockedBy is not None:
            raise exceptions.ParseError(detail='Profile "%s" already locked to "%s"' % (profile.name, ip.object_identifier_value))

        profile_ip.lock(request.user)

        if profile.profile_type == "sip":
            root = os.path.join(
                Path.objects.get(
                    entity="path_preingest_prepare"
                ).value,
                ip.object_identifier_value
            )

            step = ProcessStep.objects.create(
                name="Create Physical Model",
                information_package=ip
            )
            task = ProcessTask.objects.create(
                name="preingest.tasks.CreatePhysicalModel",
                params={
                    "structure": profile.structure,
                    "root": root
                },
                log=EventIP,
                information_package=ip,
                responsible=self.request.user,
                processstep=step,
            )

            step.run().get()

        if profile.profile_type == "transfer_project":
            archival_institution = profile.specification_data.get("archival_institution")
            archival_type = profile.specification_data.get("archival_type")
            archival_location = profile.specification_data.get("archival_location")

            if archival_institution:
                try:
                    (arch, _) = ArchivalInstitution.objects.get_or_create(
                        name=archival_institution
                    )
                except IntegrityError:
                    arch = ArchivalInstitution.objects.get(
                        name=archival_institution
                    )
                ip.archival_institution = arch

            if archival_type:
                try:
                    (arch, _) = ArchivalType.objects.get_or_create(
                        name=archival_type
                    )
                except IntegrityError:
                    arch = ArchivalType.objects.get(
                        name=archival_type
                    )
                ip.archival_type = arch

            if archival_location:
                try:
                    (arch, _) = ArchivalLocation.objects.get_or_create(
                        name=archival_location
                    )
                except IntegrityError:
                    arch = ArchivalLocation.objects.get(
                        name=archival_location
                    )
                ip.archival_location = arch

            ip.save()

        non_locked_sa_profiles = ProfileSA.objects.filter(
            submission_agreement=ip.submission_agreement,
        ).exclude(
            profile__profile_type__in=ProfileIP.objects.filter(
                ip=ip, LockedBy__isnull=False
            ).values('profile__profile_type')
        ).exists()

        if not non_locked_sa_profiles:
            ip.state = "Prepared"
            ip.save(update_fields=['state'])

        return Response({'status': 'locking profile'})


class ProfileMakerExtensionViewSet(viewsets.ModelViewSet):
    queryset = extensionPackage.objects.all()
    serializer_class = ProfileMakerExtensionSerializer


class ProfileMakerTemplateViewSet(viewsets.ModelViewSet):
    queryset = templatePackage.objects.all()
    serializer_class = ProfileMakerTemplateSerializer
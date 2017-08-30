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

import copy
import os
import uuid

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Prefetch

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import exceptions, permissions, serializers, status
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
    ProfileIPWriteSerializer,
    ProfileIPDataSerializer,
    SubmissionAgreementSerializer
)

from ESSArch_Core.profiles.models import (
    SubmissionAgreement,
    Profile,
    ProfileSA,
    ProfileIP,
    ProfileIPData,
)

from ESSArch_Core.essxml.ProfileMaker.views import calculateChildrenBefore, generateElement, removeChildren

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

    filter_backends = (DjangoFilterBackend,)
    filter_fields = ('ip', 'profile',)

    def get_serializer_class(self):
        if self.request.method in permissions.SAFE_METHODS:
            return ProfileIPSerializer

        return ProfileIPWriteSerializer


class ProfileIPDataViewSet(viewsets.ModelViewSet):
    queryset = ProfileIPData.objects.all()
    serializer_class = ProfileIPDataSerializer


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

    @detail_route(methods=['post'], url_path='add-child')
    def add_child(self, request, pk=None):
        required = ['name', 'parent']

        # validate input
        missing_items = {
            field_name: 'This field is required'
            for field_name in required
            if field_name not in request.data
        }
        if missing_items:
            raise exceptions.ValidationError(missing_items, code='required')

        obj = self.get_object()

        existingElements = obj.existingElements
        templates = obj.allElements

        new_name = request.data['name']
        parent = request.data['parent']
        new_uuid = str(uuid.uuid4())

        if parent not in existingElements:
            raise exceptions.ValidationError({'parent': '"%s" not in the tree' % parent})

        newElement = None

        # ensure that the element exists in any of the schemas
        if new_name in templates:
            newElement = copy.deepcopy(templates[new_name])
        else:
            for extension in obj.extensions.all():
                if new_name in extension.allElements:
                    newElement = copy.deepcopy(extension.allElements[new_name])

        if newElement is None:
            raise exceptions.ValidationError({'name': '"%s" not in any of the schemas' % new_name})

        newElement['parent'] = parent
        existingElements[new_uuid] = newElement

        # If there are multiple of the same element under the same parent
        # then we need to know the position of the last element with
        # the same name

        try:
            l = [c['name'] for c in existingElements[parent]['children']]
            index = len(l) - list(reversed(l)).index(new_name)
        except ValueError:
            index = 0

        # calculate which elements should be before the new element
        cb = calculateChildrenBefore(existingElements[parent]['availableChildren'], new_name)

        if index == 0:
            for child in existingElements[parent]['children']:
                if child['name'] not in cb:
                    break
                else:
                    index += 1

        e = {
            'name': new_name,
            'uuid': new_uuid
        }
        existingElements[parent]['children'].insert(index, e)
        obj.save()
        return Response(existingElements, status=status.HTTP_201_CREATED)

    @detail_route(methods=['delete'], url_path='delete-element')
    def delete_element(self, request, pk=None):
        required = ['uuid']

        # validate input
        missing_items = {
            field_name: 'This field is required'
            for field_name in required
            if field_name not in request.data
        }
        if missing_items:
            raise exceptions.ValidationError(missing_items, code='required')

        obj = self.get_object()
        el_uuid = request.data['uuid']

        try:
            el = obj.existingElements[el_uuid]
        except KeyError:
            raise exceptions.ValidationError({'uuid': 'Invalid uuid "%s" - element does not exist' % el_uuid})

        parent = obj.existingElements[el['parent']]

        # delete element in list of children of parent
        parent['children'][:] = [c for c in parent['children'] if c.get('uuid') != el_uuid]

        # delete the children of the element
        removeChildren(obj.existingElements, el)

        # delete the element
        del obj.existingElements[el_uuid]

        obj.save(update_fields=['existingElements'])
        return Response(obj.existingElements, status=status.HTTP_200_OK)

    @detail_route(methods=['put'], url_path='update-element')
    def update_element(self, request, pk=None):
        required = ['uuid', 'data']

        # validate input
        missing_items = {
            field_name: 'This field is required'
            for field_name in required
            if field_name not in request.data
        }
        if missing_items:
            raise exceptions.ValidationError(missing_items, code='required')

        obj = self.get_object()
        el_uuid = request.data['uuid']
        data = request.data['data']

        try:
            el = obj.existingElements[el_uuid]
        except KeyError:
            raise exceptions.ValidationError({'uuid': 'Invalid uuid "%s" - element does not exist' % el_uuid})

        obj.existingElements[el_uuid]['formData'] = data

        obj.save(update_fields=['existingElements'])
        return Response(obj.existingElements, status=status.HTTP_200_OK)

    @detail_route(methods=['put'], url_path='update-contains-files')
    def update_contains_files(self, request, pk=None):
        required = ['uuid', 'contains_files']

        # validate input
        missing_items = {
            field_name: 'This field is required'
            for field_name in required
            if field_name not in request.data
        }
        if missing_items:
            raise exceptions.ValidationError(missing_items, code='required')

        obj = self.get_object()
        el_uuid = request.data['uuid']
        val = request.data['contains_files']

        try:
            el = obj.existingElements[el_uuid]
        except KeyError:
            raise exceptions.ValidationError({'uuid': 'Invalid uuid "%s" - element does not exist' % el_uuid})

        if type(val) is not bool:
            raise exceptions.ValidationError({'contains_files': 'Must be a boolean'})

        obj.existingElements[el_uuid]['containsFiles'] = val
        obj.save(update_fields=['existingElements'])
        return Response(obj.existingElements, status=status.HTTP_200_OK)

    @detail_route(methods=['post'], url_path='add-attribute')
    def add_attribute(self, request, pk=None):
        required = ['uuid', 'data']

        # validate input
        missing_items = {
            field_name: 'This field is required'
            for field_name in required
            if field_name not in request.data
        }
        if missing_items:
            raise exceptions.ValidationError(missing_items, code='required')

        obj = self.get_object()
        el_uuid = request.data['uuid']
        data = request.data['data']

        try:
            el = obj.existingElements[el_uuid]
        except KeyError:
            raise exceptions.ValidationError({'uuid': 'Invalid uuid "%s" - element does not exist' % el_uuid})

        obj.existingElements[el_uuid]['userForm'].append(data)
        obj.save(update_fields=['existingElements'])
        return Response(obj.existingElements, status=status.HTTP_200_OK)

    @detail_route(methods=['post'])
    def generate(self, request, pk=None):
        class SimpleProfileSerializer(serializers.ModelSerializer):
            class Meta:
                model = Profile
                fields = (
                    'id', 'profile_type', 'name', 'type', 'status', 'label',
                )

        def addExtraAttribute(field, data, attr):
            """
            Adds extra attribute to field if it exists in data
            Args:
                field: The field to add to
                data: The data dictionary to look in
                attr: The name of the attribute to add
            Returns:
                The new field with the attribute added to it if the attribute
                exists in data. Otherwise the original field.
            """

            field_attr = field['key'] + '_' + attr

            if field_attr in data:
                field[attr] = data[field_attr]

            return field

        serializer = SimpleProfileSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data


        obj = self.get_object()
        existingElements = obj.existingElements

        form = existingElements['root']['form']
        formData = existingElements['root']['formData']

        for idx, field in enumerate(form):
            field = addExtraAttribute(field, formData, 'desc')
            field = addExtraAttribute(field, formData, 'hideExpression')
            field = addExtraAttribute(field, formData, 'readonly')

            form[idx] = field

        existingElements['root']['form'] = form

        nsmap = obj.nsmap

        for ext in obj.extensions.iterator():
            nsmap.update(ext.nsmap)

        schemaLocation = ['%s %s' % (obj.targetNamespace, obj.schemaURL)]

        XSI = 'http://www.w3.org/2001/XMLSchema-instance'

        if not nsmap.get("xsi"):
            nsmap["xsi"] = XSI

        if not nsmap.get(obj.prefix):
            nsmap[obj.prefix] = obj.targetNamespace

        for ext in obj.extensions.all():
            nsmap[ext.prefix] = ext.targetNamespace
            schemaLocation.append('%s %s' % (ext.targetNamespace, ext.schemaURL))

        jsonString, forms, data = generateElement(existingElements, 'root', nsmap=nsmap)

        schemaLocation = ({
            '-name': 'schemaLocation',
            '-namespace': 'xsi',
            '#content': [{
                'text': ' '.join(schemaLocation)
            }]
        })

        jsonString['-attr'].append(schemaLocation)

        profile = Profile.objects.create(profile_type=validated_data['profile_type'],
                    name=validated_data['name'], type=validated_data['type'],
                    status=validated_data['status'], label=validated_data['label'],
                    template=forms, specification=jsonString, specification_data=data)

        profile_data = ProfileSerializer(profile, context={'request': request}).data

        return Response(profile_data, status=status.HTTP_201_CREATED)

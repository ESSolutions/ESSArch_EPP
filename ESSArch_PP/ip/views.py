"""
    ESSArch is an open source archiving and digital preservation system

    ESSArch Preservation Platform (EPP)
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

import datetime
import errno
import glob
import mimetypes
import os
import re
import shutil
import tarfile
import uuid
import zipfile

from collections import OrderedDict
from operator import itemgetter

from celery import states as celery_states

from django.core.exceptions import ValidationError
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from django_filters.rest_framework import DjangoFilterBackend

from lxml import etree

from rest_framework import exceptions, filters, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response

from ESSArch_Core.configuration.models import (
    ArchivePolicy,
    Path,
)
from ESSArch_Core.essxml.util import get_objectpath, parse_submit_description
from ESSArch_Core.essxml.Generator.xmlGenerator import (
    find_destination
)
from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    InformationPackage,
    Order,
    EventIP,
    Workarea,
)
from ESSArch_Core.ip.permissions import (
    CanChangeSA,
    CanDeleteIP,
    CanUnlockProfile,
    IsOrderResponsibleOrAdmin,
    IsResponsibleOrReadOnly
)
from ESSArch_Core.profiles.models import (
    ProfileSA,
    SubmissionAgreement,
)
from ESSArch_Core.util import (
    get_value_from_path,
    get_files_and_dirs,
    get_tree_size_and_count,
    in_directory,
    parse_content_range_header,
    timestamp_to_datetime,
)
from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask
from ESSArch_Core.WorkflowEngine.serializers import ProcessStepSerializer
from ESSArch_Core.pagination import LinkHeaderPagination

from ip.filters import (
    ArchivalInstitutionFilter,
    ArchivistOrganizationFilter,
    ArchivalTypeFilter,
    ArchivalLocationFilter,
    InformationPackageFilter,
)
from ip.serializers import (
    ArchivalInstitutionSerializer,
    ArchivistOrganizationSerializer,
    ArchivalTypeSerializer,
    ArchivalLocationSerializer,
    InformationPackageSerializer,
    InformationPackageDetailSerializer,
    NestedInformationPackageSerializer,
    OrderSerializer,
    EventIPSerializer,
    WorkareaSerializer,
)


class ArchivalInstitutionViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows archival institutions to be viewed or edited.
    """
    queryset = ArchivalInstitution.objects.all()
    serializer_class = ArchivalInstitutionSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_class = ArchivalInstitutionFilter


class ArchivistOrganizationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows archivist organizations to be viewed or edited.
    """
    queryset = ArchivistOrganization.objects.all()
    serializer_class = ArchivistOrganizationSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_class = ArchivistOrganizationFilter


class ArchivalTypeViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows archival types to be viewed or edited.
    """
    queryset = ArchivalType.objects.all()
    serializer_class = ArchivalTypeSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_class = ArchivalTypeFilter


class ArchivalLocationViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows archival locations to be viewed or edited.
    """
    queryset = ArchivalLocation.objects.all()
    serializer_class = ArchivalLocationSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_class = ArchivalLocationFilter

class EventIPViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    queryset = EventIP.objects.all()
    serializer_class = EventIPSerializer


class InformationPackageReceptionViewSet(viewsets.ViewSet):
    search_fields = (
        'object_identifier_value', 'label', 'responsible__first_name',
        'responsible__last_name', 'responsible__username', 'state',
        'submission_agreement__name', 'start_date', 'end_date',
    )

    def find_xml_files(self, path):
        for xmlfile in glob.glob(os.path.join(path, "*.xml")):
            if os.path.isfile(xmlfile) and not xmlfile.endswith('_ipevents.xml'):
                yield xmlfile

    def get_container_for_xml(self, xmlfile):
        doc = etree.parse(xmlfile)
        root = doc.getroot()
        return get_objectpath(root)

    def get_contained_packages(self, path):
        ips = []

        for xmlfile in self.find_xml_files(path):
            container = os.path.join(path, self.get_container_for_xml(xmlfile))

            ip_id = os.path.splitext(os.path.basename(xmlfile))[0]

            if InformationPackage.objects.filter(object_identifier_value=ip_id).exists():
                continue

            ip = parse_submit_description(xmlfile, srcdir=os.path.split(container)[0])

            ip['container'] = container
            ip['xml'] = xmlfile
            ip['type'] = 'contained'
            ip['state'] = 'At reception'
            ip['status'] = 100
            ip['step_state'] = celery_states.SUCCESS
            ips.append(ip)

        return ips

    def get_extracted_packages(self, path):
        ips = []

        for d in os.listdir(path):
            if not os.path.isdir(os.path.join(path, d)):
                continue

            if InformationPackage.objects.filter(object_identifier_value=d).exists():
                continue

            ip = {
                'id': d,
                'object_identifier_value': d,
                'type': 'extracted',
                'state': 'At reception',
                'status': 100,
                'step_state': celery_states.SUCCESS,
            }

            ips.append(ip)

        return ips

    def list(self, request):
        filter_fields = ["label", "object_identifier_value", "responsible",
                         "create_date", "object_size", "archival_institution",
                         "archivist_organization", "start_date", "end_date"]

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")

        contained = self.get_contained_packages(reception)
        extracted = self.get_extracted_packages(reception)

        ips = contained + extracted
        new_ips = []

        # Remove all keys not in filter_fields
        conditions = {key: value for (key, value) in request.query_params.dict().iteritems() if key in filter_fields}

        # Filter ips based on conditions
        new_ips = filter(lambda ip: all((v in str(ip.get(k)) for (k,v) in conditions.iteritems())), ips)

        from_db = InformationPackage.objects.filter(state__in=['Prepared', 'Receiving'], **conditions)
        serializer = InformationPackageSerializer(
            data=from_db, many=True, context={'request': request, 'view': self}
        )
        serializer.is_valid()
        new_ips.extend(serializer.data)

        paginator = LinkHeaderPagination()
        page = paginator.paginate_queryset(new_ips, request)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response(new_ips)

    def retrieve(self, request, pk=None):
        path = Path.objects.values_list('value', flat=True).get(entity="reception")
        fullpath = os.path.join(path, "%s.xml" % pk)

        if not os.path.exists(fullpath):
            raise exceptions.NotFound

        return Response(parse_submit_description(fullpath, srcdir=path))

    @detail_route(methods=['post'])
    def prepare(self, request, pk=None):
        existing = InformationPackage.objects.filter(object_identifier_value=pk).first()
        if existing is not None:
            raise exceptions.ParseError('IP with id %s already exists: %s' % (pk, str(existing.pk)))

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")
        xmlfile = os.path.join(reception, '%s.xml' % pk)

        if not os.path.isfile(xmlfile):
            return Response(
                {'status': '%s does not exist' % xmlfile},
                status=status.HTTP_400_BAD_REQUEST
            )

        container = os.path.join(reception, self.get_container_for_xml(xmlfile))

        if not os.path.isfile(container):
            return Response(
                {'status': '%s does not exist' % container},
                status=status.HTTP_400_BAD_REQUEST
            )

        objid, container_type = os.path.splitext(os.path.basename(container))
        parsed = parse_submit_description(xmlfile, srcdir=os.path.split(container)[0])

        provided_sa = request.data.get('submission_agreement')
        parsed_sa = parsed.get('altrecordids', {}).get('SUBMISSIONAGREEMENT', [None])[0]

        if parsed_sa is not None and provided_sa is not None:
            if provided_sa == parsed_sa:
                sa = provided_sa
            if provided_sa != parsed_sa:
                raise exceptions.ParseError(detail='Must use SA specified in XML')
        elif parsed_sa and not provided_sa:
            sa = parsed_sa
        elif provided_sa and not parsed_sa:
            sa = provided_sa
        else:
            raise exceptions.ParseError(detail='Missing parameter submission_agreement')

        try:
            sa = SubmissionAgreement.objects.get(pk=sa)
        except (ValueError, SubmissionAgreement.DoesNotExist) as e:
            raise exceptions.ParseError(detail=e.message)

        ip = InformationPackage.objects.create(
            object_identifier_value=pk,
            package_type=InformationPackage.AIP,
            state='Prepared',
            responsible=request.user,
            generation=0,
            submission_agreement=sa,
            submission_agreement_locked=True,
        )

        data = InformationPackageSerializer(ip, context={'request': request}).data
        return Response(data, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'], url_path='receive')
    def receive(self, request, pk=None):
        try:
            ip = get_object_or_404(InformationPackage, id=pk)
        except (ValueError, ValidationError):
            raise exceptions.NotFound('Information package with id="%s" not found' % pk)

        if ip.state != 'Prepared':
            raise exceptions.ParseError('Information package must be in state "Prepared"')

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")

        objid = ip.object_identifier_value
        xmlfile = os.path.join(reception, '%s.xml' % objid)

        if not os.path.isfile(xmlfile):
            return Response(
                {'status': '%s does not exist' % xmlfile},
                status=status.HTTP_400_BAD_REQUEST
            )

        container = os.path.join(reception, self.get_container_for_xml(xmlfile))

        if not os.path.isfile(container):
            return Response(
                {'status': '%s does not exist' % container},
                status=status.HTTP_400_BAD_REQUEST
            )

        container_type = os.path.splitext(os.path.basename(container))[1]
        parsed = parse_submit_description(xmlfile, srcdir=os.path.split(container)[0])

        policy_id = request.data.get('archive_policy')

        try:
            policy = ArchivePolicy.objects.get(pk=policy_id)
        except (ArchivePolicy.DoesNotExist, TypeError):
            msg = 'Archive policy with id %s does not exist' % policy_id
            if policy_id is None:
                msg = 'archive_policy parameter missing'

            raise exceptions.ParseError(msg)

        information_class = parsed.get('information_class', policy.information_class)
        if information_class != policy.information_class:
            raise ValueError('Information class of IP and policy does not match')

        ip.object_path=os.path.join(policy.ingest_path.value, objid)
        ip.policy=policy
        ip.label=parsed.get('label')
        ip.state='Receiving'
        ip.entry_date=parsed.get('create_date')
        ip.start_date=next(iter(parsed['altrecordids'].get('STARTDATE', [])), None)
        ip.end_date=next(iter(parsed['altrecordids'].get('ENDDATE', [])), None)
        ip.information_class=information_class
        ip.save()

        step = ProcessStep.objects.create(
            name="Receive SIP", eager=False,
            information_package=ip,
        )

        validators = request.data.get('validators', {})
        available_validators = [
            'validate_xml_file', 'validate_file_format', 'validate_integrity',
            'validate_logical_physical_representation',
        ]

        if any(v is True and k in available_validators for k,v in validators.iteritems()):
            validation_step = ProcessStep.objects.create(
                name="Validate",
                parent_step=step
            )

            if validators.get('validate_xml_file', False):
                ProcessTask.objects.create(
                    name="workflow.tasks.ValidateXMLFile",
                    params={
                        "xml_filename": xmlfile
                    },
                    log=EventIP,
                    information_package=ip,
                    responsible=self.request.user,
                    processstep=validation_step
                )

            val_format = validators.get("validate_file_format", False)
            val_integrity = validators.get("validate_integrity", False)

            if val_format or val_integrity:
                ProcessTask.objects.create(
                    name="workflow.tasks.ValidateFiles",
                    params={
                        "rootdir": reception,
                        "xmlfile": xmlfile,
                        "validate_fileformat": val_format,
                        "validate_integrity": val_integrity
                    },
                    log=EventIP,
                    information_package=ip,
                    responsible=self.request.user,
                    processstep=validation_step
                )

            files = [container]

            if validators.get('validate_logical_physical_representation'):
                ProcessTask.objects.create(
                    name="workflow.tasks.ValidateLogicalPhysicalRepresentation",
                    params={
                        "files": files,
                        "files_reldir": container,
                        "xmlfile": xmlfile,
                    },
                    log=EventIP,
                    information_package=ip,
                    responsible=self.request.user,
                    processstep=validation_step
                )

        ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            args=[ip.pk, xmlfile, container, policy_id],
            params={
                'purpose': request.data.get('purpose'),
                'allow_unknown_files': request.data.get('allow_unknown_files', False),
                'tags': request.data.get('tags', [])
            },
            log=EventIP,
            information_package=ip,
            responsible=self.request.user,
            processstep=step,
            processstep_pos=0
        )

        sa = ip.submission_agreement

        aip_profile = ProfileSA.objects.get(submission_agreement=sa, profile__profile_type='aip').profile
        mets_dir, mets_name = find_destination("mets_file", aip_profile.structure)
        mets_path = os.path.join(ip.object_path, mets_dir, mets_name)


        filesToCreate = OrderedDict()
        filesToCreate[mets_path] = aip_profile.specification

        try:
            premis_profile = ProfileSA.objects.get(submission_agreement=sa, profile__profile_type='preservation_metadata').profile
        except ProfileSA.DoesNotExist as e:
            pass
        else:
            premis_dir, premis_name = find_destination("preservation_description_file", aip_profile.structure)
            premis_path = os.path.join(ip.object_path, premis_dir, premis_name)
            filesToCreate[premis_path] = premis_profile.specification

        ProcessTask.objects.create(
            name='ESSArch_Core.tasks.GenerateXML',
            params={
                'filesToCreate': filesToCreate,
                'info': aip_profile.specification_data,
                'folderToParse': ip.object_path,
            },
            responsible=request.user,
            information_package=ip,
            processstep=step,
            processstep_pos=3,
        )

        ProcessTask.objects.create(
            name="ESSArch_Core.tasks.UpdateIPSizeAndCount",
            args=[ip.pk],
            log=EventIP,
            information_package=ip,
            responsible=self.request.user,
            processstep=step,
            processstep_pos=5,
        )

        ProcessTask.objects.create(
            name='ESSArch_Core.tasks.UpdateIPStatus',
            args=[ip.pk],
            params={
                'status': 'Received',
                'prev': 'Receiving'
            },
            log=EventIP,
            information_package=ip,
            responsible=self.request.user,
            processstep=step,
            processstep_pos=10
        )

        step.run()

        return Response('Receiving %s...' % container)

    @detail_route(methods=['get'])
    def files(self, request, pk=None):
        mimetypes.suffix_map = {}
        mimetypes.encodings_map = {}
        mimetypes.types_map = {}
        mimetypes.common_types = {}
        mimetypes_file = Path.objects.get(
            entity="path_mimetypes_definitionfile"
        ).value
        mimetypes.init(files=[mimetypes_file])
        mtypes = mimetypes.types_map

        reception = Path.objects.get(entity="reception").value
        xml = os.path.join(reception, "%s.xml" % pk)

        if not os.path.exists(xml):
            raise exceptions.NotFound

        ip = parse_submit_description(xml, srcdir=reception)
        container = ip['object_path']

        path = request.query_params.get('path')

        if path is not None:
            path = path.rstrip('/ ')

        if path is not None and path.startswith(os.path.basename(container)):
            fullpath = os.path.join(os.path.dirname(container), path)
            if tarfile.is_tarfile(container):
                with tarfile.open(container) as tar:
                    if fullpath == container:
                        entries = []
                        for member in tar.getmembers():
                            if not member.isfile():
                                continue

                            entries.append({
                                "name": member.name,
                                "type": 'file',
                                "size": member.size,
                                "modified": timestamp_to_datetime(member.mtime),
                            })
                        return Response(entries)
                    else:
                        subpath = fullpath[len(container)+1:]
                        try:
                            member = tar.getmember(subpath)

                            if not member.isfile():
                                raise exceptions.NotFound

                            f = tar.extractfile(member)
                            content_type = mtypes.get(os.path.splitext(subpath)[1])
                            response = HttpResponse(f.read(), content_type=content_type)
                            response['Content-Disposition'] = 'inline; filename="%s"' % os.path.basename(f.name)
                            if content_type is None:
                                response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f.name)
                            return response
                        except KeyError:
                            raise exceptions.NotFound

            elif zipfile.is_zipfile(container):
                with zipfile.ZipFile(container) as zipf:
                    if fullpath == container:
                        entries = []
                        for member in zipf.filelist:
                            if member.filename.endswith('/'):
                                continue

                            entries.append({
                                "name": member.filename,
                                "type": 'file',
                                "size": member.file_size,
                                "modified": datetime.datetime(*member.date_time),
                            })
                        return Response(entries)
                    else:
                        subpath = fullpath[len(container)+1:]
                        try:
                            f = zipf.open(subpath)
                            content_type = mtypes.get(os.path.splitext(subpath)[1])
                            response = HttpResponse(f.read(), content_type=content_type)
                            response['Content-Disposition'] = 'inline; filename="%s"' % os.path.basename(f.name)
                            if content_type is None:
                                response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f.name)
                            return response
                        except KeyError:
                            raise exceptions.NotFound
        elif path in [os.path.basename(container), os.path.basename(xml)]:
            fullpath = os.path.join(os.path.dirname(container), path)
            content_type = mtypes.get(os.path.splitext(fullpath)[1])
            response = HttpResponse(open(fullpath).read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename="%s"' % os.path.basename(fullpath)
            if content_type is None:
                response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(fullpath)
            return response
        elif path is not None:
            raise exceptions.NotFound

        entry = {
            "name": os.path.basename(container),
            "type": 'file',
            "size": os.path.getsize(container),
            "modified": timestamp_to_datetime(os.path.getmtime(container)),
        }

        xmlentry = {
            "name": os.path.basename(xml),
            "type": 'file',
            "size": os.path.getsize(xml),
            "modified": timestamp_to_datetime(os.path.getmtime(xml)),
        }
        return Response([entry, xmlentry])


    @list_route(methods=['post'])
    def upload(self, request):
        if not request.user.has_perm('ip.can_receive_remote_files'):
            raise exceptions.PermissionDenied

        path = Path.objects.get(entity="reception").value

        f = request.FILES['the_file']
        content_range = request.META.get('HTTP_CONTENT_RANGE', 'bytes 0-0/0')
        filename = os.path.join(path, f.name)

        (start, end, total) = parse_content_range_header(content_range)

        if f.size != end - start + 1:
            raise exceptions.ParseError("File size doesn't match headers")

        if start == 0:
            with open(filename, 'wb') as dstf:
                dstf.write(f.read())
        else:
            with open(filename, 'ab') as dstf:
                dstf.seek(start)
                dstf.write(f.read())

        upload_id = request.data.get('upload_id', uuid.uuid4().hex)
        return Response({'upload_id': upload_id})

    @list_route(methods=['post'])
    def upload_complete(self, request):
        if not request.user.has_perm('ip.can_receive_remote_files'):
            raise exceptions.PermissionDenied

        path = Path.objects.get(entity="reception").value

        md5 = request.data['md5']
        filepath = request.data['path']
        filepath = os.path.join(path, filepath)

        ProcessTask.objects.create(
            name="ESSArch_Core.tasks.ValidateIntegrity",
            params={
                "filename": filepath,
                "checksum": md5,
                "algorithm": 'MD5'
            },
            responsible=self.request.user,
        ).run().get()

        return Response('Upload of %s complete' % filepath)


class InformationPackageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows information packages to be viewed or edited.
    """
    queryset = InformationPackage.objects.all()
    filter_class = InformationPackageFilter
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'label', 'responsible', 'create_date', 'state', 'eventDateTime',
        'eventType', 'eventOutcomeDetailNote', 'eventOutcome',
        'linkingAgentIdentifierValue', 'id', 'object_identifier_value',
    )
    search_fields = (
        'object_identifier_value','aic__information_packages__object_identifier_value','information_packages__object_identifier_value',
        'label','aic__information_packages__label','information_packages__label',
        'responsible__first_name','aic__information_packages__responsible__first_name','information_packages__responsible__first_name',
        'responsible__last_name','aic__information_packages__responsible__last_name','information_packages__responsible__last_name',
        'responsible__username','aic__information_packages__responsible__username','information_packages__responsible__username',
        'state','aic__information_packages__state','information_packages__state',
        'submission_agreement__name','aic__information_packages__submission_agreement__name','information_packages__submission_agreement__name',
        'start_date','aic__information_packages__start_date','information_packages__start_date',
        'end_date','aic__information_packages__end_date','information_packages__end_date',
    )

    def get_permissions(self):
        if self.action in ['partial_update', 'update']:
            if self.request.data.get('submission_agreement'):
                self.permission_classes = [CanChangeSA]
        if self.action == 'destroy':
            self.permission_classes = [CanDeleteIP]

        return super(InformationPackageViewSet, self).get_permissions()

    def update(self, request, *args, **kwargs):
        ip = self.get_object()

        if 'submission_agreement' in request.data:
            if ip.submission_agreement_locked:
                return Response("SA connected to IP is locked", status=status.HTTP_400_BAD_REQUEST)

        return super(InformationPackageViewSet, self).update(request, *args, **kwargs)

    def get_queryset(self):
        view_type = self.request.query_params.get('view_type', 'aic')

        if self.action == 'list':
            if view_type == 'ip':
                return self.queryset.exclude(
                    package_type=InformationPackage.AIC,
                ).filter(
                    Q(package_type=InformationPackage.AIP, generation=0) |
                    ~Q(package_type=InformationPackage.AIP)
                )

            return self.queryset.filter(aic__isnull=True)

        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return NestedInformationPackageSerializer

        return InformationPackageDetailSerializer

    def get_serializer_context(self):
        context = super(InformationPackageViewSet, self).get_serializer_context()
        context['view'] = self
        return context

    def get_permissions(self):
        if self.action == 'destroy':
            self.permission_classes = [CanDeleteIP]

        return super(InformationPackageViewSet, self).get_permissions()

    def destroy(self, request, pk=None):
        ip = self.get_object()

        if ip.archived:
            raise exceptions.ParseError(detail='Archived IPs cannot be deleted')

        self.check_object_permissions(request, ip)
        path = ip.object_path

        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno == errno.ENOTDIR:
                no_ext = os.path.splitext(path)[0]

                for fl in glob.glob(no_ext + "*"):
                    try:
                        os.remove(fl)
                    except:
                        raise
            elif e.errno == errno.ENOENT:
                pass
            else:
                raise

        return super(InformationPackageViewSet, self).destroy(request, pk=pk)

    @detail_route(methods=['post'], url_path='preserve')
    def preserve(self, request, pk=None):
        ip = self.get_object()

        if ip.package_type == InformationPackage.DIP:
            policy = request.data.get('policy')

            if not policy:
                return Response('Policy required', status=status.HTTP_400_BAD_REQUEST)

            try:
                ip.policy = ArchivePolicy.objects.get(pk=policy)
            except ArchivePolicy.DoesNotExist:
                return Response('Policy "%s" does not exist' % policy, status=status.HTTP_400_BAD_REQUEST)
            except ValueError as e:
                raise exceptions.ParseError(e.message)

            ip.save(update_fields=['policy'])

        main_step = ProcessStep.objects.create(
            name='Preserve AIP',
            information_package_id=pk,
            eager=False,
        )
        tasks = []

        tasks.append(ProcessTask(
            name='workflow.tasks.CacheAIP',
            params={'aip': pk},
            processstep=main_step,
            processstep_pos=10,
            responsible=self.request.user,
        ))

        tasks.append(ProcessTask(
            name='workflow.tasks.StoreAIP',
            params={'aip': pk},
            processstep=main_step,
            processstep_pos=20,
            responsible=self.request.user,
        ))

        ProcessTask.objects.bulk_create(tasks)

        main_step.run()

        return Response(['Preserving IP %s...' % pk])

    @detail_route(methods=['post'])
    def access(self, request, pk=None):
        data = request.data

        options = ['tar', 'extracted', 'new']

        if not any(x in options for x in data.keys()):
            return Response('No option set', status=status.HTTP_400_BAD_REQUEST)

        if not any(v for k, v in data.iteritems() if k in options):
            return Response('Need atleast one option set to true', status=status.HTTP_400_BAD_REQUEST)

        if Workarea.objects.filter(user=request.user, ip_id=pk, type=Workarea.ACCESS).exists():
            return Response('IP already in workarea', status=status.HTTP_400_BAD_REQUEST)

        step = ProcessStep.objects.create(
            name='Access AIP', eager=False,
            information_package_id=pk,
        )
        task = ProcessTask.objects.create(
            name='workflow.tasks.AccessAIP',
            params={
                'aip': pk,
                'tar': data.get('tar', False),
                'extracted': data.get('extracted', False),
                'new': data.get('new', False),
                'object_identifier_value': data.get('object_identifier_value'),
            },
            responsible=self.request.user,
            eager=False,
            processstep=step,
        )

        step.run()

        return Response(['Accessing AIP %s...' % pk])

    @detail_route(methods=['post'], url_path='create-dip')
    def create_dip(self, request, pk=None):
        dip = InformationPackage.objects.get(pk=pk)

        if dip.package_type != InformationPackage.DIP:
            return Response(
                {'status': '"%s" is not a DIP, it is a %s' % (dip, dip.package_type)},
                status=status.HTTP_400_BAD_REQUEST
            )

        if dip.state != 'Prepared':
            return Response(
                {'status': '"%s" is not in the "Prepared" state'},
                status=status.HTTP_400_BAD_REQUEST
            )

        step = ProcessStep.objects.create(
            name="Create DIP",
            eager=False,
            information_package=dip,
        )

        task = ProcessTask.objects.create(
            name="workflow.tasks.CreateDIP",
            params={
                'ip': str(dip.pk),
            },
            processstep=step,
            information_package=dip,
            responsible=request.user,
            eager=False,
        )

        task.run()

        return Response()

    @list_route(methods=['post'], url_path='prepare-dip')
    def prepare_dip(self, request):
        try:
            label = request.data['label']
        except KeyError:
            return Response(
                {'status': '"label" is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        object_identifier_value = request.data.get('object_identifier_value')

        if object_identifier_value:
            ip_exists = InformationPackage.objects.filter(object_identifier_value=object_identifier_value).exists()
            if ip_exists:
                return Response(
                    {'status': 'IP with object identifer value "%s" already exists' % object_identifier_value},
                    status=status.HTTP_400_BAD_REQUEST
                )

        orders = request.data.get('orders', [])

        for order in orders:
            if not Order.objects.filter(pk=order, responsible=request.user).exists():
                return Response(
                    {'status': 'Order "%s" belonging to current user does not exist' % order},
                    status=status.HTTP_400_BAD_REQUEST
                )

        main_step = ProcessStep.objects.create(name='Prepare DIP',)
        task = ProcessTask.objects.create(
            name='workflow.tasks.PrepareDIP',
            params={
                'label': label,
                'object_identifier_value': object_identifier_value,
                'orders': orders
            },
            processstep=main_step,
            responsible=self.request.user,
        )

        dip = task.run().get()

        return Response(dip, status.HTTP_201_CREATED)

    @detail_route()
    def events(self, request, pk=None):
        ip = self.get_object()
        events = filters.OrderingFilter().filter_queryset(request, ip.events.all(), self)
        page = self.paginate_queryset(events)
        if page is not None:
            serializers = EventIPSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializers.data)
        serializers = EventIPSerializer(events, many=True, context={'request': request})
        return Response(serializers.data)

    @detail_route()
    def steps(self, request, pk=None):
        ip = self.get_object()
        steps = ip.steps.all()
        serializer = ProcessStepSerializer(
            data=steps, many=True, context={'request': request}
        )
        serializer.is_valid()
        return Response(serializer.data)

    @detail_route(methods=['delete', 'get', 'post'])
    def files(self, request, pk=None):
        ip = self.get_object()

        if ip.archived:
            return Response('%s is archived' % ip, status=status.HTTP_400_BAD_REQUEST)

        if request.method == 'DELETE':
            try:
                path = request.data['path']
            except KeyError:
                return Response('Path parameter missing', status=status.HTTP_400_BAD_REQUEST)

            root = ip.object_path
            fullpath = os.path.join(root, path)

            if not in_directory(fullpath, ip.object_path):
                raise exceptions.ParseError('Illegal path %s' % path)

            try:
                shutil.rmtree(fullpath)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    raise exceptions.NotFound('Path does not exist')

                if e.errno != errno.ENOTDIR:
                    raise

                os.remove(fullpath)

            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == 'POST':
            try:
                path = request.data['path']
            except KeyError:
                return Response('Path parameter missing', status=status.HTTP_400_BAD_REQUEST)

            try:
                pathtype = request.data['type']
            except KeyError:
                return Response('Type parameter missing', status=status.HTTP_400_BAD_REQUEST)

            root = ip.object_path
            fullpath = os.path.join(root, path)

            if not in_directory(fullpath, root):
                raise exceptions.ParseError('Illegal path %s' % path)

            if pathtype == 'dir':
                try:
                    os.makedirs(fullpath)
                except OSError as e:
                    if e.errno == errno.EEXIST:
                        raise exceptions.ParseError('Directory %s already exists' % path)

                    raise
            elif pathtype == 'file':
                open(fullpath, 'a').close()
            else:
                return Response('Type must be either "file" or "dir"', status=status.HTTP_400_BAD_REQUEST)

            return Response(path, status=status.HTTP_201_CREATED)

        return ip.files(request.query_params.get('path', '').rstrip('/'))

    @detail_route(methods=['put'], url_path='check-profile')
    def check_profile(self, request, pk=None):
        ip = self.get_object()
        ptype = request.data.get("type")

        pip = get_object_or_404(ProfileIP, ip=ip, profile__profile_type=ptype)

        if not pip.LockedBy:
            pip.included = request.data.get('checked', not pip.included)
            pip.save()

        return Response()

    @detail_route(methods=['put'], url_path='change-profile')
    def change_profile(self, request, pk=None):
        ip = self.get_object()

        try:
            new_profile = get_object_or_404(Profile, pk=request.data.get("new_profile"))
        except ValueError:
            raise exceptions.NotFound

        try:
            ip.change_profile(new_profile)
        except ValueError as e:
            return Response({'status': e.message}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'updating IP (%s) with new profile (%s)' % (
                ip.pk, new_profile
            )
        })

    @detail_route(methods=['post'], url_path='unlock-profile', permission_classes=[CanUnlockProfile])
    def unlock_profile(self, request, pk=None):
        ip = self.get_object()

        if ip.state in ['Submitting', 'Submitted']:
            raise exceptions.ParseError('Cannot unlock profiles in an IP that is %s' % ip.state)

        try:
            ptype = request.data["type"]
        except KeyError:
            raise exceptions.ParseError('type parameter missing')

        ip.unlock_profile(ptype)

        return Response({
            'status': 'unlocking profile with type "%s" in IP "%s"' % (
                ptype, ip.pk
            )
        })


class WorkareaViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InformationPackage.objects.all()
    filter_class = InformationPackageFilter
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'label', 'responsible', 'create_date', 'state', 'eventDateTime',
        'eventType', 'eventOutcomeDetailNote', 'eventOutcome',
        'linkingAgentIdentifierValue', 'id'
    )
    search_fields = (
        'object_identifier_value','aic__information_packages__object_identifier_value','information_packages__object_identifier_value',
        'label','aic__information_packages__label','information_packages__label',
        'responsible__first_name','aic__information_packages__responsible__first_name','information_packages__responsible__first_name',
        'responsible__last_name','aic__information_packages__responsible__last_name','information_packages__responsible__last_name',
        'responsible__username','aic__information_packages__responsible__username','information_packages__responsible__username',
        'state','aic__information_packages__state','information_packages__state',
        'submission_agreement__name','aic__information_packages__submission_agreement__name','information_packages__submission_agreement__name',
        'start_date','aic__information_packages__start_date','information_packages__start_date',
        'end_date','aic__information_packages__end_date','information_packages__end_date',
    )
    serializer_class = WorkareaSerializer

    def get_serializer_context(self):
        context = super(WorkareaViewSet, self).get_serializer_context()
        context['view'] = self
        return context

    def get_queryset(self):
        try:
            query_wtype = self.request.query_params['type'].lower()
        except KeyError:
            return self.queryset.filter(
                workareas__user=self.request.user,
            )

        workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

        try:
            workarea_type = workarea_type_reverse[query_wtype]
        except KeyError:
            raise exceptions.ParseError('Workarea of type "%s" does not exist' % query_wtype)

        view_type = self.request.query_params.get('view_type', 'aic')

        if view_type == 'aic':
            return self.queryset.filter(
                aic__isnull=True,
                information_packages__workareas__user=self.request.user,
                information_packages__workareas__type=workarea_type
            )

        self.queryset = self.queryset.exclude(
            package_type=InformationPackage.AIC,
        ).filter(generation=0)

        return self.queryset.filter(
            Q(
                workareas__user=self.request.user,
                workareas__type=workarea_type
            ) | Q(
                aic__information_packages__workareas__user=self.request.user,
                aic__information_packages__workareas__type=workarea_type
            )
        ).only('id').distinct()

class WorkareaFilesViewSet(viewsets.ViewSet):
    def validate_workarea(self, area_type):
        workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

        try:
            workarea_type_reverse[area_type]
        except KeyError:
            raise exceptions.ParseError('Workarea of type "%s" does not exist' % area_type)

    def validate_path(self, path, root):
        if not in_directory(path, root):
            raise exceptions.ParseError('Illegal path %s' % path)

        if not os.path.exists(path):
            raise exceptions.ParseError('Path "%s" does not exist' % path)

    def list(self, request):
        try:
            workarea = self.request.query_params['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea).value, str(request.user.pk))

        entries = []
        path = os.path.join(root, request.query_params.get('path', ''))

        self.validate_path(path, root)

        if os.path.isfile(path):
            raise exceptions.ParseError('Path "%s" is a file' % path)

        for entry in get_files_and_dirs(path):
            entry_type = "dir" if entry.is_dir() else "file"

            if entry_type == 'file' and re.search(r'\_\d+$', entry.name) is not None:  # file chunk
                continue

            size, _ = get_tree_size_and_count(entry.path)

            entries.append(
                {
                    "name": os.path.basename(entry.path),
                    "type": entry_type,
                    "size": size,
                    "modified": timestamp_to_datetime(entry.stat().st_mtime),
                }
            )

        sorted_entries = sorted(entries, key=itemgetter('name'))
        return Response(sorted_entries)

    @list_route(methods=['post'], url_path='add-to-dip')
    def add_to_dip(self, request):
        try:
            workarea = self.request.data['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea).value, str(request.user.pk))

        try:
            dip = self.request.data['dip']
            ip = InformationPackage.objects.get(pk=dip, package_type=InformationPackage.DIP)

            permission = IsResponsibleOrReadOnly()
            if not permission.has_object_permission(request, self, ip):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )
        except KeyError:
            raise exceptions.ParseError('Missing dip parameter')
        except InformationPackage.DoesNotExist:
            raise exceptions.ParseError('DIP "%s" does not exist' % dip)

        try:
            src = self.request.data['src']
        except KeyError:
            raise exceptions.ParseError('Missing src parameter')

        try:
            dst = self.request.data['dst']
        except KeyError:
            raise exceptions.ParseError('Missing dst parameter')

        src = os.path.join(root, src)
        self.validate_path(src, root)

        dst = os.path.join(ip.object_path, dst)

        if os.path.isfile(src) and os.path.isdir(dst):
            dst = os.path.join(dst, os.path.basename(src))
            shutil.copy2(src, dst)
        else:
            try:
                shutil.copytree(src, dst)
            except OSError as e:
                if e.errno == errno.ENOTDIR:
                    shutil.copy2(src, dst)
                elif e.errno == errno.EEXIST:
                    shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    raise

        return Response(root)


class OrderViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows orders to be viewed or edited.
    """
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsOrderResponsibleOrAdmin]

    def get_queryset(self):
        if self.action == 'list':
            if self.request.user.is_superuser:
                return self.queryset

            return self.queryset.filter(responsible=self.request.user)

        return self.queryset

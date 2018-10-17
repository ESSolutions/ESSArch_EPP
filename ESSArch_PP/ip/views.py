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

import copy
import errno
import glob
import logging
import math
import os
import re
import shutil
import uuid

import six
from celery import states as celery_states
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import BooleanField, Case, Exists, Max, Min, OuterRef, Prefetch, Q, Subquery, Value, When
from django_filters.constants import EMPTY_VALUES
from elasticsearch.exceptions import TransportError
from elasticsearch_dsl import Index, Search
from elasticsearch_dsl import Q as ElasticQ
from groups_manager.utils import get_permission_name
from guardian.core import ObjectPermissionChecker
from guardian.shortcuts import assign_perm
from lxml import etree
from natsort import natsorted
from rest_framework import exceptions, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask
from ESSArch_Core.WorkflowEngine.util import create_workflow
from ESSArch_Core.auth.decorators import permission_required_or_403
from ESSArch_Core.auth.models import Member
from ESSArch_Core.configuration.models import ArchivePolicy, Path
from ESSArch_Core.essxml.util import get_objectpath, parse_submit_description
from ESSArch_Core.exceptions import Conflict
from ESSArch_Core.fixity.format import FormatIdentifier
from ESSArch_Core.fixity.validation.backends.checksum import ChecksumValidator
from ESSArch_Core.ip.filters import WorkareaEntryFilter
from ESSArch_Core.ip.models import Agent, EventIP, InformationPackage, Order, Workarea
from ESSArch_Core.ip.permissions import CanUnlockProfile, IsOrderResponsibleOrAdmin, \
    IsResponsibleOrReadOnly
from ESSArch_Core.ip.views import InformationPackageViewSet as InformationPackageViewSetCore
from ESSArch_Core.maintenance.models import AppraisalRule, ConversionRule
from ESSArch_Core.mixins import PaginatedViewMixin
from ESSArch_Core.profiles.models import ProfileIP, SubmissionAgreement
from ESSArch_Core.search import DEFAULT_MAX_RESULT_WINDOW
from ESSArch_Core.tags.models import TagStructure
from ESSArch_Core.util import generate_file_response, in_directory, list_files, mkdir_p, normalize_path, parse_content_range_header, \
    remove_prefix, timestamp_to_datetime

from .filters import InformationPackageFilter
from .serializers import InformationPackageDetailSerializer, InformationPackageSerializer, \
    NestedInformationPackageSerializer, OrderSerializer

User = get_user_model()


class InformationPackageReceptionViewSet(viewsets.ViewSet, PaginatedViewMixin):
    search_fields = (
        'object_identifier_value', 'label', 'responsible__first_name',
        'responsible__last_name', 'responsible__username', 'state',
        'submission_agreement__name', 'start_date', 'end_date',
    )

    def get_queryset(self):
        user = self.request.user
        return InformationPackage.objects.visible_to_user(user).filter(
            state='Prepared', package_type=InformationPackage.AIP)

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
            try:
                container = os.path.join(path, self.get_container_for_xml(xmlfile))
            except etree.LxmlError:
                continue

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
                         "create_date", "object_size", "start_date", "end_date"]

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")

        contained = self.get_contained_packages(reception)
        extracted = self.get_extracted_packages(reception)
        ips = contained + extracted

        # Remove all keys not in filter_fields
        conditions = {key: value for (key, value) in six.iteritems(request.query_params) if key in filter_fields}

        # Filter ips based on conditions
        new_ips = list(filter(lambda ip: all((v in str(ip.get(k)) for (k, v) in six.iteritems(conditions))), ips))

        from_db = InformationPackage.objects.visible_to_user(request.user).filter(package_type=InformationPackage.AIP,
                                                    state__in=['Prepared', 'Receiving'], **conditions)
        serializer = InformationPackageSerializer(
            data=from_db, many=True, context={'request': request, 'view': self}
        )
        serializer.is_valid()
        new_ips.extend(serializer.data)

        if self.paginator is not None:
            paginated = self.paginator.paginate_queryset(new_ips, request)
            return self.paginator.get_paginated_response(paginated)

        return Response(new_ips)

    def retrieve(self, request, pk=None):
        path = Path.objects.values_list('value', flat=True).get(entity="reception")
        fullpath = os.path.join(path, "%s.xml" % pk)

        if not os.path.exists(fullpath):
            raise exceptions.NotFound

        return Response(parse_submit_description(fullpath, srcdir=path))

    @transaction.atomic
    @detail_route(methods=['post'])
    def prepare(self, request, pk=None):
        logger = logging.getLogger('essarch.epp.ingest')
        perms = copy.deepcopy(getattr(settings, 'IP_CREATION_PERMS_MAP', {}))

        existing = InformationPackage.objects.filter(object_identifier_value=pk).first()
        organization = request.user.user_profile.current_organization

        if organization is None:
            raise exceptions.ParseError('You must be part of an organization to prepare an IP')

        if existing is not None:
            logger.warn('Tried to prepare IP with id %s which already exists' % pk, extra={'user': request.user.pk})
            raise exceptions.ParseError('IP with id %s already exists: %s' % (pk, str(existing.pk)))

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")
        xmlfile = normalize_path(os.path.join(reception, '%s.xml' % pk))

        if not os.path.isfile(xmlfile):
            logger.warn('Tried to prepare IP with missing XML file %s' % xmlfile, extra={'user': request.user.pk})
            raise exceptions.ParseError('%s does not exist' % xmlfile)

        try:
            container = normalize_path(os.path.join(reception, self.get_container_for_xml(xmlfile)))
        except etree.LxmlError:
            logger.warn('Tried to prepare IP with invalid XML file %s' % xmlfile, extra={'user': request.user.pk})
            raise exceptions.ParseError('Invalid XML file, %s' % xmlfile)

        if not os.path.isfile(container):
            logger.warn('Tried to prepare IP with missing container file %s' % container, extra={'user': request.user.pk})
            raise exceptions.ParseError('%s does not exist' % container)

        parsed = parse_submit_description(xmlfile, srcdir=os.path.dirname(container))
        provided_sa = request.data.get('submission_agreement')
        parsed_sa = parsed.get('altrecordids', {}).get('SUBMISSIONAGREEMENT', [None])[0]

        if parsed_sa is not None and provided_sa is not None:
            if provided_sa == parsed_sa:
                sa = provided_sa
            else:
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

        if sa.profile_aic_description is None:
            raise exceptions.ParseError('Submission agreement missing AIC Description profile')

        if sa.profile_aip is None:
            raise exceptions.ParseError('Submission agreement missing AIP profile')

        if sa.profile_aip_description is None:
            raise exceptions.ParseError('Submission agreement missing AIP Description profile')

        if sa.profile_dip is None:
            raise exceptions.ParseError('Submission agreement missing DIP profile')

        ip = InformationPackage.objects.create(
            object_identifier_value=pk,
            sip_objid=pk,
            sip_path=pk,
            package_type=InformationPackage.AIP,
            state='Prepared',
            responsible=request.user,
            submission_agreement=sa,
            submission_agreement_locked=True,
            object_path=container,
            package_mets_path=xmlfile,
        )
        ip.save()

        # refresh date fields to convert them to datetime instances instead of
        # strings to allow further datetime manipulation
        ip.refresh_from_db(fields=['entry_date', 'start_date', 'end_date'])

        member = Member.objects.get(django_user=request.user)
        user_perms = perms.pop('owner', [])

        organization.assign_object(ip, custom_permissions=perms)
        organization.add_object(ip)

        for perm in user_perms:
            perm_name = get_permission_name(perm, ip)
            assign_perm(perm_name, member.django_user, ip)

        p_types = ['aic_description', 'aip', 'aip_description', 'content_type', 'dip', 'preservation_metadata']
        ip.create_profile_rels(p_types, request.user)

        data = InformationPackageDetailSerializer(ip, context={'request': request}).data

        logger.info('Prepared information package %s' % str(ip.pk), extra={'user': request.user.pk})
        return Response(data, status=status.HTTP_201_CREATED)

    @permission_required_or_403(['ip.receive'])
    @detail_route(methods=['post'], url_path='receive')
    def receive(self, request, pk=None):
        try:
            ip = get_object_or_404(self.get_queryset(), id=pk)
        except (ValueError, ValidationError):
            raise exceptions.NotFound('Information package with id="%s" not found' % pk)

        logger = logging.getLogger('essarch.epp.ingest')

        if ip.state != 'Prepared':
            logger.warn('Tried to receive IP %s from reception which is in state "%s"' % (pk, ip.state), extra={'user': request.user.pk})
            raise exceptions.ParseError('Information package must be in state "Prepared"')

        for profile_ip in ProfileIP.objects.filter(ip=ip).iterator():
            try:
                profile_ip.clean()
            except ValidationError as e:
                raise exceptions.ParseError('%s: %s' % (profile_ip.profile.name, e[0]))

            profile_ip.LockedBy = request.user
            profile_ip.save()

        reception = Path.objects.values_list('value', flat=True).get(entity="reception")

        objid = ip.object_identifier_value
        xmlfile = os.path.join(reception, '%s.xml' % objid)

        if not os.path.isfile(xmlfile):
            logger.warn('Tried to receive IP %s from reception with missing XML file %s' % (pk, xmlfile), extra={'user': request.user.pk})
            raise exceptions.ParseError('%s does not exist' % xmlfile)

        container = os.path.join(reception, self.get_container_for_xml(xmlfile))
        if not os.path.isfile(container):
            logger.warn('Tried to receive IP %s from reception with missing container file %s' % (pk, container), extra={'user': request.user.pk})
            raise exceptions.ParseError('%s does not exist' % container)

        try:
            policy_id = request.data.get('archive_policy')
            policy = ArchivePolicy.objects.get(pk=policy_id)
        except (ArchivePolicy.DoesNotExist, TypeError):
            msg = 'Archive policy with id %s does not exist' % policy_id
            raise exceptions.ParseError(msg)

        tag_id = request.data.get('tag')
        if tag_id is not None:
            if ip.get_archive_tag() is not None:
                raise exceptions.ParseError('Cannot set tag on IP that has content_type with archive reference')

            try:
                ip.tag = TagStructure.objects.get(pk=tag_id)
            except TagStructure.DoesNotExist:
                raise exceptions.ParseError('Tag "{id}" does not exist'.format(id=tag_id))
        elif tag_id is None and ip.get_archive_tag() is None:
            raise exceptions.ParseError('No archive selected for IP')

        ip.tag = ip.get_archive_tag()
        ip.policy = policy
        ip.save()

        generate_premis = ip.profile_locked('preservation_metadata')

        validators = request.data.get('validators', {})
        validate_xml_file = validators.get('validate_xml_file', False)
        validate_logical_physical_representation = validators.get('validate_logical_physical_representation', False)

        workflow_spec = [
            {
                "name": "ESSArch_Core.tasks.UpdateIPStatus",
                "label": "Set status to receiving",
                "args": ["Receiving"],
            },
            {
                "step": True,
                "name": "Receive SIP",
                "children": [
                    {
                        "step": True,
                        "name": "Validation",
                        "if": any([validate_xml_file, validate_logical_physical_representation]),
                        "children": [
                            {
                                "name": "ESSArch_Core.tasks.ValidateXMLFile",
                                "if": validate_xml_file,
                                "label": "Validate package-mets",
                                "params": {
                                    "xml_filename": "{{_PACKAGE_METS_PATH}}",
                                }
                            },
                            {
                                "name": "ESSArch_Core.tasks.ValidateLogicalPhysicalRepresentation",
                                "if": validate_logical_physical_representation,
                                "label": "Diff-check against package-mets",
                                "args": ["{{_OBJPATH}}", "{{_PACKAGE_METS_PATH}}"],
                            },
                        ]
                    },
                    {
                        "step": True,
                        "name": "Generate AIP",
                        "children": [
                            {
                                "name": "ESSArch_Core.ip.tasks.ParseSubmitDescription",
                                "label": "Parse submit description",
                            },
                            {
                                "name": "ESSArch_Core.ip.tasks.ParseEvents",
                                "label": "Parse events",
                            },
                            {
                                "name": "ESSArch_Core.ip.tasks.CreatePhysicalModel",
                                "label": "Create Physical Model",
                                'params': {'root': '{{POLICY_INGEST_PATH}}/{{_OBJID}}'}
                            },
                            {
                                "name": "workflow.tasks.ReceiveSIP",
                                "label": "Receive SIP",
                                "params": {
                                    'purpose': request.data.get('purpose'),
                                    'allow_unknown_files': request.data.get('allow_unknown_files', False),
                                }
                            },
                            {
                                "name": "ESSArch_Core.ip.tasks.GeneratePremis",
                                "if": generate_premis,
                                "label": "Generate premis",
                            },
                            {
                                "name": "ESSArch_Core.ip.tasks.GenerateContentMets",
                                "label": "Generate content-mets",
                            },
                        ]
                    },
                    {
                        "step": True,
                        "name": "Validate AIP",
                        "children": [
                            {
                                "name": "ESSArch_Core.tasks.ValidateXMLFile",
                                "label": "Validate content-mets",
                                "params": {
                                    "xml_filename": "{{_CONTENT_METS_PATH}}",
                                }
                            },
                            {
                                "name": "ESSArch_Core.tasks.ValidateXMLFile",
                                "if": generate_premis,
                                "label": "Validate premis",
                                "params": {
                                    "xml_filename": "{{_PREMIS_PATH}}",
                                }
                            },
                            {
                                "name": "ESSArch_Core.tasks.ValidateLogicalPhysicalRepresentation",
                                "label": "Diff-check against content-mets",
                                "args": ["{{_OBJPATH}}", "{{_CONTENT_METS_PATH}}"],
                            },
                            {
                                "name": "ESSArch_Core.tasks.CompareXMLFiles",
                                "if": generate_premis,
                                "label": "Compare premis and content-mets",
                                "args": ["{{_PREMIS_PATH}}", "{{_CONTENT_METS_PATH}}"],
                            }
                        ]
                    },
                    {
                        "name": "ESSArch_Core.tasks.UpdateIPSizeAndCount",
                        "label": "Update IP size and file count",
                    },
                    {
                        "name": "ESSArch_Core.tasks.UpdateIPStatus",
                        "label": "Set status to received",
                        "args": ["Received"],
                    },
                ]
            },
        ]
        workflow = create_workflow(workflow_spec, ip)
        workflow.name = "Receive SIP"
        workflow.information_package = ip
        workflow.save()
        workflow.run()
        logger.info('Started receiving {objid} from reception'.format(objid=objid), extra={'user': request.user.pk})
        return Response({'detail': 'Receiving %s...' % objid})

    @detail_route(methods=['get'])
    def files(self, request, pk=None):
        reception = Path.objects.get(entity="reception").value
        xml = os.path.join(reception, "%s.xml" % pk)

        if not os.path.exists(xml):
            raise exceptions.NotFound

        ip = parse_submit_description(xml, srcdir=reception)
        container = ip['object_path']

        path = request.query_params.get('path', '').rstrip('/ ')
        download = request.query_params.get('download', False)

        if len(path):
            path = os.path.join(os.path.dirname(container), path)
            return list_files(path, download, paginator=self.paginator, request=request)

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

        options = {'expected': md5, 'algorithm': 'md5'}
        validator = ChecksumValidator(context='checksum_str', options=options)
        validator.validate(filepath)
        return Response({'detail': 'Upload of %s complete' % filepath})


class InformationPackageViewSet(InformationPackageViewSetCore):
    """
    API endpoint that allows information packages to be viewed or edited.
    """
    queryset = InformationPackage.objects.select_related('responsible').prefetch_related(
        Prefetch('agents', queryset=Agent.objects.prefetch_related('notes'), to_attr='prefetched_agents'), 'steps')

    def first_generation_case(self, lower_higher):
        return Case(
            When(aic__isnull=True, then=Value(1)),
            When(generation=Subquery(lower_higher.values('min_gen')[:1]),
                 then=Value(1)),
            default=Value(0),
            output_field=BooleanField(),
        )

    def last_generation_case(self, lower_higher):
        return Case(
            When(aic__isnull=True, then=Value(1)),
            When(generation=Subquery(lower_higher.values('max_gen')[:1]),
                 then=Value(1)),
            default=Value(0),
            output_field=BooleanField(),
        )

    def get_queryset(self):
        view_type = self.request.query_params.get('view_type', 'aic')
        user = self.request.user
        see_all = self.request.user.has_perm('ip.see_all_in_workspaces')

        workarea_params = {}
        for key, val in six.iteritems(self.request.query_params):
            if key.startswith('workspace_'):
                key_suffix = remove_prefix(key, 'workspace_')
                workarea_params[key_suffix] = val

        workareas = Workarea.objects.all()
        workareas = WorkareaEntryFilter(data=workarea_params, queryset=workareas, request=self.request).qs
        if not see_all:
            workareas = workareas.filter(user=self.request.user)

        if self.action == 'list' and view_type == 'aic':
            simple_inner = InformationPackage.objects.visible_to_user(user).filter(
                Q(Q(workareas=None) | Q(workareas__read_only=True)),
                active=True,
            )
            simple_inner = InformationPackageFilter(data=self.request.query_params, queryset=simple_inner, request=self.request).qs

            inner = simple_inner.select_related('responsible').prefetch_related('agents', 'steps', Prefetch('workareas',
                                                                                                  queryset=workareas,
                                                                                                  to_attr='prefetched_workareas'))
            dips = inner.filter(package_type=InformationPackage.DIP).distinct()

            lower_higher = InformationPackage.objects.filter(
                Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
            ).order_by().values('aic')
            lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

            inner = inner.annotate(first_generation=self.first_generation_case(lower_higher),
                                   last_generation=self.last_generation_case(lower_higher))

            simple_outer = InformationPackage.objects.annotate(has_ip=Exists(simple_inner.only('id').filter(aic=OuterRef('pk')))).filter(
                package_type=InformationPackage.AIC, has_ip=True,
            )
            aics = simple_outer.prefetch_related(Prefetch('information_packages', queryset=inner)).distinct()

            self.queryset = aics | dips
            self.outer_queryset = simple_outer.distinct() | dips.distinct()
            self.inner_queryset = simple_inner
            return self.queryset
        elif self.action == 'list' and view_type == 'ip':
            filtered = InformationPackage.objects.visible_to_user(user).filter(
                Q(Q(workareas=None) | Q(workareas__read_only=True)),
                active=True,
            ).exclude(package_type=InformationPackage.AIC)

            simple = InformationPackageFilter(data=self.request.query_params, queryset=filtered, request=self.request).qs

            def annotate_generations(qs):
                lower_higher = InformationPackage.objects.filter(
                    Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
                ).order_by().values('aic')
                lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

                return qs.annotate(first_generation=self.first_generation_case(lower_higher),
                                   last_generation=self.last_generation_case(lower_higher))

            def annotate_filtered_first_generation(qs):
                lower_higher = InformationPackage.objects.visible_to_user(user).filter(
                    Q(Q(workareas=None) | Q(workareas__read_only=True)),
                    active=True, aic=OuterRef('aic'),
                ).order_by().values('aic')
                lower_higher = InformationPackageFilter(data=self.request.query_params, queryset=lower_higher, request=self.request).qs
                lower_higher = lower_higher.annotate(min_gen=Min('generation'))
                return qs.annotate(filtered_first_generation=self.first_generation_case(lower_higher))

            def get_related(qs):
                qs = qs.select_related('responsible')
                return qs.prefetch_related(
                    Prefetch('agents', queryset=Agent.objects.prefetch_related('notes'), to_attr='prefetched_agents'),
                    'steps', Prefetch('workareas', queryset=workareas, to_attr='prefetched_workareas'))

            inner = annotate_generations(simple)
            inner = annotate_filtered_first_generation(inner)
            inner = get_related(inner)

            outer = annotate_generations(simple)
            outer = annotate_filtered_first_generation(outer)
            outer = get_related(outer)

            inner = inner.filter(filtered_first_generation=False)
            outer = outer.filter(filtered_first_generation=True).prefetch_related(Prefetch('aic__information_packages', queryset=inner)).distinct()

            self.inner_queryset = simple
            self.outer_queryset = simple
            self.queryset = outer
            return self.queryset

        if self.action == 'retrieve':
            lower_higher = InformationPackage.objects.filter(
                Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
            ).order_by().values('aic')
            lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

            qs = InformationPackage.objects.visible_to_user(user).filter(
                Q(Q(workareas=None) | Q(workareas__read_only=True)),
                active=True,
            )

            qs = InformationPackageFilter(data=self.request.query_params, queryset=qs, request=self.request).qs
            qs = qs.annotate(first_generation=self.first_generation_case(lower_higher),
                             last_generation=self.last_generation_case(lower_higher))
            qs = qs.select_related('responsible')
            self.queryset = qs.prefetch_related('agents', 'steps', Prefetch('workareas', to_attr='prefetched_workareas'))
            self.queryset = self.queryset.distinct()
            return self.queryset

        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return NestedInformationPackageSerializer

        return InformationPackageDetailSerializer

    def get_serializer_context(self):
        context = super(InformationPackageViewSet, self).get_serializer_context()
        context['view'] = self

        checker = ObjectPermissionChecker(self.request.user)
        if hasattr(self, 'outer_queryset') and hasattr(self, 'inner_queryset'):
            checker.prefetch_perms(self.outer_queryset.distinct() | self.inner_queryset.distinct())
        else:
            checker.prefetch_perms(self.queryset)

        context['perm_checker'] = checker

        return context


    def destroy(self, request, pk=None):
        logger = logging.getLogger('essarch.epp')

        ip = self.get_object()

        if not request.user.has_perm('delete_informationpackage', ip):
            raise exceptions.PermissionDenied('You do not have permission to delete this IP')

        logger.info('Request issued to delete %s %s' % (ip.get_package_type_display(), pk), extra={'user': request.user.pk})

        if ip.package_type == InformationPackage.AIC:
            raise exceptions.ParseError(detail='AICs cannot be deleted')

        if ip.package_type == InformationPackage.AIP:
            if ip.is_first_generation():
                if not request.user.has_perm('ip.delete_first_generation'):
                    raise exceptions.PermissionDenied('You do not have permission to delete the first generation of an IP')

            if ip.is_last_generation():
                if not request.user.has_perm('ip.delete_last_generation'):
                    raise exceptions.PermissionDenied('You do not have permission to delete the last generation of an IP')

        if ip.archived:
            if not request.user.has_perm('ip.delete_archived'):
                raise exceptions.PermissionDenied('You do not have permission to delete archived IPs')

            if request.query_params.get('delete-files', True):
                for storage_obj in ip.storage.all():
                    storage_obj.delete_files()
                    storage_obj.delete()

            ip.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        # delete files if IP is not at reception
        if ip.state != 'Prepared':
            if ip.state in 'Receiving':
                path = os.path.join(ip.policy.ingest_path.value, ip.object_identifier_value)
            else:
                path = ip.object_path

            if os.path.isdir(path):
                t = ProcessTask.objects.create(
                    name='ESSArch_Core.tasks.DeleteFiles',
                    params={'path': path},
                    eager=False,
                    responsible=request.user,
                    information_package=ip,
                )
                t.run()
            else:
                no_ext = os.path.splitext(path)[0]
                step = ProcessStep.objects.create(
                    name="Delete files",
                    eager=False,
                )

                for fl in [no_ext + '.' + ext for ext in ['xml', 'tar', 'zip']]:
                    t = ProcessTask.objects.create(
                        name='ESSArch_Core.tasks.DeleteFiles',
                        params={'path': fl},
                        processstep=step,
                        responsible=request.user,
                    )
                    t.run()

                step.run()

        return super(InformationPackageViewSet, self).destroy(request, pk=pk)

    @detail_route(methods=['post'])
    def receive(self, request, pk=None):
        ip = self.get_object()
        workarea = ip.workareas.filter(read_only=False).first()

        if workarea is None:
            raise exceptions.ParseError(detail='IP not in writeable workarea')

        step = ProcessStep.objects.create(
            name='Receive from workarea',
            eager=False,
            information_package=ip,
        )

        ProcessTask.objects.create(
            name='workflow.tasks.ReceiveAIP',
            args=[str(workarea.pk)],
            processstep=step,
            processstep_pos=10,
            information_package=ip,
            responsible=request.user,
        )

        step.run()

        return Response({'detail': 'Receiving %s' % str(ip.pk)}, status=status.HTTP_202_ACCEPTED)

    @detail_route(methods=['post'], url_path='preserve')
    def preserve(self, request, pk=None):
        ip = self.get_object()

        if ip.archived:
            raise exceptions.ParseError('IP already preserved')
        if ip.state == "Preserving":
            raise exceptions.ParseError('IP already being preserved')

        if ip.package_type == InformationPackage.DIP:
            policy = request.data.get('policy')

            if not policy:
                raise exceptions.ParseError('Policy required')

            try:
                ip.policy = ArchivePolicy.objects.get(pk=policy)
            except ArchivePolicy.DoesNotExist:
                raise exceptions.ParseError('Policy "%s" does not exist' % policy)
            except ValueError as e:
                raise exceptions.ParseError(e.message)

            ip.save(update_fields=['policy'])

        ip.state = "Preserving"
        ip.appraisal_date = request.data.get('appraisal_date', None)
        ip.save()

        main_step = ProcessStep.objects.create(
            name='Preserve AIP',
            information_package_id=pk,
            eager=False,
        )

        ProcessTask.objects.create(
            name='workflow.tasks.CacheAIP',
            information_package_id=pk,
            processstep=main_step,
            processstep_pos=10,
            responsible=self.request.user,
        )

        ProcessTask.objects.create(
            name='workflow.tasks.StoreAIP',
            information_package_id=pk,
            processstep=main_step,
            processstep_pos=20,
            responsible=self.request.user,
        )
        main_step.run()
        return Response({'detail': 'Preserving %s...' % ip.object_identifier_value})

    @detail_route(methods=['post'])
    def access(self, request, pk=None):
        aip = self.get_object()

        if aip.state != 'Received' and not aip.archived:
            raise exceptions.ParseError('IP must either have state "Received" or be archived to be accessed')

        data = request.data

        options = ['tar', 'extracted', 'new']

        if not any(x in options for x in data.keys()):
            raise exceptions.ParseError('No option set')

        if not any(v for k, v in six.iteritems(data) if k in options):
            raise exceptions.ParseError('Need at least one option set to true')

        if data.get('new'):
            if aip.archived and not request.user.has_perm('get_from_storage_as_new', aip):
                raise exceptions.PermissionDenied('You do not have permission to create new generations of this IP')

            if not aip.archived and not request.user.has_perm('add_to_ingest_workarea_as_new', aip):
                raise exceptions.PermissionDenied('You do not have permission to create new generations of this IP')

            if aip.new_version_in_progress() is not None:
                working_user = aip.new_version_in_progress().ip.responsible
                raise exceptions.ParseError('User %s already has a new generation in their workarea' % working_user.username)

            data['extracted'] = True

        workarea_type = Workarea.INGEST if aip.state == 'Received' else Workarea.ACCESS

        ip_workarea = aip.workareas.filter(user=request.user)
        ingest_path = Path.objects.get(entity='ingest_workarea')
        access_path = Path.objects.get(entity='access_workarea')

        if not data.get('new') and ip_workarea.exists() and (ip_workarea.filter(type=workarea_type).exists() or ingest_path == access_path):
            raise Conflict('IP already in workarea')

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
                'package_xml': data.get('package_xml', False),
                'aic_xml': data.get('aic_xml', False),
                'object_identifier_value': data.get('object_identifier_value'),
            },
            responsible=self.request.user,
            eager=False,
            information_package_id=pk,
            processstep=step,
        )

        step.run()

        return Response({'detail': 'Accessing AIP %s...' % pk})

    @detail_route(methods=['post'], url_path='create-dip')
    def create_dip(self, request, pk=None):
        dip = InformationPackage.objects.get(pk=pk)

        if dip.package_type != InformationPackage.DIP:
            raise exceptions.ParseError('"%s" is not a DIP, it is a %s' % (dip, dip.package_type))

        if dip.state != 'Prepared':
            raise exceptions.ParseError('"%s" is not in the "Prepared" state' % dip)

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
            raise exceptions.ParseError('"label" is required')

        object_identifier_value = request.data.get('object_identifier_value')

        if object_identifier_value:
            ip_exists = InformationPackage.objects.filter(object_identifier_value=object_identifier_value).exists()
            if ip_exists:
                raise exceptions.ParseError('IP with object identifer value "%s" already exists' % object_identifier_value)

        orders = request.data.get('orders', [])

        for order in orders:
            if not Order.objects.filter(pk=order, responsible=request.user).exists():
                raise exceptions.ParseError('Order "%s" belonging to current user does not exist' % order)

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

    @detail_route(methods=['delete', 'get', 'post'])
    def files(self, request, pk=None):
        ip = self.get_object()
        download = request.query_params.get('download', False)
        path = request.query_params.get('path', '').rstrip('/')

        if ip.archived:
            if request.method in ['DELETE', 'POST']:
                raise exceptions.ParseError('You cannot modify preserved content')
            # check if path exists
            path = request.query_params.get('path', '').rstrip('/')
            s = Search(index=['directory', 'document'])
            s = s.filter('term', ip=str(ip.pk))

            if path != '':
                dirname = os.path.dirname(path)
                basename = os.path.basename(path)
                q = ElasticQ('bool',
                             should=[ElasticQ('bool', must=[ElasticQ('term', href=dirname),
                                                            ElasticQ('term', **{'name.keyword': basename})]),
                                     ElasticQ('bool', must=[ElasticQ('term', href=dirname),
                                                            ElasticQ('match', filename=basename)])])

                s = s.query(q)
                hits = s.execute()

                try:
                    hit = hits[0]
                except IndexError:
                    raise exceptions.NotFound

                if hit.meta.index.startswith('document'):
                    fid = FormatIdentifier(allow_unknown_file_types=True)
                    content_type = fid.get_mimetype(path)
                    return generate_file_response(ip.open_file(path, 'rb'), content_type=content_type, force_download=download, name=path)

            # a directory with the path exists, get the content of it
            s = Search(index=['directory', 'document'])
            s = s.filter('term', ip=str(ip.pk)).query('term', href=path)

            if self.paginator is not None:
                # Paginate in search engine
                params = {key: value[0] for (key, value) in six.iteritems(dict(request.query_params))}

                number = params.get(self.paginator.pager.page_query_param, 1)
                size = params.get(self.paginator.pager.page_size_query_param, 10)

                try:
                    number = int(number)
                except (TypeError, ValueError):
                    raise exceptions.NotFound('Invalid page.')
                if number < 1:
                    raise exceptions.NotFound('Invalid page.')

                size = int(size)
                offset = (number-1)*size
                try:
                    max_results = int(Index('document').get_settings()['document']['settings']['index'].get('max_result_window', DEFAULT_MAX_RESULT_WINDOW))
                except KeyError:
                    max_results = DEFAULT_MAX_RESULT_WINDOW

                s = s[offset:offset+size]

            try:
                results = s.execute()
            except TransportError:
                if self.paginator is not None:
                    if offset+size > max_results:
                        raise exceptions.ParseError("Can't show more than {max} results".format(max=max_results))

                raise

            if self.paginator is not None:
                ceil = math.ceil(results.hits.total/size)
                ceil = 1 if ceil < 1 else ceil
                if results.hits.total > 0 and number > ceil:
                    raise exceptions.NotFound('Invalid page.')

            l = []
            for hit in results:
                if hit.meta.index.startswith('directory-'):
                    d = {
                        'type': 'dir',
                        'name': hit.name,
                    }
                else:
                    d = {
                        'type': 'file',
                        'name': hit.name,
                        'modified': hit.modified,
                        'size': hit.size,
                    }

                l.append(d)

            if self.paginator is not None:
                return Response(l, headers={'Count': results.hits.total})

            return Response(l)

        if request.method == 'DELETE':
            if ip.package_type != InformationPackage.DIP:
                raise exceptions.MethodNotAllowed(request.method)

            try:
                path = os.path.join(ip.object_path, request.data.__getitem__('path'))
            except KeyError:
                raise exceptions.ParseError('Path parameter missing')

            try:
                shutil.rmtree(path)
            except OSError as e:
                if e.errno != errno.ENOTDIR:
                    raise

                os.remove(path)

            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == 'POST':
            if ip.package_type != InformationPackage.DIP:
                raise exceptions.MethodNotAllowed(request.method)

            try:
                path = os.path.join(ip.object_path, request.data['path'])
            except KeyError:
                raise exceptions.ParseError('Path parameter missing')

            try:
                pathtype = request.data['type']
            except KeyError:
                raise exceptions.ParseError('Type parameter missing')

            root = ip.object_path
            fullpath = os.path.join(root, path)

            if not in_directory(fullpath, root):
                raise exceptions.ParseError('Illegal path %s' % fullpath)

            if pathtype == 'dir':
                os.mkdir(fullpath)
            elif pathtype == 'file':
                open(fullpath, 'a').close()
            else:
                raise exceptions.ParseError('Type must be either "file" or "dir"')

            return Response('%s created' % path)

        return ip.get_path_response(path, request, force_download=download, paginator=self.paginator)

    @detail_route(methods=['post'], url_path='unlock-profile', permission_classes=[CanUnlockProfile])
    def unlock_profile(self, request, pk=None):
        ip = self.get_object()

        if ip.state in ['Submitting', 'Submitted']:
            raise exceptions.ParseError('Cannot unlock profiles in an IP that is %s' % ip.state)

        try:
            ptype = request.data["type"]
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        ip.unlock_profile(ptype)

        return Response({
            'detail': 'Unlocking profile with type "%s" in IP "%s"' % (
                ptype, ip.pk
            )
        })

    @detail_route(methods=['post'], url_path='add-appraisal-rule')
    def add_appraisal_rule(self, request, pk=None):
        ip = self.get_object()

        if ip.package_type == InformationPackage.AIC:
            raise exceptions.ParseError('Cannot add appraisal rule to AIC')

        try:
            rule_id = request.data['id']
        except KeyError:
            raise exceptions.ParseError('Missing id parameter')

        try:
            rule = AppraisalRule.objects.get(pk=rule_id)
        except AppraisalRule.DoesNotExist:
            raise exceptions.ParseError('No rule with id "%s"' % rule_id)

        rule.information_packages.add(ip)
        return Response()

    @detail_route(methods=['post'], url_path='remove-appraisal-rule')
    def remove_appraisal_rule(self, request, pk=None):
        ip = self.get_object()

        try:
            rule_id = request.data['id']
        except KeyError:
            raise exceptions.ParseError('Missing id parameter')

        try:
            rule = AppraisalRule.objects.get(pk=rule_id)
        except AppraisalRule.DoesNotExist:
            raise exceptions.ParseError('No rule with id "%s"' % rule_id)

        rule.information_packages.remove(ip)
        return Response()

    @detail_route(methods=['post'], url_path='add-conversion-rule')
    def add_conversion_rule(self, request, pk=None):
        ip = self.get_object()

        if ip.package_type == InformationPackage.AIC:
            raise exceptions.ParseError('Cannot add conversion rule to AIC')

        try:
            rule_id = request.data['id']
        except KeyError:
            raise exceptions.ParseError('Missing id parameter')

        try:
            rule = ConversionRule.objects.get(pk=rule_id)
        except ConversionRule.DoesNotExist:
            raise exceptions.ParseError('No rule with id "%s"' % rule_id)

        rule.information_packages.add(ip)
        return Response()

    @detail_route(methods=['post'], url_path='remove-conversion-rule')
    def remove_conversion_rule(self, request, pk=None):
        ip = self.get_object()

        try:
            rule_id = request.data['id']
        except KeyError:
            raise exceptions.ParseError('Missing id parameter')

        try:
            rule = ConversionRule.objects.get(pk=rule_id)
        except ConversionRule.DoesNotExist:
            raise exceptions.ParseError('No rule with id "%s"' % rule_id)

        rule.information_packages.remove(ip)
        return Response()


class WorkareaViewSet(InformationPackageViewSet):
    queryset = InformationPackage.objects.select_related('responsible').all()

    def get_queryset(self):
        view_type = self.request.query_params.get('view_type', 'aic')
        user = self.request.user
        see_all = self.request.user.has_perm('ip.see_all_in_workspaces')

        workarea_params = {}
        for key, val in six.iteritems(self.request.query_params):
            if key.startswith('workspace_'):
                key_suffix = remove_prefix(key, 'workspace_')
                workarea_params[key_suffix] = val

        workareas = Workarea.objects.all()
        workareas = WorkareaEntryFilter(data=workarea_params, queryset=workareas, request=self.request).qs
        if not see_all:
            workareas = workareas.filter(user=self.request.user)

        if self.action == 'list' and view_type == 'aic':
            simple_inner = InformationPackage.objects.visible_to_user(user).annotate(
                workarea_exists=Exists(workareas.filter(ip=OuterRef('pk')))
            ).filter(workarea_exists=True, active=True)

            simple_inner = InformationPackageFilter(data=self.request.query_params, queryset=simple_inner, request=self.request).qs

            inner = simple_inner.select_related('responsible').prefetch_related('agents', 'steps', Prefetch('workareas',
                                                                                                  queryset=workareas,
                                                                                                  to_attr='prefetched_workareas'))
            dips = inner.filter(package_type=InformationPackage.DIP).distinct()

            lower_higher = InformationPackage.objects.filter(
                Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
            ).order_by().values('aic')
            lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

            inner = inner.annotate(first_generation=self.first_generation_case(lower_higher),
                                   last_generation=self.last_generation_case(lower_higher))

            simple_outer = InformationPackage.objects.annotate(has_ip=Exists(simple_inner.only('id').filter(aic=OuterRef('pk')))).filter(
                package_type=InformationPackage.AIC, has_ip=True,
            )
            aics = simple_outer.prefetch_related(Prefetch('information_packages', queryset=inner)).distinct()

            self.queryset = aics | dips
            self.outer_queryset = simple_outer.distinct() | dips.distinct()
            self.inner_queryset = simple_inner
            return self.queryset
        elif self.action == 'list' and view_type == 'ip':
            filtered = InformationPackage.objects.visible_to_user(user).annotate(
                workarea_exists=Exists(workareas.filter(ip=OuterRef('pk')))
            ).filter(workarea_exists=True, active=True).exclude(
                package_type=InformationPackage.AIC
            )

            simple = InformationPackageFilter(data=self.request.query_params, queryset=filtered, request=self.request).qs

            def annotate_generations(qs):
                lower_higher = InformationPackage.objects.filter(
                    Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
                ).order_by().values('aic')
                lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

                return qs.annotate(first_generation=self.first_generation_case(lower_higher),
                                   last_generation=self.last_generation_case(lower_higher))

            def annotate_filtered_first_generation(qs):
                lower_higher = InformationPackage.objects.visible_to_user(user).annotate(
                    workarea_exists=Exists(workareas.filter(ip=OuterRef('pk')))
                ).filter(workarea_exists=True, active=True, aic=OuterRef('aic')).exclude(
                    package_type=InformationPackage.AIC
                ).order_by().values('aic')

                if not see_all:
                    lower_higher = lower_higher.filter(workareas__user=self.request.user)

                lower_higher = InformationPackageFilter(data=self.request.query_params, queryset=lower_higher, request=self.request).qs
                lower_higher = lower_higher.annotate(min_gen=Min('generation'))
                return qs.annotate(filtered_first_generation=self.first_generation_case(lower_higher))

            def get_related(qs):
                qs = qs.select_related('responsible')
                return qs.prefetch_related('agents', 'steps', Prefetch('workareas', queryset=workareas, to_attr='prefetched_workareas'))

            inner = annotate_generations(simple)
            inner = annotate_filtered_first_generation(inner)
            inner = get_related(inner)

            outer = annotate_generations(simple)
            outer = annotate_filtered_first_generation(outer)
            outer = get_related(outer)

            inner = inner.filter(filtered_first_generation=False)
            outer = outer.filter(filtered_first_generation=True).prefetch_related(Prefetch('aic__information_packages', queryset=inner)).distinct()

            self.inner_queryset = simple
            self.outer_queryset = simple
            self.queryset = outer
            return self.queryset

        if self.action == 'retrieve':
            lower_higher = InformationPackage.objects.filter(
                Q(aic=OuterRef('aic')), Q(Q(workareas=None) | Q(workareas__read_only=True))
            ).order_by().values('aic')
            lower_higher = lower_higher.annotate(min_gen=Min('generation'), max_gen=Max('generation'))

            qs = InformationPackage.objects.visible_to_user(user).filter(
                Q(Q(workareas=None) | Q(workareas__read_only=True)),
                active=True,
            )

            qs = InformationPackageFilter(data=self.request.query_params, queryset=qs, request=self.request).qs
            qs = qs.annotate(first_generation=self.first_generation_case(lower_higher),
                             last_generation=self.last_generation_case(lower_higher))
            qs = qs.select_related('responsible')
            self.queryset = qs.prefetch_related('agents', 'steps', Prefetch('workareas', queryset=workareas, to_attr='prefetched_workareas'))
            return self.queryset

        return self.queryset


class WorkareaFilesViewSet(viewsets.ViewSet, PaginatedViewMixin):
    def get_user(self, request):
        requested_user = self.request.query_params.get('user')
        if requested_user in EMPTY_VALUES or requested_user == str(request.user.pk):
            return request.user

        if not self.request.user.has_perm('ip.see_all_in_workspaces'):
            raise exceptions.PermissionDenied('No permission to see files in other users workspaces')

        try:
            user_id = self.request.query_params['user']
            organization = self.request.user.user_profile.current_organization
            organization_users = organization.get_members(subgroups=True)
            user = User.objects.get(pk=user_id, essauth_member__in=organization_users)
            return user
        except User.DoesNotExist:
            raise exceptions.NotFound('User not found in organization')

    def validate_workarea(self, area_type):
        workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

        try:
            workarea_type_reverse[area_type]
        except KeyError:
            raise exceptions.ParseError('Workarea of type "%s" does not exist' % area_type)

    def validate_path(self, path, root, existence=True):
        relpath = os.path.relpath(path, root)

        if not in_directory(path, root):
            raise exceptions.ParseError('Illegal path %s' % relpath)

        if existence and not os.path.exists(path):
            raise exceptions.NotFound('Path "%s" does not exist' % relpath)

    def list(self, request):
        try:
            workarea = self.request.query_params['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)

        path = request.query_params.get('path', '').strip('/ ')
        force_download = request.query_params.get('download', False)
        fullpath = os.path.join(root, path)

        try:
            self.validate_path(fullpath, root)
        except exceptions.NotFound:
            if len(fullpath.split('.tar/')) == 2:
                tar_path, tar_subpath = fullpath.split('.tar/')
                tar_path += '.tar'
                if not os.path.isfile(tar_path):
                    raise
            else:
                raise

        return list_files(fullpath, force_download, paginator=self.paginator, request=request)

    @list_route(methods=['post'], url_path='add-directory')
    def add_directory(self, request):
        try:
            workarea = self.request.data['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)

        path = os.path.join(root, request.data.get('path', ''))
        self.validate_path(path, root, existence=False)

        relative_root = path[len(root)+1:].split('/')[0]

        try:
            workarea_obj = Workarea.objects.get(ip__object_identifier_value=relative_root)
        except Workarea.DoesNotExist:
            raise exceptions.NotFound

        if workarea_obj.read_only:
            detail = 'You are not allowed to modify read-only IPs'
            raise exceptions.MethodNotAllowed(method=request.method, detail=detail)

        try:
            os.makedirs(path)
        except OSError as e:
            if e.errno == errno.EEXIST:
                raise exceptions.ParseError('Directory already exists')

        return Response(status=status.HTTP_201_CREATED)


    @list_route(methods=['delete'], url_path='')
    def delete(self, request):
        try:
            workarea = self.request.data['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)

        path = os.path.join(root, request.data.get('path', ''))
        self.validate_path(path, root)

        relative_root = path[len(root)+1:].split('/')[0]

        try:
            workarea_obj = Workarea.objects.get(ip__object_identifier_value=relative_root)
        except Workarea.DoesNotExist:
            raise exceptions.NotFound

        if workarea_obj.read_only:
            detail = 'You are not allowed to modify read-only IPs'
            raise exceptions.MethodNotAllowed(method=request.method, detail=detail)

        try:
            shutil.rmtree(path)
        except OSError as e:
            if e.errno != errno.ENOTDIR:
                raise

            os.remove(path)

        return Response(status=status.HTTP_204_NO_CONTENT)

    @list_route(methods=['get', 'post'], url_path='upload')
    def upload(self, request):
        try:
            workarea = self.request.query_params['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)

        if request.method == 'GET':
            path = os.path.join(root, request.query_params.get('destination', ''))
        else:
            path = os.path.join(root, request.data.get('destination', ''))

        self.validate_path(path, root)
        relative_root = path[len(root)+1:].split('/')[0]

        try:
            workarea_obj = Workarea.objects.get(ip__object_identifier_value=relative_root)
        except Workarea.DoesNotExist:
            raise exceptions.NotFound

        if workarea_obj.read_only:
            detail = 'You are not allowed to modify read-only IPs'
            raise exceptions.MethodNotAllowed(method=request.method, detail=detail)

        if request.method == 'GET':
            relative_path = request.query_params.get('flowRelativePath', '')

            if len(relative_path) == 0:
                raise exceptions.ParseError('The path cannot be empty')

            path = os.path.join(path, relative_path)

            try:
                chunk_nr = request.query_params['flowChunkNumber']
            except KeyError:
                raise exceptions.ParseError('flowChunkNumber parameter missing')

            chunk_path = "%s_%s" % (path, chunk_nr)

            if os.path.exists(chunk_path):
                return Response(status=status.HTTP_200_OK)
            return Response(status=status.HTTP_204_NO_CONTENT)

        if request.method == 'POST':
            relative_path = request.data.get('flowRelativePath', '')

            if len(relative_path) == 0:
                raise exceptions.ParseError('The path cannot be empty')

            try:
                chunk_nr = request.data['flowChunkNumber']
            except KeyError:
                raise exceptions.ParseError('flowChunkNumber parameter missing')

            path = os.path.join(path, relative_path)

            chunk_path = "%s_%s" % (path, chunk_nr)
            chunk = request.FILES['file']
            mkdir_p(os.path.dirname(chunk_path))

            with open(chunk_path, 'wb+') as dst:
                for c in chunk.chunks():
                    dst.write(c)

            return Response(status=status.HTTP_201_CREATED)

    @list_route(methods=['post'], url_path='merge-uploaded-chunks')
    def merge_uploaded_chunks(self, request):
        try:
            workarea = self.request.query_params['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)
        relative_path = request.data.get('path', '')

        if len(relative_path) == 0:
            raise exceptions.ParseError('The path cannot be empty')

        path = os.path.join(root, relative_path)

        self.validate_path(path, root, existence=False)

        relative_root = path[len(root)+1:].split('/')[0]

        try:
            workarea_obj = Workarea.objects.get(ip__object_identifier_value=relative_root)
        except Workarea.DoesNotExist:
            raise exceptions.NotFound

        if workarea_obj.read_only:
            raise exceptions.MethodNotAllowed(request.method)

        chunks = natsorted(glob.glob('%s_*' % re.sub(r'([\[\]])', '[\\1]', path)))
        if len(chunks) == 0:
            raise exceptions.NotFound('No chunks found')

        with open(path, 'wb') as f:

            for chunk_file in natsorted(glob.glob('%s_*' % re.sub(r'([\[\]])', '[\\1]', path))):
                f.write(open(chunk_file).read())
                os.remove(chunk_file)

        return Response({'detail': 'Merged chunks'})

    @list_route(methods=['post'], url_path='add-to-dip')
    def add_to_dip(self, request):
        try:
            workarea = self.request.data['type'].lower()
        except KeyError:
            raise exceptions.ParseError('Missing type parameter')

        user = self.get_user(request)

        self.validate_workarea(workarea)
        root = os.path.join(Path.objects.get(entity=workarea + '_workarea').value, user.username)

        try:
            dip = self.request.data['dip']
        except KeyError:
            raise exceptions.ParseError('Missing dip parameter')

        try:
            ip = InformationPackage.objects.get(pk=dip, package_type=InformationPackage.DIP)

            permission = IsResponsibleOrReadOnly()
            if not permission.has_object_permission(request, self, ip):
                self.permission_denied(
                    request, message=getattr(permission, 'message', None)
                )
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

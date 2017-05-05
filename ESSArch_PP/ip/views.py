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

import glob
import os

from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend

from lxml import etree

from rest_framework import exceptions, filters, permissions, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ESSArch_Core.configuration.models import (
    Path,
)
from ESSArch_Core.essxml.util import parse_submit_description
from ESSArch_Core.ip.models import (
    ArchivalInstitution,
    ArchivistOrganization,
    ArchivalType,
    ArchivalLocation,
    InformationPackage,
    EventIP,
    Workarea,
)
from ESSArch_Core.util import get_value_from_path
from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask
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
    EventIPSerializer,
)
from workflow.serializers import ProcessStepSerializer


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
    def find_xml_files(self, path):
        for xmlfile in glob.glob(os.path.join(path, "*.xml")):
            if os.path.isfile(xmlfile) and not xmlfile.endswith('_ipevents.xml'):
                yield xmlfile

    def get_objectpath(self, el):
        e = el.xpath('.//*[local-name()="%s"]' % "FLocat")[0]
        if e is not None:
            return get_value_from_path(e, "@href").split('file:///')[1]

    def get_container_for_xml(self, xmlfile):
        doc = etree.parse(xmlfile)
        root = doc.getroot()
        return self.get_objectpath(root)

    def get_contained_packages(self, path):
        ips = []

        for xmlfile in self.find_xml_files(path):
            container = os.path.join(path, self.get_container_for_xml(xmlfile))

            ip_id = os.path.splitext(os.path.basename(xmlfile))[0]

            if InformationPackage.objects.filter(ObjectIdentifierValue=ip_id).exists():
                continue

            ip = parse_submit_description(xmlfile, srcdir=os.path.split(container)[0])

            ip['container'] = container
            ip['xml'] = xmlfile
            ip['type'] = 'contained'
            ips.append(ip)

        return ips

    def get_extracted_packages(self, path):
        ips = []

        for d in os.listdir(path):
            if not os.path.isdir(os.path.join(path, d)):
                continue

            if InformationPackage.objects.filter(ObjectIdentifierValue=d).exists():
                continue

            ip = {
                'id': d,
                'type': 'extracted',
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

        paginator = LinkHeaderPagination()
        page = paginator.paginate_queryset(new_ips, request)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response(new_ips)

    @detail_route(methods=['post'], url_path='receive')
    def receive(self, request, pk=None):
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

        step = ProcessStep.objects.create(
            name="Receive SIP", eager=False,
        )

        t1 = ProcessTask(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xmlfile,
                'container': container,
                'purpose': request.data.get('purpose'),
                'archive_policy': request.data.get('archive_policy'),
                'allow_unknown_files': request.data.get('allow_unknown_files', False),
                'tags': request.data.get('tags', [])
            },
            responsible=self.request.user,
            processstep=step,
            processstep_pos=0
        )

        t2 = ProcessTask(
            name='ESSArch_Core.tasks.UpdateIPStatus',
            params={
                'status': 'Received',
                'prev': 'Receiving'
            },
            result_params={'ip': t1.pk},
            responsible=self.request.user,
            processstep=step,
            processstep_pos=1
        )

        ProcessTask.objects.bulk_create([t1, t2])
        step.run()

        return Response('Receiving %s...' % container)


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
        'Label', 'Responsible', 'CreateDate', 'State', 'eventDateTime',
        'eventType', 'eventOutcomeDetailNote', 'eventOutcome',
        'linkingAgentIdentifierValue', 'id'
    )
    search_fields = (
        'ObjectIdentifierValue','aic__information_packages__ObjectIdentifierValue','information_packages__ObjectIdentifierValue',
        'Label','aic__information_packages__Label','information_packages__Label',
        'Responsible__first_name','aic__information_packages__Responsible__first_name','information_packages__Responsible__first_name',
        'Responsible__last_name','aic__information_packages__Responsible__last_name','information_packages__Responsible__last_name',
        'Responsible__username','aic__information_packages__Responsible__username','information_packages__Responsible__username',
        'State','aic__information_packages__State','information_packages__State',
        'SubmissionAgreement__name','aic__information_packages__SubmissionAgreement__name','information_packages__SubmissionAgreement__name',
        'Startdate','aic__information_packages__Startdate','information_packages__Startdate',
        'Enddate','aic__information_packages__Enddate','information_packages__Enddate',
    )

    def get_queryset(self):
        view_type = self.request.query_params.get('view_type', 'aic')

        if self.action == 'list':
            if view_type == 'ip':
                return self.queryset.exclude(
                    package_type=InformationPackage.AIC,
                ).filter(generation=0)

            return self.queryset.filter(aic__isnull=True)

        return self.queryset

    def get_serializer_class(self):
        if self.action == 'list':
            return InformationPackageSerializer

        return InformationPackageDetailSerializer

    @detail_route(methods=['post'], url_path='preserve')
    def preserve(self, request, pk=None):
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
            responsible=self.request.user,
        ))

        tasks.append(ProcessTask(
            name='workflow.tasks.StoreAIP',
            params={'aip': pk},
            processstep=main_step,
            responsible=self.request.user,
        ))

        ProcessTask.objects.bulk_create(tasks)

        main_step.run()

        return Response(['Preserving AIP %s...' % pk])

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


class WorkareaViewSet(viewsets.ModelViewSet):
    queryset = InformationPackage.objects.filter(workareas__type=Workarea.ACCESS)
    serializer_class = InformationPackageSerializer
    http_method_names = [p.lower() for p in permissions.SAFE_METHODS]

    def get_queryset(self):
        try:
            workarea_type = self.request.query_params['type'].lower()
            workarea_type_reverse = dict((v.lower(), k) for k, v in Workarea.TYPE_CHOICES)

            try:
                return self.queryset.filter(
                    workareas__user=self.request.user,
                    workareas__type=workarea_type_reverse[workarea_type]
                )
            except KeyError:
                raise exceptions.ParseError('Workarea of type "%s" does not exist' % workarea_type)
        except KeyError:
            return self.queryset.filter(
                workareas__user=self.request.user,
            )

    filter_backends = DjangoFilterBackend,
    filter_class = InformationPackageFilter
    filter_backends = (
        filters.OrderingFilter, DjangoFilterBackend, filters.SearchFilter,
    )
    ordering_fields = (
        'Label', 'Responsible', 'CreateDate', 'State', 'eventDateTime',
        'eventType', 'eventOutcomeDetailNote', 'eventOutcome',
        'linkingAgentIdentifierValue', 'id'
    )
    search_fields = (
        'ObjectIdentifierValue', 'Label', 'Responsible__first_name',
        'Responsible__last_name', 'Responsible__username', 'State',
        'SubmissionAgreement__name', 'Startdate', 'Enddate',
    )
    filter_class = InformationPackageFilter

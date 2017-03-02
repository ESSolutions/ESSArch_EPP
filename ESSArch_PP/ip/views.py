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

from lxml import etree

from rest_framework import filters, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ESSArch_Core.configuration.models import (
    Path,
)
from ESSArch_Core.ip.models import EventIP, InformationPackage
from ESSArch_Core.util import get_value_from_path
from ESSArch_Core.WorkflowEngine.models import ProcessStep, ProcessTask
from ESSArch_Core.pagination import LinkHeaderPagination

from ip.serializers import EventIPSerializer, InformationPackageSerializer, InformationPackageDetailSerializer


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

            ip = {
                'id': ip_id,
                'container': container,
                'xml': xmlfile,
                'type': 'contained',
            }

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
        reception = Path.objects.values_list('value', flat=True).get(entity="reception")

        contained = self.get_contained_packages(reception)
        extracted = self.get_extracted_packages(reception)

        ips = contained + extracted

        paginator = LinkHeaderPagination()
        page = paginator.paginate_queryset(ips, request)
        if page is not None:
            return paginator.get_paginated_response(page)

        return Response(ips)

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

        t = ProcessTask.objects.create(
            name='workflow.tasks.ReceiveSIP',
            params={
                'xml': xmlfile,
                'container': container,
                'purpose': request.data.get('purpose'),
                'archive_policy': request.data.get('archive_policy'),
                'allow_unknown_files': request.data.get('allow_unknown_files', False),
            },
            responsible=self.request.user,
        )

        t.run()

        return Response(['Receiving %s...' % container, t.params])


class InformationPackageViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows information packages to be viewed or edited.
    """
    queryset = InformationPackage.objects.all()

    def get_serializer_class(self):
        if self.action == 'list':
            return InformationPackageSerializer

        return InformationPackageDetailSerializer

    @detail_route(methods=['post'], url_path='preserve')
    def preserve(self, request, pk=None):
        main_step = ProcessStep.objects.create(name='Preserve AIP')
        tasks = []

        tasks.append(ProcessTask(
            name='workflow.tasks.CacheAIP',
            params={'aip': pk},
            processstep=main_step
        ))

        ProcessTask.objects.bulk_create(tasks)

        main_step.run()

        return Response(['Preserving AIP %s...' % pk])

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

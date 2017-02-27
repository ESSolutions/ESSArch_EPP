from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from ESSArch_Core.ip.models import InformationPackage
from ESSArch_Core.tags.models import Tag

from ip.serializers import InformationPackageSerializer
from tags.filters import TagFilter
from tags.serializers import TagSerializer


class TagViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows tags to be viewed or edited.
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    filter_backends = (DjangoFilterBackend,)
    filter_class = TagFilter

    @detail_route(url_path='information-packages')
    def information_packages(self, request, pk=None):
        tag = self.get_object()
        leaves = tag.get_leafnodes(include_self=True).prefetch_related('information_packages')
        ips = list(set(ip for l in leaves for ip in l.information_packages.all()))

        page = self.paginate_queryset(ips)
        if page is not None:
            serializers = InformationPackageSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializers.data)
        serializers = InformationPackageSerializer(ips, many=True, context={'request': request})
        return Response(serializers.data)

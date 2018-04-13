from django.db.models import Q

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from rest_framework_extensions.mixins import NestedViewSetMixin

from ESSArch_Core.ip.models import InformationPackage
from ESSArch_Core.tags.models import TagVersion
from ESSArch_Core.tags.serializers import TagVersionSerializerWithoutSource

from ip.serializers import InformationPackageSerializer
from ip.views import InformationPackageViewSet
from tags.filters import TagFilter


class TagViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    """
    API endpoint that allows tags to be viewed or edited.
    """
    queryset = TagVersion.objects.all()
    serializer_class = TagVersionSerializerWithoutSource

    filter_backends = (DjangoFilterBackend,)
    filter_class = TagFilter

    def get_queryset(self):
        qs = self.queryset
        ancestor = self.kwargs.get('parent_lookup_tag')

        if ancestor is not None:
            ancestor = TagVersion.objects.get(pk=ancestor)
            structure = self.request.query_params.get('structure')
            qs = ancestor.get_descendants(structure)

        return qs


class TagInformationPackagesViewSet(NestedViewSetMixin, InformationPackageViewSet):
    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        tag = parents_query_dict['tag']
        leaves = Tag.objects.get(pk=tag).get_leafnodes(include_self=True)

        return queryset.filter(
            Q(tags__in=leaves) | Q(information_packages__tags__in=leaves) |
            Q(aic__information_packages__tags__in=leaves)
        ).distinct()

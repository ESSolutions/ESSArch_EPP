from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from mptt.templatetags.mptt_tags import cache_tree_children
from rest_framework import exceptions, viewsets
from rest_framework.decorators import detail_route
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework_extensions.mixins import NestedViewSetMixin

from ESSArch_Core.tags.filters import TagFilter
from ESSArch_Core.tags.models import Structure, StructureUnit, Tag
from ESSArch_Core.tags.serializers import TagSerializer, StructureSerializer, StructureUnitSerializer
from ESSArch_Core.util import mptt_to_dict
from ip.views import InformationPackageViewSet


class StructureViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Structure.objects.prefetch_related('units')
    serializer_class = StructureSerializer
    filter_backends = (OrderingFilter, SearchFilter,)
    ordering_fields = ('name', 'create_date', 'version',)
    search_fields = ('name',)

    @detail_route(methods=['get'])
    def tree(self, request, pk=None):
        obj = self.get_object()

        root_nodes = cache_tree_children(StructureUnit.objects.filter(structure=obj))
        dicts = []
        for n in root_nodes:
            dicts.append(mptt_to_dict(n, StructureUnitSerializer))

        return Response(dicts)


class StructureUnitViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = StructureUnit.objects.select_related('structure')
    serializer_class = StructureUnitSerializer

    def perform_create(self, serializer):
        try:
            structure = self.get_parents_query_dict()['structure']
        except KeyError:
            structure = self.get_parents_query_dict()['parent__structure']
        parent = serializer.validated_data.get('parent')
        if parent is not None and str(parent.structure.pk) != structure:
            raise exceptions.ValidationError('Parent must be from the same classification structure')
        serializer.save(structure_id=structure)


class TagViewSet(NestedViewSetMixin, viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = TagFilter
    search_fields = ('current_version__name',)

    http_method_names = ('get', 'head', 'options')

    def get_queryset(self):
        qs = self.queryset
        ancestor = self.kwargs.get('parent_lookup_tag')

        if ancestor is not None:
            ancestor = Tag.objects.get(pk=ancestor)
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

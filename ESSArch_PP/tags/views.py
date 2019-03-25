from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.filters import SearchFilter
from rest_framework_extensions.mixins import NestedViewSetMixin

from ESSArch_Core.tags.models import (
    Search,
    Tag,
)

from ip.views import InformationPackageViewSet
from tags.serializers import StoredSearchSerializer


class TagInformationPackagesViewSet(NestedViewSetMixin, InformationPackageViewSet):
    def filter_queryset_by_parents_lookups(self, queryset):
        parents_query_dict = self.get_parents_query_dict()
        tag = parents_query_dict['tag']
        leaves = Tag.objects.get(pk=tag).get_leafnodes(include_self=True)

        return queryset.filter(
            Q(tags__in=leaves) | Q(information_packages__tags__in=leaves) |
            Q(aic__information_packages__tags__in=leaves)
        ).distinct()


class StoredSearchViewSet(viewsets.ModelViewSet):
    queryset = Search.objects.all()
    serializer_class = StoredSearchSerializer

    filter_backends = (DjangoFilterBackend, SearchFilter)
    search_fields = ('name',)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

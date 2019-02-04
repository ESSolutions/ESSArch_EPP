from django.db.models import F

from django_filters import rest_framework as filters
from django_filters.widgets import BooleanWidget

from ESSArch_Core.tags.models import TagVersion


class TagFilter(filters.FilterSet):
    include_leaves = filters.BooleanFilter(method='filter_leaves', widget=BooleanWidget())
    only_roots = filters.BooleanFilter(method='filter_roots', widget=BooleanWidget())
    all_versions = filters.BooleanFilter(method='filter_all_versions', widget=BooleanWidget())

    def filter_leaves(self, queryset, name, value):
        if not value:
            return queryset.exclude(lft=F('rght') - 1)

        return queryset

    def filter_roots(self, queryset, name, value):
        if value:
            return queryset.filter(parent__isnull=True)

        return queryset

    def filter_all_versions(self, queryset, name, value):
        if not value:
            return queryset.filter(tag__current_version=F('pk'))

        return queryset

    class Meta:
        model = TagVersion
        fields = ['include_leaves', 'elastic_index', 'all_versions']

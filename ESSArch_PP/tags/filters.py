from django.db.models import F

import django_filters
from django_filters.widgets import BooleanWidget

from ESSArch_Core.tags.models import Tag


class TagFilter(django_filters.FilterSet):
    include_leaves = django_filters.BooleanFilter(method='filter_leaves', widget=BooleanWidget())

    def filter_leaves(self, queryset, name, value):
        if not value:
            return queryset.exclude(lft=F('rght')-1)

        return queryset

    class Meta:
        model = Tag
        fields = ['include_leaves']

from __future__ import division

import copy
import datetime
import math

from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django_filters.constants import EMPTY_VALUES
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Index, Q, FacetedSearch, TermsFacet
from rest_framework import exceptions, status
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from six import iteritems

from ESSArch_Core.ip.models import ArchivalInstitution, ArchivistOrganization
from ESSArch_Core.mixins import PaginatedViewMixin
from ESSArch_Core.search import get_connection, DEFAULT_MAX_RESULT_WINDOW
from ESSArch_Core.tags.documents import Archive, VersionedDocType
from ESSArch_Core.tags.models import Tag, TagStructure, TagVersion
from ESSArch_Core.tags.serializers import TagVersionNestedSerializer, TagVersionSerializer, \
    TagVersionSerializerWithVersions, \
    TagVersionWriteSerializer
from tags.permissions import SearchPermissions
from tags.serializers import SearchSerializer


class ComponentSearch(FacetedSearch):
    index = ['component', 'archive', 'document', 'information_package']
    fields = ['name', 'desc', 'attachment.content']

    facets = {
        # use bucket aggregations to define facets
        'index': TermsFacet(field='_index', min_doc_count=0),
        'parents': TermsFacet(field='parents', min_doc_count=0),
        'type': TermsFacet(field='type', min_doc_count=0),
        'archive': TermsFacet(field='archive', min_doc_count=0),
        'institution': TermsFacet(field='institution', min_doc_count=0),
        'organization': TermsFacet(field='organization', min_doc_count=0),
        'extension': TermsFacet(field='extension', min_doc_count=0),
    }

    def __init__(self, *args, **kwargs):
        self.filter_values = kwargs.pop('filter_values', {})
        self.start_date = self.filter_values.get('start_date', None)
        self.end_date = self.filter_values.get('end_date', None)
        self.archive = self.filter_values.get('archive', None)

        def validate_date(d):
            try:
                return datetime.datetime.strptime(d, '%Y')
            except ValueError:
                try:
                    return datetime.datetime.strptime(d, '%Y-%m')
                except ValueError:
                    try:
                        return datetime.datetime.strptime(d, '%Y-%m-%d')
                    except ValueError:
                        raise exceptions.ParseError('Invalid date format, should be YYYY[-MM-DD]')

        if self.start_date not in EMPTY_VALUES:
            self.start_date = self.start_date.zfill(4)
            self.start_date = validate_date(self.start_date)

        if self.end_date not in EMPTY_VALUES:
            self.end_date = self.end_date.zfill(4)
            self.end_date = validate_date(self.end_date)

        if self.start_date not in EMPTY_VALUES and self.end_date not in EMPTY_VALUES:
            if self.start_date > self.end_date:
                raise exceptions.ParseError('start_date cannot be set to date after end_date')

        super(ComponentSearch, self).__init__(*args, **kwargs)

    def search(self):
        """
        We override this to add filters on archive, start and end date

        We have to manually filter archives since we want to filter against a
        script field representing the archive which is the `archive` field on
        components and `_id` on archives.
        """

        s = super(ComponentSearch, self).search()

        if self.start_date not in EMPTY_VALUES:
            s = s.filter('range', end_date={'gte': self.start_date})

        if self.end_date not in EMPTY_VALUES:
            s = s.filter('range', start_date={'lte': self.end_date})

        if self.archive is not None:
            s = s.query(Q('bool', must=Q('script', script={
                'source': "(doc.containsKey('archive') && doc['archive'].value==params.archive) || doc['_id'].value==params.archive",
                'params': {'archive': self.archive},
            })))
        return s

    def aggregate(self, search):
        """
        Add aggregations representing the facets selected, including potential
        filters.

        We override this to also aggregate on fields in `facets`
        """
        for f, facet in iteritems(self.facets):
            agg = facet.get_aggregation()
            agg_filter = Q('match_all')
            for field, filter in iteritems(self._filters):
                agg_filter &= filter
            search.aggs.bucket(
                '_filter_' + f,
                'filter',
                filter=agg_filter
            ).bucket(f, agg)


        search.aggs.bucket('_filter_archive', 'filter', filter=agg_filter).bucket(
            'archive', 'terms',
            script="doc['_index'].value != 'information_package' ? (doc.containsKey('archive') ? doc['archive'].value : doc['_id'].value) : null"
        )

    def highlight(self, search):
        """
        We override this to set the highlighting options
        """

        pre_tags = ["<strong>"]
        post_tags = ["</strong>"]
        search = search.highlight_options(number_of_fragments=0, pre_tags=pre_tags, post_tags=post_tags, require_field_match=True)
        return super(ComponentSearch, self).highlight(search)

def get_archive(id):
    # try to get from cache first
    cache_key = 'archive_%s' % id
    cached = cache.get(cache_key)
    if cached:
        return cached

    archive = Archive.get(id=id)
    archive_data = archive.to_dict()
    cache.set(cache_key, archive_data)
    return archive_data

def get_institution(id):
    inst = ArchivalInstitution.objects.get(pk=id)
    return {
        'name': inst.name
    }

def get_organization(id):
    org = ArchivistOrganization.objects.get(pk=id)
    return {
        'name': org.name,
    }

class ComponentSearchViewSet(ViewSet, PaginatedViewMixin):
    permission_classes = (SearchPermissions,)
    index = ComponentSearch.index
    lookup_field = 'pk'
    lookup_url_kwarg = None

    def __init__(self, *args, **kwargs):
        get_connection('default')
        super(ComponentSearchViewSet, self).__init__(*args, **kwargs)

    def get_object(self, index=None):
        """
        Returns the object the view is displaying.
        """

        index = index or self.index

        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        # Search for object in index by id
        id = self.kwargs[lookup_url_kwarg]

        try:
            return VersionedDocType.get(id, index=index)
        except NotFoundError:
            raise exceptions.NotFound

    def get_tag_object(self):
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
                'Expected view %s to be called with a URL keyword argument '
                'named "%s". Fix your URL conf, or set the `.lookup_field` '
                'attribute on the view correctly.' %
                (self.__class__.__name__, lookup_url_kwarg)
        )

        # Search for object in index by id
        id = self.kwargs[lookup_url_kwarg]

        tag_version = TagVersion.objects.select_related('tag').prefetch_related('tag__structures')

        return get_object_or_404(tag_version, pk=id)

    def list(self, request, index=None):
        params = {key: value[0] for (key, value) in dict(request.query_params).iteritems()}
        query = params.pop('q', '')
        if query:
            query = '%s' % query

        filters = {
            'extension': params.pop('extension', None),
            'index': params.pop('index', index),
            'type': params.pop('type', None),
            'institution': params.pop('institution', None),
            'organization': params.pop('organization', None),
        }

        for k, v in iteritems(filters):
            filters[k] = v.split(',') if v is not None else v

        filter_values = copy.copy(params)
        for f in ('page', 'page_size'):
            filter_values.pop(f, None)

        s = ComponentSearch(query, filters=filters, filter_values=filter_values)

        if self.paginator is not None:
            # Paginate in search engine
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
            max_results = int(Index('archive').get_settings()['archive']['settings']['index'].get('max_result_window', DEFAULT_MAX_RESULT_WINDOW))
            s[offset:offset+size]

        try:
            results = s.execute()
        except TransportError:
            if self.paginator is not None:
                if offset+size > max_results:
                    raise exceptions.ParseError("Can't show more than {max} results".format(max=max_results))

            raise

        if self.paginator is not None:
            if size > 0 and results.hits.total > 0 and number > math.ceil(results.hits.total/size):
                raise exceptions.NotFound('Invalid page.')

        results_dict = results.to_dict()

        for archive in results_dict['aggregations']['_filter_archive']['archive']['buckets']:
            archive_data = get_archive(archive['key'])
            archive['name'] = archive_data['name']

        for institution in results_dict['aggregations']['_filter_institution']['institution']['buckets']:
            institution_data = get_institution(institution['key'])
            institution['name'] = institution_data['name']

        for organization in results_dict['aggregations']['_filter_organization']['organization']['buckets']:
            organization_data = get_organization(organization['key'])
            organization['name'] = organization_data['name']

        if len(results_dict['_shards'].get('failures', [])):
            return Response(results_dict['_shards']['failures'], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        r = {
            'hits': results_dict['hits']['hits'],
            'aggregations': results_dict['aggregations'],
        }

        if self.paginator is not None:
            return Response(r, headers={'Count': results.hits.total})

        return Response(r)

    def serialize(self, obj):
        return obj.to_dict(include_meta=True)

    def retrieve(self, request, index=None, pk=None):
        if index is None:
            return self.list(request, index=pk)

        tag = self.get_tag_object()
        structure = self.request.query_params.get('structure')
        context = {'structure': structure}

        try:
            if not tag.get_structures().filter(structure=structure).exists():
                raise exceptions.ParseError('Structure "%s" does not exist for node' % structure)
        except ValidationError:
            raise exceptions.ParseError('Invalid structure id')

        serialized = TagVersionSerializerWithVersions(tag, context=context).data

        return Response(serialized)

    @detail_route(methods=['get'])
    def children(self, request, index=None, pk=None):
        parent = self.get_tag_object()
        structure = self.request.query_params.get('structure')

        try:
            if not parent.get_structures().filter(structure=structure).exists():
                raise exceptions.ParseError('Structure "%s" does not exist for node' % structure)
        except ValidationError:
            raise exceptions.ParseError('Invalid structure id')

        context = {'structure': structure}

        children = parent.get_children(structure)

        if self.paginator is not None:
            paginated = self.paginator.paginate_queryset(children, request)
            serialized = TagVersionNestedSerializer(instance=paginated, many=True, context=context).data
            return self.paginator.get_paginated_response(serialized)

        return Response(serialized = TagVersionSerializer(children, many=True).data)

    @detail_route(methods=['post'], url_path='new-version')
    def new_version(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        new_tag = tag.create_new()
        return Response()

    @detail_route(methods=['patch'], url_path='set-as-current-version')
    def set_as_current_version(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        tag.set_as_current_version()
        return Response()

    def create(self, request, index=None):
        request.data.setdefault('index', index)
        refresh = request.query_params.get('refresh', False)
        serializer = SearchSerializer(data=request.data)

        if serializer.is_valid(raise_exception=True):
            data = serializer.data

            with transaction.atomic():
                tag = Tag.objects.create()
                tag_version = TagVersion.objects.create(
                    tag=tag, elastic_index=data['index'], name=data['name'],
                    type=data['type'])
                tag.current_version = tag_version
                tag.save()
                tag_structure = TagStructure(tag=tag)

                if data.get('parent') is not None:
                    parent_version = TagVersion.objects.select_for_update().get(pk=data.get('parent'))
                    parent_structure = parent_version.get_active_structure()
                    tag_structure.parent = parent_structure
                    tag_structure.structure = parent_structure.structure

                tag_structure.save()

            return Response(self.serialize(tag_version.to_search()))

    def partial_update(self, request, index=None, pk=None):
        tag = self.get_tag_object()

        if 'parent' in request.data:
            parent = request.data.pop('parent')
            parent_tag_version = TagVersion.objects.get(pk=parent)
            rep = tag.get_active_structure()
            parent_rep = parent_tag_version.tag.structures.get(structure=rep.structure)
            rep.parent = parent_rep
            rep.save()

        db_fields = [f.name for f in TagVersion._meta.get_fields()]
        db_fields_request_data = {}

        for f in db_fields:
            if f in request.data:
                db_fields_request_data[f] = request.data.pop(f)

        serializer = TagVersionWriteSerializer(tag, data=db_fields_request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if request.data:
            tag.update_search(request.data)

        return Response(serializer.data)

    def destroy(self, request, index=None, pk=None):
        obj = self.get_tag_object()
        obj.get_descendants(include_self=True).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

from __future__ import division

import copy
import datetime
import json
import logging
import math
import os
import tempfile

import six
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.utils import timezone
from django_filters.constants import EMPTY_VALUES
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Index, Q, FacetedSearch, TermsFacet
from rest_framework import exceptions, status
from rest_framework.decorators import detail_route, list_route
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from six import iteritems
from weasyprint import HTML

from ESSArch_Core.auth.models import Group, GroupGenericObjects
from ESSArch_Core.auth.util import get_objects_for_user, get_organization_groups
from ESSArch_Core.csv import UnicodeCSVWriter
from ESSArch_Core.ip.models import Agent, InformationPackage
from ESSArch_Core.ip.utils import get_cached_objid
from ESSArch_Core.mixins import PaginatedViewMixin
from ESSArch_Core.search import get_connection, DEFAULT_MAX_RESULT_WINDOW
from ESSArch_Core.tags.documents import Archive, VersionedDocType
from ESSArch_Core.tags.models import Structure, Tag, TagStructure, TagVersion
from ESSArch_Core.tags.serializers import TagVersionNestedSerializer, TagVersionSerializer, \
    TagVersionSerializerWithVersions, \
    TagVersionWriteSerializer
from ESSArch_Core.util import generate_file_response, remove_prefix
from tags.permissions import SearchPermissions
from tags.serializers import SearchSerializer

logger = logging.getLogger('essarch.epp.search')
EXPORT_FORMATS = ('csv', 'pdf')
SORTABLE_FIELDS = (
    {'name.keyword': {'unmapped_type': 'keyword'}},
    {'reference_code': {'unmapped_type': 'keyword'}}
)


class ComponentSearch(FacetedSearch):
    index = ['component', 'archive', 'document', 'information_package']
    fields = ['name', 'desc', 'attachment.content']

    facets = {
        # use bucket aggregations to define facets
        'index': TermsFacet(field='_index', min_doc_count=0),
        'parents': TermsFacet(field='parents', min_doc_count=0),
        'type': TermsFacet(field='type', min_doc_count=0),
        'archive': TermsFacet(field='archive', min_doc_count=0),
        'information_package': TermsFacet(field='ip', min_doc_count=0),
        'institution': TermsFacet(field='institution', min_doc_count=0),
        'organization': TermsFacet(field='organization', min_doc_count=0),
        'extension': TermsFacet(field='extension', min_doc_count=0),
    }

    def __init__(self, *args, **kwargs):
        self.query_params_filter = kwargs.pop('filter_values', {})
        self.start_date = self.query_params_filter.pop('start_date', None)
        self.end_date = self.query_params_filter.pop('end_date', None)
        self.archive = self.query_params_filter.pop('archive', None)
        self.personal_identification_number = self.query_params_filter.pop('personal_identification_number', None)
        self.user = kwargs.pop('user')
        self.filter_values = {
            'indices': self.query_params_filter.pop('indices', [])
        }

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

        organization_archives = get_objects_for_user(self.user, TagVersion.objects.filter(elastic_index='archive'), [])
        organization_archives = list(organization_archives.values_list('pk', flat=True))

        s = super(ComponentSearch, self).search()
        s = s.source(exclude=["attachment.content"])
        s = s.filter('term', current_version=True)

        s = s.query(Q('bool', should=[
            Q('terms', archive=organization_archives),
            Q('terms', _id=organization_archives)
        ]))

        if self.personal_identification_number not in EMPTY_VALUES:
            s = s.filter('term', personal_identification_numbers=self.personal_identification_number)

        if self.start_date not in EMPTY_VALUES:
            s = s.filter('range', end_date={'gte': self.start_date})

        if self.end_date not in EMPTY_VALUES:
            s = s.filter('range', start_date={'lte': self.end_date})

        if self.archive is not None:
            s = s.query(Q('bool', must=Q('script', script={
                'source': "(doc.containsKey('archive') && doc['archive'].value==params.archive) || doc['_id'].value==params.archive",
                'params': {'archive': self.archive},
            })))

        for filter_k, filter_v in six.iteritems(self.query_params_filter):
            if filter_v not in EMPTY_VALUES:
                s = s.query('match', **{filter_k: filter_v})

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

def get_information_package(id):
    return {'object_identifier_value': get_cached_objid(id)}

def get_organization(id):
    org = Agent.objects.get(pk=id)
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
        self.client = Elasticsearch()
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

        prefetched_structures = TagStructure.objects.select_related('tag__current_version', 'parent__tag__current_version')
        tag_version = TagVersion.objects.select_related('tag').prefetch_related(Prefetch('tag__structures', prefetched_structures))

        obj = get_object_or_404(tag_version, pk=id)
        user_archives = get_objects_for_user(self.request.user, tag_version.filter(elastic_index='archive'), []).values_list('pk', flat=True)
        if obj.get_root() is not None and obj.get_root().pk not in user_archives:
            raise exceptions.NotFound
        return obj

    def verify_sort_field(self, field, direction='asc'):
        for f in [field, '{}.keyword'.format(field)]:
            if f in SORTABLE_FIELDS:
                return direction + f
            for sf in copy.deepcopy(SORTABLE_FIELDS):
                if isinstance(sf, dict):
                    if f in sf:
                        sf[f]['order'] = direction
                        return sf
        return False

    def get_sorting(self, request):
        sort = list()
        ordering = request.query_params.get('ordering', '').strip()
        if ordering == '':
            return sort
        fields = ordering.split(',')
        for f in fields:
            direction = 'desc' if f.startswith('-') else 'asc'
            f = remove_prefix(f, '-')
            verified_f = self.verify_sort_field(f, direction)
            if verified_f is False:
                raise exceptions.ParseError('Invalid sort field: {}'.format(f))
            sort.append(verified_f)

        return sort


    def list(self, request, index=None):
        params = {key: value[0] for (key, value) in dict(request.query_params).iteritems()}
        query = params.pop('q', '')
        export = params.pop('export', None)

        if export is not None and export not in EXPORT_FORMATS:
            raise exceptions.ParseError('Invalid export format "{}"'.format(export))

        filters = {
            'extension': params.pop('extension', None),
            'index': params.pop('index', index),
            'type': params.pop('type', None),
            'information_package': params.pop('information_package', None),
            'institution': params.pop('institution', None),
            'organization': params.pop('organization', None),
        }

        for k, v in iteritems(filters):
            filters[k] = v.split(',') if v is not None else v

        filter_values = copy.copy(params)
        for f in ('page', 'page_size'):
            filter_values.pop(f, None)

        sort = self.get_sorting(request)
        s = ComponentSearch(query, filters=filters, filter_values=filter_values, sort=sort, user=self.request.user)

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
            max_results = DEFAULT_MAX_RESULT_WINDOW
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
            try:
                archive_data = get_archive(archive['key'])
                archive['name'] = archive_data['name']
            except NotFoundError:
                logger.warn('Archive "%s" not found in search index, it might be queued for indexing' % archive['key'])

        for ip in results_dict['aggregations']['_filter_information_package']['information_package']['buckets']:
            try:
                ip_data = get_information_package(ip['key'])
                ip['name'] = ip_data['object_identifier_value']
            except ObjectDoesNotExist:
                logger.warn('Information package "%s" not found' % ip['key'])

        for organization in results_dict['aggregations']['_filter_organization']['organization']['buckets']:
            try:
                organization_data = get_organization(organization['key'])
                organization['name'] = organization_data['name']
            except ObjectDoesNotExist:
                logger.error('Archivist organization "%s" not found' % organization['key'])

        if len(results_dict['_shards'].get('failures', [])):
            return Response(results_dict['_shards']['failures'], status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        r = {
            'hits': results_dict['hits']['hits'],
            'aggregations': results_dict['aggregations'],
        }

        if export is not None:
            return self.generate_report(results_dict['hits']['hits'], export, request.user)

        if self.paginator is not None:
            return Response(r, headers={'Count': results.hits.total})

        return Response(r)

    def generate_report(self, hits, format, user):
        template = 'search_results.html'.format()

        f = tempfile.TemporaryFile()
        formatted_hits = []

        for hit in hits:
            hit = hit['_source']
            try:
                hit['archive'] = get_archive(hit['archive'])
            except KeyError:
                pass
            formatted_hits.append(hit)

        if format == 'pdf':
            ctype = 'application/pdf'
            render = render_to_string(template, {'hits': formatted_hits, 'user': user, 'timestamp': timezone.now()})
            HTML(string=render).write_pdf(f)
        elif format == 'csv':
            ctype = 'text/csv'
            writer = UnicodeCSVWriter(f)
            for hit in formatted_hits:
                writer.writerow(
                    [hit.get('archive', {}).get('name'), hit.get('name'), hit.get('reference_code'), hit.get('name'),
                     hit.get('unit_dates', {}).get('date'), hit.get('desc')])
        else:
            raise ValueError('Unsupported format {}'.format(format))

        f.seek(0)
        name = 'search_results_{time}_{user}.{format}'.format(time=timezone.localtime(), user=user.username,
                                                              format=format)
        return generate_file_response(f, content_type=ctype, name=name)

    def serialize(self, obj):
        return obj.to_dict(include_meta=True)

    def verify_structure(self, tag_version, structure):
        query_filter = {}

        if structure is not None:
            query_filter['structure'] = structure

        try:
            if not tag_version.get_structures().filter(**query_filter).exists():
                if structure is None:
                    return None
                raise exceptions.ParseError('Structure "%s" does not exist for node' % structure)
        except ValidationError:
            raise exceptions.ParseError('Invalid structure id')

    def retrieve(self, request, index=None, pk=None):
        if index is None:
            return self.list(request, index=pk)

        tag = self.get_tag_object()
        structure = self.request.query_params.get('structure')
        self.verify_structure(tag, structure)
        context = {'structure': structure, 'user': request.user}
        serialized = TagVersionSerializerWithVersions(tag, context=context).data

        return Response(serialized)

    @detail_route(methods=['post'], url_path='send-as-email')
    def send_as_email(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        user = self.request.user

        if not user.email:
            raise exceptions.ParseError('Missing email address')

        metadata = tag.from_search()['_source']
        subject = u'Export: {}'.format(tag.name)

        body = u'\n'.join([u'{}: {}'.format(k, json.dumps(v, ensure_ascii=False)) for k, v in six.iteritems(metadata)])
        email = EmailMessage(subject=subject, body=body, to=[user.email])

        if tag.elastic_index == 'document':
            ip = tag.tag.information_package
            path = os.path.join(metadata['href'], metadata['filename'])
            email.attach(os.path.basename(path), ip.open_file(path, 'rb').read())

        email.send()
        return Response('Email sent to {}'.format(user.email))

    @detail_route(methods=['get'])
    def children(self, request, index=None, pk=None):
        parent = self.get_tag_object()
        structure = self.request.query_params.get('structure')
        self.verify_structure(parent, structure)
        context = {'structure': structure, 'user': request.user}
        children = parent.get_children(structure)

        if self.paginator is not None:
            paginated = self.paginator.paginate_queryset(children, request)
            serialized = TagVersionNestedSerializer(instance=paginated, many=True, context=context).data
            return self.paginator.get_paginated_response(serialized)

        return Response(TagVersionNestedSerializer(children, many=True, context=context).data)

    @detail_route(methods=['post'], url_path='new-version')
    def new_version(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        new_tag = tag.create_new()
        return Response()

    @detail_route(methods=['post'], url_path='new-structure')
    def new_structure(self, request, index=None, pk=None):
        try:
            name = request.data['name']
        except KeyError:
            raise exceptions.ParseError('Missing "name" parameter')

        with transaction.atomic():
            structure = Structure.objects.create(name=name)
            tag = self.get_tag_object()
            tag.get_active_structure().create_new(structure)

        return Response()

    @detail_route(methods=['patch'], url_path='set-as-current-version')
    def set_as_current_version(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        tag.set_as_current_version()
        return Response()

    @detail_route(methods=['post'], url_path='change-organization')
    def change_organization(self, request, index=None, pk=None):
        tag = self.get_tag_object()

        if tag.elastic_index != 'archive':
            raise exceptions.ParseError(detail='Only archives can be moved to other organizations')

        try:
            org_id = request.data['organization']
        except KeyError:
            raise exceptions.ParseError(detail='Missing "organization" parameter')

        try:
            org = get_organization_groups(request.user).get(pk=org_id)
        except Group.DoesNotExist:
            raise exceptions.ParseError('Invalid organization')

        ctype = ContentType.objects.get_for_model(tag)
        self._update_tag_metadata(tag, {'organization_group': org.pk})
        GroupGenericObjects.objects.update_or_create(object_id=tag.pk, content_type=ctype,
                                                     defaults={'group': org})
        return Response()

    def create(self, request, index=None):
        request.data.setdefault('index', index)
        refresh = request.query_params.get('refresh', False)
        serializer = SearchSerializer(data=request.data)
        organization = request.user.user_profile.current_organization

        if serializer.is_valid(raise_exception=True):
            data = serializer.data

            if data.get('index') == 'archive':
                if not request.user.has_perm('tags.create_archive'):
                    raise exceptions.PermissionDenied('You do not have permission to create new archives')
                if organization is None:
                    raise exceptions.ParseError('You must be part of an organization to create a new archive')

            with transaction.atomic():
                tag = Tag.objects.create()
                tag_structure = TagStructure(tag=tag)
                structure = data.get('structure')

                try:
                    structure = Structure.objects.get(pk=data.get('structure'))
                except Structure.DoesNotExist:
                    if structure is not None:
                        raise exceptions.ParseError(u'Structure {} does not exist'.format(data.get('structure')))

                if data.get('parent') is not None:
                    parent_version = TagVersion.objects.select_for_update().get(pk=data.get('parent'))
                    if structure is None:
                        raise exceptions.ParseError('Missing "structure" parameter')
                    parent_structure = parent_version.get_structures(structure).get()
                    tag_structure.parent = parent_structure
                    tag_structure.structure = parent_structure.structure
                elif structure is not None:
                    tag_structure.structure = structure
                tag_structure.save()

                tag_version = TagVersion.objects.create(
                    tag=tag, elastic_index=data['index'], name=data['name'],
                    type=data['type'], reference_code=data['reference_code'])
                tag.current_version = tag_version
                tag.save()

                if tag_version.elastic_index == 'archive':
                    org = request.user.user_profile.current_organization
                    org.add_object(tag_version)

                    # create descendants from structure
                    for unit in tag_structure.structure.units.all():
                        tag = Tag.objects.create()
                        tv = TagVersion.objects.create(tag=tag, elastic_index='component', name=unit.name,
                                                       reference_code=unit.reference_code)
                        tv.update_search({'archive': str(tag_version.pk), 'desc': unit.description})
                        tag.save()
                        ts = TagStructure(tag=tag, structure=structure)
                        if unit.parent is not None:
                            parent = unit.parent.reference_code
                            ts.parent = TagStructure.objects.filter(tree_id=tag_structure.tree_id,
                                                                    tag__versions__elastic_index='component')\
                                                            .filter(tag__versions__reference_code=parent)\
                                                            .distinct().get()
                        else:
                            ts.parent = tag_structure
                        ts.save()

                return Response(self.serialize(tag_version.to_search()))

    def _update_tag_metadata(self, tag, data):
        if 'parent' in data:
            try:
                structure = data.pop('structure')
            except KeyError:
                raise exceptions.ParseError('Missing "structure" parameter')
            structure = Structure.objects.get(pk=structure)
            parent = data.pop('parent')
            parent_tag_version = TagVersion.objects.get(pk=parent)
            parent_tag_structure = parent_tag_version.tag.structures.get(structure=structure)
            tag_structure, _ = TagStructure.objects.update_or_create(tag=tag.tag, structure=structure,
                                                                     defaults={'parent': parent_tag_structure})

        db_fields = [f.name for f in TagVersion._meta.get_fields()]
        db_fields_request_data = {}

        for f in db_fields:
            if f in data:
                db_fields_request_data[f] = data.pop(f)

        serializer = TagVersionWriteSerializer(tag, data=db_fields_request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        if data:
            tag.update_search(data)
        return tag.from_search()

    def partial_update(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        return Response(self._update_tag_metadata(tag, request.data))

    def _get_delete_field_script(self, field):
        field_path = '.'.join(field.split('.')[:-1])
        field_path = '.' + field_path if field_path else field_path
        field = field.split('.')[-1]

        return "ctx._source{path}.remove(\"{field}\")".format(path=field_path, field=field)

    def _delete_field(self, tag, field):
        index = tag.elastic_index
        script = self._get_delete_field_script(field)
        self.client.update(index=index, doc_type='doc', id=tag.pk, body={"script": script})

    @detail_route(methods=['post'], url_path='update-descendants')
    def update_descendants(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        include_self = request.query_params.get('include_self', False)
        for descendant in tag.get_descendants(include_self=include_self):
            self._update_tag_metadata(descendant, request.data)
            try:
                for field in request.query_params['deleted_fields'].split(','):
                    self._delete_field(descendant, field)
            except KeyError:
                pass

        return Response()

    @list_route(methods=['post'], url_path='mass-update')
    def mass_update(self, request, index=None):
        try:
            ids = request.query_params['ids'].split(',')
        except KeyError:
            raise exceptions.ParseError('Missing "ids" parameter')

        for id in ids:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            self.kwargs[lookup_url_kwarg] = id
            tag = self.get_tag_object()
            self._update_tag_metadata(tag, request.data)
            try:
                for field in request.query_params['deleted_fields'].split(','):
                    self._delete_field(tag, field)
            except KeyError:
                pass

        return Response()

    @detail_route(methods=['post'], url_path='delete-field')
    def delete_field(self, request, index=None, pk=None):
        tag = self.get_tag_object()
        try:
            field = request.data['field']
        except KeyError:
            raise exceptions.ParseError('Missing "field" parameter')

        self._delete_field(tag, field)
        return Response(tag.from_search())

    @detail_route(methods=['post'], url_path='remove-from-structure')
    def remove_from_structure(self, request, index=None, pk=None):
        obj = self.get_tag_object()
        try:
            structure = request.data['structure']
        except KeyError:
            raise exceptions.ParseError('Missing "structure" parameter')
        self.verify_structure(obj, structure)
        obj.tag.structures.get(structure=structure).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, index=None, pk=None):
        obj = self.get_tag_object()
        if request.query_params.get('delete_descendants', False):
            structure = request.query_params.get('structure')
            obj.get_descendants(structure=structure, include_self=True).delete()
        else:
            obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

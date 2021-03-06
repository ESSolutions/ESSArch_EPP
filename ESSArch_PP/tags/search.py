import copy
import csv
import datetime
import json
import logging
import math
import os
import tempfile

from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Prefetch
from django.template.loader import render_to_string
from django.utils import timezone
from django_filters.constants import EMPTY_VALUES
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Q, FacetedSearch, TermsFacet
from elasticsearch_dsl.connections import get_connection
from rest_framework import exceptions, serializers, status
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet
from weasyprint import HTML

from ESSArch_Core.auth.models import GroupGenericObjects
from ESSArch_Core.auth.serializers import ChangeOrganizationSerializer
from ESSArch_Core.auth.util import get_objects_for_user
from ESSArch_Core.ip.models import Agent
from ESSArch_Core.ip.utils import get_cached_objid
from ESSArch_Core.mixins import PaginatedViewMixin
from ESSArch_Core.search import DEFAULT_MAX_RESULT_WINDOW
from ESSArch_Core.tags.documents import Archive, VersionedDocType
from ESSArch_Core.tags.models import Structure, StructureUnit, Tag, TagStructure, TagVersion
from ESSArch_Core.tags.serializers import TagVersionNestedSerializer, \
    TagVersionSerializerWithVersions, \
    TagVersionWriteSerializer
from ESSArch_Core.util import generate_file_response, remove_prefix
from tags.permissions import SearchPermissions
from tags.serializers import SearchSerializer

logger = logging.getLogger('essarch.epp.search')
EXPORT_FORMATS = ('csv', 'pdf')
SORTABLE_FIELDS = (
    {'name.keyword': {'unmapped_type': 'keyword'}},
    {'reference_code.keyword': {'unmapped_type': 'keyword'}}
)


class ComponentSearch(FacetedSearch):
    index = ['component', 'archive', 'document', 'information_package']
    fields = [
        'reference_code.keyword^5', 'reference_code^3', 'name^2', 'desc', 'attachment.content',
        'attachment.keywords',
    ]

    facets = {
        # use bucket aggregations to define facets
        'index': TermsFacet(field='_index', min_doc_count=0),
        'parents': TermsFacet(field='parents', min_doc_count=0),
        'type': TermsFacet(field='type', min_doc_count=0),
        'archive': TermsFacet(field='archive', min_doc_count=0),
        'information_package': TermsFacet(field='ip', min_doc_count=0),
        'archive_creator': TermsFacet(field='archive_creator', min_doc_count=0),
        'archive_responsible': TermsFacet(field='archive_responsible', min_doc_count=0),
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

        super().__init__(*args, **kwargs)

    def search(self):
        """
        We override this to add filters on archive, start and end date

        We have to manually filter archives since we want to filter against a
        script field representing the archive which is the `archive` field on
        components and `_id` on archives.
        """

        organization_archives = get_objects_for_user(self.user, TagVersion.objects.filter(elastic_index='archive'), [])
        organization_archives = list(organization_archives.values_list('pk', flat=True))

        s = super().search()
        s = s.source(exclude=["attachment.content"])
        s = s.filter('term', current_version=True)

        s = s.query(Q('bool', should=[
            # no archive
            Q('bool', must=[Q('bool', **{'must_not': {'exists': {'field': 'archive'}}}),
                            Q('bool', **{'must_not': {'term': {'_index': 'archive-*'}}})]),
            # in archive connected to organization
            Q('terms', archive=organization_archives),
            # is archive connected to organization
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
                'source': (
                    "(doc.containsKey('archive') && doc['archive'].value==params.archive)"
                    "|| doc['_id'].value==params.archive"
                ),
                'params': {'archive': self.archive},
            })))

        for filter_k, filter_v in self.query_params_filter.items():
            if filter_v not in EMPTY_VALUES:
                s = s.query('match', **{filter_k: filter_v})

        return s

    def aggregate(self, search):
        """
        Add aggregations representing the facets selected, including potential
        filters.

        We override this to also aggregate on fields in `facets`
        """
        for f, facet in self.facets.items():
            agg = facet.get_aggregation()
            agg_filter = Q('match_all')
            for field, filter in self._filters.items():
                agg_filter &= filter
            search.aggs.bucket(
                '_filter_' + f,
                'filter',
                filter=agg_filter
            ).bucket(f, agg)

        search.aggs.bucket('_filter_archive', 'filter', filter=agg_filter).bucket(
            'archive', 'terms',
            script=(
                "doc['_index'].value != 'information_package'"
                " ? (doc.containsKey('archive')"
                " ? doc['archive'].value : doc['_id'].value) : null"
            )
        )

    def highlight(self, search):
        """
        We override this to set the highlighting options
        """

        pre_tags = ["<strong>"]
        post_tags = ["</strong>"]
        search = search.highlight_options(
            number_of_fragments=0, pre_tags=pre_tags, post_tags=post_tags, require_field_match=True
        )
        return super().highlight(search)


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
    permission_classes = (IsAuthenticated, SearchPermissions,)
    index = ComponentSearch.index
    lookup_field = 'pk'
    lookup_url_kwarg = None

    def __init__(self, *args, **kwargs):
        self.client = get_connection()
        super().__init__(*args, **kwargs)

    def get_view_name(self):
        return u'Search {}'.format(getattr(self, 'suffix', None))

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

    def get_tag_object(self, qs=None):
        # Perform the lookup filtering.
        lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field

        assert lookup_url_kwarg in self.kwargs, (
            'Expected view %s to be called with a URL keyword argument '
            'named "%s". Fix your URL conf, or set the `.lookup_field` '
            'attribute on the view correctly.' %
            (self.__class__.__name__, lookup_url_kwarg)
        )

        if qs is None:
            qs = TagVersion.objects.all()

        # Search for object in index by id
        id = self.kwargs[lookup_url_kwarg]

        prefetched_structures = TagStructure.objects.select_related(
            'tag__current_version', 'parent__tag__current_version'
        )
        tag_version = qs.select_related('tag').prefetch_related(Prefetch('tag__structures', prefetched_structures))

        obj = get_object_or_404(tag_version, pk=id)
        user_archives = get_objects_for_user(
            self.request.user,
            tag_version.filter(elastic_index='archive'), []
        ).values_list('pk', flat=True)

        root = obj.get_root()
        if root is not None and root.pk not in user_archives:
            obj_ctype = ContentType.objects.get_for_model(root)
            in_any_groups = GroupGenericObjects.objects.filter(object_id=str(root.pk), content_type=obj_ctype).exists()

            if in_any_groups:
                raise exceptions.NotFound

        logger.info(f"User '{self.request.user}' accessing tag object '{obj}'")
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

    @property
    def paginator(self):
        """
        The paginator instance associated with the view, or `None`.
        """
        pager = self.request.query_params.get('pager', None)
        if pager == 'none':
            return None

        return super().paginator

    def list(self, request):
        params = {key: value[0] for (key, value) in dict(request.query_params).items()}
        query = params.pop('q', '')
        export = params.pop('export', None)
        params.pop('pager', None)

        logger.info(f"User '{request.user}' queried for '{query}'")

        if export is not None and export not in EXPORT_FORMATS:
            raise exceptions.ParseError('Invalid export format "{}"'.format(export))

        filters = {
            'extension': params.pop('extension', None),
            'type': params.pop('type', None),
            'information_package': params.pop('information_package', None),
            'archive_creator': params.pop('archive_creator', None),
            'archive_responsible': params.pop('archive_responsible', None),
            'institution': params.pop('institution', None),
            'organization': params.pop('organization', None),
        }

        for k, v in filters.items():
            filters[k] = v.split(',') if v is not None else v

        filter_values = copy.copy(params)
        for f in ('page', 'page_size', 'ordering'):
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
            offset = (number - 1) * size
            s = s[offset:offset + size]
        else:
            s = s[0:DEFAULT_MAX_RESULT_WINDOW]

        try:
            results = s.execute()
        except TransportError:
            if self.paginator is not None:
                if offset + size > DEFAULT_MAX_RESULT_WINDOW:
                    raise exceptions.ParseError(
                        "Can't show more than {max} results".format(max=DEFAULT_MAX_RESULT_WINDOW)
                    )

            raise

        if self.paginator is not None:
            if size > 0 and results.hits.total > 0 and number > math.ceil(results.hits.total / size):
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

        return Response(r, headers={'Count': results.hits.total})

    def generate_report(self, hits, format, user):
        try:
            tag_versions = [hit.get('_source').get('name') for hit in hits]
        except Exception:
            tag_versions = hits
        logger.info(f"User '{user}' generating a {format} report, with tag versions: '{tag_versions}'")
        template = 'tags/search_results.html'.format()

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
            writer = csv.writer(f)
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

    def retrieve(self, request, pk=None):
        tag = self.get_tag_object()
        structure = self.request.query_params.get('structure')
        self.verify_structure(tag, structure)
        context = {'structure': structure, 'user': request.user}
        serialized = TagVersionSerializerWithVersions(tag, context=context).data

        return Response(serialized)

    def send_mass_email(self, ids, user):
        tags = []
        body = []
        attachments = []

        for id in ids:
            lookup_url_kwarg = self.lookup_url_kwarg or self.lookup_field
            self.kwargs[lookup_url_kwarg] = id
            tag = self.get_tag_object()
            tags.append(tag)
            metadata = tag.from_search()['_source']

            body.append(u'\n'.join([u'{}: {}'.format(
                k, json.dumps(v, ensure_ascii=False)
            ) for k, v in metadata.items()]))

            if tag.elastic_index == 'document':
                ip = tag.tag.information_package
                path = os.path.join(metadata['href'], metadata['filename'])
                attachments.append((os.path.basename(path), ip.open_file(path, 'rb').read()))

        subject = u'Export: {}'.format(u', '.join([t.name for t in tags]))
        body = '\n\n'.join(body)
        email = EmailMessage(subject=subject, body=body, to=[user.email])
        for attachment in attachments:
            email.attach(*attachment)
        email.send()
        return Response(u'Email sent to {}'.format(user.email))

    @action(detail=True, methods=['post'], url_path='send-as-email')
    def send_as_email(self, request, pk=None):
        tag = self.get_tag_object()
        user = self.request.user

        if not user.email:
            raise exceptions.ParseError('Missing email address')

        if request.data.get('include_descendants', False):
            ids = tag.get_descendants(include_self=True).values_list('id', flat=True)
            return self.send_mass_email(ids, user)

        metadata = tag.from_search()['_source']
        subject = u'Export: {}'.format(tag.name)

        body = u'\n'.join([u'{}: {}'.format(k, json.dumps(v, ensure_ascii=False)) for k, v in metadata.items()])
        email = EmailMessage(subject=subject, body=body, to=[user.email])

        if tag.elastic_index == 'document':
            ip = tag.tag.information_package
            path = os.path.join(metadata['href'], metadata['filename'])
            email.attach(os.path.basename(path), ip.open_file(path, 'rb').read())

        email.send()
        return Response(u'Email sent to {}'.format(user.email))

    @action(detail=False, methods=['post'], url_path='mass-email')
    def mass_email(self, request):
        try:
            ids = request.data['ids']
        except KeyError:
            raise exceptions.ParseError('Missing "ids" parameter')

        user = self.request.user
        if not user.email:
            raise exceptions.ParseError('Missing email address')

        return self.send_mass_email(ids, user)

    @action(detail=True, methods=['get'])
    def children(self, request, pk=None):
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

    @action(detail=True, methods=['get'], url_path='child-by-value')
    def child_by_value(self, request, pk=None):
        class ByValueSerializer(serializers.Serializer):
            field = serializers.CharField(required=True)
            value = serializers.CharField(required=True)
            structure = serializers.UUIDField(required=False)

        parent = self.get_tag_object()

        serializer = ByValueSerializer(data=request.query_params, context={'request': request.user})
        serializer.is_valid(raise_exception=True)

        field = serializer.validated_data['field']
        value = serializer.validated_data['value']
        structure = serializer.validated_data.get('structure')

        self.verify_structure(parent, structure)

        filter_values = {field: value, 'parent.id': pk}
        s = ComponentSearch('', filter_values=filter_values, user=self.request.user)
        results = s.execute().to_dict()['hits']

        if results['total'] > 1:
            raise exceptions.ParseError('More than 1 result, found {}'.format(results['total']))

        try:
            return Response(results['hits'][0])
        except IndexError:
            raise exceptions.NotFound()

    @action(detail=True, methods=['post'], url_path='new-version')
    def new_version(self, request, pk=None):
        tag = self.get_tag_object()
        tag.create_new()
        return Response()

    @action(detail=True, methods=['post'], url_path='new-structure')
    def new_structure(self, request, pk=None):
        try:
            name = request.data['name']
        except KeyError:
            raise exceptions.ParseError('Missing "name" parameter')

        with transaction.atomic():
            structure = Structure.objects.create(name=name)
            tag = self.get_tag_object()
            tag.get_active_structure().create_new(structure)

        return Response()

    @action(detail=True, methods=['patch'], url_path='set-as-current-version')
    def set_as_current_version(self, request, pk=None):
        tag = self.get_tag_object()
        tag.set_as_current_version()
        return Response()

    @action(detail=True, methods=['post'], url_path='change-organization')
    def change_organization(self, request, pk=None):
        tag = self.get_tag_object(qs=TagVersion.objects.filter(elastic_index='archive'))

        serializer = ChangeOrganizationSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        org = serializer.validated_data['organization']

        ctype = ContentType.objects.get_for_model(tag)
        self._update_tag_metadata(tag, {'organization_group': org.pk})
        GroupGenericObjects.objects.update_or_create(object_id=tag.pk, content_type=ctype,
                                                     defaults={'group': org})
        return Response()

    def create(self, request):
        serializer = SearchSerializer(data=request.data)
        organization = request.user.user_profile.current_organization

        if serializer.is_valid(raise_exception=True):
            data = serializer.validated_data

            if data.get('index') == 'archive':
                if not request.user.has_perm('tags.create_archive'):
                    raise exceptions.PermissionDenied('You do not have permission to create new archives')
                if organization is None:
                    raise exceptions.ParseError('You must be part of an organization to create a new archive')
            else:
                if not request.user.has_perm('tags.add_tag'):
                    raise exceptions.PermissionDenied('You do not have permission to create nodes')

            with transaction.atomic():
                tag = Tag.objects.create()
                tag_structure = TagStructure(tag=tag)
                structure = data.pop('structure')

                if data.get('index') != 'archive':
                    if 'structure_unit' in data:
                        structure_unit = StructureUnit.objects.get(pk=data.pop('structure_unit'))
                        tag_structure.structure_unit = structure_unit
                        tag_structure.structure = structure_unit.structure

                        archive_structure = TagStructure.objects.get(tag__versions=data.pop('archive'))
                        tag_structure.parent = archive_structure

                        tag_structure.save()

                    elif 'parent' in data:
                        parent_version = TagVersion.objects.select_for_update().get(pk=data.pop('parent'))
                        if structure is None:
                            parent_structure = parent_version.get_active_structure()
                        else:
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

                self._update_tag_metadata(tag_version, data)

                if tag_version.elastic_index == 'archive':
                    org = request.user.user_profile.current_organization
                    org.add_object(tag_version)

                    search_data = {}
                    if data.get('archive_creator'):
                        search_data['archive_creator'] = data.get('archive_creator')
                    if data.get('archive_responsible'):
                        search_data['archive_responsible'] = data.get('archive_responsible')

                    if search_data:
                        self._update_tag_metadata(tag_version, search_data)

                    # create descendants from structure
                    for unit in tag_structure.structure.units.all():
                        tag = Tag.objects.create()
                        tv = TagVersion.objects.create(tag=tag, elastic_index='component', name=unit.name,
                                                       reference_code=unit.reference_code, type=unit.type)
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

                return Response(self.serialize(tag_version.to_search()), status=status.HTTP_201_CREATED)

    def _update_tag_metadata(self, tag_version, data):
        if 'structure_unit' in data:
            try:
                structure = data.pop('structure')
            except KeyError:
                raise exceptions.ParseError('Missing "structure" parameter')

            structure = Structure.objects.get(pk=structure)
            tag_structure, _ = TagStructure.objects.get_or_create(tag=tag_version.tag, structure=structure)
            tag_structure.parent = tag_structure.get_root()
            tag_structure.structure_unit_id = data.get('structure_unit')
            tag_structure.save()

        elif 'parent' in data:
            try:
                structure = data.pop('structure')
            except KeyError:
                raise exceptions.ParseError('Missing "structure" parameter')

            parent = data.pop('parent')

            structure = Structure.objects.get(pk=structure)
            parent_tag_version = TagVersion.objects.get(pk=parent)
            parent_tag_structure = parent_tag_version.tag.structures.get(structure=structure)

            with transaction.atomic():
                tag_structure, _ = TagStructure.objects.get_or_create(tag=tag_version.tag, structure=structure)

                if not structure.is_move_allowed(tag_structure, parent_tag_structure):
                    raise exceptions.ParseError(
                        '{} cannot be moved to {}'.format(tag_version.name, parent_tag_version.name)
                    )

                tag_structure.parent = parent_tag_structure
                if tag_structure.parent != tag_structure.get_root():
                    tag_structure.structure_unit = None

                tag_structure.save()

        db_fields = [f.name for f in TagVersion._meta.get_fields()]
        db_fields_request_data = {}

        for f in db_fields:
            if f in data:
                db_fields_request_data[f] = data.pop(f)

        serializer = TagVersionWriteSerializer(tag_version, data=db_fields_request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        tag_version.update_search(data)
        return tag_version.from_search()

    def partial_update(self, request, pk=None):
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

    @action(detail=True, methods=['post'], url_path='update-descendants')
    def update_descendants(self, request, pk=None):
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

    @action(detail=False, methods=['post'], url_path='mass-update')
    def mass_update(self, request):
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

    @action(detail=True, methods=['post'], url_path='delete-field')
    def delete_field(self, request, pk=None):
        tag = self.get_tag_object()
        try:
            field = request.data['field']
        except KeyError:
            raise exceptions.ParseError('Missing "field" parameter')

        self._delete_field(tag, field)
        return Response(tag.from_search())

    @action(detail=True, methods=['post'], url_path='remove-from-structure')
    def remove_from_structure(self, request, pk=None):
        obj = self.get_tag_object()

        if obj.elastic_index == 'archive':
            perm = 'tags.delete_archive'
        else:
            perm = 'tags.delete_tag'

        if not request.user.has_perm(perm):
            raise exceptions.PermissionDenied('You do not have permission to delete this node')

        try:
            structure = request.data['structure']
        except KeyError:
            raise exceptions.ParseError('Missing "structure" parameter')
        self.verify_structure(obj, structure)
        obj.tag.structures.get(structure=structure).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def destroy(self, request, pk=None):
        obj = self.get_tag_object()

        if obj.elastic_index == 'archive':
            perm = 'tags.delete_archive'
        else:
            perm = 'tags.delete_tag'

        if not request.user.has_perm(perm):
            raise exceptions.PermissionDenied('You do not have permission to delete this node')

        if request.query_params.get('delete_descendants', False):
            structure = request.query_params.get('structure')
            obj.get_descendants(structure=structure, include_self=True).delete()
        else:
            obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

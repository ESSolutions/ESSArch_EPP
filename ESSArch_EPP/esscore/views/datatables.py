from django_datatables_view.base_datatable_view import DatatableMixin
from rest_framework import viewsets, mixins, permissions, views
from rest_framework.response import Response
from django.db.models import Q
from django.conf import settings

import logging
logger = logging.getLogger(__name__)

class DatatableBaseView(views.APIView, DatatableMixin):
    permission_classes = (permissions.IsAuthenticated,)
    absolute_url_link_flag = False
    qs = None

    def get_initial_queryset(self):
        if self.qs:
            return self.qs
        elif self.model:
            return self.model.objects.all()
        else:
            raise NotImplementedError('Need to provide a model or qs "queryset" or implement get_initial_queryset!')

    def filter_ip_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            ip_search_global = False
            if ip_search_global:
                # get global search value
                search = self._querydict.get('search[value]', None)
                col_data = self.extract_datatables_column_data()
                q = Q()
                for col_no, col in enumerate(col_data):
                    # apply global search to all searchable columns
                    if search and col['searchable']:
                        q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
    
                qs = qs.filter(q)

            # IP specific filter
            archiveobjects__StatusProcess__lt = self._querydict.get('archiveobjects__StatusProcess__lt', None)
            archiveobjects__StatusProcess__in = self._querydict.get('archiveobjects__StatusProcess__in', None)
            archiveobjects__StatusActivity__in = self._querydict.get('archiveobjects__StatusActivity__in', None)
            archiveobjects__StatusProcess_or_StatusActivity__in = self._querydict.get('archiveobjects__StatusProcess_or_StatusActivity__in', None)
            archiveobjects__exclude_generation_0_and_latest = self._querydict.get('archiveobjects__exclude_generation_0_and_latest', None)
            #exclude_aic_without_ips = self._querydict.get('exclude_aic_without_ips', None)
            if archiveobjects__StatusProcess__lt:
                qs = qs.filter(StatusProcess__lt = archiveobjects__StatusProcess__lt)
            if archiveobjects__StatusProcess__in:
                qs = qs.filter(StatusProcess__in = eval(archiveobjects__StatusProcess__in))
            if archiveobjects__StatusActivity__in:
                qs = qs.filter(StatusActivity__in = eval(archiveobjects__StatusActivity__in))
            if archiveobjects__StatusProcess_or_StatusActivity__in:
                StatusProcess__in, StatusActivity__in = eval(archiveobjects__StatusProcess_or_StatusActivity__in)
                qs = qs.filter(Q(StatusProcess__in = StatusProcess__in) | Q(StatusActivity__in = StatusActivity__in))
            if archiveobjects__exclude_generation_0_and_latest:
                if archiveobjects__exclude_generation_0_and_latest == 'true':
                    if qs.count() > 0:
                        latest_generation = qs.order_by('-Generation')[:1].get()
                        qs = qs.exclude(StatusProcess__in=[5000,5100], Generation__in=[0,latest_generation.Generation])
                    else:
                        qs = qs.exclude(Generation=0)
            #if exclude_aic_without_ips:
            #    if exclude_aic_without_ips == 'true':
            #        qs = qs.exclude(OAISPackageType=1, archiveobjects=[])       
        return qs
    
    def filter_extra_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            # Extra IP filter
            StatusProcess__lt = self._querydict.get('StatusProcess__lt', None)
            StatusProcess__in = self._querydict.get('StatusProcess__in', None)
            StatusActivity__in = self._querydict.get('StatusActivity__in', None)
            StatusProcess_or_StatusActivity__in = self._querydict.get('StatusProcess_or_StatusActivity__in', None)
            exclude_ip_without_aic = self._querydict.get('exclude_ip_without_aic', None)
            if StatusProcess__lt:
                qs = qs.filter(Q(StatusProcess__lt = StatusProcess__lt) | Q(OAISPackageType=1))
            if StatusProcess__in:
                qs = qs.filter(Q(StatusProcess__in = eval(StatusProcess__in)) | Q(OAISPackageType=1))
            if StatusActivity__in:
                qs = qs.filter(StatusActivity__in = eval(StatusActivity__in))
            if StatusProcess_or_StatusActivity__in:
                StatusProcess__in, StatusActivity__in = eval(StatusProcess_or_StatusActivity__in)
                qs = qs.filter(Q(StatusProcess__in = StatusProcess__in) | Q(StatusActivity__in = StatusActivity__in) | Q(OAISPackageType=1))
            if exclude_ip_without_aic:
                if exclude_ip_without_aic == 'true':
                    qs = qs.exclude(OAISPackageType__in=[0,2], aic_set__isnull=True)   
        return qs

    def filter_queryset(self, qs):
        """ If search['value'] is provided then filter all searchable columns using istartswith
        """
        if not self.pre_camel_case_notation:
            # get global search value
            search = self._querydict.get('search[value]', None)
            col_data = self.extract_datatables_column_data()
            q = Q()
            for col_no, col in enumerate(col_data):
                # apply global search to all searchable columns
                if search and col['searchable']:
                    q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})

                # column specific filter
                if col['search.value']:
                    qs = qs.filter(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): col['search.value']})
            qs = qs.filter(q)
            qs = self.filter_extra_queryset(qs)
        return qs
    
    def render_column(self, row, column):
        """ Renders a column on a row
        """

        if hasattr(row, 'get_%s_display' % column):
            # It's a choice field
            text = getattr(row, 'get_%s_display' % column)()
        else:
            try:
                text = getattr(row, column)
            except AttributeError:
                obj = row
                for part in column.split('.'):
                    if obj is None:
                        break
                    obj = getattr(obj, part)

                text = obj
        if text is None:
            text = self.none_string
        
        if hasattr(text,'all'):
            data = []
            for item in text.all():
                d={}
                for column in self.get_columns():
                    d[column]=self.render_column(item, column)
                data.append(d)
            text=data
        
        if text and hasattr(row, 'get_absolute_url') and self.absolute_url_link_flag:
            return '<a href="%s">%s</a>' % (row.get_absolute_url(), text)
        else:
            return text

    is_clean = False

    def prepare_results(self, qs):
        data = []
        for item in qs:
            d={}
            for column in self.get_columns():
                d[column]=self.render_column(item, column)
            data.append(d)
        return data

    def post(self, *args, **kwargs):
        return self.get(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        self.request = request
        response = None

        try:
            func_val = self.get_context_data(**kwargs)
            if not self.is_clean:
                assert isinstance(func_val, dict)
                response = dict(func_val)
                if 'result' not in response:
                    response['result'] = 'ok'
            else:
                response = func_val
        except KeyboardInterrupt:
            # Allow keyboard interrupts through for debugging.
            raise
        except Exception as e:
            #logger.error('JSON view error: %s' % request.path, exc_info=True)

            # Come what may, we're returning JSON.
            if hasattr(e, 'message'):
                msg = e.message
                msg += str(e)
            else:
                msg = _('Internal error') + ': ' + str(e)
            response = {'result': 'error',
                        'sError': msg,
                        'text': msg}

        return Response(response)
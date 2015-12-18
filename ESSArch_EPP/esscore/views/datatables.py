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
        if self.qs is not None:
            return self.qs
        elif self.model:
            return self.model.objects.all()
        else:
            raise NotImplementedError('Need to provide a model or qs "queryset" or implement get_initial_queryset!')
    
    def filter_extra_queryset(self, qs):
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
                    #q |= Q(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): search})
                    if col['name']:
                        q |= Q(**{'{0}__icontains'.format(col['name'].replace('.', '__')): search})
                    else:
                        print 'WARNING - colums.name is not defined in datatables'

                # column specific filter
                if col['search.value']:
                    #qs = qs.filter(**{'{0}__icontains'.format(self.columns[col_no].replace('.', '__')): col['search.value']})
                    if col['name']:
                        qs = qs.filter(**{'{0}__icontains'.format(col['name'].replace('.', '__')): col['search.value']})
                    else:
                        print 'WARNING - colums.name is not defined in datatables'                    
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
            exclude_filtered_from_information = self._querydict.get('exclude_filtered_from_information', None)
            if exclude_filtered_from_information:
                if exclude_filtered_from_information == 'true':
                    if self.pre_camel_case_notation:
                        response['iTotalDisplayRecords'] = response['iTotalRecords']
                    else:
                        response['recordsTotal'] = response['recordsFiltered']
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
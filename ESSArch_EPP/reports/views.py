from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Q

from essarch.models import ArchiveObject, eventIdentifier
from configuration.models import Path, Parameter

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, BaseUpdateView
from django.utils import timezone

from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import permission_required


class deliveryReport(ListView):
    """
    Delivery report
    """
    model = ArchiveObject
    template_name='reports/listdelivery.html'
    #context_object_name='access_list'
    #queryset=ArchiveObject.objects.filter(Q(StatusProcess=3000) | Q(OAISPackageType=1)).order_by('id','Generation')
    queryset=ArchiveObject.objects.filter(StatusProcess=3000).order_by('id','Generation')

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(deliveryReport, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(deliveryReport, self).get_context_data(**kwargs)
        context['type'] = 'delivery'
        context['label'] = 'Delivery report'
        ip_list = []
        a_list = context['object_list']
        for a in a_list: 
            #rel_obj_list = a.relaic_set.all().order_by('UUID__Generation')
            rel_obj_list = a.reluuid_set.all()
            #print 'rel_obj_list: %s' % rel_obj_list
            if rel_obj_list:
                #for rel_obj in a.relaic_set.all().order_by('UUID__Generation'):
                for rel_obj in a.reluuid_set.all():
                    #print 'rel_obj: %s' % rel_obj
                    aic_obj = rel_obj.AIC_UUID
                    ip_obj = rel_obj.UUID
                    ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                    if ip_obj_data_list:
                        ip_obj_data = ip_obj_data_list[0]
                    else:
                        ip_obj_data = None
                    ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                    if ip_obj_metadata_list:
                        ip_obj_metadata = ip_obj_metadata_list[0]
                    else:
                        ip_obj_metadata = None
                    ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
            else:
                aic_obj = None
                ip_obj = a
                ip_obj_data_list = ip_obj.archiveobjectdata_set.all()
                if ip_obj_data_list:
                    ip_obj_data = ip_obj_data_list[0]
                else:
                    ip_obj_data = None
                ip_obj_metadata_list = ip_obj.archiveobjectmetadata_set.all()
                if ip_obj_metadata_list:
                    ip_obj_metadata = ip_obj_metadata_list[0]
                else:
                    ip_obj_metadata = None
                ip_list.append([aic_obj,ip_obj,None,ip_obj_data,ip_obj_metadata])
        context['ip_list'] = ip_list

        Creator_list = []
        for aic_obj,ip_obj,test,ip_obj_data,ip_obj_metadata in ip_list:
            if aic_obj is not None:
                Creator_list.append(ip_obj.EntryAgentIdentifierValue) 
        #print '#####################################: %s' % str(Creator_list)
        Creator_list2 = []
        for i in list(set(Creator_list)):
            Creator_list2.append([i,Creator_list.count(i)])
        #print '#####################################: %s' % str(Creator_list2)
        
        context['Creator_list'] = sorted(Creator_list2)
        return context

class eventsReport(ListView):
    """
    events report
    """
    model = eventIdentifier
    template_name='reports/listevent.html'
    #context_object_name='access_list'
    #queryset=ArchiveObject.objects.filter(Q(StatusProcess=3000) | Q(OAISPackageType=1)).order_by('id','Generation')
    #queryset=ArchiveObject.objects.filter(StatusProcess=3000).order_by('id','Generation')

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(eventsReport, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(eventsReport, self).get_context_data(**kwargs)
        context['type'] = 'event'
        context['label'] = 'Events report'
        eventobject_list = context['object_list']
        
        event_list = []
        for i in eventobject_list:
            event_list.append(i.eventType)
        #print '#####################################: %s' % str(event_list)
        event_list2 = []
        for i in list(set(event_list)):
            event_list2.append([i,event_list.count(i)])
        #print '#####################################: %s' % str(event_list2)

        context['event_list'] = sorted(event_list2)
        return context
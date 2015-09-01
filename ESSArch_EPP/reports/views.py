'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.shortcuts import get_object_or_404
from django.db.models import Q

from essarch.models import ArchiveObject, eventIdentifier, eventType_codes
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
    queryset=ArchiveObject.objects.filter(Q(StatusProcess=3000) | Q(OAISPackageType=1)).order_by('id','Generation')

    @method_decorator(permission_required('essarch.list_accessqueue'))
    def dispatch(self, *args, **kwargs):
        return super(deliveryReport, self).dispatch( *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(deliveryReport, self).get_context_data(**kwargs)
        context['type'] = 'delivery'
        context['label'] = 'REPORTS - Delivery report'
        ip_list = []
        object_list = context['object_list']      
        for obj in object_list: 
            for ip in obj.get_ip_list(StatusProcess=3000):
                ip_list.append(ip)
        context['ip_list'] = ip_list

        Creator_list = []
        for aic_obj,ip_obj,test,ip_obj_data,ip_obj_metadata in ip_list:
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
        context['label'] = 'REPORTS - Log Events report'
        eventobject_list = context['object_list']
        
        eventCodes = eventType_codes.objects.values('code','desc_sv')
        eventCodesDict = {}
        for e in eventCodes:
            eventCodesDict[e['code']] = e['desc_sv']
        print(eventCodesDict)
        event_list = []
        for i in eventobject_list:
            event_list.append(i.eventType)
        
        #print '#####################################: %s' % str(event_list)
        event_list2 = []
        for i in list(set(event_list)):
            try:
                event_desc = eventCodesDict[int(i)]
            except KeyError:
                event_desc = '-'
            event_list2.append([i, event_desc, event_list.count(i)])
            
            #event_list2.append([i,event_list[i].eventDetail])
        #print '#####################################: %s' % str(event_list2)
        
        context['event_list'] = sorted(event_list2)
        return context
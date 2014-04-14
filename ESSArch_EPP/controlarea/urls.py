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
from django.conf.urls import patterns, url
from views import CheckinFromReceptionListView, CheckinFromReception, CheckinFromReceptionResult, \
                  CheckoutToWorkListView, CheckoutToWork, CheckoutToWorkResult, \
                  CheckinFromWorkListView, CheckinFromWork, CheckinFromWorkResult, \
                  CheckoutToGateFromWork, CheckoutToGateFromWorkResult, \
                  CheckinFromGateToWork, CheckinFromGateToWorkResult, \
                  CheckinFromGateListView, \
                  DiffCheckListView, DiffCheck, DiffCheckResult, \
                  PreserveIPListView, PreserveIP, PreserveIPResult, \
                  ControlareaDeleteIPListView, ControlareaDeleteIP, ControlareaDeleteIPResult

#import views

urlpatterns = patterns('', 
    url(r'^checkinfromreceptionlist/$', CheckinFromReceptionListView.as_view(),name='controlarea_checkinfromreception_list'),  
    url(r'^checkinfromreception/(?P<ip_uuid>[^&]*)/$', CheckinFromReception.as_view(), name='controlarea_checkinfromreception'),
    url(r'^checkinfromreceptionresult/(?P<pk>\d+)/$', CheckinFromReceptionResult.as_view(), name='controlarea_checkinfromreceptionresult'),  
    url(r'^checkouttoworklist/$', CheckoutToWorkListView.as_view(),name='controlarea_checkouttowork_list'),
    url(r'^checkouttowork/(?P<pk>\d+)/$', CheckoutToWork.as_view(), name='controlarea_checkouttowork'),
    url(r'^checkouttoworkresult/(?P<pk>\d+)/$', CheckoutToWorkResult.as_view(), name='controlarea_checkouttoworkresult'),
    url(r'^checkinfromworklist/$', CheckinFromWorkListView.as_view(),name='controlarea_checkinfromwork_list'),
    url(r'^checkinfromwork/(?P<pk>\d+)/$', CheckinFromWork.as_view(), name='controlarea_checkinfromwork'),
    url(r'^checkinfromworkresult/(?P<pk>\d+)/$', CheckinFromWorkResult.as_view(), name='controlarea_checkinfromworkresult'),
    url(r'^checkouttogatefromwork/$', CheckoutToGateFromWork.as_view(), name='controlarea_checkouttogatefromwork'),
    url(r'^checkouttogatefromworkresult/(?P<pk>\d+)/$', CheckoutToGateFromWorkResult.as_view(), name='controlarea_checkouttogatefromworkresult'),
    url(r'^checkinfromgatetowork/$', CheckinFromGateToWork.as_view(), name='controlarea_checkinfromgatetowork'),
    url(r'^checkinfromgatetoworkresult/(?P<pk>\d+)/$', CheckinFromGateToWorkResult.as_view(), name='controlarea_checkinfromgatetoworkresult'),
    url(r'^checkinfromgatelist/$', CheckinFromGateListView.as_view(),name='controlarea_checkinfromgate_list'),  
    url(r'^diffchecklist/$', DiffCheckListView.as_view(),name='controlarea_diffcheck_list'),
    url(r'^diffcheck/(?P<pk>\d+)/$', DiffCheck.as_view(), name='controlarea_diffcheck'),
    url(r'^diffcheckresult/(?P<pk>\d+)/$', DiffCheckResult.as_view(), name='controlarea_diffcheckresult'),
    url(r'^preserveiplist/$', PreserveIPListView.as_view(),name='controlarea_preserveip_list'),
    url(r'^preserveip/(?P<pk>\d+)/$', PreserveIP.as_view(), name='controlarea_preserveip'),
    url(r'^preserveipresult/(?P<pk>\d+)/$', PreserveIPResult.as_view(), name='controlarea_preserveipresult'),
    url(r'^controlareadeleteiplist/$', ControlareaDeleteIPListView.as_view(),name='controlarea_deleteip_list'),
    url(r'^controlareadeleteip/(?P<pk>\d+)/$', ControlareaDeleteIP.as_view(), name='controlarea_deleteip'),
    url(r'^controlareadeleteipresult/(?P<pk>\d+)/$', ControlareaDeleteIPResult.as_view(), name='controlarea_deleteipresult'),
)

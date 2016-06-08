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
from views import CheckinFromReceptionListView, CheckinFromReception,\
                  FromReceptionProgress,\
                  ToWorkListTemplateView,ToWorkListInfoView, CheckoutToWork,\
                  ToWorkProgress,\
                  FromWorkListTemplateView,FromWorkListInfoView, CheckinFromWork,\
                  FromWorkProgress,\
                  CheckoutToGateFromWork,CheckoutToGateProgress,\
                  CheckinFromGateToWork,CheckinFromGateProgress,\
                  CheckinFromGateListView,\
                  DiffCheckListTemplateView, DiffCheckListInfoView, DiffCheck,\
                  DiffcheckProgress,\
                  PreserveTemplateView,PreserveListInfoView, PreserveIP,\
                  PreserveProgress,\
                  DeleteIPListTemplateView, DeleteIPListInfoView, ControlareaDeleteIP,\
                  DeleteProgress,\
                  TasksInfo, TaskOverviewView,TestTaskView,ProgressTasksInfo, TaskResult

#import views

urlpatterns = patterns('',
    url(r'^checkinfromreceptionlist/$', CheckinFromReceptionListView.as_view(),name='controlarea_checkinfromreception_list'),
    url(r'^checkinfromreception/(?P<ip_uuid>[^&]*)/$', CheckinFromReception.as_view(), name='controlarea_checkinfromreception'),
    url(r'^fromreceptionprogress/(?P<taskid>[^&]*)/$', FromReceptionProgress.as_view(), name='controlarea_fromreceptionprogress'),
    url(r'^checkouttoworklist/$', ToWorkListTemplateView.as_view(),name='controlarea_checkouttowork_list'),
    url(r'^checkouttoworkinfo/$', ToWorkListInfoView.as_view(), name='controlarea_checkouttowork_info'),
    #url(r'^checkouttowork/(?P<pk>\d+)/$', CheckoutToWork.as_view(), name='controlarea_checkouttowork'),
    url(r'^checkouttowork/(?P<pk>[^&]*)/$', CheckoutToWork.as_view(), name='controlarea_checkouttowork'),
    url(r'^toworkprogress/(?P<taskid>[^&]*)/$', ToWorkProgress.as_view(), name='controlarea_checkouttoworkprogress'),
    url(r'^checkinfromworklist/$', FromWorkListTemplateView.as_view(),name='controlarea_checkinfromwork_list'),
    url(r'^checkinfromworkinfo/$', FromWorkListInfoView.as_view(), name='controlarea_checkinfromwork_info'),
    url(r'^checkinfromwork/(?P<pk>[^&]*)/$', CheckinFromWork.as_view(), name='controlarea_checkinfromwork'),
    url(r'^fromworkprogress/(?P<taskid>[^&]*)/$', FromWorkProgress.as_view(), name='controlarea_checkinfromworkprogress'),
    url(r'^checkouttogatefromwork/$', CheckoutToGateFromWork.as_view(), name='controlarea_checkouttogatefromwork'),
    url(r'^checkouttogateprogress/(?P<taskid>[^&]*)/$', CheckoutToGateProgress.as_view(), name='controlarea_checkouttogate_progress'),
    url(r'^checkinfromgatetowork/$', CheckinFromGateToWork.as_view(), name='controlarea_checkinfromgatetowork'),
    url(r'^checkinfromgateprogress/(?P<taskid>[^&]*)/$', CheckinFromGateProgress.as_view(), name='controlarea_checkinfromgate_progress'),
    url(r'^checkinfromgatelist/$', CheckinFromGateListView.as_view(),name='controlarea_checkinfromgate_list'),
    url(r'^diffchecklist/$', DiffCheckListTemplateView.as_view(),name='controlarea_diffcheck_list'),
    url(r'^diffcheckinfo/$', DiffCheckListInfoView.as_view() ,name='controlarea_diffcheck_info'),
    #url(r'^diffcheck/(?P<pk>\d+)/$', DiffCheck.as_view(), name='controlarea_diffcheck'),
    url(r'^diffcheck/(?P<pk>[^&]*)/$', DiffCheck.as_view(), name='controlarea_diffcheck'),
    url(r'^diffcheckprogress/(?P<taskid>[^&]*)/$', DiffcheckProgress.as_view(), name='controlarea_diffcheckprogress'),
    url(r'^preserveiplist/$', PreserveTemplateView.as_view(),name='controlarea_preserveip_list'),
    url(r'^preserveipinfo/$', PreserveListInfoView.as_view(), name='controlarea_preserveip_info'),
    #url(r'^preserveip/(?P<pk>\d+)/$', PreserveIP.as_view(), name='controlarea_preserveip'),
    url(r'^preserveip/(?P<pk>[^&]*)/$', PreserveIP.as_view(), name='controlarea_preserveip'),
    url(r'^preserveprogress/(?P<taskid>[^&]*)/$', PreserveProgress.as_view(), name='controlarea_checkinfromworkprogress'),
    url(r'^controlareadeleteiplist/$', DeleteIPListTemplateView.as_view(),name='controlarea_deleteip_list'),
    url(r'^controlareadeleteipinfo/$', DeleteIPListInfoView.as_view(), name='controlarea_deleteip_info'),
    #url(r'^controlareadeleteip/(?P<pk>\d+)/$', ControlareaDeleteIP.as_view(), name='controlarea_deleteip'),
    url(r'^controlareadeleteip/(?P<pk>[^&]*)/$', ControlareaDeleteIP.as_view(), name='controlarea_deleteip'),
    url(r'^deleteprogress/(?P<taskid>[^&]*)/$', DeleteProgress.as_view(), name='controlarea_deleteprogress'),
    url(r'^taskoverview/$', TaskOverviewView.as_view(), name='taskoverview'),
    url(r'^tasksinfo/(?P<days>[^&]*)$', TasksInfo.as_view(), name='tasksinfo'),
    url(r'^progress/$', ProgressTasksInfo.as_view(), name='progress'),
    url(r'^testtask/$', TestTaskView.as_view(), name='testtask'),
    url(r'^testtask/(?P<time>[^&]*)/$', TestTaskView.as_view(), name='testtask'),
    url(r'^taskresult/(?P<taskid>[^&]*)/$', TaskResult.as_view(), name='taskresult'),
)
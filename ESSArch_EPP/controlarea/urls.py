from django.conf.urls.defaults import *
from views import CheckinFromReceptionListView, CheckinFromReception, CheckoutToWorkListView, CheckoutToWork, \
                  CheckinFromWorkListView, CheckinFromWork, DiffCheckListView, DiffCheckWork, IngestIPListView, IngestIP

#import views

urlpatterns = patterns('', 
    url(r'^checkinfromreceptionlist/$', CheckinFromReceptionListView.as_view(),name='controlarea_checkinfromreception_list'),  
    url(r'^checkinfromreception/(?P<ip_uuid>[^&]*)/$', CheckinFromReception.as_view(), name='controlarea_checkinfromreception'),  
    url(r'^checkouttoworklist/$', CheckoutToWorkListView.as_view(),name='controlarea_checkouttowork_list'),
    url(r'^checkouttowork/(?P<pk>\d+)/$', CheckoutToWork.as_view(), name='controlarea_checkouttowork'),
    url(r'^checkinfromworklist/$', CheckinFromWorkListView.as_view(),name='controlarea_checkinfromwork_list'),
    url(r'^checkinfromwork/(?P<pk>\d+)/$', CheckinFromWork.as_view(), name='controlarea_checkinfromwork'),
    url(r'^diffchecklist/$', DiffCheckListView.as_view(),name='controlarea_diffcheck_list'),
    url(r'^diffcheckwork/(?P<pk>\d+)/$', DiffCheckWork.as_view(), name='controlarea_diffcheckwork'),
    url(r'^ingestiplist/$', IngestIPListView.as_view(),name='controlarea_ingestip_list'),
    url(r'^ingestip/(?P<pk>\d+)/$', IngestIP.as_view(), name='controlarea_ingestip'),
)

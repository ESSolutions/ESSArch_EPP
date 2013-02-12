from django.conf.urls.defaults import *
from views import CheckinFromReceptionListView, CheckinFromReception, CheckoutToWorkListView, CheckoutToWork, \
                  CheckinFromWorkListView, CheckinFromWork, DiffCheckListView, DiffCheckWork, IngestIPListView, IngestIP,\
                  NoteCreate ,NoteUpdate, NoteDelete, NoteDetail

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
#    url(r'^detail/(?P<pk>\d+)/$', NoteDetail.as_view(), name='notes_detail'),  
#    url(r'^new/$', NoteCreate.as_view(), name='notes_create'),  
#    url(r'^update/(?P<pk>\d+)/$', NoteUpdate.as_view(), name='notes_update'),  
#    url(r'^delete/(?P<pk>\d+)/$', NoteDelete.as_view(), name='notes_delete'),  
)

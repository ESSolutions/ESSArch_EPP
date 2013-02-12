from django.conf.urls.defaults import *
from views import IngestList, IngestDetail, IngestCreate, IngestUpdate, IngestDelete, ArchObjectListUpdate

#import views

urlpatterns = patterns('',   
    url(r'^listobj/$', ArchObjectListUpdate.as_view(),name='ingest_listobj'),
    url(r'^listobjupd/(?P<pk>\d+)/$', ArchObjectListUpdate.as_view(),name='ingest_listobjupd'),
    url(r'^list/$', IngestList.as_view(),name='ingest_list'),
    url(r'^detail/(?P<pk>\d+)/$', IngestDetail.as_view(), name='ingest_detail'),
    url(r'^new$', IngestCreate.as_view(), name='ingest_create_parameter'),
    url(r'^new/$', IngestCreate.as_view(), name='ingest_create'),
    url(r'^new/(?P<ip_uuid>[^&]*)/$', IngestCreate.as_view(), name='ingest_create_ip_uuid'),
    url(r'^update/(?P<pk>\d+)/$', IngestUpdate.as_view(), name='ingest_update'),
    url(r'^delete/(?P<pk>\d+)/$', IngestDelete.as_view(), name='ingest_delete'),  
)
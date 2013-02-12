from django.conf.urls.defaults import *
from views import AccessList, AccessDetail, AccessCreate ,AccessUpdate, AccessDelete, ArchObjectList

#import views

urlpatterns = patterns('',   
    url(r'^listobj/$', ArchObjectList.as_view(),name='access_listobj'),
    url(r'^list/$', AccessList.as_view(),name='access_list'),
    url(r'^detail/(?P<pk>\d+)/$', AccessDetail.as_view(), name='access_detail'),
    url(r'^new$', AccessCreate.as_view(), name='access_create_parameter'),
    url(r'^new/$', AccessCreate.as_view(), name='access_create'),
    url(r'^new/(?P<ip_uuid>[^&]*)/$', AccessCreate.as_view(), name='access_create_ip_uuid'),
    url(r'^update/(?P<pk>\d+)/$', AccessUpdate.as_view(), name='access_update'),
    url(r'^delete/(?P<pk>\d+)/$', AccessDelete.as_view(), name='access_delete'),  
)
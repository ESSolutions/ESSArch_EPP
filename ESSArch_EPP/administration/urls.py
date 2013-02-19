from django.conf.urls.defaults import *
from views import storageMediumList, storageMediumDetail, storageList, robotList, robotReqCreate, robotInventory

#import views

urlpatterns = patterns('',   
    url(r'^liststoragemedium/$', storageMediumList.as_view(),name='admin_liststoragemedium'),
    url(r'^detailstoragemedium/(?P<pk>\d+)/$', storageMediumDetail.as_view(), name='admin_detailstoragemedium'),
    url(r'^liststorage/$', storageList.as_view(),name='admin_liststorage'),
    url(r'^listrobot/$', robotList.as_view(),name='admin_listrobot'),
    url(r'^newrobotreq/(?P<storageMediumID>[^&]*)/(?P<command>\d+)/$', robotReqCreate.as_view(), name='admin_create_robotreq'),
    url(r'^robotinventory/(?P<command>\d+)/$', robotInventory.as_view(), name='admin_create_robotinventory'),
)
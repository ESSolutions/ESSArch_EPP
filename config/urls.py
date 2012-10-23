#from django.conf.urls.defaults import patterns, url
from django.conf.urls import patterns, include, url
from django.views.generic import DetailView, ListView

from django.conf import settings

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Configuration URLS:
    url(r'^$', 'configuration.views.index', name='home'),
    url(r'^logout$', 'configuration.views.logout_view'),
    url(r'^changepassword$', 'configuration.views.change_password'),
    #url(r'^configuration/parameters$', 'configuration.views.parameters'),
    #url(r'^configuration/parameters/(?P<username>\w+)$', 'configuration.views.userparameters'),


    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login' ),

    # StorageLogistics_ws URLS:
    url(r'^webservice/StorageLogisticsService$', "storagelogistics.views.dispatch"),

    # grappelli admin
    #(r'^grappelli/', include('grappelli.urls')),
)

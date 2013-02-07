from django.conf.urls.defaults import *

urlpatterns = patterns('',
    url(r'^changepassword$', 'configuration.views.change_password'),
    url(r'^install_defaults$', 'configuration.views.installogdefaults'),
    url(r'^install_defaultschemas$', 'configuration.views.installdefaultschemaprofiles'),
    url(r'^install_defaultparameters$', 'configuration.views.installdefaultparameters'),
    url(r'^install_defaultusers$', 'configuration.views.createdefaultusers'),
    #url(r'^parameters$', 'configuration.views.parameters'),
    #url(r'^parameters/(?P<username>\w+)$', 'configuration.views.userparameters'),
)
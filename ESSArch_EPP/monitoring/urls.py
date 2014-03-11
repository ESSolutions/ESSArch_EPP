from django.conf.urls import patterns, url
from monitoring.views import sysstat, sysinfo

urlpatterns = patterns('',
    url(r'^sysstat/$', sysstat, name='monitoring_sysstat'),
    url(r'^sysinfo/$', sysinfo, name='monitoring_sysinfo'),
)

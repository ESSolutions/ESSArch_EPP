from django.conf.urls import url
from monitoring.views import sysstat, sysinfo

urlpatterns = [
    url(r'^sysstat/$', sysstat, name='monitoring_sysstat'),
    url(r'^sysinfo/$', sysinfo, name='monitoring_sysinfo'),
]

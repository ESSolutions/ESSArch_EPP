from django.conf.urls.defaults import *
from views import deliveryReport, eventsReport

#import views

urlpatterns = patterns('',   
    url(r'^deliveryreport/$', deliveryReport.as_view(),name='reports_deliveryreport'),
    url(r'^eventsreport/$', eventsReport.as_view(),name='reports_eventsreport'),
)
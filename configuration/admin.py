from configuration.models import Parameter, LogEvent
from django.contrib import admin


class LogEventAdmin( admin.ModelAdmin ):
    list_display = ( 'eventDetail', 'eventType' )
    search_fields = ( 'eventDetail', )

admin.site.register( LogEvent, LogEventAdmin )
 

class ParameterAdmin( admin.ModelAdmin ):
    list_display = ( 'username', 'policy_id', 'receipt_mail' )
    search_fields = ( 'username', )


admin.site.register(Parameter, ParameterAdmin)

#from django.contrib.auth.models import Permission
#admin.site.register(Permission)

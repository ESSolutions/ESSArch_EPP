from django import forms
from django.core.validators import validate_email


class LogEventForm(forms.Form):
    eventType   = forms.IntegerField()
    eventDetail = forms.CharField( max_length = 200 )


    

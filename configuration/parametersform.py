from django import forms
from django.core.validators import validate_email


class EmailField(forms.CharField):
    default_error_messages = {
        'invalid': (u'Enter a valid e-mail address.'),
        }
    default_validators = [validate_email]


class ParametersForm(forms.Form):
    agent_identifier_value         = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    label                          = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    archivist_organization         = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    archivist_organization_note    = forms.CharField( widget=forms.Textarea,
                                   required=False) 
    creator_organization           = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    creator_organization_note      = forms.CharField( widget=forms.Textarea,
                                   required=False ) 
    creator_individual             = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    creator_individual_email       = EmailField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    creator_individual_phone       = forms.CharField( max_length = 50,
                                   widget=forms.TextInput(attrs={'size':'30'}),
                                   required=False )
    
    preservation_organization      = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    preservation_organization_note = forms.CharField( widget=forms.Textarea,
                                   required=False ) 
    preservation_software          = forms.CharField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}),
                                   required=False )
    policy_id                      = forms.IntegerField(
                                   widget=forms.TextInput(attrs={'size':'10'}) )
    receipt_mail                   = EmailField( max_length = 200,
                                   widget=forms.TextInput(attrs={'size':'52'}) )


    mets_namespace                 = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    mods_namespace                 = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    mets_schemalocation            = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    mets_profile                   = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    premis_namespace               = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    premis_schemalocation          = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    premis_version                 = forms.CharField( max_length = 50,
                                   widget=forms.TextInput(attrs={'size':'10'}) )
    xlink_namespace                = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )

    xsi_namespace                  = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    xsd_namespace                  = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    mix_namespace                  = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    mix_schemalocation             = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    addml_namespace                = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    addml_schemalocation           = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    xhtml_namespace                = forms.URLField( max_length = 400,
                                   widget=forms.TextInput(attrs={'size':'52'}) )
    xhtml_schemalocation           = forms.URLField( max_length = 400, 
                                   widget=forms.TextInput(attrs={'size':'52'}) )

    

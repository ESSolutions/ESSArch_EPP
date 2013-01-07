'''
    ESSArch - ESSArch is an Electronic Archive system
    Copyright (C) 2010-2013  ES Solutions AB, Henrik Ek

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

    Contact information:
    Web - http://www.essolutions.se
    Email - essarch@essolutions.se
'''
__majorversion__ = "2.5"
__revision__ = "$Revision$"
__date__ = "$Date$"
__author__ = "$Author$"
import re
__version__ = '%s.%s' % (__majorversion__,re.sub('[\D]', '',__revision__))
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

    

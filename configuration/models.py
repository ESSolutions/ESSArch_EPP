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
from django.db import models
from django.contrib import admin

import datetime
import sys


class LogEvent(models.Model):
    #eventIdentifierType            = models.CharField( max_length = 36, blank=True )
    #eventIdentifierTypeValue       = models.CharField( max_length = 36 )
    eventType                      = models.IntegerField( default=0, unique=True )
    #eventDateTime                  = models.DateTimeField( default=datetime.datetime.now() )
    eventDetail                    = models.CharField( max_length = 255 )
    #eventOutcome                   = models.IntegerField( default=0 )
    #eventOutcomeDetailNote         = models.CharField( max_length = 255 )
    #linkingAgentIdentifierType     = models.CharField( max_length = 36 )
    #linkingAgentIdentifierValue    = models.CharField( max_length = 255 )
    #linkingObjectIdentifierType    = models.CharField( max_length = 36 )
    #linkingObjectIdentifierValue   = models.CharField( max_length = 255 )

 

    class Meta:
        ordering = ["eventType"]

    def __unicode__(self):
        # create a unicode representation of this object
        return self.eventDetail

    def populate_from_form(self, form):
        # pull out all fields from a form and use them to set
        # the values of this Parameter object.
        for field in LogEvent._meta.fields:
            if field.name in form.cleaned_data:
                setattr( self, field.name, form.cleaned_data[field.name] )

    def get_value_array(self):
        # make an associative array of all fields  mapping the field
        # name to the current value of the field
        return { field.name: field.value_to_string(self) 
                 for field in LogEvent._meta.fields }



class InfoXML(models.Model):
    template = models.TextField()

class Parameter(models.Model):
    username                       = models.CharField( max_length = 255 )
    agent_identifier_value         = models.CharField( max_length = 255,
                                                       default="ESSArch_Globen",
                                                       blank=True )
    label                          = models.CharField( max_length = 255,
                                                       default="ESS Exempel SIP",
                                                       blank=True )
    archivist_organization         = models.CharField( max_length = 255,
                                                       blank=True )
    archivist_organization_note    = models.TextField( blank=True )
    creator_organization           = models.CharField( max_length = 255,
                                                       blank=True )
    creator_organization_note      = models.TextField( blank=True )
    creator_individual             = models.CharField( max_length = 255,
                                                       blank=True )
    creator_individual_email       = models.CharField( max_length = 255,
                                                       blank=True )
    creator_individual_phone       = models.CharField( max_length = 50,
                                                       blank=True )
    
    preservation_organization      = models.CharField( max_length = 255,
                                                       blank=True )
    preservation_organization_note = models.TextField( blank=True )    
    preservation_software          = models.CharField( max_length = 255,
                                                       blank=True )
    policy_id                      = models.IntegerField( default=1,
                                                          blank=True )
    receipt_mail                   = models.CharField( max_length = 255,
                                                       blank=True )

    mets_namespace                 = models.URLField( max_length = 400,
        default="http://xml.ra.se/METS/",
                                                      blank=True )
    mods_namespace                 = models.URLField( max_length = 400,
        default="http://www.loc.gov/mods/v3",
                                                      blank=True )
    mets_schemalocation            = models.URLField( max_length = 400,
        default="http://xml.ra.se/METS/SWEIP_METS.xsd",
                                                       blank=True )
    mets_profile                   = models.URLField( max_length = 400,
        default="http://xml.ra.se/METS/SWEIP.xml")
    premis_namespace               = models.URLField( max_length = 400,
        default="http://xml.ra.se/PREMIS",
                                                      blank=True )
    premis_schemalocation          = models.URLField( max_length = 400,
        default="http://xml.ra.se/PREMIS/RA_PREMIS.xsd",
                                                      blank=True )
    premis_version                 = models.CharField( max_length = 50,
                                                       default="2.0",
                                                       blank=True )
    xlink_namespace                = models.URLField( max_length = 400,
        default="http://www.w3.org/1999/xlink",
                                                      blank=True )

    xsi_namespace                  = models.URLField( max_length = 400,
        default="http://www.w3.org/2001/XMLSchema-instance",
                                                      blank=True )
    xsd_namespace                  = models.URLField( max_length = 400,
        default="http://www.w3.org/2001/XMLSchema",
                                                      blank=True )
    mix_namespace                  = models.URLField( max_length = 400,
        default="http://xml.ra.se/MIX",
                                                      blank=True )
    mix_schemalocation             = models.URLField( max_length = 400,
        default="http://xml.ra.se/MIX/RA_MIX.xsd",
                                                      blank=True )
    addml_namespace                = models.URLField( max_length = 400,
        default="http://xml.ra.se/addml",
                                                      blank=True )
    addml_schemalocation           = models.URLField( max_length = 400,
        default="http://xml.ra.se/addml/ra_addml.xsd",
                                                      blank=True )
    xhtml_namespace                = models.URLField( max_length = 400,
        default="http://www.w3.org/1999/xhtml",
                                                      blank=True )
    xhtml_schemalocation           = models.URLField( max_length = 400,
        default="http://www.w3.org/MarkUp/SCHEMA/xhtml11.xsd",
                                                      blank=True )

    class Meta:
        ordering = ["username"]

    def __unicode__(self):
        # create a unicode representation of this object
        return self.username


    def populate_from_form(self, form):
        # pull out all fields from a form and use them to set
        # the values of this Parameter object.
        for field in Parameter._meta.fields:
            if field.name not in [ "id", "username" ]:
                setattr( self, field.name, form.cleaned_data[field.name] )

    def get_value_array(self):
        # make an associative array of all fields  mapping the field
        # name to the current value of the field
        return { field.name: field.value_to_string(self) 
                 for field in Parameter._meta.fields }


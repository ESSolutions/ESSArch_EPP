from django.db import models
from django.core.urlresolvers import reverse

class MyFile(object):
    media                       = ''
    EntryAgentIdentifierValue   = ''
    label                       = ''
    startdate                   = ''
    enddate                     = ''
    createdate                  = ''
    iptype                      = ''
    uuid                        = ''
    aic_uuid                    = ''
    directory                   = ''
    site_profile                = ''
    state                       = ''
    zone                        = ''
    progress                    = 0

class permission(models.Model):
    class Meta:
        permissions = (
            ("CheckinFromReception", "CheckinFromReception"),
            ("CheckoutToWork", "CheckoutToWork"),
            ("CheckinFromWork", "CheckinFromWork"),
            ("CheckoutToGate", "CheckoutToGate"),
            ("CheckinFromGate", "CheckinFromGate"),
            ("DiffCheck", "DiffCheck"),
        )

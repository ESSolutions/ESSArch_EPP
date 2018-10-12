# -*- coding: utf-8 -*-

from __future__ import absolute_import

from soapfish.core import SOAPRequest
from soapfish.soap_dispatch import SOAPDispatcher

__all__ = ['django_dispatcher']

import logging
logger = logging.getLogger('essarch.storagelogistics')

class DjangoEnvironWrapper(object):

    def __init__(self, environ):
        self.environ = environ

    def get(self, name, default=None):
        cgi_name = 'HTTP_' + name
        for key in (name, cgi_name):
            if key in self.environ:
                return self.environ[key]
        return default


def django_dispatcher(service, **dispatcher_kwargs):
    from django.http import HttpResponse
    from django.views.decorators.csrf import csrf_exempt

    def django_dispatch(request):
        soap_request = SOAPRequest(DjangoEnvironWrapper(request.environ), request.body)
        soap_request._original_request = request
        soap_dispatcher = SOAPDispatcher(service, **dispatcher_kwargs)
        soap_response = soap_dispatcher.dispatch(soap_request)

        response = HttpResponse(soap_response.http_content)
        response.status_code = soap_response.http_status_code
        if soap_response.http_status_code>200:
            logger.error('status_code: %s', response.status_code)
            logger.error('http_content: %s', repr(soap_response.http_content))
        if soap_response.http_status_code==200:
            logger.debug('status_code: %s', response.status_code)
            logger.debug('http_content: %s', repr(soap_response.http_content))
        for k, v in soap_response.http_headers.items():
            response[k] = v
        return response

    return csrf_exempt(django_dispatch)

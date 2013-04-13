"""
Middleware to automatically set the schema (namespace).

if request.user.is_staff, then look for a ?__schema=XXX and set the schema to that.

Otherwise, set the schema to the one associated with the logged in user.


"""

import logging
import re

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError
from django.http import HttpResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _

from models import Schema

logger = logging.getLogger('multi_schema')

def activate_schema(available_schemata, session):
    """
    Activate the session's schema
    """
    if available_schemata.count() == 1:
        schema = available_schemata.get()
        session['schema'] = schema.schema
        schema.activate()
        return True
    
    if session.get('schema', None):
        try:
            available_schemata.get(pk=session['schema']).activate()
        except ObjectDoesNotExist:
            logger.warning(
                u'Unable to find Schema matching query: %s' % session['schema']
            )
            session.pop('schema')

class SchemaMiddleware:
    """
    Middleware to set the postgres schema for the current request.
    
    The schema that will be used is stored in the session. A lookup will
    occur (but this could easily be cached) on each request.
    
    To change schema, simply request a page with a querystring of:
    
        https://example.com/page/?__schema=<schema-name>
    
    The schema will be changed (or cleared, if this user cannot view 
    that schema), and the page will be re-loaded (if it was a GET).
    
    Alternatively, you may add a request header:
    
        X-Change-Schema: <schema-name>
    
    This will not cause a redirect to the same page without query string. It
    is the preferred method, because of that.
    
    There is also an injected url route:
    
        https://example.com/__change_schema__/<schema-name>/
    
    This is designed to be used from AJAX requests, or as part of
    an API call, as it returns a status code (and a short message) 
    about the schema change request.
    
    """
    def process_request(self, request):
        available_schemata = Schema.objects.none()
        if request.user.is_anonymous():
            request.session['schema'] = None
            return None
        if request.user.is_staff or request.user.is_superuser:
            available_schemata = Schema.objects
        else:
            available_schemata = request.user.schemata
        
        # Ways of changing the schema.
        # 1. URL /__change_schema__/<name>/
        if request.path.startswith('/__change_schema__/'):
            request.session['schema'] = request.path.split('/')[2]
            activate_schema(available_schemata, request.session)
            if request.session.get('schema'):
                response = 'Schema changed to %s' % request.session['schema']
            else:
                response = "No schema found: schema deselected."
            return HttpResponse(response)
        # 2. GET querystring ...?__schema=<name>
        elif request.GET.get('__schema', None) is not None:
            request.session['schema'] = request.GET['__schema']
            if request.method == "GET":
                data = request.GET.copy()
                data.pop('__schema')
                if data:
                    return redirect(request.path + '?' + data.urlencode())
                return redirect(request.path)
        # 3. Header "X-Change-Schema: <name>"
        elif 'HTTP_X_CHANGE_SCHEMA' in request.META:
            request.session['schema'] = request.META['HTTP_X_CHANGE_SCHEMA']
        
        activate_schema(available_schemata, request.session)


    def process_exception(self, request, exception):
        if isinstance(exception, DatabaseError) and not request.session.get('schema'):
            if re.search('relation ".*" does not exist', exception.message):
                # TODO: make this styleable?
                return HttpResponse("You must select a schema to access this resource", status=449)
        
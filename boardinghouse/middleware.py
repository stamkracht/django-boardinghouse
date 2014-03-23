import logging
import re

from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.db import DatabaseError, transaction
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _

from .schema import (
    TemplateSchemaActivation, Forbidden,
    get_schema_model,
    activate_schema, deactivate_schema,
)
from .signals import session_requesting_schema_change

logger = logging.getLogger('boardinghouse.middleware')

def change_schema(request, schema):
    """
    Change the schema for the current request's session.
    """
    session = request.session
    user = request.user
    
    if not schema:
        session.pop('schema', None)
        return
    
    if user.is_anonymous():
        session.pop('schema', None)
        raise Forbidden()
    
    if isinstance(schema, basestring):
        if schema == '__template__':
            raise TemplateSchemaActivation()

        Schema = get_schema_model()
        try:
            schema = Schema.objects.get(schema=schema)
        except Schema.DoesNotExist:
            raise Forbidden()
    
    if schema.schema == '__template__':
        raise TemplateSchemaActivation()
    
    if not (user.is_superuser or user.is_staff):
        if not schema.is_active:
            raise Forbidden()
        if schema not in user.schemata.all():
            raise Forbidden()
    
    # Allow exceptions to prevent this occurring.
    session_requesting_schema_change.send(sender=request, schema=schema)
    session['schema'] = schema.schema
    

class SchemaChangeMiddleware:
    """
    Middleware to set the postgres schema for the current request.
    
    The schema that will be used is stored in the session. A lookup will
    occur (but this could easily be cached) on each request.
    
    There are three ways to change the schema as part of a request.
    
    1. Request a page with a querystring containg a ``__schema`` value::
    
        https://example.com/page/?__schema=<schema-name>
    
      The schema will be changed (or cleared, if this user cannot view 
      that schema), and the page will be re-loaded (if it was a GET). This
      method of changing schema allows you to have a link that changes the
      current schema and then loads the data with the new schema active.

      It is used within the admin for having a link to data from an
      arbitrary schema in the ``LogEntry`` history.
      
      This type of schema change request should not be done with a POST
      request.
    
    2. Add a request header::
    
        X-Change-Schema: <schema-name>
    
      This will not cause a redirect to the same page without query string. It
      is the only way to do a schema change within a POST request, but could
      be used for any request type.
      
    3. Use a specific request::
    
        https://example.com/__change_schema__/<schema-name>/
    
      This is designed to be used from AJAX requests, or as part of
      an API call, as it returns a status code (and a short message) 
      about the schema change request. If you were storing local data,
      and did one of these, you are probably going to have to invalidate
      much of that.
      
    You could also come up with other methods.
    
    """
    def process_request(self, request):
        FORBIDDEN = HttpResponseForbidden(_('You may not select that schema'))
        # Ways of changing the schema.
        # 1. URL /__change_schema__/<name>/
        # This will return a whole page.
        # We don't need to activate, that happens on the next request.
        if request.path.startswith('/__change_schema__/'):
            schema = request.path.split('/')[2]
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN
            
            return HttpResponse(
                _('Schema changed to %s') % request.session['schema']
            )
        # 2. GET querystring ...?__schema=<name>
        # This will change the query, and then redirect to the page
        # without the schema name included.
        elif request.GET.get('__schema', None) is not None:
            schema = request.GET['__schema']
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN
            
            if request.method == "GET":
                data = request.GET.copy()
                data.pop('__schema')
                if data:
                    return redirect(request.path + '?' + data.urlencode())
                return redirect(request.path)
        # 3. Header "X-Change-Schema: <name>"
        elif 'HTTP_X_CHANGE_SCHEMA' in request.META:
            schema = request.META['HTTP_X_CHANGE_SCHEMA']
            try:
                change_schema(request, schema)
            except Forbidden:
                return FORBIDDEN
        elif request.user.schemata.count() == 1:
            change_schema(request, request.user.schemata.get())
        


class SchemaActivationMiddleware:
    """
    Middleware that actually activates the schema from the session.
    """
    def process_request(self, request):
        deactivate_schema()
        
        if 'schema' in request.session:
            try:
                activate_schema(request.session['schema'])
            except TemplateSchemaActivation:
                request.session.pop('schema', None)
                return HttpResponseForbidden(_('You may not select that schema'))

    def process_exception(self, request, exception):
        """
        In the case a request returned a DatabaseError, and there was no
        schema set on ``request.session``, then look and see if the error
        that was provided by the database may indicate that we should have
        been looking inside a schema.
        
        In the case we had a :class:`TemplateSchemaActivation` exception,
        then we want to remove that key from the session.
        """
        if isinstance(exception, DatabaseError) and not request.session.get('schema'):
            if re.search('relation ".*" does not exist', exception.message):
                # TODO: make this styleable? Maybe use a template?
                transaction.rollback()
                return HttpResponse(_("You must select a schema to access this resource"), status=449)
        if isinstance(exception, TemplateSchemaActivation):
            request.session.pop('schema', None)
            return HttpResponseForbidden(_('You may not select that schema'))

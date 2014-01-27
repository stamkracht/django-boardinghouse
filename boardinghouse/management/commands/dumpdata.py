from django.core.management.commands import dumpdata
from django.core.management.base import CommandError
from django.db import models

from optparse import make_option

from ...schema import is_shared_model, get_schema_model, get_template_schema

class Command(dumpdata.Command):
    option_list = dumpdata.Command.option_list + (
        make_option('--schema', action='store', dest='schema',
            help='Specify which schema to dump schema-aware models from',
            default='__template__',
        ),
    )
    
    def handle(self, *app_labels, **options):
        Schema = get_schema_model()
        template_schema = get_template_schema()
        
        schema_name = options.get('schema')
        if schema_name == '__template__':
            schema = template_schema
        else:
            try:
                schema = Schema.objects.get(schema=options.get('schema'))
            except Schema.DoesNotExist:
                raise CommandError('No Schema found named "%s"' % schema_name)

        # If we have have any explicit models that are aware, then we should
        # raise an exception if we weren't handed a schema.
        get_model = models.get_model
        aware_required = any([
            not is_shared_model(get_model(*label.split('.')))
            for label in app_labels if '.' in label
            and get_model(*label.split('.'))
        ])
        
        if aware_required and schema == template_schema:
            raise CommandError('You must pass a schema when an explicit model is aware.')
        
        schema.activate()
        data = super(Command, self).handle(*app_labels, **options)
        schema.deactivate()

        return data
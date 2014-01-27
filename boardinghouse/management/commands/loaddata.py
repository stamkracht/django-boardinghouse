from django.core.management.commands import loaddata
from django.core.management.base import CommandError
from django.db import DatabaseError

from optparse import make_option

from ...schema import get_schema_model

class Command(loaddata.Command):
    option_list = loaddata.Command.option_list + (
        make_option('--schema', action='store', dest='schema',
            help='Specify which schema to load schema-aware models to',
        ),
    )
    
    def handle(self, *app_labels, **options):
        Schema = get_schema_model()
        
        schema_name = options.get('schema')
        if schema_name == '__template__':
            # Hmm, we don't want to accidentally write data to this, so
            # we should raise an exception if we are going to be
            # writing any schema-aware objects.
            schema = None
        elif schema_name:
            try:
                schema = Schema.objects.get(schema=options.get('schema'))
            except Schema.DoesNotExist:
                raise CommandError('No Schema found named "%s"' % schema_name)
        
            schema.activate()
        
        super(Command, self).handle(*app_labels, **options)

        Schema().deactivate()
        
        # Ensure we create any schemata that are new.
        for schema in Schema.objects.all():
            schema.create_schema()

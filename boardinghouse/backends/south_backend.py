import inspect
import sys

from south.db import postgresql_psycopg2, generic

from django.db import models

RAW_SQL_WARNING = "You are performing a raw SQL operation: this will not be applied to multiple schemata."

def is_model_aware(table):
    data = [x for x in models.get_models() if x._meta.db_table == table]
    if data:
        return data[0]._is_schema_aware
    return False

def wrap(name):
    if isinstance(name, basestring):
        function = getattr(postgresql_psycopg2.DatabaseOperations, name)
    else:
        function = name
    
    def apply_to_all(self, table, *args, **kwargs):
        # Need a late import to prevent circular importing error.
        from boardinghouse.models import Schema, template_schema
        if is_model_aware(table):
            for schema in Schema.objects.all():
                schema.activate()
                function(self, table, *args, **kwargs)
            template_schema.activate()
        function(self, table, *args, **kwargs)
        template_schema.deactivate()
    return apply_to_all
    
class DatabaseOperations(postgresql_psycopg2.DatabaseOperations):
    create_table = wrap('create_table')
    rename_table = wrap('rename_table')
    delete_table = wrap('delete_table')
    clear_table = wrap('clear_table')
    add_column = wrap('add_column')
    alter_column = wrap('alter_column')
    # see alter_column below...not sure if it's required yet.
    create_unique = wrap('create_unique')
    delete_unique = wrap('delete_unique')
    delete_foreign_key = wrap('delete_foreign_key')
    create_index = wrap('create_index')
    delete_index = wrap('delete_index')
    drop_index = wrap('delete_index')
    delete_column = wrap('delete_column')
    drop_column = wrap('delete_column')
    rename_column = wrap('rename_column')
    delete_primary_key = wrap('delete_primary_key')
    drop_primary_key = wrap('delete_primary_key')
    create_primary_key = wrap('create_primary_key')
    
    # # Need custom handling, as this may be called by add_column.
    @generic.invalidate_table_constraints
    def alter_column(self, table_name, *args, **kwargs):
        operation = super(DatabaseOperations, self).alter_column
        stack = inspect.stack()
        if stack[2][3] != "add_column":
            return wrap(operation)(table_name, *args, **kwargs)
        return operation(table_name, *args, **kwargs)

    # These deliberately skip our immediate parent.
    def _db_type_for_alter_column(self, field):
        return super(postgresql_psycopg2.DatabaseOperations, self)._db_type_for_alter_column(field)

    def _alter_add_column_mods(self, *args, **kwargs):
        return super(postgresql_psycopg2.DatabaseOperations, self)._alter_add_column_mods(*args ,**kwargs)
        
    def add_deferred_sql(self, sql):
        from boardinghouse.schema import get_schema
        schema = get_schema().schema if get_schema() else '__template__'
        sql = "SET search_path TO %s,public; %s; SET search_path TO public;" % (schema, sql)
        self.deferred_sql.append(sql)
    
    def execute(self, *args, **kwargs):
        # We want to output a warning that this will not apply to all
        # schemata.
        sys.stderr.write(RAW_SQL_WARNING)
        return super(DatabaseOperations, self).execute(*args, **kwargs)
    
    def execute_many(self, *args, **kwargs):
        sys.stderr.write(RAW_SQL_WARNING)
        return super(DatabaseOperations, self).execute_many(*args, **kwargs)
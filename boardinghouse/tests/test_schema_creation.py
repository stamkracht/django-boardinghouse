from django.test import TestCase
from django.db import connection
from django import forms

from ..models import Schema, template_schema
from ..schema import (
    get_schema, _get_schema_or_template, 
    activate_schema, deactivate_schema,
    TemplateSchemaActivation,
    is_shared_model,
)

SCHEMA_QUERY = "SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s"
TABLE_QUERY = "SELECT table_name FROM information_schema.tables WHERE table_schema = %s AND table_name = %s"

class TestPostgresSchemaCreation(TestCase):
    def test_schema_table_is_in_public(self):
        deactivate_schema()
        cursor = connection.cursor()
        table_name = Schema._meta.db_table
        cursor.execute(TABLE_QUERY, ['public', table_name])
        data = cursor.fetchone()
        self.assertEquals((table_name,), data)
        cursor.close()
    
    def test_template_schema_is_created(self):
        cursor = connection.cursor()
        cursor.execute(SCHEMA_QUERY, ['__template__'])
        data = cursor.fetchone()
        self.assertEquals(('__template__',), data)
        cursor.close()
    
    def test_schema_object_creation_creates_schema(self):
        Schema.objects.create(name="Test Schema", schema="test_schema")
        cursor = connection.cursor()
        cursor.execute(SCHEMA_QUERY, ['test_schema'])
        data = cursor.fetchone()
        self.assertEquals(('test_schema',), data)
        cursor.close()
    
    def test_schema_object_creation_does_not_leak_between_tests(self):
        cursor = connection.cursor()
        cursor.execute(SCHEMA_QUERY, ['test_schema'])
        data = cursor.fetchone()
        self.assertEquals(None, data)
        cursor.close()
    
    def test_schema_creation_clones_template(self):
        template_schema.activate()
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE foo (id SERIAL NOT NULL PRIMARY KEY)")
        dup = Schema.objects.create(name="Duplicate", schema='duplicate')
        cursor.execute(TABLE_QUERY, ['duplicate', 'foo'])
        data = cursor.fetchone()
        self.assertEquals(('foo',), data)
        cursor.close()
    
    def test_bulk_create_creates_schemata(self):
        schemata = ['first', 'second', 'third']
        created = Schema.objects.bulk_create([
            Schema(name=x, schema=x) for x in schemata
        ])
        cursor = connection.cursor()
        for schema in schemata:
            activate_schema(schema)
            cursor.execute(SCHEMA_QUERY, [schema])
            data = cursor.fetchone()
            self.assertEquals((schema,), data)
        cursor.close()
    
    def test_mass_create(self):
        Schema.objects.mass_create('a','b','c')
        self.assertEquals(
            ['a','b','c'], 
            list(Schema.objects.values_list('schema', flat=True))
        )
    
class TestSchemaClassValidationLogic(TestCase):
    def test_ensure_schema_model_is_not_schema_aware(self):
        self.assertTrue(is_shared_model(Schema))
        self.assertTrue(is_shared_model(Schema()))
    
    def test_schema_schema_validation_rejects_invalid_chars(self):
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='_foo', name="1")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='-foo', name="2")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='a'*37, name="3")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='foo1', name="4")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='Foo', name="5")
    
    def test_schema_validation_allows_valid_chars(self):
        Schema.objects.create(schema='foo', name="Foo 1")
        Schema.objects.create(schema='a'*36, name="Foo 2")
        Schema.objects.create(schema='foo_bar', name="Foo 3")
    
    def test_schema_rejects_duplicate_values(self):
        Schema.objects.create(schema='foo', name="Foo")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='foo_bar', name="Foo")
        self.assertRaises(forms.ValidationError, Schema.objects.create, schema='foo', name="Foo 2")
    
    def test_schema_rejects_schema_change(self):
        schema = Schema.objects.create(schema='foo', name="Foo")
        schema.name = "Bar"
        schema.save()
        schema.schema = 'bar'
        self.assertRaises(forms.ValidationError, schema.save)


class TestGetSetSearchPath(TestCase):
    def test_default_search_path(self):
        self.assertEquals(None, get_schema())

    def test_activate_schema_sets_search_path(self):
        schema = Schema.objects.create(name='a', schema='a')
        schema.activate()
        self.assertEquals(schema, get_schema())
        
        template_schema.activate()
        self.assertEquals(template_schema, get_schema())
    
    def test_deactivate_schema_resets_search_path(self):
        schema = Schema.objects.create(name='a', schema='a')
        schema.activate()
        schema.deactivate()
        self.assertEquals(None, get_schema())
    
    def test_get_schema_or_template_helper(self):
        schema = Schema.objects.create(name='a', schema='a')
        self.assertEquals('__template__', _get_schema_or_template())
        
        schema.activate()
        self.assertEquals('a', _get_schema_or_template())
        
        schema.deactivate()
        self.assertEquals('__template__', _get_schema_or_template())
    
    def test_activate_schema_function(self):
        self.assertRaises(TemplateSchemaActivation, activate_schema, '__template__')
        self.assertRaises(TemplateSchemaActivation, activate_schema, template_schema)
    
        Schema.objects.mass_create('a', 'b')
        
        activate_schema('a')
        self.assertEquals('a', get_schema().schema)
        
        activate_schema('b')
        self.assertEquals('b', get_schema().schema)
        
        deactivate_schema()
        self.assertEquals(None, get_schema())
        
        activate_schema(Schema.objects.get(schema='a'))
        self.assertEquals('a', get_schema().schema)
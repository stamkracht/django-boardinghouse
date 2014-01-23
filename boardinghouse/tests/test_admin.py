import unittest

from django.test import TestCase
from django.contrib import admin, auth
from django.core.urlresolvers import reverse

from ..schema import get_schema
from ..models import Schema
from .models import AwareModel, NaiveModel, User

class TestAdminAdditions(TestCase):
    def test_ensure_schema_schema_is_not_editable(self):
        Schema.objects.mass_create('a','b','c')
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
        response = self.client.get('/admin/boardinghouse/schema/a/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' not in form.fields, 'Schema.schema should be read-only on edit.')
        
        response = self.client.get('/admin/boardinghouse/schema/add/')
        form = response.context['adminform'].form
        self.assertTrue('name' in form.fields)
        self.assertTrue('schema' in form.fields, 'Schema.schema should be editable on create.')
    
    def test_schema_aware_models_when_no_schema_selected(self):
        Schema.objects.mass_create('a','b','c')
        # Schema.objects.get(name='a').activate()
        # AwareModel.objects.create(name="foo")
        # Schema().deactivate()
        
        user = User.objects.create_superuser(
            username="su",
            password="su",
            email="su@example.com"
        )
        
        self.client.login(username='su', password='su')
        
        response = self.client.get('/admin/boardinghouse/awaremodel/')
        # Should we handle this, and provide feedback?
        self.assertEquals(449, response.status_code)
    
    def test_schemata_list(self):
        from boardinghouse.admin import schemata
        
        user = User.objects.create_user(
            username='user', password='password', email='user@example.com'
        )
        Schema.objects.mass_create('a','b','c')
        self.assertEquals('', schemata(user))
        
        user.schemata.add(*Schema.objects.all())
        self.assertEquals('a<br>b<br>c', schemata(user))
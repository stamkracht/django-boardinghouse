import uuid

from django.test import TestCase
from django.contrib.auth.models import User, Permission
from django.db import connection, migrations, models
from django.db.migrations.state import ProjectState
from django.utils import six

from boardinghouse.contrib.template.models import SchemaTemplate
from boardinghouse.models import Schema
from boardinghouse.schema import (
    _schema_exists,
    get_active_schema_name,
)

from ..models import AwareModel

CREDENTIALS = {
    'username': 'username',
    'password': 'password'
}


def get_table_list():
    with connection.cursor() as cursor:
        table_list = connection.introspection.get_table_list(cursor)
    if table_list and not isinstance(table_list[0], six.string_types):
        table_list = [table.name for table in table_list]
    return table_list


class TestContribTemplate(TestCase):
    def test_template_str(self):
        template = SchemaTemplate(name='Foo')
        self.assertEqual(u'Foo', six.text_type(template))

    def test_templates_can_be_created(self):
        template = SchemaTemplate.objects.create(name='Foo')
        self.assertTrue(_schema_exists(template.schema))
        template.activate()
        self.assertEqual(get_active_schema_name(), template.schema)
        template.deactivate()

    def test_templates_cannot_be_activated_normally(self):
        template = SchemaTemplate.objects.create(name='Foo')
        User.objects.create_user(**CREDENTIALS)
        self.client.login(**CREDENTIALS)
        response = self.client.get('/__change_schema__/{}/'.format(template.schema))
        self.assertEquals(403, response.status_code)

    def test_templates_can_be_activated_with_permission(self):
        template = SchemaTemplate.objects.create(name='Foo')
        user = User.objects.create_user(**CREDENTIALS)
        user.user_permissions.add(Permission.objects.get(codename='activate_schematemplate'))
        self.client.login(**CREDENTIALS)
        response = self.client.get('/__change_schema__/{}/'.format(template.schema))
        self.assertEquals(200, response.status_code)

    def test_invalid_template_raises_forbidden(self):
        template = SchemaTemplate.objects.create(name='Foo')
        user = User.objects.create_user(**CREDENTIALS)
        user.user_permissions.add(Permission.objects.get(codename='activate_schematemplate'))
        self.client.login(**CREDENTIALS)
        response = self.client.get('/__change_schema__/{}1/'.format(template.schema))
        self.assertEquals(403, response.status_code)

    def test_cloning_templates_clones_data(self):
        template = SchemaTemplate.objects.create(name='Foo')
        template.activate()

        aware = AwareModel.objects.create(name=uuid.uuid4().hex[:10])

        schema = Schema(name='cloned', schema='cloned')
        schema._clone = template.schema
        schema.save()

        schema.activate()
        AwareModel.objects.get(name=aware.name)

    def test_editing_template_does_not_change_template_data(self):
        template = SchemaTemplate.objects.create(name='Foo')
        template.activate()

        original = AwareModel.objects.create(name=uuid.uuid4().hex[:10])

        schema = Schema(name='cloned', schema='cloned')
        schema._clone = template.schema
        schema.save()

        schema.activate()
        cloned = AwareModel.objects.get(name=original.name)
        cloned.status = True
        cloned.save()

        template.activate()
        self.assertEqual(1, AwareModel.objects.filter(status=False).count())
        self.assertEqual(0, AwareModel.objects.filter(status=True).count())

        schema.activate()
        self.assertEqual(0, AwareModel.objects.filter(status=False).count())
        self.assertEqual(1, AwareModel.objects.filter(status=True).count())

    def test_migrations_apply_to_templates(self):
        template = SchemaTemplate.objects.create(name='a')
        operation = migrations.CreateModel("Pony", [
            ('pony_id', models.AutoField(primary_key=True)),
            ('pink', models.IntegerField(default=1)),
        ])
        project_state = ProjectState()
        new_state = project_state.clone()
        operation.state_forwards('tests', new_state)

        template.activate()
        self.assertFalse('tests_pony' in get_table_list())

        with connection.schema_editor() as editor:
            operation.database_forwards('tests', editor, project_state, new_state)
        template.activate()
        self.assertTrue('tests_pony' in get_table_list())

        with connection.schema_editor() as editor:
            operation.database_backwards('tests', editor, new_state, project_state)
        template.activate()
        self.assertFalse('tests_pony' in get_table_list())

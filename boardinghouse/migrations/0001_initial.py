# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import os

from django.db import models, migrations
from django.conf import settings
import django.core.validators
import boardinghouse.base

CLONE_SCHEMA = open(os.path.join(os.path.dirname(__file__), '..', 'sql', 'clone_schema.001.sql')).read()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        migrations.swappable_dependency(settings.BOARDINGHOUSE_SCHEMA_MODEL),
        ('admin', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Schema',
            fields=[
                ('schema', models.CharField(primary_key=True, serialize=False, max_length=36, validators=[django.core.validators.RegexValidator(regex=r'^[a-z][a-z0-9_]*$', message='May only contain lowercase letters, digits and underscores. Must start with a letter.')], help_text='The internal name of the schema.<br>May only contain lowercase letters, digits and underscores. Must start with a letter.<br>May not be changed after creation.', unique=True)),
                ('name', models.CharField(help_text='The display name of the schema.', unique=True, max_length=128)),
                ('is_active', models.BooleanField(default=True, help_text='Use this instead of deleting schemata.')),
                ('users', models.ManyToManyField(help_text='Which users may access data from this schema.', related_name='schemata', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'swappable': 'BOARDINGHOUSE_SCHEMA_MODEL',
                'verbose_name_plural': 'schemata',
            },
            bases=(boardinghouse.base.SharedSchemaMixin, models.Model),
        ),
        # No reverse on these, as we want this migration to fail when going
        # backwards: otherwise there are all sorts of really bad implications.
        migrations.RunSQL(sql=CLONE_SCHEMA),
        migrations.RunSQL(sql='CREATE SCHEMA __template__'),
    ]

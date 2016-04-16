==================
Installation/Usage
==================

Requirements
============

* Django_
* Postgres_
* psycopg2_ or psycopg2cffi_ if using PyPy_

This application requires, and depends upon Django_ being installed. Only Django 1.7 and above is supported, but if you are still using 1.7 then you really should upgrade!

Postgres is required to allow schema to be used. psycopg2_ or psycopg2cffi_ is required as per normal Django/Postgres integration.


Installation and Configuration
==============================

Install it using your favourite installer: mine is `pip`_::

    pip install django-boardinghouse

You will need to add ``boardinghouse`` to your ``settings.INSTALLED_APPS``.

You will need to use the provided database engine in your ``settings.DATABASES``::

    'boardinghouse.backends.postgres'

You will need to add the provided middleware to your ``settings.MIDDLEWARE_CLASSES``::

    'boardinghouse.middleware.SchemaMiddleware'

You will probably also want to install the context processor::

   'boardinghouse.context_processors.schemata'

Where this needs to go depends on your version of django: in 1.8 and newer it goes in ``settings.TEMPLATES...['context_processors']``. In older versions, it goes in ``settings.TEMPLATE_CONTEXT_PROCESSORS``.

If you have the admin installed, it adds a column to the admin :class:`django.contrib.admin.models.LogEntry` class, to store the object schema when applicable.

It's probably much easier to start using ``django-boardinghouse`` right from the beginning of a project: trying to split an existing database may be possible, but is not supported at this stage.

Usage
=====

Schema Model
------------

By default, the model :class:`boardinghouse.models.Schema` will be used for the object representing the schemata, however you may override this by using the setting ``settings.BOARDINGHOUSE_SCHEMA_MODEL``. You'll probably want to subclass :class:`boardinghouse.models.AbstractSchema`.

Shared Models
-------------

Some models are required by the system to be shared: these can be seen in:

.. autodata:: boardinghouse.schema.REQUIRED_SHARED_MODELS
  :noindex:

Other shared classes must subclass :class:`boardinghouse.base.SharedSchemaModel`, or mixin :class:`boardinghouse.base.SharedSchemaMixin`. This is required because the migration creation code will not pick up the ``_is_shared_model`` attribute, and will attempt to create the table in all schemata.

If a model is listed in the :const:`settings.SHARED_MODELS` list, then it is deemed to be a shared model. This is how you can define that a 3rd-party application's models should be shared.

If a model contains only foreign keys to other models (and possibly a primary key), then this model will be shared if all linked-to models are shared (or any of the above conditions are true).

All other models are deemed to be schema-specific models, and will be put into each schema that is created.


Management commands
-------------------

When ``django-boardinghouse`` has been installed, it will override the following commands:

.. automodule:: boardinghouse.management.commands.loaddata
  :noindex:

.. automodule:: boardinghouse.management.commands.dumpdata
  :noindex:


.. _middleware:

Middleware
----------

The included middleware must be installed:

.. autoclass:: boardinghouse.middleware.SchemaMiddleware
  :noindex:

.. _template_variables:

Template Variables
------------------

You will probably want to install the context processor: this will ensure that there is always a context variable ``schemata``.

.. autofunction:: boardinghouse.context_processors.schemata
  :noindex:


.. _changing_schema:

Changing Schema
---------------

As outlined in :ref:`middleware`, there are three ways to change the schema: a ``__schema`` querystring, a request header and a specific request.

These all work without any required additions to your ``urls.py``.


.. _pip: https://pip-installer.org/
.. _Django: https://www.djangoproject.com/
.. _Postgres: http://www.postgresql.org/
.. _PostgresApp: http://postgresapp.com/
.. _psycopg2: https://pypi.python.org/pypi/psycopg2/
.. _psycopg2cffi: https://pypi.python.org/pypi/psycopg2cffi
.. _PyPy: https://pypy.org/
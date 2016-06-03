Included Extensions
===================

.. _invite:

boardinghouse.contrib.invite
----------------------------

.. note:: This app is incomplete.

One of the real ideas for how this type of system might work is `Xero`_, which allows a user to invite other people to access their application. This is a little more than just the normal registration process, as if the user is an existing Xero user, they will get the opportunity to link this Xero Organisation to their existing account.

Then, when they use Xero, they get the option to switch between organisations... sound familiar?

The purpose of this contrib application is to provide forms, views and url routes that could be used, or extended, to recreate this type of interaction.

The general pattern of interaction is:

* User with required permission (invite.create_invitation) is able to generate an invitation. This results in an email being sent to the included email address (and, if a matching email in this system, an entry in the pending_acceptance_invitations view), with the provided message.

.. note:: Permission-User relations should really be per-schema, as it is very likely that the same user will not have the same permission set within different schemata. This can be enabled by using :ref:`groups`, for instance.

* Recipient is provided with a single-use redemption code, which is part of a link in the email, or embedded in the view detailed above. When they visit this URL, they get the option to accept or decline the invitation.

* Declining the invitation marks it as declined, provides a timestamp, and prevents this invitation from being used again. It is still possible to re-invite a user who has declined (but should provide a warning to the logged in user that this user has already declined an invitation).

* Accepting the invitation prompts the user to either add this schema to their current user (if logged in), or create a new account. If they are not logged in, they get the option to create a new account, or to log in and add the schema to that account. Acceptance of an invitation prevents it from being re-used.

It is possible for a logged in user to see the following things (dependent upon permissions in the current schema):

* A list of pending (non-accepted) invitations they (and possibly others) have sent.

* A list of declined and accepted invitations they have sent.

* A list of pending invitation they have not yet accepted or declined. This page can be used to accept or decline.

.. _Xero: http://www.xero.com

.. _template:

boardinghouse.contrib.template
------------------------------

Introduces the concept of "SchemaTemplate" objects, which can be used to create a schema that contains initial data.

Actions:

* Create schema from template
* Create template from schema

Template schema have schema names like: `__template_<id>`, and can only be activated by users who have the relevant permission.


.. _groups:

boardinghouse.contrib.groups
----------------------------

By default, django-boardinghouse puts all of the `django.contrib.auth` models into the "shared" category, but maintains the relationships between `User` ⟷ `Permission`, and between `User` ⟷ `Group` as private/per-schema relationships. This actually makes lots of sense, as authorisation to perform an action belongs to the schema.

The relationship between `Group` ⟷ `Permission` is also shared: the philosophy here is that everything except group *allocation* (and per-user permission) should be maintained by the system administrator, not by schema owners.

However, if you desire the `Group` instances to be per-schema (and by inference, the `Group` ⟷ `Permission` relations), then installing this package makes this possible.


.. _demo:

boardinghouse.contrib.demo
--------------------------

.. note:: This app has not been completed.

Borrowing again from `Xero`_, we have the ability to create a demo schema: there can be at most one per user, and it expires after a certain period of time, can be reset at any time by the user, and can have several template demos to be based upon.

Actions:

* Create a new demo schema for the logged in user (replacing any existing one), from the provided demo-template.

Automated tasks:

* Delete any demo schemata that have expired.

Settings:

* `BOARDINGHOUSE_DEMO_PERIOD`
* `BOARDINGHOUSE_DEMO_PREFIX`


.. _access:

boardinghouse.contrib.access
----------------------------

.. note:: This app is still being planned.

Store the last accessor of each schema, like in the `Xero`_ dashboard view.

Organisations

+-----------------------+---------------------+------------------+
| Name                  | Last accessed       | Role             |
+-----------------------+---------------------+------------------+
| Larson, Inc.          | Today, 5:58pm       | Adviser          |
|                       | by Bob Smith        |                  |
+-----------------------+---------------------+------------------+
| Leffler, Mertz and    | Today, 7:58pm       | Adviser          |
| Roberts               | by Bob Smith        |                  |
+-----------------------+---------------------+------------------+

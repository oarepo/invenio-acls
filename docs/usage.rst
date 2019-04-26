Usage
-----

Description part
================

The description part is called `ACL` within the library.

The following implementations are built-in:

    IdACL:
        the ACL applies to records identified by their internal Invenio UUIDs

    DefaultACL:
        the ACL applies to all records in a given schema(s)

    ElasticsearchACL:
        the ACL applies to all records in the given schema(s) that match the given ES query

    PropertyValueACL:
        simpler implementation of ElasticsearchACL.
        The ACL applies to all records in the given schema(s) whose named property/set of properties has a given value


Actors
======

Actor defines who has access to a set of resources identified by mapping above.
The following implementations are built-in:

    UserActor:
        a set of users (direct enumeration) that have access

    RoleActor:
        a set of user roles that have access

    SystemRoleActor:
        an actor that matches anonymous users, authenticated users or everyone


Admin interface
===============

The ACLs and actors can be set in the admin interface (albeit not comfortably -
we expect that the ACLs are created by your custom code/ui to restrict users
to create only ACLs of certain type).

  .. image:: ./images/menu.png

At first create an ACL Actor, in this example a Role ACL (make sure you have
the role defined in User Management / Role tab).

  .. image:: ./images/create_actor.png

In the second step map the actor to operation and records, for example property-value
based:

  .. image:: ./images/create_acl.png


Within Python code
==================

The ACL and Actors are normal sqlalchemy models, use them as usual.
To (re)apply the ACL to existing records do not forget to call:

.. code-block:: python

    from invenio_explicit_acls.proxies import current_explicit_acls

    acl = ....
    current_explicit_acls.reindex_acl(acl, delayed=False)

for cases when ACL is created / modified and:

.. code-block:: python

    from invenio_explicit_acls.proxies import current_explicit_acls

    acl = .... # (a removed acl)
    current_explicit_acls.reindex_acl_removed(acl, delayed=False)

when ACL has been removed.

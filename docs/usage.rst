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
        The ACL applies to all records in the given schema(s) whose named property has a given value


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

The ACLs and actors can be set in the admin interface.

Within Python code
==================

Both the description part (:class:`invenio_explicit_acls.models.ACL`)
and actor part (:class:`invenio_explicit_acls.models.Actor`)
are extensible and custom implementation can be provided via inheriting
from these classes.


TBD.

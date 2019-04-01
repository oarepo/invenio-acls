Usage
-----

Principles
==========

An ACL rule consists of two parts:

1. Mapping part that defines the set of records
   the ACL applies to and the operation that can be performed on them
2. Actor part that defines the actors and allowed operations.

An ACL also contains a priority field. When several ACLs match a given
record, only those with the highest priority are applied.
This enables exceptions in ACLs. For example:

*ACL 1:*

* Mapping: "*All records in a repository*",
* Actor: "*Readable by everyone*"
* Priority: 0

*ACL 2:*

* Mapping: "*Records that have a property `secret=true`*",
* Actor: "admin"
* Priority: 1

When ACLs are applied to a secret record, both ACLs match,
but only the second one is used.

Both the mapping part (:class:`invenio_explicit_acls.models.ACL`)
and actor part (:class:`invenio_explicit_acls.models.Actor`)
are extensible and custom implementation can be provided by extending from these classes.


Mappings
========

Mapping define a set of records to which a given operation and ACLs are applied.
Every mapping contains the following required properties:

    name:
        the name of the ACL, only for humans

    priority:
        the priority of the ACL rule, for its meaning see the principles above

    operation:
        an abstract operation the ACL describes, for example "get", "update"
        "delete" for standard REST operations. Can be any string for custom
        operations (such as "approve", "publish", ...).

    schemas:
        set it to a list of schemas to which the ACL is applied.
        Records having other schemas are not affected by the ACL.

The following implementations of mappings are built-in:

    IdACL:
        the ACL applies to records identified by their internal Invenio UUIDs

    DefaultACL:
        the ACL applies to all records in given schema(s)

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

TBD.

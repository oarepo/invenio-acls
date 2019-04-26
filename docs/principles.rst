Principles
==========

This library provides framework for writing / using declarative ACLs
(Access Control Lists) for Invenio Records. The ACLs are stored in the
local database and indexed into Elasticsearch for fast record retrieval.

ACLs can be assigned to a single record or a set of records identified
by configurable selectors. ACLs can be added/modified/removed during
runtime.

ACL anatomy
-----------

An ACL rule consists of two parts:

1. Description part (what can be done on which records)
2. Actor part (who can do it)

Examples:

ACL 1

    Actor: *everyone*

    Description: Can *Read* *All records* in a repository,

ACL 2

    Actor: *admin*

    Description: Can *Read* Records that have a property `secret=true`,


Description part
----------------

Description part is a database model stored in the database and consists of:

    name:
        the name of the ACL, not used within the system, only for administrators

    priority:
        the priority of the ACL rule, see below for details

    operation:
        an abstract operation which the ACL allows, for example "get", "update"
        "delete" for standard REST operations. Can be any string for custom
        operations (such as "approve", "publish", ...).

    schemas:
        a list of schemas to which the ACL is applicable.
        Records having other schemas (in `$schema` metadata property)
        are not affected by the ACL.

Priority field: when several ACLs match a given
record, only those with the highest priority are applied.
This enables exceptions in ACLs. For example:

*ACL 1:*

* Description: "*Can Read All records in a repository*",
* Actor: "*everyone*"
* Priority: 0

*ACL 2:*

* Mapping: "*Can Read records that have a property `secret=true`*",
* Actor: "*admin*"
* Priority: 1

When ACLs are applied to a secret record, both ACLs match,
but only the second one is used.


Actor part
----------

An Actor is an abstract database model that decides who is allowed to perform
an operation. Several implementations are provided, selecting users by their
id, invenio role, or selecting system users (everyone, authenticated, ...).


Extensibility
-------------

Both the description part and actor part are extensible and can use your
own implementations.

Performance
-----------

+------------------------------------+----------------------------------------------------------------------+
| Get record                         | Fast (no extra query to elasticsearch)                               |
+------------------------------------+----------------------------------------------------------------------+
| List record                        | Fast (no extra query to elasticsearch)                               |
+------------------------------------+----------------------------------------------------------------------+
| Create a new record                | Reasonably Fast (1 extra query to ES)                                |
+------------------------------------+----------------------------------------------------------------------+
| Edit record                        | Reasonably Fast (1 extra query to ES)                                |
+------------------------------------+----------------------------------------------------------------------+
| Delete record                      | Fast, no extra query                                                 |
+------------------------------------+----------------------------------------------------------------------+
| Create a new ACL                   | Depends on number of records: Must reindex all records it applies to |
+------------------------------------+----------------------------------------------------------------------+
| ACL modification                   | Depends on number of records: Must reindex all records it applies to |
+------------------------------------+----------------------------------------------------------------------+
| ACL deletion                       | Depends on number of records: Must reindex all records it applies to |
+------------------------------------+----------------------------------------------------------------------+


* If your use case involves lot of ACLs each assigned to a small subset
  of records, this library might be for you.

* If your use case involves frequently changing ACLs each assigned to a small subset
  of records, this library might be for you.

* If your use case involves setting up "default" ACLs in advance and not modifying
  them afterwards, this library might be for you.

* On the other hand if you plan to have ACLs that will change frequently and each will
  affect a lot of records, then this library is definitely not for you.

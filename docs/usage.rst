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

Actors can also take data from the indexed document. For example, if the document
contains a property "creator_id", one can use `RecordUserActor(..., path='/creator_id')`
to write an ACL matching the creator (whoever it is).

The following record actors are built-in:

    RecordUserActor:
        a set of users enumerated in a property in the indexed record

    RecordRoleActor:
        a set of user roles enumerated in a property in the indexed record

Again, these are extensible, so for example if the record metadata contains
property `faculty`, one can write a custom
`PRBACRoleActor(role='administrator', parameter='faculty', path='/faculty')`
to assign rights to the correct faculty administrator defined in a local PRBAC
(parametrized role-based access control) system - would match all users
with prbac role "administrator[faculty=<value of faculty property in the document>]"


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

**Creating/Updating/Deleting ACLs**


The ACL and Actors are normal sqlalchemy models, use them as usual.
For example:

.. code-block:: python

    acl = DefaultACL(name='record default', schemas=[RECORD_SCHEMA],
                     operation='get',
                     originator=current_user)
    user = User.query.filter(email='...').one()
    actor = UserActor(name='VIP users', originator=test_users.u1,
                      users=[user])
    db.session.add(acl)
    db.session.add(actor)

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


**Searching with current_user**

To search records within a request for the `current_user` just replace
RecordsSearch class with ACLRecordsSearch. For example:

.. code-block:: python

    index, doc_type = schema_to_index(RECORD_SCHEMA)

    data = ACLRecordsSearch(index=index, doc_type=doc_type).execute().hits

For more info see `https://invenio-search.readthedocs.io <https://invenio-search.readthedocs.io/en/latest/usage.html>`_.

**Searching on behalf of another user**

Sometimes we need to search on behalf of another user or the current_user is not
set (when working outside the request context, such as in celery task). The ACLs
need to get:

   * the user
   * set of system roles, such as `any_user`, `authenticated_user`
     from `invenio_access.permissions`

.. code-block:: python

    from invenio_access.permissions import authenticated_user

    tested_user = ...

    data = ACLRecordsSearch(
        index=index, doc_type=doc_type,
        user=tested_user,
        context = {
            system_roles=[authenticated_user]
        }
    ).execute().hits

Always provide `system_roles`. If not provided, `SystemRoleActor` will take them
from `g.identity` which is probably not what you want in this context !

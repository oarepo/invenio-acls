# Declarative ACLs for Invenio v3

## Warning

This is a work in progress. The APIs, data representation, schemas of
indices might change any time.

## Filtering elasticsearch results on REST api

To filter ES results by effective ACLs, use `ACLRecordsSearch`
instead of `RecordsSearch`. Also use `acl_*_permission_factory` 
to allow "get", "update", "delete" acl-based operations:

```python
from invenio_explicit_acls import ACLRecordsSearch, \
                         acl_read_permission_factory, \
                         acl_update_permission_factory, \ 
                         acl_delete_permission_factory

REST_ENDPOINTS = {

    'thesis': dict(
        # ...

        # search class
        search_class=ACLRecordsSearch,

        # ACL based permissions
        create_permission_factory_imp=...,
        read_permission_factory_imp=acl_read_permission_factory,
        update_permission_factory_imp=acl_update_permission_factory,
        delete_permission_factory_imp=acl_delete_permission_factory,
        # ...
    ),
}
```

# Programmatic access to the library

## Instantiating builtin ACLs

```python
from invenio_explicit_acls.acls.id_acls import IdAcl
from invenio_explicit_acls.proxies import current_acls

idacl = IdACL(
  name="My first ACL",
  priority=0,
  indices=["theses-thesis-v1.0.0"],
  record_id = '<uuid>',
  database_operations = [
    {"operation": "get", "actors": {"roles": ["authenticated"]}}
  ],
  originator = current_user,
)
db.session.add(idacl)
db.session.commit()

# save the ACL to supplementary index and enrich all matching records
# with ACL mapping

current_acls.index_acl(idacl)

```

## Creating custom ACLs

### ACL database mixin and handlers

A custom implementation of ACL rule consists of two classes: database
(or database-like) ACL object and a handler for ACL application.

TBD.

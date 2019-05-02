Configuration
-------------

`invenio-explicit-acls` discriminates records via their `$schema` property that
needs to be present in the metadata of guarded records.

The following configuration steps should be carried out for each enabled record
type:

1. Make sure that the `$schema` property is always set and can not be
   changed or removed to circumvent ACLs. To guarantee that on internal API level,
   use your own implementation of `Record` inherited from `SchemaKeepingRecordMixin`
   or `SchemaEnforcingRecord` (a helper class inheriting from
   `Record` and `SchemaKeepingRecordMixin`). The `ALLOWED_SCHEMAS` is a list of schemas
   that are allowed in user data, `PREFERRED_SCHEMA` will be used when user does not
   specify a schema. Whenever you call (internally) a `ThesisRecord.create(...)`
   the `$schema` will get added automatically.

.. code-block:: python

    # myapp/constants.py
        ACL_ALLOWED_SCHEMAS = ('http://localhost/schemas/theses/thesis-v1.0.0.json',)
        ACL_PREFERRED_SCHEMA = 'http://localhost/schemas/theses/thesis-v1.0.0.json'

    # myapp/api.py
    class ThesisRecord(SchemaEnforcingRecord):
        ALLOWED_SCHEMAS = ACL_ALLOWED_SCHEMAS
        PREFERRED_SCHEMA = ACL_PREFERRED_SCHEMA

    # myapp/config.py
    RECORDS_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            record_class=ThesisRecord,
            # ...
        )
    }


2. Make Invenio use your Record class for all API calls (just a precaution, real
   validation on REST calls is in the next step):

.. code-block:: python

    THESES_PID = 'pid(recid,record_class="myapp.api:ThesisRecord")'

    # myapp/config.py
    RECORDS_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            item_route='/theses/<{0}:pid_value>'.format(THESES_PID),
            # ...
        )
    }


3. For metadata validation during REST, extend your marshmallow schema
   to inherit from `SchemaEnforcingMixin` and do not forget to set
   `ALLOWED_SCHEMAS` and `PREFERRED_SCHEMA`:

.. code-block:: python

    # myapp/marshmallow/json.py
    class ThesisMetadataSchemaV1(SchemaEnforcingMixin,
                                 StrictKeysMixin):
        """Schema for the thesis metadata."""

        ALLOWED_SCHEMAS = ACL_ALLOWED_SCHEMAS
        PREFERRED_SCHEMA = ACL_PREFERRED_SCHEMA

        title = SanitizedUnicode(required=True, validate=validate.Length(min=3))
        # ... metadata fields

    # myapp/loaders/init.py
    json_v1 = marshmallow_loader(ThesisMetadataSchemaV1)

    # myapp/config.py
    RECORDS_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            record_loaders={
                'application/json': 'myapp.loaders:json_v1',
            },
            # ...
        )
    }


4. Use ACLRecordsSearch as your REST search class:

.. code-block:: python

    # myapp/config.py
    RECORDS_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            search_class=ACLRecordsSearch,
            # ...
        )
    }



5. Use permissions from `invenio_explicit_acls.permissions` as your
   permission factory impl:

.. code-block:: python

    # myapp/config.py
    RECORDS_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            read_permission_factory_imp=acl_read_permission_factory,
            update_permission_factory_imp=acl_update_permission_factory,
            delete_permission_factory_imp=acl_delete_permission_factory,
            # ...
        )
    }


6. Do not forget to supply your own `create_permission_factory_impl` - it is not handled
   by this library!


7. If not using marshmallow, adapt your loader to check and fill the `$schema` property.
   Never trust user (or your code) and always check!

8. For each of the schemas defined in step 1, create additional indices in ES:

.. code-block:: bash

    # run in bash
    invenio explicit-acls prepare <schema-url>

schema-url is a relative (short) schema name, for example records/record-v1.0.0.json

9. Restart the server and you are ready to go.

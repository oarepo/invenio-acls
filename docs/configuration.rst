.. highlight:: python

Configuration
-------------

`invenio-explicit-acls` is mapped to the resources via the resource `$schema` property.
The following configuration steps are necessary to configure:

1. Making sure that the `$schema` property is always set and can not be
   changed or removed to circumvent ACLs. To guarantee that on internal API level,
   use your own implementation of `Record` inherited from `SchemaKeepingRecordMixin`
   or `SchemaEnforcingRecord` (a helper class inheriting from
   `Record` and `SchemaKeepingRecordMixin`). The `ALLOWED_SCHEMAS` is a list of schemas
   that are allowed in user data, `PREFERRED_SCHEMA` will be used when user does not
   specify a schema.

.. code-block:: python

    # myapp/constants.py
        ACL_ALLOWED_SCHEMAS = ('http://localhost/schemas/theses/thesis-v1.0.0.json',)
        ACL_PREFERRED_SCHEMA = 'http://localhost/schemas/theses/thesis-v1.0.0.json'

    # myapp/api.py
    class ThesisRecord(SchemaEnforcingRecord):
        ALLOWED_SCHEMAS = ACL_ALLOWED_SCHEMAS
        PREFERRED_SCHEMA = ACL_PREFERRED_SCHEMA

    # myapp/config.py
    THESES_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            record_class=ThesisRecord,
            # ...
        )
    }



2. In some cases Invenio uses default Record class instead of the configured one
   (in PUT, PATCH operations). To make them safe, extend your marshmallow schema
   to inherit from `SchemaEnforcingMixin` and do not forget to set `ALLOWED_SCHEMAS`
   and `PREFERRED_SCHEMA`:

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
    THESES_REST_ENDPOINTS = {
        'thesis': dict(
            # ...
            record_loaders={
                'application/json': 'myapp.loaders:json_v1',
            },
            # ...
        )
    }


3. If not using marshmallow, adapt your loader to check and fill the `$schema` property.
   Never trust user (or your code) and always check!

4. Enable `invenio-explicit-acls` for the schemas defined in step 1:

.. code-block:: python

    # myapp/config.py
    INVENIO_EXPLICIT_ACL_ENABLED_SCHEMAS = [
        *ACL_ALLOWED_SCHEMAS
    ]

5. For each of the schemas defined in step 1, create additional indices in ES:

.. code-block:: bash

    invenio explicit-acls prepare <schema-url>

6. Restart the server and you are ready to go.

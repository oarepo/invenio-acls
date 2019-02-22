from marshmallow import fields


class ACLRecordSchemaMixinV1:
    invenio_acls = fields.Dict(dump_only=True)

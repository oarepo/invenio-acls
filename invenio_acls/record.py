from invenio_records import Record


class SchemaKeepingRecord(Record):

    # DO NOT forget to set these up in subclasses
    ALLOWED_SCHEMAS = ()
    PREFERRED_SCHEMA = None

    def clear(self):
        schema = self.get('$schema')
        self.clear()
        if schema:
            self['$schema'] = schema

    def update(self, e=None, **f):
        has_schema = '$schema' in (e or f)
        if has_schema:
            schema = (e or f).get('$schema')
            if schema not in self.ALLOWED_SCHEMAS:
                raise AttributeError('Bad schema passed')

        return super().update(e, **f)


    @classmethod
    def create(cls, data, id_=None, **kwargs):
        if '$schema' not in data:
            data['$schema'] = cls.PREFERRED_SCHEMA
        ret = super().create(data, id_, **kwargs)
        return ret

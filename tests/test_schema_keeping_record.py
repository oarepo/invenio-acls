import pytest

from helpers import create_record
from invenio_explicit_acls.record import SchemaEnforcingRecord


def test_schema_create(app, db):
    pid, rec = create_record({}, clz=SchemaEnforcingRecord)
    assert rec['$schema'] == SchemaEnforcingRecord.PREFERRED_SCHEMA

    with pytest.raises(AttributeError):
        create_record({'$schema': 'http://blah'}, clz=SchemaEnforcingRecord)


def test_clear(app, db):
    pid, rec = create_record({}, clz=SchemaEnforcingRecord)
    rec.clear()
    assert rec['$schema'] == SchemaEnforcingRecord.PREFERRED_SCHEMA


def test_update(app, db):
    pid, rec = create_record({}, clz=SchemaEnforcingRecord)
    with pytest.raises(AttributeError):
        rec.update({'$schema': 'http://blah'})

    rec.update({'title': 'blah'})
    assert rec['title'] == 'blah'

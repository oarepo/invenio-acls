#
# Copyright (c) 2019 UCT Prague.
# 
# test_propertyvalue_acl_unittests.py is part of Invenio Explicit ACLs 
# (see https://github.com/oarepo/invenio-explicit-acls).
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
import elasticsearch
import pytest
from flask import current_app
from helpers import create_record
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client

from invenio_explicit_acls.acls import PropertyValueACL
from invenio_explicit_acls.acls.propertyvalue_acls import MatchOperation
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'https://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'https://localhost/schemas/records/blah-v1.0.0.json'


def test_propertyvalue_acl_get_record_acl(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['test']}, clz=SchemaEnforcingRecord)

    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='keywords',
                               property_value='blah')
        db.session.add(acl)
        acl2 = PropertyValueACL(name='test 2', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                property_name='keywords',
                                property_value='test')
        db.session.add(acl2)

    acl.update()
    acl2.update()

    acls = list(PropertyValueACL.get_record_acls(record))
    assert len(acls) == 1
    assert isinstance(acls[0], PropertyValueACL)
    assert acls[0].id == acl.id

    acls = list(PropertyValueACL.get_record_acls(record1))
    assert len(acls) == 1
    assert isinstance(acls[0], PropertyValueACL)
    assert acls[0].id == acl2.id


def test_propertyvalue_acl_get_record_match_acl(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah'], 'title': 'Hello world'},
                                clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['test'], 'title': 'Goodbye world'},
                                  clz=SchemaEnforcingRecord)

    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='title',
                               property_value='hello',
                               match_operation=MatchOperation.match.value)
        db.session.add(acl)
        acl2 = PropertyValueACL(name='test 2', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                property_name='title',
                                property_value='goodbye',
                                match_operation=MatchOperation.match.value)
        db.session.add(acl2)

    acl.update()
    acl2.update()

    acls = list(PropertyValueACL.get_record_acls(record))
    assert len(acls) == 1
    assert isinstance(acls[0], PropertyValueACL)
    assert acls[0].id == acl.id

    acls = list(PropertyValueACL.get_record_acls(record1))
    assert len(acls) == 1
    assert isinstance(acls[0], PropertyValueACL)
    assert acls[0].id == acl2.id


def test_propertyvalue_acl_prepare_schema_acl(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    PropertyValueACL.prepare_schema_acls(RECORD_SCHEMA)

    idx = PropertyValueACL.get_acl_index_name(schema_to_index(RECORD_SCHEMA)[0])
    mapping = current_search_client.indices.get_mapping(idx)
    assert idx in mapping

    idx, doc_type = schema_to_index(RECORD_SCHEMA)
    mapping = current_search_client.indices.get_mapping(idx)
    assert '_invenio_explicit_acls' in mapping[idx]['mappings'][doc_type]['properties']


def test_propertyvalue_acl_get_matching_resources(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['test']}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)
    RecordIndexer().index(record1)
    current_search_client.indices.flush()

    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='keywords',
                               property_value='blah')
        db.session.add(acl)

        acl1 = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                property_name='keywords',
                                property_value='test')
        db.session.add(acl1)

    ids = list(acl.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid.object_uuid)

    ids = list(acl1.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid1.object_uuid)


def test_propertyvalue_acl_update(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='keywords',
                               property_value='test')
        db.session.add(acl)
    acl.update()  # makes version 1
    acl.update()  # makes version 2
    idx = acl.get_acl_index_name(schema_to_index(RECORD_SCHEMA)[0])
    acl_md = current_search_client.get(
        index=idx,
        doc_type=current_app.config['INVENIO_EXPLICIT_ACLS_DOCTYPE_NAME'],
        id=acl.id
    )
    assert acl_md == {
        '_id': acl.id,
        '_index': 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0',
        '_source': {'__acl_record_selector': {'term': {'keywords': 'test'}}, '__acl_record_type': 'propertyvalue'},
        '_type': '_doc',
        '_version': 2,
        'found': True
    }


def test_propertyvalue_acl_delete(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='keywords',
                               property_value='test')
        db.session.add(acl)
    acl.update()
    idx = acl.get_acl_index_name(schema_to_index(RECORD_SCHEMA)[0])
    acl_md = current_search_client.get(
        index=idx,
        doc_type=current_app.config['INVENIO_EXPLICIT_ACLS_DOCTYPE_NAME'],
        id=acl.id
    )
    assert acl_md == {
        '_id': acl.id,
        '_index': 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0',
        '_source': {'__acl_record_selector': {'term': {'keywords': 'test'}}, '__acl_record_type': 'propertyvalue'},
        '_type': '_doc',
        '_version': 1,
        'found': True
    }
    acl.delete()
    with pytest.raises(elasticsearch.exceptions.NotFoundError):
        current_search_client.get(
            index=idx,
            doc_type=current_app.config['INVENIO_EXPLICIT_ACLS_DOCTYPE_NAME'],
            id=acl.id
        )


def test_propertyvalue_acl_repr(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = PropertyValueACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               property_name='keywords',
                               property_value='test')
        db.session.add(acl)
    assert repr(acl) == "\"test\" (%s) on schemas ['https://localhost/schemas/records/record-v1.0.0.json']" % acl.id


def test_no_es_prepared_index(app, db, es, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    with pytest.raises(RuntimeError, match='Explicit ACLs were not prepared for the given schema. '
                                           'Please run invenio explicit-acls prepare '
                                           'https://localhost/schemas/records/record-v1.0.0.json'):
        list(PropertyValueACL.get_record_acls(record))

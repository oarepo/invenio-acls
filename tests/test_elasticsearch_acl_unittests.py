#
# Copyright (c) 2019 UCT Prague.
# 
# test_elasticsearch_acl_unittests.py is part of Invenio Explicit ACLs 
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
import json

import elasticsearch
import pytest
from flask import current_app
from helpers import create_record
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client

from invenio_explicit_acls.acls import ElasticsearchACL
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'records/blah-v1.0.0.json'


def test_elasticsearch_acl_get_record_acl(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': 'https://localhost/schemas/' + RECORD_SCHEMA, 'keywords': ['blah']},
                                clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': 'https://localhost/schemas/' + RECORD_SCHEMA, 'keywords': ['test']},
                                  clz=SchemaEnforcingRecord)

    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'blah'
                               }})
        db.session.add(acl)
        acl2 = ElasticsearchACL(name='test 2', schemas=[ANOTHER_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                record_selector={'term': {
                                    'keywords': 'test'
                                }})
        db.session.add(acl2)

    acl.update()
    with pytest.raises(AttributeError,
                       match='No index found for schema records/blah-v1.0.0.json'):
        acl2.update()

    acls = list(ElasticsearchACL.get_record_acls(record))
    assert len(acls) == 1
    assert isinstance(acls[0], ElasticsearchACL)
    assert acls[0].id == acl.id


def test_elasticsearch_acl_prepare_schema_acl(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    ElasticsearchACL.prepare_schema_acls(RECORD_SCHEMA)

    idx = ElasticsearchACL.get_acl_index_name(schema_to_index(RECORD_SCHEMA)[0])
    mapping = current_search_client.indices.get_mapping(idx)
    assert idx in mapping

    idx, doc_type = schema_to_index(RECORD_SCHEMA)
    mapping = current_search_client.indices.get_mapping(idx)
    assert len(mapping) == 1
    key = list(mapping.keys())[0]
    assert '_invenio_explicit_acls' in mapping[key]['mappings'][doc_type]['properties']


def test_elasticsearch_acl_get_matching_resources(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['test']}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)
    RecordIndexer().index(record1)
    current_search_client.indices.flush()

    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'blah'
                               }})
        db.session.add(acl)

        acl1 = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                record_selector={'term': {
                                    'keywords': 'test'
                                }})
        db.session.add(acl1)

    ids = list(acl.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid.object_uuid)

    ids = list(acl1.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid1.object_uuid)


def test_elasticsearch_acl_update(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'test'
                               }})
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
        '_source': {'__acl_record_selector': {'term': {'keywords': 'test'}}, '__acl_record_type': 'elasticsearch'},
        '_type': '_doc',
        '_version': 2,
        'found': True
    }


def test_elasticsearch_acl_delete(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'test'
                               }})
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
        '_source': {'__acl_record_selector': {'term': {'keywords': 'test'}}, '__acl_record_type': 'elasticsearch'},
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


def test_elasticsearch_acl_repr(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'test'
                               }})
        db.session.add(acl)
    assert repr(acl) == "\"test\" (%s) on schemas ['records/record-v1.0.0.json']" % acl.id


def test_no_es_prepared_index(app, db, es, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    with pytest.raises(RuntimeError, match='Explicit ACLs were not prepared for the given schema. '
                                           'Please run invenio explicit-acls prepare '
                                           'https://localhost/schemas/records/record-v1.0.0.json'):
        list(ElasticsearchACL.get_record_acls(record))

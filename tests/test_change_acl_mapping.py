#
# Copyright (c) 2019 UCT Prague.
# 
# test_change_acl_mapping.py is part of Invenio Explicit ACLs 
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

from helpers import clear_timestamp, create_record, get_json, login, \
    records_url
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import current_search_client

from invenio_explicit_acls.acls import DefaultACL, ElasticsearchACL
from invenio_explicit_acls.actors import SystemRoleActor, UserActor
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'


def test_change_acl_mapping(app, db, es, es_acl_prepare, test_users):
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
        actor = UserActor(users=[test_users.u1], acl=acl, originator=test_users.u1)
        db.session.add(acl)
        db.session.add(actor)

    current_explicit_acls.reindex_acl(acl, delayed=False)
    current_search_client.indices.flush()

    index, doc_type = schema_to_index(RECORD_SCHEMA)

    hits = current_search_client.search(
        index=index,
        doc_type=doc_type,
        body={
            'query': {
                'nested': {
                    'path': '_invenio_explicit_acls',
                    'query': {
                        'term': {
                            '_invenio_explicit_acls.id': str(acl.id)
                        }
                    }
                }
            },
            '_source': False
        }
    )['hits']['hits']

    assert len(hits) == 1
    assert hits[0]['_id'] == str(pid.object_uuid)

    with db.session.begin_nested():
        acl.record_selector = {
            'term': {
                'keywords': 'test'
            }
        }
        db.session.add(acl)

    current_explicit_acls.reindex_acl(acl, delayed=False)
    current_search_client.indices.flush()

    hits = current_search_client.search(
        index=index,
        doc_type=doc_type,
        body={
            'query': {
                'nested': {
                    'path': '_invenio_explicit_acls',
                    'query': {
                        'term': {
                            '_invenio_explicit_acls.id': str(acl.id)
                        }
                    }
                }
            },
            '_source': False
        }
    )['hits']['hits']

    assert len(hits) == 1
    assert hits[0]['_id'] == str(pid1.object_uuid)

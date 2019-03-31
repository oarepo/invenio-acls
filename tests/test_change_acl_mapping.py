import json

from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import current_search_client

from helpers import get_json, login, records_url, clear_timestamp, create_record
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

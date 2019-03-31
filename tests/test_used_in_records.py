import datetime
import time

from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client

from helpers import create_record, clear_timestamp
from invenio_explicit_acls.acls import ElasticsearchACL
from invenio_explicit_acls.actors import SystemRoleActor
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'http://localhost/schemas/records/blah-v1.0.0.json'


def test_used_in_records(app, db, es, es_acl_prepare, test_users):
    with db.session.begin_nested():
        acl1 = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                record_selector={'term': {
                                    'keywords': 'blah'
                                }})
        actor1 = SystemRoleActor(name='auth', acl=acl1, originator=test_users.u1, system_role='authenticated_user')
        db.session.add(acl1)
        db.session.add(actor1)

        acl2 = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                                priority=0, operation='get', originator=test_users.u1,
                                record_selector={'term': {
                                    'keywords': 'test'
                                }})
        actor2 = SystemRoleActor(name='noauth', acl=acl2, originator=test_users.u1, system_role='any_user')
        db.session.add(actor2)
        db.session.add(acl2)

    acl1.update()
    acl2.update()

    pid1, record1 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    pid2, record2 = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['test']}, clz=SchemaEnforcingRecord)

    ts1 = datetime.datetime.now()
    time.sleep(0.1)
    RecordIndexer().index(record1)
    current_search_client.indices.flush()

    time.sleep(1)
    ts2 = datetime.datetime.now()
    time.sleep(0.1)
    RecordIndexer().index(record2)
    current_search_client.indices.flush()

    time.sleep(1)
    ts3 = datetime.datetime.now()

    # the records should have cached ACLs, let's check
    idx, doc_type = schema_to_index(RECORD_SCHEMA)
    assert clear_timestamp(current_search_client.get(
        index=idx,
        doc_type=doc_type,
        id=str(record1.id)
    )['_source']['_invenio_explicit_acls']) == [
        {
            'operation': 'get',
            'id': acl1.id,
            'timestamp': 'cleared',
            'system_role': ['authenticated_user']
        }
    ]

    assert clear_timestamp(current_search_client.get(
        index=idx,
        doc_type=doc_type,
        id=str(record2.id)
    )['_source']['_invenio_explicit_acls']) == [
        {
            'operation': 'get',
            'id': acl2.id,
            'timestamp': 'cleared',
            'system_role': ['any_user']
        }
    ]

    # there should be no resource for acl1 before ts1
    assert list(acl1.used_in_records(older_than_timestamp=ts1)) == []
    # one record before ts2 and ts3
    assert list(acl1.used_in_records(older_than_timestamp=ts2)) == [str(record1.id)]
    assert list(acl1.used_in_records(older_than_timestamp=ts3)) == [str(record1.id)]
    # and one record before now
    assert list(acl1.used_in_records()) == [str(record1.id)]

    # there should be no resource for acl2 before ts1 and ts2
    assert list(acl2.used_in_records(older_than_timestamp=ts1)) == []
    assert list(acl2.used_in_records(older_than_timestamp=ts2)) == []
    # one record before ts3
    assert list(acl2.used_in_records(older_than_timestamp=ts3)) == [str(record2.id)]
    # and one record before now
    assert list(acl2.used_in_records()) == [str(record2.id)]



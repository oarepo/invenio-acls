import json

import pytest
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_rest.utils import allow_all
from invenio_search import current_search_client

from helpers import record_url, get_json, create_record, get_from_es, login, records_url
from invenio_explicit_acls.record import SchemaEnforcingRecord

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            search_class='invenio_search.RecordsSearch',
            record_serializers={
                'application/json': ('tests.records.serializers'
                                     ':json_v1_orig_response'),
            },
            search_serializers={
                'application/json': ('tests.records.serializers'
                                     ':json_v1_orig_search'),
            },
        )
    ),
)], indirect=['app'])
def test_get_record_without_enabled_acl(app, db, es):
    pid, record = create_record({}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)

    # make sure it is flushed
    current_search_client.indices.flush()

    # try to get it ...
    with app.test_client() as client:
        res = client.get(record_url(pid))
        assert res.status_code == 200
        assert get_json(res)['metadata'] == {
            'control_number': pid.pid_value,
            '$schema': 'http://localhost/schemas/records/record-v1.0.0.json'
        }

    # get it directly from ES
    res = get_from_es(pid)['_source']
    assert res['control_number'] == pid.pid_value
    assert res['$schema'] == RECORD_SCHEMA


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            search_class='invenio_search.RecordsSearch',
            create_permission_factory_imp=allow_all,
            record_serializers={
                'application/json': ('tests.records.serializers'
                                     ':json_v1_orig_response'),
            },
            search_serializers={
                'application/json': ('tests.records.serializers'
                                     ':json_v1_orig_search'),
            },
        )
    ),
)], indirect=['app'])
def test_create_record_without_enabled_acl(app, db, es):
    with app.test_client() as client:
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': []}),
                               content_type='application/json')
        # print("Response", response.get_data(as_text=True))
        assert response.status_code == 201
        assert 'control_number' in get_json(response)['metadata']


def test_get_record_no_acls_anonymous(app, db, es, es_acl_prepare):
    pid, record = create_record({}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)

    # make sure it is flushed
    current_search_client.indices.flush()

    # try to get it ...
    with app.test_client() as client:
        res = client.get(record_url(pid))
        assert res.status_code == 401  # unauthorized

    # get it directly from ES
    res = get_from_es(pid)['_source']
    assert res['control_number'] == pid.pid_value
    assert res['$schema'] == RECORD_SCHEMA
    assert '_invenio_explicit_acls' in res


def test_get_record_no_acls_authenticated(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)

    # make sure it is flushed
    current_search_client.indices.flush()

    # try to get it ...
    with app.test_client() as client:
        login(client, test_users.u1)
        res = client.get(record_url(pid))
        assert res.status_code == 403  # Forbidden


def test_create_record_no_acls_anonymous(app, db, es, es_acl_prepare):
    with app.test_client() as client:
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': []}),
                               content_type='application/json')
        # print("Response", response.get_data(as_text=True))
        assert response.status_code == 401


def test_create_record_no_acls_authenticated(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        login(client, test_users.u1)
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': []}),
                               content_type='application/json')
        print("Response", response.get_data(as_text=True))
        assert response.status_code == 201

        created_record_metadata = get_json(response)['metadata']

        # check that ACLs are not leaking
        assert 'invenio_explicit_acls' not in created_record_metadata

        pid = PersistentIdentifier.get('recid', created_record_metadata['control_number'])
        res = get_from_es(pid)['_source']

        assert res['control_number'] == pid.pid_value
        assert res['$schema'] == RECORD_SCHEMA
        assert '_invenio_explicit_acls' in res

        # still can not get it
        res = client.get(record_url(pid))
        assert res.status_code == 403  # Forbidden

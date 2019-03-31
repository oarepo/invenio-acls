import json

from flask import g
from flask_login import current_user, login_user
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import current_search_client

from helpers import get_json, login, records_url, clear_timestamp
from invenio_explicit_acls.acl_records_search import ACLRecordsSearch
from invenio_explicit_acls.acls import DefaultACL, ElasticsearchACL
from invenio_explicit_acls.actors import SystemRoleActor, UserActor
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'


def test_aclrecordsearch_returnall(app, db, es, es_acl_prepare, test_users):

    with db.session.begin_nested():
        acl1 = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'test'
                               }})
        actor1 = SystemRoleActor(name='auth', system_role='any_user', acl=acl1, originator=test_users.u1)
        db.session.add(acl1)
        db.session.add(actor1)

    current_explicit_acls.reindex_acl(acl1, delayed=False)

    with app.test_client() as client:
        login(client, test_users.u1)
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': [], 'keywords': ['blah']}),
                               content_type='application/json')
        assert response.status_code == 201
        rest_metadata = get_json(response)['metadata']
        assert 'control_number' in rest_metadata

    # make sure indices are flushed
    current_search_client.indices.flush()

    index, doc_type = schema_to_index(RECORD_SCHEMA)

    record_uuid = PersistentIdentifier.get('recid', rest_metadata['control_number']).object_uuid
    with app.test_request_context():
        login_user(test_users.u1)
        assert current_user == test_users.u1

        # acl1 does not apply to the resource so the search must return no data
        assert not len(ACLRecordsSearch(index=index, doc_type=doc_type, operation='get').get_record(record_uuid).execute())

        # when acl_return_all is specified, return all matching records regardless of ACL
        with_all = ACLRecordsSearch(index=index, doc_type=doc_type).acl_return_all().get_record(record_uuid).execute().hits
        assert len(with_all) == 1
        assert with_all[0]['_invenio_explicit_acls'] == []

    # add another acl, this one maps to the record
    with db.session.begin_nested():

        acl2 = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'blah'
                               }})
        actor2 = UserActor(name='u2', users=[test_users.u2], acl=acl2, originator=test_users.u1)
        db.session.add(acl2)
        db.session.add(actor2)

    current_explicit_acls.reindex_acl(acl2, delayed=False)

    # make sure indices are flushed
    current_search_client.indices.flush()

    # for the same user acl_return_all() must return the record and effective acls
    with app.test_request_context():
        login_user(test_users.u1)

        # when acl_return_all is specified, return all matching records regardless of ACL
        with_all = ACLRecordsSearch(index=index, doc_type=doc_type).acl_return_all().get_record(record_uuid).execute().hits
        assert len(with_all) == 1
        assert clear_timestamp(with_all[0].to_dict()['_invenio_explicit_acls']) == [
            {
                'operation': 'get',
                'id': acl2.id,
                'timestamp': 'cleared',
                'user': [2]
            }
        ]

    # for user2 plain ACLRecordsSearch must return the record and effective acls
    with app.test_request_context():
        login_user(test_users.u2)

        # when acl_return_all is specified, return all matching records regardless of ACL
        with_all = ACLRecordsSearch(index=index, doc_type=doc_type).get_record(record_uuid).execute().hits
        assert len(with_all) == 1
        assert clear_timestamp(with_all[0].to_dict()['_invenio_explicit_acls']) == [
            {
                'operation': 'get',
                'id': acl2.id,
                'timestamp': 'cleared',
                'user': [2]
            }
        ]


#
# Copyright (c) 2019 UCT Prague.
# 
# test_aclrecordsearch.py is part of Invenio Explicit ACLs 
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
import uuid

from elasticsearch_dsl.query import Ids
from flask_login import current_user, login_user
from helpers import clear_timestamp, get_json, login, records_url
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.minters import recid_minter
from invenio_pidstore.models import PersistentIdentifier
from invenio_search import current_search_client

from invenio_explicit_acls.acl_records_search import ACLDefaultFilter, \
    ACLRecordsSearch
from invenio_explicit_acls.acls import DefaultACL, ElasticsearchACL
from invenio_explicit_acls.actors import SystemRoleActor, UserActor
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'records/record-v1.0.0.json'


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
        assert not len(
            ACLRecordsSearch(index=index, doc_type=doc_type, operation='get').get_record(record_uuid).execute())

        # when acl_return_all is specified, return all matching records regardless of ACL
        with_all = ACLRecordsSearch(index=index, doc_type=doc_type).acl_return_all().get_record(
            record_uuid).execute().hits
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
        with_all = ACLRecordsSearch(index=index, doc_type=doc_type).acl_return_all().get_record(
            record_uuid).execute().hits
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


def test_aclrecordsearch_explicit_user(app, db, es, es_acl_prepare, test_users):

    current_explicit_acls.prepare(RECORD_SCHEMA)

    with db.session.begin_nested():
        acl1 = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                          priority=0, operation='get', originator=test_users.u1)
        actor1 = UserActor(name='auth', acl=acl1, users=[test_users.u1], originator=test_users.u1)
        db.session.add(acl1)
        db.session.add(actor1)

    current_explicit_acls.reindex_acl(acl1, delayed=False)

    record_uuid = uuid.uuid4()
    data = {'title': 'blah', 'contributors': [], 'keywords': ['blah']}
    recid_minter(record_uuid, data)
    rec = SchemaEnforcingRecord.create(data, id_=record_uuid)
    RecordIndexer().index(rec)

    current_search_client.indices.flush()

    rs = ACLRecordsSearch(user=test_users.u1)
    rec_id = str(rec.id)

    assert rs.query(Ids(values=[rec_id])).query.to_dict() == {'bool': {'minimum_should_match': '100%', 'filter': [{'bool': {
        'should': [{'nested': {'path': '_invenio_explicit_acls', '_name': 'invenio_explicit_acls_match_get', 'query': {
            'bool': {'must': [{'term': {'_invenio_explicit_acls.operation': 'get'}}, {
                'bool': {'minimum_should_match': 1, 'should': [{'terms': {'_invenio_explicit_acls.role': [1]}},
                                                               {'term': {'_invenio_explicit_acls.user': 1}}]}}]}}}}],
        'minimum_should_match': 1}}], 'must': [{'ids': {'values': [str(rec.id)]}}]}}

    hits = list(ACLRecordsSearch(user=test_users.u1).get_record(rec.id).execute())

    assert len(hits) == 1
    assert hits[0].meta.id == rec_id
    print(hits)

    hits = list(ACLRecordsSearch(user=test_users.u2).get_record(rec.id).execute())
    assert hits == []

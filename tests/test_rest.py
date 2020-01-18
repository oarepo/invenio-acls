#
# Copyright (c) 2019 UCT Prague.
#
# test_rest.py is part of Invenio Explicit ACLs
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

import pytest
from helpers import clear_timestamp, create_record, get_json, login, \
    record_url, records_url
from invenio_indexer.api import RecordIndexer
from invenio_pidstore.models import PersistentIdentifier
from invenio_records import Record
from invenio_search import current_search_client
from sqlalchemy.orm.exc import NoResultFound

from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.actors import SystemRoleActor, UserActor
from invenio_explicit_acls.permissions import acl_read_permission_factory, \
    acl_update_permission_factory
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'records/record-v1.0.0.json'


def test_create_record_check_acl_priority(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        with db.session.begin_nested():
            acl1 = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1, operation='get')
            actor1 = SystemRoleActor(name='auth', system_role='any_user', acl=acl1, originator=test_users.u1)

            acl2 = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=1, originator=test_users.u1, operation='get')
            actor2 = SystemRoleActor(name='auth', system_role='authenticated_user', acl=acl2, originator=test_users.u1)

            db.session.add(acl1)
            db.session.add(actor1)
            db.session.add(acl2)
            db.session.add(actor2)

        login(client, test_users.u1)
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': []}),
                               content_type='application/json')
        assert response.status_code == 201
        rest_metadata = get_json(response)['metadata']
        assert 'control_number' in rest_metadata

        index, doctype = schema_to_index(RECORD_SCHEMA)

        rec_md = current_search_client.get(
            index=index,
            doc_type=doctype,
            id=str(PersistentIdentifier.get('recid', rest_metadata['control_number']).object_uuid)
        )

        clear_timestamp(rec_md)

        assert rec_md['_source']['_invenio_explicit_acls'] == [
            {
                'operation': 'get',
                'id': acl2.id,
                'timestamp': 'cleared',
                'system_role': ['authenticated_user']
            }
        ]


def test_create_acl_after_record(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        login(client, test_users.u1)
        response = client.post(records_url(),
                               data=json.dumps({'title': 'blah', 'contributors': []}),
                               content_type='application/json')
        assert response.status_code == 201
        rest_metadata = get_json(response)['metadata']
        assert 'control_number' in rest_metadata

        with db.session.begin_nested():
            acl1 = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1, operation='get')
            actor1 = SystemRoleActor(name='auth', system_role='any_user', acl=acl1, originator=test_users.u1)
            db.session.add(acl1)
            db.session.add(actor1)

        # reindex all resources that might be affected by the ACL change
        current_explicit_acls.reindex_acl(acl1, delayed=False)

        index, doctype = schema_to_index(RECORD_SCHEMA)

        rec_md = current_search_client.get(
            index=index,
            doc_type=doctype,
            id=str(PersistentIdentifier.get('recid', rest_metadata['control_number']).object_uuid)
        )

        clear_timestamp(rec_md)

        assert rec_md['_source']['_invenio_explicit_acls'] == [
            {
                'operation': 'get',
                'id': acl1.id,
                'timestamp': 'cleared',
                'system_role': ['any_user']
            }
        ]

        # remove the ACL from the database
        with db.session.begin_nested():
            db.session.delete(acl1)

        # reindex records affected by the removal of ACL
        current_explicit_acls.reindex_acl_removed(acl1, delayed=False)

        # make sure all changes had time to propagate and test
        current_search_client.indices.flush()

        rec_md = current_search_client.get(
            index=index,
            doc_type=doctype,
            id=str(PersistentIdentifier.get('recid', rest_metadata['control_number']).object_uuid)
        )

        # there is no ACL in the database => no acls are defined nor enforced on the record
        assert '_invenio_explicit_acls' not in rec_md['_source']


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            read_permission_factory_imp=acl_read_permission_factory,
            record_class=SchemaEnforcingRecord
        )
    ),
)], indirect=['app'], scope="function")
def test_rest_get_record(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        with db.session.begin_nested():
            acl = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1,
                             operation='get')
            actor = UserActor(name='u1', users=[test_users.u1], acl=acl, originator=test_users.u1)

            db.session.add(acl)
            db.session.add(actor)

        pid, record = create_record({'keywords': ['blah']}, clz=SchemaEnforcingRecord)
        RecordIndexer().index(record)
        current_search_client.indices.flush()

        login(client, test_users.u1)
        response = client.get(record_url(pid))
        assert response.status_code == 200

        login(client, test_users.u2)
        response = client.get(record_url(pid))
        assert response.status_code == 403


@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            update_permission_factory_imp=acl_update_permission_factory,
        )
    ),
)], indirect=['app'], scope="function")
def test_rest_update_record(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        with db.session.begin_nested():
            acl = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1,
                             operation='update')
            actor = UserActor(name='u1', users=[test_users.u1], acl=acl, originator=test_users.u1)

            db.session.add(acl)
            db.session.add(actor)

        pid, record = create_record({'keywords': ['blah']}, clz=SchemaEnforcingRecord)
        RecordIndexer().index(record)
        current_search_client.indices.flush()

        login(client, test_users.u1)
        response = client.put(record_url(pid), data=json.dumps({
            'keywords': ['test'],
            'title': 'blah',
            'contributors': []
        }), content_type='application/json')
        assert response.status_code == 200

        # put valid but relative schema
        response = client.put(record_url(pid), data=json.dumps({
            'keywords': ['test'],
            'title': 'blah',
            'contributors': [],
            '$schema': 'records/record-v1.0.0.json'
        }), content_type='application/json')
        assert response.status_code == 200

        rec1 = Record.get_record(pid.object_uuid)
        assert rec1['keywords'] == ['test']
        assert rec1['$schema'] == 'https://localhost/schemas/' + RECORD_SCHEMA

        login(client, test_users.u2)
        response = client.put(record_url(pid), data=json.dumps({
            'keywords': ['test1'],
            'title': 'blah',
            'contributors': [],
        }), content_type='application/json')
        assert response.status_code == 403

        rec1 = Record.get_record(pid.object_uuid)
        assert rec1['keywords'] == ['test']         # check value not overwritten

        # try to pu invalid schema
        login(client, test_users.u1)
        response = client.put(record_url(pid), data=json.dumps({
            'keywords': ['test-invalid'],
            'title': 'blah-invalid',
            'contributors': [],
            '$schema': 'https://localhost/invalid-schema'
        }), content_type='application/json')
        assert response.status_code == 400



@pytest.mark.parametrize('app', [dict(
    records_rest_endpoints=dict(
        recid=dict(
            delete_permission_factory_imp=acl_update_permission_factory,
        )
    ),
)], indirect=['app'], scope="function")
def test_rest_delete_record(app, db, es, es_acl_prepare, test_users):
    with app.test_client() as client:
        with db.session.begin_nested():
            acl = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1,
                             operation='update')
            actor = UserActor(name='u1', users=[test_users.u1], acl=acl, originator=test_users.u1)

            db.session.add(acl)
            db.session.add(actor)

        pid, record = create_record({'keywords': ['blah']}, clz=SchemaEnforcingRecord)
        RecordIndexer().index(record)
        current_search_client.indices.flush()


        login(client, test_users.u2)
        response = client.delete(record_url(pid))
        assert response.status_code == 403

        login(client, test_users.u1)
        response = client.delete(record_url(pid))
        assert response.status_code == 204

        with pytest.raises(NoResultFound):
            Record.get_record(pid.object_uuid)

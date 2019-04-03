#
# Copyright (c) 2019 UCT Prague.
# 
# test_aclserializer.py is part of Invenio Explicit ACLs 
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

from flask import url_for
from flask_login import login_user
from helpers import create_record, get_json, login, set_identity
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client
from records.marshmallow import RecordSchemaV1

from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.actors import UserActor
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.serializers import ACLJSONSerializer
from invenio_explicit_acls.utils import schema_to_index

RECORD_SCHEMA = 'https://localhost/schemas/records/record-v1.0.0.json'


def test_aclserializer(app, db, es, es_acl_prepare, test_users):
    with db.session.begin_nested():
        acl1 = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1, operation='get')
        actor1 = UserActor(name='auth', users=[test_users.u1], acl=acl1, originator=test_users.u1)

        db.session.add(acl1)
        db.session.add(actor1)

    pid, rec = create_record({'title': 'blah'}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(rec)
    current_search_client.indices.flush()

    assert rec['$schema'] in current_explicit_acls.enabled_schemas
    assert list(DefaultACL.get_record_acls(rec)) != []

    index, doc_type = schema_to_index(RECORD_SCHEMA)
    data = current_search_client.get(index=index, doc_type=doc_type, id=str(pid.object_uuid))['_source']
    assert '_invenio_explicit_acls' in data
    assert len(data['_invenio_explicit_acls']) == 1

    with app.test_request_context():
        login_user(test_users.u1)
        set_identity(app, test_users.u1)

        acljson_serializer = ACLJSONSerializer(RecordSchemaV1, acl_rest_endpoint='recid', replace_refs=True)
        serialized = json.loads(acljson_serializer.serialize(pid, rec))
        assert serialized['invenio_explicit_acls'] == ["get"]

    with app.test_client() as client:
        login(client, test_users.u1)
        search_results = client.get(url_for('invenio_records_rest.recid_list'))
        search_results = get_json(search_results)
        hits = search_results['hits']['hits']
        assert len(hits) == 1
        assert hits[0]['invenio_explicit_acls'] == ["get"]

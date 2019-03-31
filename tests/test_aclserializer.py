import json

from flask import url_for
from flask_login import login_user
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client

from helpers import get_json, login, create_record, set_identity
from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.actors import UserActor
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.serializers import ACLJSONSerializer
from records.marshmallow import RecordSchemaV1

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'


def test_aclserializer(app, db, es, es_acl_prepare, test_users):
    with db.session.begin_nested():
        acl1 = DefaultACL(name='default', schemas=[RECORD_SCHEMA], priority=0, originator=test_users.u1, operation='get')
        actor1 = UserActor(name='auth', users=[test_users.u1], acl=acl1, originator=test_users.u1)

        db.session.add(acl1)
        db.session.add(actor1)

    pid, rec = create_record({'title': 'blah'}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(rec)
    current_search_client.indices.flush()

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

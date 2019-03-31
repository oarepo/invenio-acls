from elasticsearch import VERSION as ES_VERSION
from elasticsearch_dsl.query import Term
from flask_security import AnonymousUser

from invenio_explicit_acls.actors import UserActor

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'http://localhost/schemas/records/blah-v1.0.0.json'


def test_get_es_schema(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)

    assert {'type': 'integer'} == actor.get_elasticsearch_schema(ES_VERSION[0])


def test_get_elasticsearch_representation(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert [test_users.u2.id] == actor.get_elasticsearch_representation()


def test_get_elasticsearch_query(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert Term(_invenio_explicit_acls__user=test_users.u3.id) == actor.get_elasticsearch_query(test_users.u3)

    assert actor.get_elasticsearch_query(AnonymousUser()) is None


def test_user_matches(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert not actor.user_matches(test_users.u1)
    assert actor.user_matches(test_users.u2)
    assert not actor.user_matches(test_users.u3)
    assert not actor.user_matches(AnonymousUser())


def test_get_matching_users(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert [test_users.u2.id] == list(actor.get_matching_users())


def test_str(app, db, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert 'UserActor[test]' == str(actor)

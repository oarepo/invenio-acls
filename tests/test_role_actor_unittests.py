from elasticsearch import VERSION as ES_VERSION
from elasticsearch_dsl.query import Term, Terms
from flask_security import AnonymousUser

from invenio_explicit_acls.actors import RoleActor

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'http://localhost/schemas/records/blah-v1.0.0.json'


def test_get_es_schema(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)

    assert {'type': 'integer'} == actor.get_elasticsearch_schema(ES_VERSION[0])


def test_get_elasticsearch_representation(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)
    assert [test_users.r1.id] == actor.get_elasticsearch_representation()


def test_get_elasticsearch_query(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)
    assert Terms(_invenio_explicit_acls__role=[test_users.r1.id]) == actor.get_elasticsearch_query(test_users.u1)
    assert Terms(_invenio_explicit_acls__role=[test_users.r1.id, test_users.r2.id]) == \
           actor.get_elasticsearch_query(test_users.u2)
    assert Terms(_invenio_explicit_acls__role=[test_users.r2.id]) == actor.get_elasticsearch_query(test_users.u3)

    assert actor.get_elasticsearch_query(AnonymousUser()) is None


def test_user_matches(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)
    assert actor.user_matches(test_users.u1)
    assert actor.user_matches(test_users.u2)
    assert not actor.user_matches(test_users.u3)
    assert not actor.user_matches(AnonymousUser())


def test_get_matching_users(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)
    assert {test_users.u1.id, test_users.u2.id} == set(actor.get_matching_users())


def test_str(app, db, test_users):
    with db.session.begin_nested():
        actor = RoleActor(name='test', originator=test_users.u1, roles=[test_users.r1])
        db.session.add(actor)
    assert 'RoleActor[test]' == str(actor)

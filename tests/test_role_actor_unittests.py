#
# Copyright (c) 2019 UCT Prague.
# 
# test_role_actor_unittests.py is part of Invenio Explicit ACLs 
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
from elasticsearch import VERSION as ES_VERSION
from elasticsearch_dsl.query import Term, Terms
from flask_security import AnonymousUser

from invenio_explicit_acls.actors import RoleActor

RECORD_SCHEMA = 'records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'records/blah-v1.0.0.json'


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

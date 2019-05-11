#
# Copyright (c) 2019 UCT Prague.
# 
# test_user_actor_unittests.py is part of Invenio Explicit ACLs 
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
from elasticsearch_dsl.query import Term
from flask_security import AnonymousUser
from invenio_access import any_user, authenticated_user

from invenio_explicit_acls.actors import UserActor

RECORD_SCHEMA = 'records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'records/blah-v1.0.0.json'


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
    assert Term(_invenio_explicit_acls__user=test_users.u3.id) == \
           actor.get_elasticsearch_query(test_users.u3, {'system_roles': [authenticated_user]})

    assert actor.get_elasticsearch_query(AnonymousUser(), {'system_roles': [any_user]}) is None


def test_user_matches(app, db, es, test_users):
    with db.session.begin_nested():
        actor = UserActor(name='test', originator=test_users.u1, users=[test_users.u2])
        db.session.add(actor)
    assert not actor.user_matches(test_users.u1, {'system_roles': [authenticated_user]})
    assert actor.user_matches(test_users.u2, {'system_roles': [authenticated_user]})
    assert not actor.user_matches(test_users.u3, {'system_roles': [authenticated_user]})
    assert not actor.user_matches(AnonymousUser(), {'system_roles': [any_user]})


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

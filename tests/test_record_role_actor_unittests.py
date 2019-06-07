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
import pytest
from elasticsearch import VERSION as ES_VERSION
from elasticsearch_dsl.query import Terms
from flask_security import AnonymousUser
from invenio_access import any_user, authenticated_user

from invenio_explicit_acls.actors import RecordRoleActor

RECORD_SCHEMA = 'records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'records/blah-v1.0.0.json'


def test_get_es_schema(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)

    assert {'type': 'integer'} == actor.get_elasticsearch_schema(ES_VERSION[0])


def test_get_elasticsearch_representation(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)

    with pytest.raises(Exception, message='This Actor works on record, so pass one!'):
        actor.get_elasticsearch_representation()

    assert [test_users.r1.id] == actor.get_elasticsearch_representation(record={
        'roles': test_users.r1.id
    })
    assert [test_users.r1.id] == actor.get_elasticsearch_representation(record={
        'roles': [test_users.r1.id]
    })

    others = ['aaa']
    assert [test_users.r1.id] + others == actor.get_elasticsearch_representation(others, record={
        'roles': [test_users.r1.id]
    })



def test_get_elasticsearch_query(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)
    assert Terms(_invenio_explicit_acls__role=[test_users.r1.id]) == \
           actor.get_elasticsearch_query(test_users.u1, {'system_roles': [authenticated_user]})
    assert Terms(_invenio_explicit_acls__role=[test_users.r1.id, test_users.r2.id]) == \
           actor.get_elasticsearch_query(test_users.u2, {'system_roles': [authenticated_user]})
    assert Terms(_invenio_explicit_acls__role=[test_users.r2.id]) == \
           actor.get_elasticsearch_query(test_users.u3, {'system_roles': [authenticated_user]})

    assert actor.get_elasticsearch_query(AnonymousUser(), {'system_roles': [any_user]}) is None


def test_user_matches(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)
    assert not actor.user_matches(test_users.u1, {'system_roles': [authenticated_user]})
    assert not actor.user_matches(test_users.u2, {'system_roles': [authenticated_user]})
    assert not actor.user_matches(test_users.u3, {'system_roles': [authenticated_user]})
    assert not actor.user_matches(AnonymousUser(), {'system_roles': [any_user]})

    assert actor.user_matches(test_users.u1, {'system_roles': [authenticated_user]}, record={
        'roles': test_users.r1.id
    })
    assert actor.user_matches(test_users.u2, {'system_roles': [authenticated_user]}, record={
        'roles': test_users.r1.id
    })
    assert not actor.user_matches(test_users.u3, {'system_roles': [authenticated_user]}, record={
        'roles': test_users.r1.id
    })
    assert not actor.user_matches(AnonymousUser(), {'system_roles': [any_user]}, record={
        'roles': test_users.r1.id
    })


def test_get_matching_users(app, db, es, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)
    assert set() == set(actor.get_matching_users())
    assert {test_users.u1.id, test_users.u2.id} == set(actor.get_matching_users(record={
        'roles': test_users.r1.id
    }))


def test_str(app, db, test_users):
    with db.session.begin_nested():
        actor = RecordRoleActor(name='test', originator=test_users.u1, path='/roles')
        db.session.add(actor)
    assert 'RecordRoleActor[test; /roles]' == str(actor)

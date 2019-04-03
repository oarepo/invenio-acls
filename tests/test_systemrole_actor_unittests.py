#
# Copyright (c) 2019 UCT Prague.
# 
# test_systemrole_actor_unittests.py is part of Invenio Explicit ACLs 
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
from elasticsearch_dsl.query import Term, Terms
from flask import current_app
from flask_principal import Identity, identity_changed
from flask_security import AnonymousUser
from helpers import set_identity
from invenio_access import authenticated_user

from invenio_explicit_acls.actors import SystemRoleActor

ANY_USER = 'any_user'

RECORD_SCHEMA = 'https://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'https://localhost/schemas/records/blah-v1.0.0.json'


def test_get_es_schema(app, db, es, test_users):
    with db.session.begin_nested():
        actor = SystemRoleActor(name='test', originator=test_users.u1, system_role=ANY_USER)
        db.session.add(actor)

    assert {'type': 'keyword'} == actor.get_elasticsearch_schema(ES_VERSION[0])


def test_get_elasticsearch_representation(app, db, es, test_users):
    with db.session.begin_nested():
        actor = SystemRoleActor(name='test', originator=test_users.u1, system_role=ANY_USER)
        db.session.add(actor)
    assert [ANY_USER] == actor.get_elasticsearch_representation()


def test_get_elasticsearch_query(app, db, es, test_users):
    with current_app.test_request_context():
        assert Term(_invenio_explicit_acls__system_role='any_user') == SystemRoleActor.get_elasticsearch_query(
            AnonymousUser())

        set_identity(app, test_users.u1)
        assert Terms(_invenio_explicit_acls__system_role=['any_user',
                                                          'authenticated_user']) == SystemRoleActor.get_elasticsearch_query(
            test_users.u1)

        # faked user - different identity in flask.g than user
        assert SystemRoleActor.get_elasticsearch_query(test_users.u2) is None

        set_identity(app, test_users.u2)
        assert Terms(_invenio_explicit_acls__system_role=['any_user', 'authenticated_user']) == \
               SystemRoleActor.get_elasticsearch_query(test_users.u2)


def test_user_matches(app, db, es, test_users):
    with db.session.begin_nested():
        actor = SystemRoleActor(name='test', originator=test_users.u1, system_role='authenticated_user')
        db.session.add(actor)

    with current_app.test_request_context():
        assert not actor.user_matches(AnonymousUser())

        set_identity(app, test_users.u1)
        assert actor.user_matches(test_users.u1)

        # faked user - different identity in flask.g than user
        set_identity(app, test_users.u1)
        assert not actor.user_matches(test_users.u2)

        set_identity(app, test_users.u2)
        assert actor.user_matches(test_users.u2)

        set_identity(app, test_users.u3)
        assert actor.user_matches(test_users.u3)


def test_get_matching_users(app, db, es, test_users):
    with db.session.begin_nested():
        actor = SystemRoleActor(name='test', originator=test_users.u1, system_role='authenticated_user')
        actor1 = SystemRoleActor(name='test 1', originator=test_users.u1, system_role='custom_system_role')
        db.session.add(actor)
        db.session.add(actor1)

    assert {test_users.u1.id, test_users.u2.id, test_users.u3.id} == set(actor.get_matching_users())

    # custom system role can not return matching roles in this implementation
    with pytest.raises(NotImplementedError):
        list(actor1.get_matching_users())


def test_str(app, db, test_users):
    with db.session.begin_nested():
        actor = SystemRoleActor(name='test', originator=test_users.u1, system_role='authenticated_user')
        db.session.add(actor)
    assert 'SystemRoleActor[test]' == str(actor)

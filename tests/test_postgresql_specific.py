#
# Copyright (c) 2019 UCT Prague.
# 
# test_postgresql_specific.py is part of Invenio Explicit ACLs 
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
from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.proxies import current_explicit_acls

RECORD_SCHEMA = 'records/record-v1.0.0.json'


def test_empty_database_queries(app, db, es, es_acl_prepare, test_users):
    assert list(current_explicit_acls.enabled_schemas) == []


def test_existing_acls_database_queries(app, db, es, es_acl_prepare, test_users):
    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=['aaa', RECORD_SCHEMA], operation='get', originator=test_users.u1)
        db.session.add(acl)

    assert set(current_explicit_acls.enabled_schemas) == {'aaa', RECORD_SCHEMA}

    with db.session.begin_nested():
        acl = DefaultACL(name='test1', schemas=[RECORD_SCHEMA], operation='get', originator=test_users.u1)
        db.session.add(acl)

    assert DefaultACL.query.count() == 2
    assert set(current_explicit_acls.enabled_schemas) == {'aaa', RECORD_SCHEMA}
    assert len(list(current_explicit_acls.enabled_schemas)) == 2


def test_filter_schemas(app, db, es, es_acl_prepare, test_users):
    if db.engine.dialect.name != 'postgresql':
        return

    assert DefaultACL.query.filter(DefaultACL.schemas.any('aaa')).count() == 0

    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=['aaa', RECORD_SCHEMA], operation='get', originator=test_users.u1)
        db.session.add(acl)

    assert DefaultACL.query.filter(DefaultACL.schemas.any('aaa')).count() == 1
    assert DefaultACL.query.filter(DefaultACL.schemas.any(RECORD_SCHEMA)).count() == 1

    with db.session.begin_nested():
        acl1 = DefaultACL(name='test1', schemas=[RECORD_SCHEMA], operation='get', originator=test_users.u1)
        db.session.add(acl1)

    assert DefaultACL.query.filter(DefaultACL.schemas.any('aaa')).count() == 1
    assert DefaultACL.query.filter(DefaultACL.schemas.any(RECORD_SCHEMA)).count() == 2

    with db.session.begin_nested():
        acl1.schemas = ['aaa']
        db.session.add(acl1)

    assert DefaultACL.query.filter(DefaultACL.schemas.any('aaa')).count() == 2
    assert DefaultACL.query.filter(DefaultACL.schemas.any(RECORD_SCHEMA)).count() == 1

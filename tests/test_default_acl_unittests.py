#
# Copyright (c) 2019 UCT Prague.
# 
# test_default_acl_unittests.py is part of Invenio Explicit ACLs 
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
from helpers import create_record
from invenio_indexer.api import RecordIndexer
from invenio_search import current_search_client

from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.record import SchemaEnforcingRecord

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'http://localhost/schemas/records/blah-v1.0.0.json'


def test_default_acl_get_record_acl(app, db, es, es_acl_prepare, test_users):
    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                         priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl)
        acl2 = DefaultACL(name='test 2', schemas=[ANOTHER_SCHEMA],
                          priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl2)

    pid, record = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)

    acls = list(DefaultACL.get_record_acls(record))
    assert len(acls) == 1
    assert isinstance(acls[0], DefaultACL)
    assert acls[0].id == acl.id


def test_default_acl_prepare_schema_acl(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    DefaultACL.prepare_schema_acls(RECORD_SCHEMA)


def test_default_acl_get_matching_resources(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)
    current_search_client.indices.flush()

    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                         priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl)
    ids = list(acl.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid.object_uuid)


def test_default_acl_update(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                         priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl)
    acl.update()


def test_default_acl_delete(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                         priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl)
    acl.delete()

def test_default_acl_repr(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = DefaultACL(name='test', schemas=[RECORD_SCHEMA],
                         priority=0, operation='get', originator=test_users.u1)
        db.session.add(acl)
    assert repr(acl) == "Default ACL on ['http://localhost/schemas/records/record-v1.0.0.json']"

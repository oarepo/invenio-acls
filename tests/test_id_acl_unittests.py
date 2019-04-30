#
# Copyright (c) 2019 UCT Prague.
# 
# test_id_acl_unittests.py is part of Invenio Explicit ACLs 
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

from invenio_explicit_acls.acls import IdACL
from invenio_explicit_acls.record import SchemaEnforcingRecord

RECORD_SCHEMA = 'records/record-v1.0.0.json'
ANOTHER_SCHEMA = 'records/blah-v1.0.0.json'


def test_id_acl_get_record_acl(app, db, es, es_acl_prepare, test_users):

    pid, record = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)

    with db.session.begin_nested():
        acl = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1,
                    record_id=str(record.id))
        db.session.add(acl)
        acl2 = IdACL(name='test 2', schemas=[ANOTHER_SCHEMA],
                     priority=0, operation='get', originator=test_users.u1,
                     record_id=str(record1.id))
        db.session.add(acl2)

    acls = list(IdACL.get_record_acls(record))
    assert len(acls) == 1
    assert isinstance(acls[0], IdACL)
    assert acls[0].id == acl.id


def test_id_acl_prepare_schema_acl(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    IdACL.prepare_schema_acls(RECORD_SCHEMA)


def test_id_acl_get_matching_resources(app, db, es, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)
    pid1, record1 = create_record({'$schema': RECORD_SCHEMA}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)
    RecordIndexer().index(record1)
    current_search_client.indices.flush()

    with db.session.begin_nested():
        acl = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1, record_id=str(record.id))
        db.session.add(acl)

        acl1 = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1, record_id=str(record1.id))
        db.session.add(acl1)

    ids = list(acl.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid.object_uuid)

    ids = list(acl1.get_matching_resources())
    assert len(ids) == 1
    assert ids[0] == str(pid1.object_uuid)


def test_id_acl_update(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1, record_id='1111-11111111-11111111-1111')
        db.session.add(acl)
    acl.update()


def test_id_acl_delete(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1, record_id='1111-11111111-11111111-1111')
        db.session.add(acl)
    acl.delete()


def test_id_acl_repr(app, db, es, es_acl_prepare, test_users):
    # should pass as it does nothing
    with db.session.begin_nested():
        acl = IdACL(name='test', schemas=[RECORD_SCHEMA],
                    priority=0, operation='get', originator=test_users.u1, record_id='1111-11111111-11111111-1111')
        db.session.add(acl)
    assert repr(acl) == "ID ACL on 1111-11111111-11111111-1111"


def test_id_acl_record_str(app, db, es, es_acl_prepare, test_users):

    pid1, record1 = create_record({})
    pid2, record2 = create_record({'title': 'blah'})
    pid3, record3 = create_record({'title': {'_': 'blah', 'cs': 'blah cs', 'en': 'blah en'}})

    acl1 = IdACL(name='test', schemas=[RECORD_SCHEMA],
                priority=0, operation='get', originator=test_users.u1, record_id=str(record1.id))
    acl2 = IdACL(name='test', schemas=[RECORD_SCHEMA],
                priority=0, operation='get', originator=test_users.u1, record_id=str(record2.id))
    acl3 = IdACL(name='test', schemas=[RECORD_SCHEMA],
                priority=0, operation='get', originator=test_users.u1, record_id=str(record3.id))
    acl4 = IdACL(name='test', schemas=[RECORD_SCHEMA],
                priority=0, operation='get', originator=test_users.u1, record_id='1111-11111111-11111111-1111')

    assert acl1.record_str == "%s: {'control_number': '1'}" % record1.id
    assert acl2.record_str == "%s: blah" % record2.id
    assert acl3.record_str == "%s: blah" % record3.id
    assert acl4.record_str == "No record for ID ACL on 1111-11111111-11111111-1111"

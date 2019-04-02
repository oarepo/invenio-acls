from invenio_explicit_acls.acls import DefaultACL
from invenio_explicit_acls.proxies import current_explicit_acls

RECORD_SCHEMA = 'http://localhost/schemas/records/record-v1.0.0.json'


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

import pytest

from invenio_explicit_acls.models import ACL, Actor


def test_abstracts_in_acl(app, db):
    acl = ACL()

    with pytest.raises(NotImplementedError):
        acl.prepare_schema_acls(None)

    with pytest.raises(NotImplementedError):
        acl.get_record_acls(None)

    with pytest.raises(NotImplementedError):
        acl.get_matching_resources()

    with pytest.raises(NotImplementedError):
        acl.update()

    with pytest.raises(NotImplementedError):
        acl.delete()


def test_abstracts_in_actor(app, db):
    actor = Actor()

    with pytest.raises(NotImplementedError):
        actor.get_elasticsearch_schema(None)

    with pytest.raises(NotImplementedError):
        actor.get_elasticsearch_representation(None)

    with pytest.raises(NotImplementedError):
        actor.get_elasticsearch_query(None)

    with pytest.raises(NotImplementedError):
        actor.user_matches(None)

    with pytest.raises(NotImplementedError):
        actor.get_matching_users()

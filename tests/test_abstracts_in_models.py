#
# Copyright (c) 2019 UCT Prague.
# 
# test_abstracts_in_models.py is part of Invenio Explicit ACLs 
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

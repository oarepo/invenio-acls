#
# Copyright (c) 2019 UCT Prague.
# 
# helpers.py is part of Invenio Explicit ACLs 
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

"""Helper methods for tests."""

import copy
import json
import uuid

import flask
from flask import current_app, url_for
from flask_principal import Identity, identity_changed
from invenio_access import authenticated_user
from invenio_db import db
from invenio_pidstore import current_pidstore
from invenio_records import Record
from invenio_search import current_search_client
from jsonschema.exceptions import ValidationError
from six.moves.urllib.parse import parse_qs, urlparse

from invenio_explicit_acls.utils import schema_to_index


def get_json(response):
    """Get JSON from response."""
    return json.loads(response.get_data(as_text=True))


def create_record(data, clz=Record):
    """Create a test record."""
    with db.session.begin_nested():
        data = copy.deepcopy(data)
        rec_uuid = uuid.uuid4()
        pid = current_pidstore.minters['recid'](rec_uuid, data)
        record = clz.create(data, id_=rec_uuid)
    return pid, record


def assert_hits_len(res, hit_length):
    """Assert number of hits."""
    assert res.status_code == 200
    assert len(get_json(res)['hits']['hits']) == hit_length


def parse_url(url):
    """Build a comparable dict from the given url.

    The resulting dict can be comparend even when url's query parameters
    are in a different order.
    """
    parsed = urlparse(url)
    return {
        'scheme': parsed.scheme,
        'netloc': parsed.netloc,
        'path': parsed.path,
        'qs': parse_qs(parsed.query),
    }


def to_relative_url(url):
    """Build relative URL from external URL.

    This is needed because the test client discards query parameters on
    external urls.
    """
    parsed = urlparse(url)
    return parsed.path + '?' + '&'.join([
        '{0}={1}'.format(param, val[0]) for
        param, val in parse_qs(parsed.query).items()
    ])


def record_url(pid):
    """Get URL to a record."""
    if hasattr(pid, 'pid_value'):
        val = pid.pid_value
    else:
        val = pid

    return url_for('invenio_records_rest.recid_item', pid_value=val)


def records_url():
    """Get URL to record collection."""
    return url_for('invenio_records_rest.recid_list')


def _mock_validate_fail(self):
    """Simulate a validation fail."""
    raise ValidationError("")


def get_from_es(pid, schema='records/record-v1.0.0.json'):
    """Retrieves a record from elasticsearch."""
    index, doctype = schema_to_index(schema)
    return current_search_client.get(index=index, doc_type=doctype, id=pid.object_uuid)


def login(http_client, user):
    """Calls test login endpoint to log user."""
    resp = http_client.get(f'/test/login/{user.id}')
    assert resp.status_code == 200


def clear_timestamp(x):
    """Replaces (recursively) values of all keys named 'timestamp'."""
    if isinstance(x, dict):
        if 'timestamp' in x:
            x['timestamp'] = 'cleared'
        for v in x.values():
            clear_timestamp(v)
    elif isinstance(x, list) or isinstance(x, tuple):
        for v in x:
            clear_timestamp(v)
    return x


def set_identity(u):
    """Sets identity in flask.g to the user."""
    identity = Identity(u.id)
    identity.provides.add(authenticated_user)
    identity_changed.send(current_app._get_current_object(), identity=identity)
    assert flask.g.identity.id == u.id

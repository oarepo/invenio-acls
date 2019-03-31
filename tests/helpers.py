# -*- coding: utf-8 -*-
#
# This file is part of Invenio.
# Copyright (C) 2015-2018 CERN.
#
# Invenio is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
# this file was taken from https://github.com/inveniosoftware/invenio-records-rest/blob/master/tests/helpers.py
#
#

"""Helper methods for tests."""

import copy
import json
import uuid

from flask import url_for
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
    """Get URL to record collection"""
    return url_for('invenio_records_rest.recid_list')


def _mock_validate_fail(self):
    """Simulate a validation fail."""
    raise ValidationError("")


def get_from_es(pid, schema='records/record-v1.0.0.json'):
    index, doctype = schema_to_index(schema)
    return current_search_client.get(index=index, doc_type=doctype, id=pid.object_uuid)


def login(http_client, user):
    resp = http_client.get(f'/test/login/{user.id}')
    assert resp.status_code == 200


def clear_timestamp(x):
    if isinstance(x, dict):
        if 'timestamp' in x:
            x['timestamp'] = 'cleared'
        for v in x.values():
            clear_timestamp(v)
    elif isinstance(x, list) or isinstance(x, tuple):
        for v in x:
            clear_timestamp(v)
    return x


def set_identity(app, u):
    identity = Identity(u.id)
    identity.provides.add(authenticated_user)
    identity_changed.send(app, identity=identity)

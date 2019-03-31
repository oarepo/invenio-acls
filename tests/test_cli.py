#
# Copyright (c) 2019 UCT Prague.
# 
# test_cli.py is part of Invenio Explicit ACLs 
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
from invenio_search import current_search_client

from invenio_explicit_acls.version import __version__


def test_version():
    assert __version__.startswith('2.0.')


def test_cli_prepare(app, db, es, es_acl_prepare):
    assert 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0' in current_search_client.indices.get('*')
    mapping = current_search_client.indices.get_mapping('records-record-v1.0.0')
    mapping = mapping['records-record-v1.0.0']['mappings']['record-v1.0.0']['properties']
    assert '_invenio_explicit_acls' in mapping

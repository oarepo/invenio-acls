#
# Copyright (c) 2019 UCT Prague.
# 
# __init__.py is part of Invenio Explicit ACLs 
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

"""Record serializers."""

from __future__ import absolute_import, print_function

from invenio_records_rest.serializers.json import JSONSerializer
from invenio_records_rest.serializers.response import record_responsify, \
    search_responsify

from invenio_explicit_acls.serializers import ACLJSONSerializer

from ..marshmallow import RecordSchemaV1

# Serializers
# ===========
#: JSON serializer definition.
json_v1 = ACLJSONSerializer(RecordSchemaV1, replace_refs=True)

json_v1_orig = JSONSerializer(RecordSchemaV1, replace_refs=True)

# Records-REST serializers
# ========================
#: JSON record serializer for individual records.
json_v1_response = record_responsify(json_v1, 'application/json')
#: JSON record serializer for search results.
json_v1_search = search_responsify(json_v1, 'application/json')

#: JSON record serializer for individual records.
json_v1_orig_response = record_responsify(json_v1_orig, 'application/json')
#: JSON record serializer for search results.
json_v1_orig_search = search_responsify(json_v1_orig, 'application/json')

__all__ = (
    'json_v1',
    'json_v1_response',
    'json_v1_search',
    'json_v1_orig_response',
    'json_v1_orig_search'
)

#
# Copyright (c) 2019 UCT Prague.
# 
# utils.py is part of Invenio Explicit ACLs 
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
"""Utility functions."""
import json

from invenio_search import current_search
from invenio_search.utils import schema_to_index as invenio_schema_to_index
from sqlalchemy.schema import Column
from sqlalchemy.types import Integer, String, TypeDecorator


def schema_to_index(schema):
    """Converts schema to a pair of (index, doctype)."""
    index_names = current_search.mappings.keys()
    index, doc_type = invenio_schema_to_index(schema, index_names=index_names)
    if index is None:
        raise AttributeError('No index found for schema %s. '
                             'The parameter must be an url ending with something similar to '
                             'records/record-v1.0.0.json' % schema)
    return index, doc_type


class ArrayType(TypeDecorator):
    """
    Sqlite-like does not support arrays, so let's use a custom type decorator.

    See http://docs.sqlalchemy.org/en/latest/core/types.html#sqlalchemy.types.TypeDecorator
    """

    impl = String

    def __init__(self, impl_type, *args, **kwargs):
        """Init."""
        self.impl = impl_type
        super().__init__(*args, **kwargs)

    def process_bind_param(self, value, dialect):
        """Receive a bound parameter value to be converted."""
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        """Receive a result-row column value to be converted."""
        return json.loads(value)

    def copy(self):
        """Produce a copy of this :class:`.TypeDecorator` instance."""
        return ArrayType(self.impl.length)

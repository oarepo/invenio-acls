#
# Copyright (c) 2019 UCT Prague.
# 
# propertyvalue_acls.py is part of Invenio Explicit ACLs 
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
"""Simple ACL matching all records that have a metadata property equal to a given value."""
import enum
import logging

from invenio_db import db
from sqlalchemy_utils import ChoiceType

from invenio_explicit_acls.models import ACL

from .es_mixin import ESACLMixin

logger = logging.getLogger(__name__)


class MatchOperation(enum.Enum):
    """The operation for matching property to value might be either term or match - choose according to the schema."""

    match = 'match'
    term  = 'term'


class PropertyValueACL(ESACLMixin, ACL):
    """An ACL that matches all records that have a metadata property equal to a given constant value."""

    __tablename__ = 'explicit_acls_propertyvalueacl'
    __mapper_args__ = {
        'polymorphic_identity': 'propertyvalue',
    }

    #
    # Fields
    #
    id = db.Column(db.String(36), db.ForeignKey('explicit_acls_acl.id'), primary_key=True)
    """Id maps to base class' id"""

    property_name = db.Column(db.String(64))
    """Name of the property in elasticsearch."""

    property_value = db.Column(db.String(128))
    """Value of the property in elasticsearch."""

    match_operation = db.Column(ChoiceType(MatchOperation, impl=db.String(length=10)), default=MatchOperation.term.value)
    """Search mode: can be either term or match"""

    @property
    def record_selector(self):
        """Returns an elasticsearch query matching resources that this ACL maps to."""
        return {
            self.match_operation: {
                self.property_name: self.property_value
            }
        }

    def __repr__(self):
        """String representation for model."""
        return '"{0.name}" ({0.id}) on schemas {0.schemas}'.format(self)

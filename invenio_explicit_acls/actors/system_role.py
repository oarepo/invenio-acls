#
# Copyright (c) 2019 UCT Prague.
# 
# system_role.py is part of Invenio Explicit ACLs 
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
"""A modul that defines anonymous actor."""
import logging
from typing import Iterable

from elasticsearch_dsl import Q
from flask import g
from invenio_accounts.models import User
from invenio_db import db

from ..models import Actor

logger = logging.getLogger(__name__)


class SystemRoleActor(Actor):
    """An actor matching authenticated users, anonymous users or everyone."""

    __tablename__ = 'explicit_acls_system_role'
    __mapper_args__ = {
        'polymorphic_identity': 'system_role',
    }

    id = db.Column(db.String(36), db.ForeignKey('explicit_acls_actor.id'), primary_key=True)
    """Id maps to base class' id"""

    system_role = db.Column(db.String(32))
    """The system role (any_user, authenticated_user)."""

    def __str__(self):
        """Returns the string representation of the actor."""
        return 'SystemRoleActor[%s]' % self.name

    @classmethod
    def get_elasticsearch_schema(clz, _es_version):
        """
        Returns the elasticsearch schema for the _invenio_explicit_acls property.

        The property looks like::

            _invenio_explicit_acls [{
               "timestamp": "...when the ACL has been applied to the resource",
               "acl": <id of the acl>,
               "operation": name of the operation
                system_role: ["any_user", "authenticated_user"]
            }]

        :return:
        """
        return {
            'type': 'keyword'
        }

    def get_elasticsearch_representation(self, another=None):
        """
        Returns ES representation of this Actor.

        :param another: A serialized representation of the previous Actor of the same type.
                        The implementation should merge it with its own ES representation
        :return: The elasticsearch representation of the property on Record
        """
        return [self.system_role] + (another or [])

    @classmethod
    def get_elasticsearch_query(clz, user: User) -> Q or None:
        """
        Returns elasticsearch query (elasticsearch_dls.Q) for the ACL.

        This is the counterpart of get_elasticsearch_representation and will be placed inside "nested" query
        _invenio_explicit_acls

        :param user:  the user to be checked
        :return:      elasticsearch query that enforces the user
        """
        if user.is_anonymous:
            return Q('term', _invenio_explicit_acls__system_role='any_user')
        if not hasattr(g, 'identity'):  # pragma: no cover
            logger.error('Can not determine system role for a user that does not have Identity in flask.g')
            return None

        identity = g.identity
        if not identity:  # pragma: no cover
            logger.error('Can not determine system role for a user that does not have Identity in flask.g')
            return None

        if identity.id != user.id:
            logger.error('Can not determine system role for a user whose id does not match Identity in flask.g')
            return None

        # sorting for easier tests
        roles = sorted([p[1] for p in identity.provides if p[0] == 'system_role'])

        return Q('terms', _invenio_explicit_acls__system_role=roles)

    def user_matches(self, user: User) -> bool:
        """
        Checks if a user is allowed to perform any operation according to the ACL.

        :param user: user being checked against the ACL
        """
        if user.is_anonymous:
            return self.system_role == 'any_user'

        identity = g.identity
        if identity.id != user.id:
            logger.error('Can not determine system role for a user whose id does not match Identity in flask.g')
            return False

        roles = [p[1] for p in identity.provides if p[0] == 'system_role']
        return self.system_role in roles

    def get_matching_users(self) -> Iterable[int]:
        """
        Returns a list of users matching this Actor.

        :return: Iterable of a user ids
        """
        if self.system_role == 'any_user' or self.system_role == 'authenticated_user':
            for u in User.query.all():
                yield u.id
        else:
            raise NotImplementedError(
                'Can not get a list of matching users for system role %s - not implemented' % self.system_role)

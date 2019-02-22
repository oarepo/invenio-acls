"""Models for storing ACLs."""
from invenio_accounts.models import User, Role
from invenio_db import db
from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy_utils import Timestamp
from werkzeug.utils import cached_property

association_table = db.Table(
    'invenio_acls_index_mapping', db.Model.metadata,
    Column('index_id', Integer, ForeignKey('invenio_acls_index.id')),
    Column('acl_id', Integer, ForeignKey('invenio_acls_recordacl.id'))
)


class Index(db.Model):
    """Elasticsearch Index"""

    __tablename__ = 'invenio_acls_index'

    #
    # Fields
    #
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    """Primary key."""

    elasticsearch_index = db.Column(
        db.String,
        nullable=False,
        unique=True
    )

    acls = relationship("ACL", secondary=association_table, back_populates='indices')

    def __str__(self):
        return self.elasticsearch_index


class ACL(db.Model, Timestamp):
    """Storage for ACL Sets."""

    __tablename__ = 'invenio_acls_recordacl'

    #
    # Fields
    #
    id = db.Column(
        db.Integer,
        primary_key=True,
        autoincrement=True
    )
    """Primary key."""

    name = db.Column(
        db.String,
        nullable=False
    )

    record_selector = db.Column(JSONB)
    """JSON field with pattern to which the ACL applies. 
        For example, {'faculty': 'FCHI'} pattern selects all resources with faculty FCHI
    """

    indices = relationship("Index", secondary=association_table, back_populates='acls')

    database_operations = db.Column(
        JSONB, name='operations', default=list
    )
    """Operations with actors. JSON with top-level array"""

    @cached_property
    def operations(self):
        if self.database_operations is None:
            self.database_operations = []
        return Operations(self.database_operations)

    def __repr__(self):
        """String representation for model."""
        return '"{0.name}" ({0.id}) on ES indices {0.indices}'.format(self)

    def as_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'indices': [x.elasticsearch_index for x in self.indices],
            'record_selector': self.record_selector,
            'acls': self.database_operations
        }


class Actors:
    def __init__(self, data):
        self.__data = data

    @property
    def user_ids(self):
        return tuple(self.__data.get('users', []))

    @user_ids.setter
    def user_ids(self, user_ids):
        self.__data['users'] = user_ids

    @property
    def users(self):
        return User.query.filter(User.id.in_(self.__data.get('users', [])))

    @users.setter
    def users(self, users):
        self.__data['users'] = [x.id for x in users]

    @property
    def role_ids(self):
        return tuple(self.__data.get('roles', []))

    @role_ids.setter
    def role_ids(self, role_ids):
        self.__data['roles'] = role_ids

    @property
    def roles(self):
        return Role.query.filter(Role.id.in_(self.__data.get('roles', [])))

    @roles.setter
    def roles(self, roles):
        self.__data['roles'] = [x.id for x in roles]


class Operation:
    def __init__(self, data):
        self.__data = data

    @property
    def operation(self):
        return self.__data['operation']

    @operation.setter
    def operation(self, operation):
        self.__data['operation'] = operation

    @cached_property
    def actors(self):
        if 'actors' not in self.__data:
            self.__data['actors'] = {}
        return Actors(self.__data['actors'])


class Operations:
    def __init__(self, operations):
        self.__data = operations
        self.__operations = [Operation(x) for x in operations]

    def __getitem__(self, item):
        return self.__operations[item]

    def add_operation(self, operation_type, users=None, roles=None) -> Operation:
        proto = {
            "operation": operation_type,
            "actors": {

            }
        }
        if users:
            proto['actors']['users'] = [x.id if isinstance(x, User) else x for x in users]
        if roles:
            proto['actors']['roles'] = [str(x.id) if isinstance(x, Role) else str(x) for x in roles]

        op = Operation(proto)
        self.__data.append(proto)
        self.__operations.append(op)
        return op

    def __iter__(self):
        return iter(self.__operations)

    def __delitem__(self, key):
        del self.__operations[key]
        del self.__data[key]

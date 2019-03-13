import sqlalchemy
from invenio_accounts.models import User, Role
from invenio_db import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.utils import cached_property


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


class ACL(object):
    id = db.Column(
        UUID(as_uuid=True),
        server_default=sqlalchemy.text("gen_random_uuid()"),
        primary_key=True
    )
    """Primary key."""

    priority = db.Column(
        db.Integer,
        default=0)
    """Priority of the acl rule. Only the applicable rules with the highest priority get applied to the resource"""

    database_operations = db.Column(
        JSONB, name='operations', default=list
    )
    """Operations with actors. JSON with top-level array"""

    @cached_property
    def operations(self):
        if self.database_operations is None:
            self.database_operations = []
        return Operations(self.database_operations)

    indices = db.Column(ARRAY(db.String))

    @declared_attr
    def originator_id(cls):
        return db.Column(db.ForeignKey(User.id, ondelete='CASCADE', ),
                         nullable=False, index=True)

    @declared_attr
    def originator(cls):
        return db.relationship(
            User,
            backref=db.backref(
                "authored_acls_%s" % cls.__name__
            )
        )

    @property
    def handler_name(self):
        """
        returns the name under which the handler is registered in entry points
        """
        raise NotImplementedError(
            'Implement handler_name property or set up handler instance on this acl: %s' % type(self))


__all__ = [
    'ACL',
    'Operations',
    'Operation',
    'Actors'
]

"""Models for storing Elasticsearch ACLs."""
from invenio_db import db
from invenio_records import Record
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy_continuum import make_versioned
from sqlalchemy_utils import Timestamp

from invenio_acls.models_acl import ACL

make_versioned()


class DefaultACL(ACL, db.Model, Timestamp):
    """Storage for ACL Sets."""

    __tablename__ = 'invenio_acls_defaultacl'
    __versioned__ = {}

    name = db.Column(
        db.String,
        nullable=False
    )

    def __repr__(self):
        """String representation for model."""
        return 'Default ACL on {0.indices}'.format(self)

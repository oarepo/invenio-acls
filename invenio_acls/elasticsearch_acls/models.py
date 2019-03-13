"""Models for storing Elasticsearch ACLs."""
from invenio_db import db
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy_utils import Timestamp

from invenio_acls.models_acl import ACL


class ElasticsearchACL(ACL, db.Model, Timestamp):
    """Storage for ACL Sets."""

    __tablename__ = 'invenio_acls_elasticsearchacl'

    #
    # Fields
    #

    name = db.Column(
        db.String,
        nullable=False
    )

    record_selector = db.Column(JSONB)
    """JSON field with pattern to which the ACL applies. 
        For example, {'faculty': 'FCHI'} pattern selects all resources with faculty FCHI
    """

    def __repr__(self):
        """String representation for model."""
        return '"{0.name}" ({0.id}) on ES indices {0.indices}'.format(self)

    def as_json(self):
        return {
            'id': self.id,
            'type': self.TYPE,
            'name': self.name,
            'indices': [x.elasticsearch_index for x in self.indices],
            'record_selector': self.record_selector,
            'acls': self.database_operations
        }

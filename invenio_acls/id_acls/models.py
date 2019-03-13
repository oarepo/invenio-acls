"""Models for storing Elasticsearch ACLs."""
from invenio_db import db
from invenio_records import Record
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy_utils import Timestamp

from invenio_acls.models_acl import ACL


class IdACL(ACL, db.Model, Timestamp):
    """Storage for ACL Sets."""

    __tablename__ = 'invenio_acls_idacl'

    name = db.Column(
        db.String,
        nullable=False
    )

    #
    # Fields
    #
    record_id = db.Column(UUID, nullable=False)

    @property
    def record_str(self):
        try:
            rec = Record.get_record(self.record_id)
            if 'title' in rec:
                if '_' in rec['title']:
                    return '%s: %s' % (self.record_id, rec['title']['_'])
                else:
                    return '%s: %s' % (self.record_id, rec['title'])
            else:
                return '%s: %s' % (self.record_id, repr(rec))
        except:
            pass
        return str(self)

    def __repr__(self):
        """String representation for model."""
        return 'ID ACL on {0.record_id}'.format(self)

    def as_json(self):
        return {
            'id': self.id,
            'type': self.TYPE,
            'record_id': self.record_id,
            'acls': self.database_operations
        }

from typing import List, Iterable

from invenio_records import Record

from invenio_acls.acl_handlers import ACLHandler
from invenio_acls.models_acl import ACL
from .models import IdACL


class IdAclHandler(ACLHandler):

    def handles(self, acl: ACL) ->bool:
        return isinstance(acl, IdACL)

    def get_acl(self, id: str) -> ACL or None:
        return IdACL.query.filter_by(id=id).one_or_none()

    def get_record_acls(self, record: Record) -> Iterable[ACL]:
        id_ = str(record.model.id)  # bug in sqlalchemy - can not search with UUID value, need string here
        return IdACL.query.filter_by(record_id=id_)

    def get_matching_resources(self, acl) -> Iterable[str]:
        return [acl.record_id]

    def prepare(self, index, doc_type):
        # no need to prepare any index
        pass

    def update(self, acl):
        # no need to update any index
        pass

    def delete(self, acl):
        # no need to update any index
        pass

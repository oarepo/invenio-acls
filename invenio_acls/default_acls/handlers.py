from typing import List, Iterable

from invenio_indexer import current_record_to_index
from invenio_records import Record
from invenio_search import current_search_client

from invenio_acls.acl_handlers import ACLHandler
from invenio_acls.models_acl import ACL
from .models import DefaultACL


class DefaultAclHandler(ACLHandler):

    def handles(self, acl: ACL) ->bool:
        return isinstance(acl, DefaultACL)

    def get_acl(self, id: str) -> ACL or None:
        return DefaultACL.query.filter_by(id=id).one_or_none()

    def get_record_acls(self, record: Record) -> Iterable[ACL]:
        index, _doc_type = current_record_to_index(record)
        return DefaultACL.query.filter(DefaultACL.indices.any(index)).all()

    def get_matching_resources(self, acl) -> Iterable[str]:
        for index in acl.indices:
            for r in current_search_client.search(
                index=index,
                body={
                    "query": {
                        "match_all": {}
                    }
                }
            )['hits']['hits']:
                yield r['_id']

    def prepare(self, index, doc_type):
        # no need to prepare any index
        pass

    def update(self, acl):
        # no need to update any index
        pass

    def delete(self, acl):
        # no need to update any index
        pass

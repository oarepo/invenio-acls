import datetime
import json
import logging

from flask import current_app
from invenio_search import current_search_client

from invenio_acls.acl_handlers import ACLHandlers
from invenio_acls.models_acl import ACL
from invenio_acls.tasks import record_acl_changed_reindex, record_acl_deleted_reindex

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class AclAPI:
    def __init__(self, app, handlers: ACLHandlers):
        self.app = app
        self.handlers = handlers

    def get_matching_acls(self, record):
        return self.handlers.get_record_acls(record)

    def prepare_record_acls(self, record_acls):

        timestamp = datetime.datetime.now().astimezone().isoformat()

        acl_def = []

        operations = set()
        for record_acl in record_acls:
            for acl in record_acl.database_operations:
                acl_def.append({
                    'operation': acl['operation'],
                    **acl['actors'],
                    'id': str(record_acl.id),
                    'timestamp': timestamp
                })
                operations.add(acl['operation'])

        return acl_def

    def list_doctypes(self):
        """
        Helper method to return list of indexes and doctypes from the current elasticsearch instance
        :return: list of (index, doctype)
        """
        for index in current_search_client.indices.get('*'):
            for index_data in current_search_client.indices.get_mapping(index).values():
                mappings = index_data['mappings']
                for doctype in mappings:
                    yield index, doctype

    def setup_model(self, index_name, doc_type):
        self.handlers.prepare(index_name, doc_type)

    def index_acl(self, record_acl: ACL):
        try:
            self.handlers.update(record_acl)
        except:
            # TODO: send mail to admin
            print('Error: could not update ACL index')
        if current_app.config['INVENIO_ACLS_DELAYED_REINDEX']:
            record_acl_changed_reindex.delay(str(record_acl.id))
        else:
            record_acl_changed_reindex(str(record_acl.id))

    def unindex_acl(self, record_acl: ACL):
        try:
            self.handlers.delete(record_acl)
        except:
            # TODO: send mail to admin
            print('Error: could not update ACL index')
        if current_app.config['INVENIO_ACLS_DELAYED_REINDEX']:
            record_acl_deleted_reindex.delay(record_acl.indices, str(record_acl.id))
        else:
            record_acl_deleted_reindex(record_acl.indices, str(record_acl.id))


__all__ = ('AclAPI',)

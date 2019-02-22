import datetime
import json
import os

from elasticsearch import VERSION as ES_VERSION
from invenio_db import db
from invenio_search import current_search_client, current_search

from invenio_acls.models import ACL, Index

import logging

from invenio_acls.tasks import record_acl_changed_reindex, record_acl_deleted_reindex

logger = logging.getLogger(__name__)


# noinspection PyMethodMayBeStatic
class AclAPI:
    def __init__(self, app):
        self.app = app

    @property
    def index_name(self):
        return self.app.config['INVENIO_ACLS_INDEX_NAME']

    @property
    def doctype_name(self):
        return self.app.config['INVENIO_ACLS_DOCTYPE_NAME']

    def setup_model(self, index_name, doc_type):
        extra_mapping = os.path.join(os.path.dirname(__file__), 'mappings', 'mixins',
                                     'v%s' % ES_VERSION[0], self.app.config['INVENIO_ACLS_MIXIN_NAME'] + '.json')
        with open(extra_mapping, 'r') as f:
            extra_mapping = json.load(f)

        resp = current_search_client.indices.put_mapping(index=index_name, doc_type=doc_type, body=extra_mapping)

        acl_index_name = self.get_acl_index_name(index_name)
        # create mapping for acl index

        target_mapping_resource = current_search.mappings[index_name]
        with open(target_mapping_resource) as f:
            mapping = json.load(f)

        fk = next(iter(mapping['mappings'].keys()))
        mapping['mappings'][self.doctype_name] = mapping['mappings'][fk]
        del mapping['mappings'][fk]

        mapping['mappings'][self.doctype_name]['properties'] = {
            **mapping['mappings'][self.doctype_name]['properties'],
            "__acl_record_selector": {
                "type": "percolator"
            }
        }
        try:
            current_search_client.indices.create(index=acl_index_name, body=mapping)
        except Exception as e:
            logger.error('Error in creating index for ACLs: %s', e)

        if not Index.query.filter_by(elasticsearch_index=index_name).count():
            # create record in Index table if it does not exist already
            idx = Index(elasticsearch_index=index_name)
            db.session.add(idx)
            db.session.commit()

    def get_acl_index_name(self, target_index_name):
        return f'{self.index_name}-{target_index_name}'

    def prepare_record_acls(self, record_acl_ids):

        timestamp = datetime.datetime.now().astimezone().isoformat()

        acl_def = []

        operations = set()
        for record_acl_id in record_acl_ids:
            record_acl = ACL.query.get(record_acl_id)
            for acl in record_acl.database_operations:
                acl_def.append({
                    'operation': acl['operation'],
                    **acl['actors'],
                    'id': record_acl.id,
                    'timestamp': timestamp
                })
                operations.add(acl['operation'])

        # if there is no 'GET' permission, add it for everyone
        if 'get' not in operations:
            acl_def.append({
                'operation': 'get',
                'roles': ['anonymous', 'authenticated'],
                'id': None,
                'timestamp': timestamp
            })

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

    def get_matching_acls(self, index, document):
        query = {
            "query": {
                "percolate": {
                    "field": "__acl_record_selector",
                    "document": document
                }
            }
        }

        if logger.isEnabledFor(logging.DEBUG) <= logging.DEBUG:
            logger.debug('get_material_acls: query %s', json.dumps(query, indent=4, ensure_ascii=False))
        return current_search_client.search(
            index=self.get_acl_index_name(index),
            doc_type=self.doctype_name,
            body=query
        )['hits']['hits']

    def index_acl(self, record_acl: ACL):
        body = {
            '__acl_record_selector': record_acl.record_selector,
        }
        if logger.isEnabledFor(logging.DEBUG) <= logging.DEBUG:
            logger.debug('get_material_acls: query %s', json.dumps(body, indent=4, ensure_ascii=False))
        acl_index_names = [self.get_acl_index_name(x.elasticsearch_index) for x in record_acl.indices]
        try:
            for acl_idx_name in acl_index_names:
                return current_search_client.index(
                    index=acl_idx_name,
                    doc_type=self.doctype_name,
                    id=record_acl.id,
                    body=body
                )
        finally:
            for acl_idx_name in acl_index_names:
                current_search_client.indices.flush(index=acl_idx_name)

            record_acl_changed_reindex.delay(record_acl.id)

    def unindex_acl(self, index_name, record_acl_id):
        acl_index_name = self.get_acl_index_name(index_name)
        try:
            return current_search_client.delete(
                index=acl_index_name,
                doc_type=self.doctype_name,
                id=record_acl_id
            )
        finally:
            current_search_client.indices.flush(index=acl_index_name)
            record_acl_deleted_reindex.delay(index_name, record_acl_id)


__all__ = ('AclAPI',)

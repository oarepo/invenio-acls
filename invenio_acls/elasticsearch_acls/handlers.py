import json
import logging
import os
from typing import List, Iterable

import elasticsearch.helpers
from elasticsearch import VERSION as ES_VERSION
from flask import current_app
from invenio_db import db
from invenio_indexer import current_record_to_index
from invenio_records import Record
from invenio_search import current_search_client, current_search

from invenio_acls.acl_handlers import ACLHandler
from invenio_acls.elasticsearch_acls.models import ElasticsearchACL
from invenio_acls.models_acl import ACL

logger = logging.getLogger(__name__)


class ElasticsearchAclHandler(ACLHandler):

    def handles(self, acl: ACL) ->bool:
        return isinstance(acl, ElasticsearchACL)

    def get_acl(self, id: str) -> ACL or None:
        return ElasticsearchACL.query.filter_by(id=id).one_or_none()

    def get_record_acls(self, record: Record) -> Iterable[ACL]:
        # run percolate query on the index record's index
        query = {
            "query": {
                "percolate": {
                    "field": "__acl_record_selector",
                    "document": dict(record)
                }
            }
        }

        if logger.isEnabledFor(logging.DEBUG) <= logging.DEBUG:
            logger.debug('get_material_acls: query %s', json.dumps(query, indent=4, ensure_ascii=False))

        index, _doc_type = current_record_to_index(record)

        for r in current_search_client.search(
            index=self.get_acl_index_name(index),
            doc_type=self.doctype_name,
            body=query
        )['hits']['hits']:
            yield ElasticsearchACL.query.get(r['_id'])

    def get_matching_resources(self, acl) -> Iterable[str]:
        for index in acl.indices:

            try:
                for doc in elasticsearch.helpers.scan(current_search_client,
                                                      query={"query": acl.record_selector},
                                                      index=index):
                    yield doc['_id']
            except:
                logger.exception('Error getting resources from index %s', index)

    def prepare(self, index_name, doc_type):
        extra_mapping = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'mappings', 'mixins',
                                     'v%s' % ES_VERSION[0], current_app.config['INVENIO_ACLS_MIXIN_NAME'] + '.json')
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

    @property
    def index_name(self):
        return current_app.config['INVENIO_ACLS_INDEX_NAME']

    def get_acl_index_name(self, target_index_name):
        return f'{self.index_name}-{target_index_name}'

    @property
    def doctype_name(self):
        return current_app.config['INVENIO_ACLS_DOCTYPE_NAME']

    def update(self, acl):
        body = {
            '__acl_record_selector': acl.record_selector,
        }
        if logger.isEnabledFor(logging.DEBUG) <= logging.DEBUG:
            logger.debug('get_material_acls: query %s', json.dumps(body, indent=4, ensure_ascii=False))
        acl_index_names = [self.get_acl_index_name(x) for x in acl.indices]
        try:
            for acl_idx_name in acl_index_names:
                return current_search_client.index(
                    index=acl_idx_name,
                    doc_type=self.doctype_name,
                    id=acl.id,
                    body=body
                )
        finally:
            for acl_idx_name in acl_index_names:
                current_search_client.indices.flush(index=acl_idx_name)

    def delete(self, acl):
        for index_name in acl.indices:
            acl_index_name = self.get_acl_index_name(index_name)
            try:
                return current_search_client.delete(
                    index=acl_index_name,
                    doc_type=self.doctype_name,
                    id=acl.id
                )
            finally:
                current_search_client.indices.flush(index=acl_index_name)

import datetime

import elasticsearch.helpers
from celery import shared_task
from invenio_indexer.api import RecordIndexer
from invenio_records import Record
from invenio_search import current_search_client

from invenio_acls.models import ACL

import logging

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def record_acl_changed_reindex(record_acl_id):
    """
    ACL has been changed so reindex all the documents in the given index

    :param record_acl_id:   if of the ACL instance that has been changed
    """

    logger.info('Reindexing started for ACL=%s', record_acl_id)

    record_acl = ACL.query.get(record_acl_id)
    if not record_acl:
        # deleted in the meanwhile, so return
        return

    timestamp = datetime.datetime.now().astimezone().isoformat()

    indexer = RecordIndexer()
    updated_count = 0
    removed_count = 0

    for index in record_acl.indices:
        index = index.elasticsearch_index

        try:
            for doc in elasticsearch.helpers.scan(current_search_client,
                                                  query={"query": record_acl.record_selector},
                                                  index=index):
                try:
                    indexer.index(Record.get_record(doc['_id']))
                    updated_count += 1
                except:
                    logger.exception('Error indexing resource %s', doc['_id'])
        except:
            logger.exception('Error indexing index %s', index)

        try:
            # reindex all the records with this acl that do not have timestamp
            # greater than this timestamp - that is those that have this acl but have
            # not been indexed in the previous indexing cycle
            for doc in elasticsearch.helpers.scan(current_search_client,
                                                  query={
                                                      "query": {
                                                          "nested": {
                                                              "path": "_invenio_acls",
                                                              "score_mode": "min",
                                                              "query": {
                                                                  "bool": {
                                                                      "must": [
                                                                          {"term": {"_invenio_acls.id": record_acl_id}},
                                                                          {"range": {
                                                                              "_invenio_acls.timestamp": {"lt": timestamp}}}
                                                                      ]
                                                                  }
                                                              }
                                                          }
                                                      }
                                                  },
                                                  index=index):
                try:
                    removed_count += 1
                    indexer.index(Record.get_record(doc['_id']))
                except:
                    logger.exception('Error indexing resource %s', doc['_id'])
        except:
            logger.exception('Error removing obsolete occurrences of ACL from indexing index %s', index)

    logger.info('Reindexing finished for ACL=%s, acl applied to %s records, acl removed from %s records',
                record_acl_id, updated_count, removed_count)


@shared_task(ignore_result=True)
def record_acl_deleted_reindex(index, record_acl_id):
    """
    ACL has been deleted so reindex all the documents that contain reference to it

    :param index: the index of documents
    :param record_acl_id:   if of the ACL instance that has been deleted
    """

    logger.info('Reindexing started for deleted ACL=%s', record_acl_id)

    indexer = RecordIndexer()

    try:
        for doc in elasticsearch.helpers.scan(current_search_client,
                                              query={
                                                  "query": {
                                                      "nested": {
                                                          "path": "_invenio_acls",
                                                          "query": {
                                                              "term": {"_invenio_acls.id": record_acl_id}
                                                          }
                                                      }
                                                  }
                                              },
                                              index=index):
            try:
                indexer.index(Record.get_record(doc['_id']))
            except:
                logger.exception('Error indexing resource %s', doc['_id'])
    except:
        logger.exception('Error removing ACL from index %s', index)

    logger.info('Reindexing finished for deleted ACL=%s', record_acl_id)


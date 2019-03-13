import datetime
import logging
import traceback

import elasticsearch.helpers
from celery import shared_task
from invenio_indexer.api import RecordIndexer
from invenio_records import Record
from invenio_search import current_search_client

logger = logging.getLogger(__name__)


@shared_task(ignore_result=True)
def record_acl_changed_reindex(record_acl_id):
    """
    ACL has been changed so reindex all the documents in the given index

    :param record_acl_id:   if of the ACL instance that has been changed
    """
    from invenio_acls.proxies import current_acls

    logger.info('Reindexing started for ACL=%s', record_acl_id)

    timestamp = datetime.datetime.now().astimezone().isoformat()

    record_acl = current_acls.handlers.get_acl(record_acl_id)
    if not record_acl:
        # deleted in the meanwhile, so just return
        return

    indexer = RecordIndexer()
    updated_count = 0
    removed_count = 0

    for id in current_acls.handlers.get_matching_resources(record_acl):
        print("ACL changed, indexing", id)
        try:
            rec = Record.get_record(id)
        except:
            continue
        try:
            indexer.index(rec)
            updated_count += 1
        except Exception as e:
            logger.exception('Error indexing ACL for resource %s: %s', id, e)

    for id in current_acls.handlers.get_matching_resources_from_cache(record_acl, older_than_timestamp=timestamp):
        try:
            rec = Record.get_record(id)
        except:
            continue
        try:
            removed_count += 1
            indexer.index(rec)
        except:
            logger.exception('Error indexing ACL for obsolete resource %s', id)

    logger.info('Reindexing finished for ACL=%s, acl applied to %s records, acl removed from %s records',
                record_acl_id, updated_count, removed_count)


@shared_task(ignore_result=True)
def record_acl_deleted_reindex(indices, record_acl_id):
    """
    ACL has been deleted so reindex all the documents that contain reference to it

    :param index: the index of documents
    :param record_acl_id:   if of the ACL instance that has been deleted
    """
    from invenio_acls.proxies import current_acls

    logger.info('Reindexing started for deleted ACL=%s', record_acl_id)

    indexer = RecordIndexer()

    try:
        for id in current_acls.handlers.get_matching_resources_from_cache(record_acl_id, indices=indices):
            try:
                indexer.index(Record.get_record(id))
            except:
                logger.exception('Error indexing resource %s', id)
    except:
        logger.exception('Error removing ACL from indices %s', indices)

    logger.info('Reindexing finished for deleted ACL=%s', record_acl_id)

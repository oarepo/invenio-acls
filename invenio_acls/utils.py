from functools import partial

from flask import request
from flask_login import current_user

import logging

logger = logging.getLogger(__name__)


def _check_elasticsearch(operation, record, *args, **kwargs):
    """Return permission that check if the record exists in ES index.

    :params record: A record object.
    :returns: A object instance with a ``can()`` method.
    """

    def can(self):
        """Try to search for given record."""
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('Check called, operation %s, record %s, current user %s', operation, record, current_user)
        search = request._methodview.search_class(operation=operation)
        search = search.get_record(str(record.id))
        # print(search.query.to_dict())
        resp = search.count() == 1
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug('      -> allowed', resp)
        return resp

    return type(f'CheckES-{operation}', (), {'can': can})()


check_elasticsearch_acls_get = partial(_check_elasticsearch, operation='get')
check_elasticsearch_acls_update = partial(_check_elasticsearch, operation='update')
check_elasticsearch_acls_delete = partial(_check_elasticsearch, operation='delete')

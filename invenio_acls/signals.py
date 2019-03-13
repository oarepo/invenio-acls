from invenio_indexer.signals import before_record_index

from invenio_acls.proxies import current_acls


def add_acls(app, json=None, index=None, record=None, doc_type=None, **kwargs):

    if index not in app.config.get('INVENIO_ACL_ENABLED_INDICES', []):
        return

    matching_acls = current_acls.get_matching_acls(record)
    json['_invenio_acls'] = current_acls.prepare_record_acls(matching_acls)


before_record_index.connect(add_acls)

from invenio_indexer.signals import before_record_index

from invenio_acls.proxies import acl_api


def add_acls(app, json=None, index=None, record=None, doc_type=None, **kwargs):

    if index not in app.config.get('INVENIO_ACL_ENABLED_INDICES', []):
        return

    matching_acls = acl_api.get_matching_acls(index, json)
    json['_invenio_acls'] = acl_api.prepare_record_acls([x['_id'] for x in matching_acls])


before_record_index.connect(add_acls)

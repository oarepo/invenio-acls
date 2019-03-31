from invenio_search import current_search_client
from invenio_explicit_acls.version import __version__


def test_version():
    assert __version__.startswith('1.0.')


def test_cli_prepare(app, db, es, es_acl_prepare):
    assert 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0' in current_search_client.indices.get('*')
    mapping = current_search_client.indices.get_mapping('records-record-v1.0.0')
    mapping = mapping['records-record-v1.0.0']['mappings']['record-v1.0.0']['properties']
    assert '_invenio_explicit_acls' in mapping

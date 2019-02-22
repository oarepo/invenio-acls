import json
import re
import textwrap

import click
from flask import cli

from invenio_acls.models import ACL
from invenio_acls.proxies import acl_api


@click.group()
def acls():
    """Invenio ACLs commands."""


@acls.command()
@click.argument('index')
@click.argument('doctype')
@cli.with_appcontext
def setup_model(index, doctype):
    """
        Setup record index to be used with invenio acls.

    :param index:       name of the index in elasticsearch
    """
    acl_api.setup_model(index_name=index, doc_type=doctype)


@acls.command()
@cli.with_appcontext
def list_doctypes():
    """
        List all doctypes and indices registered in elasticsearch
    """
    for index, doctype in acl_api.list_doctypes():
        print('%-40s %s' % (index, doctype))


@acls.command()
@click.argument('index', required=False)
@cli.with_appcontext
def list(index):
    """
        List all acls. If index is set than limit them to the index given
    """
    if index:
        q = ACL.query.filter_by(index=index)
    else:
        q = ACL.query.all()
    for acl in q:
        print(acl)
        print(textwrap.indent(json.dumps(acl.database_operations, indent=4, ensure_ascii=False), '    '))

@acls.command()
@click.option('--acl', default=None)
@click.option('--index', default=None)
@click.option('--document', default=None)
@cli.with_appcontext
def reindex(acl, index, document):
    if document is not None:
        resp = acl_api.reindex_document(document, acl)
    elif acl is not None:
        resp = acl_api.reindex_acl(acl)
    elif index is not None:
        resp = acl_api.reindex_index(index)
    else:
        resp = acl_api.reindex_all_indices()

    print("Return status: ")
    for k, v in resp.items():
        print(f'    RecordACL "{k[1]}" (id={k[0]}): {v["updated"]} updated documents, '
              f'{v["removed"]} documents with ACLs revoked')


__all__ = ('acls', 'setup_model', 'list_doctypes', 'reindex')

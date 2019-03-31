#
# Copyright (c) 2019 UCT Prague.
# 
# cli.py is part of Invenio Explicit ACLs 
# (see https://github.com/oarepo/invenio-explicit-acls).
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
"""Command-line client extension."""

import click
from flask import cli
from invenio_search import current_search

from invenio_explicit_acls.proxies import current_explicit_acls


@click.group(name='explicit-acls')
def explicit_acls():
    """Invenio ACLs commands."""


@explicit_acls.command()
@click.argument('schema')
@cli.with_appcontext
def prepare(schema):
    """
        Setup schema to be used with invenio explicit acls.

    :param schema:       the name of the schema that should be prepared for explicit ACLs
    """
    current_explicit_acls.prepare(schema)


@explicit_acls.command()
@cli.with_appcontext
def list_schemas():
    """List all schemas registered in invenio."""
    for schema in current_search.mappings.keys():
        print("   ", schema)

#
# TODO: to be refactored
#
# @explicit_acls.command()
# @click.argument('index', required=False)
# @cli.with_appcontext
# def list(index):
#     """
#         List all acls. If index is set than limit them to the index given
#     """
#     if index:
#         q = ACL.query.filter_by(index=index)
#     else:
#         q = ACL.query.all()
#     for acl in q:
#         print(acl)
#         print(textwrap.indent(json.dumps(acl.database_operations, indent=4, ensure_ascii=False), '    '))
#
# @explicit_acls.command()
# @click.option('--acl', default=None)
# @click.option('--index', default=None)
# @click.option('--document', default=None)
# @cli.with_appcontext
# def reindex(acl, index, document):
#     if document is not None:
#         resp = current_explicit_acls.reindex_document(document, acl)
#     elif acl is not None:
#         resp = current_explicit_acls.reindex_acl(acl)
#     elif index is not None:
#         resp = current_explicit_acls.reindex_index(index)
#     else:
#         resp = current_explicit_acls.reindex_all_indices()
#
#     print("Return status: ")
#     for k, v in resp.items():
#         print(f'    RecordACL "{k[1]}" (id={k[0]}): {v["updated"]} updated documents, '
#               f'{v["removed"]} documents with ACLs revoked')
#
#
# __all__ = ('explicit_acls', 'setup_model', 'list_doctypes', 'reindex')

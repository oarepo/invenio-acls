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
from invenio_db import db
from invenio_indexer.api import RecordIndexer
from invenio_jsonschemas import current_jsonschemas
from invenio_records.models import RecordMetadata
from invenio_search import current_search
from sqlalchemy import cast

from invenio_explicit_acls.models import ACL
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
    for schema in current_jsonschemas.list_schemas():
        print("   ", schema)


@explicit_acls.command(name='full-reindex')
@click.option('--verbose/--no-verbose', default=False)
@click.option('--records/--no-records', default=True)
@cli.with_appcontext
def full_reindex(verbose, records):
    """Updates index of all ACLs and optionally reindexes all documents"""
    # 1. for each ACL update the ACL's index etc
    if verbose:
        print('Reindexing ACLs')
    for acl in ACL.query.all():
        if verbose:
            print('Updating ACL representation for', acl)
        acl.update()
    if not records:
        return
    # 2. for each of ACL enabled indices reindex all documents
    uuids = set()
    import sqlalchemy.dialects.postgresql
    for schema in current_explicit_acls.enabled_schemas:
        if verbose:
            print('Getting records for schema', schema)
        full_schema = current_jsonschemas.path_to_url(schema)
        # filter all records with the given schema
        recs = set()
        recs.update(str(x[0]) for x in db.session.query(RecordMetadata.id).filter(
            RecordMetadata.json['$schema'] == cast(schema, sqlalchemy.dialects.postgresql.JSONB)
        ))
        recs.update(str(x[0]) for x in db.session.query(RecordMetadata.id).filter(
            RecordMetadata.json['$schema'] == cast(full_schema, sqlalchemy.dialects.postgresql.JSONB)
        ))
        if verbose:
            print('   ... collected %s records' % len(recs))
        uuids.update(recs)

    if verbose:
        print('Adding %s records to indexing queue' % len(uuids))
    RecordIndexer().bulk_index(uuids)

    if verbose:
        print('Running bulk indexer on %s records' % len(uuids))
    RecordIndexer(version_type=None).process_bulk_queue(
        es_bulk_kwargs={'raise_on_error': False})

#
# Copyright (c) 2019 UCT Prague.
# 
# test_cli.py is part of Invenio Explicit ACLs 
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
import json
import os
import tempfile

import pytest
from helpers import clear_timestamp, create_record
from invenio_indexer.api import RecordIndexer
from invenio_search import RecordsSearch, current_search_client

from invenio_explicit_acls.acls import ElasticsearchACL
from invenio_explicit_acls.actors import UserActor
from invenio_explicit_acls.proxies import current_explicit_acls
from invenio_explicit_acls.record import SchemaEnforcingRecord
from invenio_explicit_acls.utils import schema_to_index
from invenio_explicit_acls.version import __version__

RECORD_SCHEMA = 'records/record-v1.0.0.json'


def test_version():
    assert __version__.startswith('4.')


def test_prepare(app, db, es, es_acl_prepare):
    assert 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0' in current_search_client.indices.get('*')
    mapping = current_search_client.indices.get_mapping('records-record-v1.0.0')
    assert len(mapping) == 1
    key = list(mapping.keys())[0]
    mapping = mapping[key]['mappings']['record-v1.0.0']['properties']
    assert '_invenio_explicit_acls' in mapping


def test_cli_list(app, db, es, capsys):
    from invenio_explicit_acls.cli import list_schemas_impl
    list_schemas_impl()
    captured = capsys.readouterr()
    assert 'records/record-v1.0.0.json' in captured.out.strip()
    assert captured.err.strip() == ''


def test_cli_prepare(app, db, es, capsys):
    from invenio_explicit_acls.cli import prepare_impl
    prepare_impl('records/record-v1.0.0.json')
    captured = capsys.readouterr()
    assert captured.out.strip() == ''
    assert captured.err.strip() == ''
    assert 'invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0' in current_search_client.indices.get('*')
    mapping = current_search_client.indices.get_mapping('records-record-v1.0.0')
    assert len(mapping) == 1
    key = list(mapping.keys())[0]
    mapping = mapping[key]['mappings']['record-v1.0.0']['properties']
    assert '_invenio_explicit_acls' in mapping


def test_cli_full_reindex(app, db, es, capsys, es_acl_prepare, test_users):
    pid, record = create_record({'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, clz=SchemaEnforcingRecord)
    RecordIndexer().index(record)
    current_search_client.indices.flush()
    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'blah'
                               }})
        db.session.add(acl)
        u = UserActor(name='test', acl=acl, originator=test_users.u1, users=[test_users.u1])
        db.session.add(u)

    # now the record is not indexed and ACL is not in the helper index, check it ...
    retrieved = RecordsSearch(index=schema_to_index(RECORD_SCHEMA)[0]).get_record(record.id).execute().hits[0].to_dict()
    assert '_invenio_explicit_acls' not in retrieved

    # just a precaution test
    assert current_explicit_acls.enabled_schemas == {RECORD_SCHEMA}

    # and run the reindex - should reindex one record
    from invenio_explicit_acls.cli import full_reindex_impl
    full_reindex_impl(verbose=True, records=True, in_bulk=False)

    captured = capsys.readouterr()
    assert captured.out.strip() == """
Reindexing ACLs
Updating ACL representation for "test" (%s) on schemas ['records/record-v1.0.0.json']
Getting records for schema records/record-v1.0.0.json
   ... collected 1 records
Adding 1 records to indexing queue""".strip() % (acl.id)

    current_search_client.indices.flush()

    retrieved = RecordsSearch(index=schema_to_index(RECORD_SCHEMA)[0]).get_record(record.id).execute().hits[0].to_dict()
    assert clear_timestamp(retrieved['_invenio_explicit_acls']) == [{'id': str(acl.id),
                                                                     'operation': 'get',
                                                                     'timestamp': 'cleared',
                                                                     'user': [1]}]


def normalize(x):
    ret = [line.strip() for line in x.split('\n')]
    ret = [line for line in ret if '"timestamp"' not in line]
    ret = [line for line in ret if 'id =' not in line]
    ret = [line for line in ret if 'created =' not in line]
    ret = [line for line in ret if 'updated =' not in line]
    ret = [x for x in ret if x]
    return '\n'.join(ret)


def check_explain(capsys, recdata, expected):
    fd, name = tempfile.mkstemp('.json')
    with open(name, 'a') as f:
        json.dump(recdata, f)

    from invenio_explicit_acls.cli import explain_impl
    explain_impl(name, debug=True)

    captured = capsys.readouterr()
    assert normalize(captured.out.strip()) == normalize(expected)
    os.close(fd)
    os.unlink(name)


def test_cli_explain(app, db, es, capsys, es_acl_prepare, test_users):
    check_explain(capsys, {'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, """
Possible ACLs
Checking ACLs of type <class 'invenio_explicit_acls.acls.default_acls.DefaultACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.elasticsearch_acls.ElasticsearchACL'>
Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
{
"query": {
"bool": {
"must": [
{
"percolate": {
"field": "__acl_record_selector",
"document": {
"$schema": "records/record-v1.0.0.json",
"keywords": [
"blah"
]
}
}
},
{
"term": {
"__acl_record_type": "elasticsearch"
}
}
]
}
}
}
Checking ACLs of type <class 'invenio_explicit_acls.acls.id_acls.IdACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.propertyvalue_acls.PropertyValueACL'>
Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
{
"query": {
"bool": {
"must": [
{
"percolate": {
"field": "__acl_record_selector",
"document": {
"$schema": "records/record-v1.0.0.json",
"keywords": [
"blah"
]
}
}
},
{
"term": {
"__acl_record_type": "propertyvalue"
}
}
]
}
}
}
The record is not matched by any ACLs
    """)

    with db.session.begin_nested():
        acl = ElasticsearchACL(name='test', schemas=[RECORD_SCHEMA],
                               priority=0, operation='get', originator=test_users.u1,
                               record_selector={'term': {
                                   'keywords': 'blah'
                               }})
        db.session.add(acl)
        u = UserActor(name='test', acl=acl, originator=test_users.u1, users=[test_users.u1])
        db.session.add(u)
    acl.update()

    current_search_client.indices.flush()

    check_explain(capsys, {}, """Please add $schema to record metadata""")
    check_explain(capsys, {'$schema': RECORD_SCHEMA, 'keywords': ['blah']}, """
Possible ACLs
ElasticsearchACL "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json']
actors = ['UserActor[test]']
created = 2019-05-10 11:27:26.013084
id = ebb91d27-70fd-4077-b6e1-6aadd7fa0bcd
name = test
operation = get
originator = User <id=1, email=1@test.com>
originator_id = 1
priority_group = default
record_selector = {'term': {'keywords': 'blah'}}
schemas = ['records/record-v1.0.0.json']
type = elasticsearch
updated = 2019-05-10 11:27:26.013093

Checking ACLs of type <class 'invenio_explicit_acls.acls.default_acls.DefaultACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.elasticsearch_acls.ElasticsearchACL'>
   Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
        {
            "query": {
                "bool": {
                    "must": [
                        {
                            "percolate": {
                                "field": "__acl_record_selector",
                                "document": {
                                    "$schema": "records/record-v1.0.0.json",
                                    "keywords": [
                                        "blah"
                                    ]
                                }
                            }
                        },
                        {
                            "term": {
                                "__acl_record_type": "elasticsearch"
                            }
                        }
                    ]
                }
            }
        }
    found match: "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json'] with priority of 0
         UserActor[test]
Checking ACLs of type <class 'invenio_explicit_acls.acls.id_acls.IdACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.propertyvalue_acls.PropertyValueACL'>
   Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
        {
            "query": {
                "bool": {
                    "must": [
                        {
                            "percolate": {
                                "field": "__acl_record_selector",
                                "document": {
                                    "$schema": "records/record-v1.0.0.json",
                                    "keywords": [
                                        "blah"
                                    ]
                                }
                            }
                        },
                        {
                            "term": {
                                "__acl_record_type": "propertyvalue"
                            }
                        }
                    ]
                }
            }
        }

Of these, the following ACLs will be used (have the highest priority):
     "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json']
         UserActor[test]

The ACLs will get serialized to the following element
{
    "_invenio_explicit_acls": [
        {
            "operation": "get",
            "id": "%(acl_id)s",
            "timestamp": "2019-05-10T10:24:21.812875+00:00",
            "user": [
                1
            ]
        }
    ]
}
""".strip() % {'acl_id': str(acl.id)})

    check_explain(capsys, {'$schema': 'https://localhost/schemas/' + RECORD_SCHEMA, 'keywords': ['blah']}, """
Possible ACLs
ElasticsearchACL "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json']
actors = ['UserActor[test]']
created = 2019-05-10 11:27:26.013084
id = ebb91d27-70fd-4077-b6e1-6aadd7fa0bcd
name = test
operation = get
originator = User <id=1, email=1@test.com>
originator_id = 1
priority_group = default
record_selector = {'term': {'keywords': 'blah'}}
schemas = ['records/record-v1.0.0.json']
type = elasticsearch
updated = 2019-05-10 11:27:26.013093

Checking ACLs of type <class 'invenio_explicit_acls.acls.default_acls.DefaultACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.elasticsearch_acls.ElasticsearchACL'>
   Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
        {
            "query": {
                "bool": {
                    "must": [
                        {
                            "percolate": {
                                "field": "__acl_record_selector",
                                "document": {
                                    "$schema": "https://localhost/schemas/records/record-v1.0.0.json",
                                    "keywords": [
                                        "blah"
                                    ]
                                }
                            }
                        },
                        {
                            "term": {
                                "__acl_record_type": "elasticsearch"
                            }
                        }
                    ]
                }
            }
        }
    found match: "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json'] with priority of 0
         UserActor[test]
Checking ACLs of type <class 'invenio_explicit_acls.acls.id_acls.IdACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.propertyvalue_acls.PropertyValueACL'>
   Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
        {
            "query": {
                "bool": {
                    "must": [
                        {
                            "percolate": {
                                "field": "__acl_record_selector",
                                "document": {
                                    "$schema": "https://localhost/schemas/records/record-v1.0.0.json",
                                    "keywords": [
                                        "blah"
                                    ]
                                }
                            }
                        },
                        {
                            "term": {
                                "__acl_record_type": "propertyvalue"
                            }
                        }
                    ]
                }
            }
        }

Of these, the following ACLs will be used (have the highest priority):
     "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json']
         UserActor[test]

The ACLs will get serialized to the following element
{
    "_invenio_explicit_acls": [
        {
            "operation": "get",
            "id": "%(acl_id)s",
            "timestamp": "2019-05-10T10:24:21.812875+00:00",
            "user": [
                1
            ]
        }
    ]
}
""".strip() % {'acl_id': str(acl.id)})


    check_explain(capsys, {'$schema': RECORD_SCHEMA, 'keywords': ['aaa']}, """
Possible ACLs
ElasticsearchACL "test" (%(acl_id)s) on schemas ['records/record-v1.0.0.json']
actors = ['UserActor[test]']
name = test
operation = get
originator = User <id=1, email=1@test.com>
priority_group = default
record_selector = {'term': {'keywords': 'blah'}}
schemas = ['records/record-v1.0.0.json']
type = elasticsearch
Checking ACLs of type <class 'invenio_explicit_acls.acls.default_acls.DefaultACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.elasticsearch_acls.ElasticsearchACL'>
Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
{
"query": {
"bool": {
"must": [
{
"percolate": {
"field": "__acl_record_selector",
"document": {
"$schema": "records/record-v1.0.0.json",
"keywords": [
"aaa"
]
}
}
},
{
"term": {
"__acl_record_type": "elasticsearch"
}
}
]
}
}
}
Checking ACLs of type <class 'invenio_explicit_acls.acls.id_acls.IdACL'>
Checking ACLs of type <class 'invenio_explicit_acls.acls.propertyvalue_acls.PropertyValueACL'>
Will run percolate query on index invenio_explicit_acls-acl-v1.0.0-records-record-v1.0.0 and doc_type _doc:
{
"query": {
"bool": {
"must": [
{
"percolate": {
"field": "__acl_record_selector",
"document": {
"$schema": "records/record-v1.0.0.json",
"keywords": [
"aaa"
]
}
}
},
{
"term": {
"__acl_record_type": "propertyvalue"
}
}
]
}
}
}
The record is not matched by any ACLs

""" % {'acl_id': str(acl.id)})

    with pytest.raises(RuntimeError, match='Explicit ACLs were not prepared for the given schema. Please run invenio explicit-acls prepare http://bla'):
        check_explain(capsys, {'$schema': 'http://blah', 'keywords': ['aaa']}, """""")

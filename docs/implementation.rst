==============
Implementation
==============

This section summarizes how the ACLs are implemented.

--------------------
prepare index script
--------------------

When the following script is run:

.. code-block:: bash

    # run in bash
    invenio explicit-acls prepare <schema-url>

the following steps will take place:

Adding Property to Existing Index Mapping
-----------------------------------------

The mapping for elasticsearch index corresponding to the schema-url
(retrieved from `invenio_search.utils.schema_to_index` call) is enhanced
with an extra property `_invenio_explicit_acls` (called ACL field in this text).
The definition of the mapping for the ACL field looks like this:

.. code-block:: javascript

    {
        _invenio_explicit_acls: {
            type: "nested",
            properties: {
                id: {
                    type: "keyword"
                },
                operation: {
                    type: "keyword"
                },
                role: {
                    type: "integer"
                },
                system_role: {
                    type: "keyword"
                },
                timestamp: {
                    type: "date"
                },
                user: {
                    type: "integer"
                }
            }
        }
    }

During indexing the library at first gets a set of ACLs that match the record
being indexed. Each matching ACL is serialized into the ACL field as follows:

       +-----------------------+--------------------------------------------------+
       | id                    | The database id of the ACL rule                  |
       +-----------------------+--------------------------------------------------+
       | operation             | The operation (get, update, delete or custom     |
       +-----------------------+--------------------------------------------------+
       | timestamp             | The current server timestamp                     |
       +-----------------------+--------------------------------------------------+

The rest of the sub-properties (role, system_role, user) are coming from Actor instances
and define which role, system_role or user have access to the resource's operation. If a
custom Actor is implemented, other sub-properties will be present in the ACL field as well.

An example of ACL field as found in a document in the index:

.. code-block:: javascript

    {
        _invenio_explicit_acls: [
            {
                "id": 1,
                "operation": "update",
                "timestamp": "2019-01-01T00:00:00Z",
                "user": [1, 2]
            },
            {
                "id": 2,
                "operation": "get",
                "timestamp": "2019-01-01T00:00:00Z",
                "system_role": "any_user"
            }

    }

Only users with ids 1 or 2 (= id of the User model) will be able to update this document
and everyone will be able to read it.

During get/search (performed by `invenio_explicit_acls.acl_records_search.ACLRecordsSearch`)
the search query is wrapped with the following query (simplified, the real bool query contains operation checks
and role as well) so that the search returns only the resources to which the user has access
(under the operation being checked - get, update, delete or any custom operation):

.. code-block:: javascript

    {
        "must": [
            original_query,
            "bool": {
                "should": [
                    {
                         "nested" : {
                            "path" : "_invenio_explicit_acls",
                            "query" : {
                                "term": { "_invenio_explicit_acls.user": current_user_id }
                            }
                         }
                    },
                    {
                         "nested" : {
                            "path" : "_invenio_explicit_acls",
                            "query" : {
                                "term": { "_invenio_explicit_acls.system_role": "any_user" }
                            }
                         }
                    },
                ],
                "min_should_match": 1
            }
        ]
    }



Creating a new index for percolate queries
------------------------------------------

The second half of the story is that given a record we need to get the set of ACLs
that describe the record. It is easy for the simple ones:

  1. DefaultACL - maps to every record with a given `$schema` property
  2. IdACL - maps to just one record whose Invenio uuid is stored in the ACL

The more usable ACLs need more handling:

  3. PropertyValueACL defines a set of properties, their values and matching operation
     in elasticsearch (term, match) and a combining operation (must, should, must not).
     If the condition holds against a given record, the ACL matches
  4. ElasticsearchACL allows to specify a generic ES query that is run against the record.

To efficiently match record against these types of ACL we define a new index,
called for example `invenio_explicit_acls-acl-v1.0.0-theses-thesis-v1.0.0` with the following
mapping:

.. code-block:: javascript

    {
        $schema: {
            type: "keyword",
            index: false
        },
        __acl_record_selector: {
            type: "percolator"
        },
        __acl_record_type: {
            type: "keyword"
        },
        // the rest of the mapping from theses-thesis-v1.0.0
    }

Whenever an ES-backed ACL is defined to operate on thesis record type, its query is stored
to the `__acl_record_selector` property.

Later on, when we search which ACLs describe a record we perform a percolate query
against this index that efficiently evaluates all the `__acl_record_selector` and
returns those ACLs that match the record.

-------------------
The role of $schema
-------------------

The percolate index above needs to be defined for every data model as it has to contain
the properties from the data model. To know which percolate index to use we need to know
the type of the record being indexed and the only reliable record property we can use is
its schema stored in the `$schema` property.

To make sure that the ACLs are not circumvented we need to make sure that once the schema
is set it can not be removed or modified. This logic is contained in
`invenio_explicit_acls.record.SchemaKeepingRecordMixin` and
`invenio_explicit_acls.record.SchemaEnforcingRecord` that make sure that:

   1. If `$schema` is not set, it will be set with a default value, defined by
      `self.PREFERRED_SCHEMA` class property
   2. If `$schema` is set, it will not be removed
      (with `clear()`, `update()`, `record['$schema']='...'` or `del record['$schema']`)
   3. If `$schema` is changed, it might get changed only to a set of predefined values,
      defined by `self.ALLOWED_SCHEMAS` property

Any other modifications to `$schema` will raise an `AttributeError`.

To be double protected on the REST level, extend your metadata marshmallow with
`invenio_explicit_acls.marshmallow.SchemaEnforcingMixin` that performs the same checks
as above before the record is converted to its internal form.

----------
ACL update
----------

Whenever ACL is updated, we need to modify the ACL field of records in the target index.
Unfortunately this can not be done effectively with ES update-by-query call as Invenio
depends on external versioning in Elasticsearch that would get broken by update-by-query.
That's why the following code gets called (defined in `invenio_explicit_acls.tasks`):

.. code-block:: python

    @shared_task(ignore_result=True)
    def acl_changed_reindex(acl_id):
        """
        ACL has been changed so reindex all the documents in the given index.

        :param acl_id:   id of ACL instance
        """
        logger.info('Reindexing started for ACL=%s', acl_id)


At first we remember the current time. It will be used later to handle records
that are no longer covered by the ACL. We also flush the index to get the following
queries up to date:


.. code-block:: python

        timestamp = datetime.datetime.now().astimezone().isoformat()

        acl = ACL.query.filter_by(id=acl_id).one_or_none()

        if not acl:
            # deleted in the meanwhile, so just return
            return          # pragma no cover

        # make sure all indices are flushed so that no resource is obsolete in index
        for schema in acl.schemas:
            current_search_client.indices.flush(index=schema_to_index(schema)[0])

        indexer = RecordIndexer()
        updated_count = 0
        removed_count = 0


For each of the matching records we reindex them. This will propagate the changes
made to the ACL and will also update the `timestamp` property on ACL field.

.. code-block:: python


        for id in acl.get_matching_resources():
            try:
                rec = Record.get_record(id)
            except:     # pragma no cover
                # record removed in the meanwhile by another thread/process,
                # indexer should have been called to remove it from ES
                # won't test this so pragma no cover
                continue
            try:
                indexer.index(rec)
                updated_count += 1
            except Exception as e:  # pragma no cover
                logger.exception('Error indexing ACL for resource %s: %s', id, e)

Finally we select all the records that were covered by the ACL and whose `timestamp`
property is older than the time of the beginning of the indexing. This will reindex
records that will no longer be covered by the ACL:

.. code-block:: python

        # reindex the resources those were indexed by this acl but no longer should be
        for id in acl.used_in_records(older_than_timestamp=timestamp):
            try:
                rec = Record.get_record(id)
            except NoResultFound:                           # pragma no cover
                continue
            except:                                         # pragma no cover
                logger.exception('Unexpected exception in record reindexing')
                continue

            try:
                removed_count += 1
                indexer.index(rec)
            except:     # pragma no cover
                logger.exception('Error indexing ACL for obsolete resource %s', id)

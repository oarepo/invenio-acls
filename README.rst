..
    Copyright (C) 2019 CIS UCT Prague.

    CIS theses repository is free software; you can redistribute it and/or modify it
    under the terms of the MIT License; see LICENSE file for more details.

============================================================
 ACLs for OARepo Invenio
============================================================

.. image:: https://img.shields.io/github/license/cis/invenio-acls.svg
        :target: https://github.com/cis/invenio-acls/blob/master/LICENSE

.. image:: https://img.shields.io/travis/cis/invenio-acls.svg
        :target: https://travis-ci.org/cis/invenio-acls

.. image:: https://img.shields.io/coveralls/cis/invenio-acls.svg
        :target: https://coveralls.io/r/cis/invenio-acls

.. image:: https://img.shields.io/pypi/v/invenio-acls.svg
        :target: https://pypi.org/pypi/invenio-acls

A package that adds support for elasticsearch-executed ACLs

Further documentation is available on
https://invenio-acls.readthedocs.io/

==========================================================

Installation
------------


.. code-block:: bash

    pip install invenio-acls

Setup
-----

For each data model that should be guarded by ACLs, execute the following code in terminal:

.. code-block:: bash

    invenio invenio-acls setup-model <elasticsearch_index_name> <doctype_name>

To get a list of all indices & document types, execute:

.. code-block:: bash

    invenio invenio-acls list-doctypes

Add the index name to a list of acl-enabled indices:

.. code-block:: python

    invenio_ACL_ENABLED_INDICES = [ '<elasticsearch_index_name>' ]


Create ACLs
-----------

For low-level access you can use administration console to create ACLs.
The ACL consists of two parts:


* description of the resources to which the ACL applies (RecordACL)
* description of actors and allowed operations (ACL)

The `RecordACL` has the following fields:

    Name
        human name of the ACL
    Index
        elasticsearch index on which the ACL is applied
    Record Selector
        the selector of resources that this ACL applies to.
        For example ``{"match_all": {}}`` to match all documents in the index

The `associated actors and operations` are in the following form:

    Operation
        get, update or delete
    Actors
        actors to which the ACL maps to. It is a json file

Giving access to a direct set of users:

.. code-block:: json

    {
        "users": [1,3,4],
    }

Giving access to users in invenio role:

.. code-block:: json

    {
        "roles": [2]
    }

Giving access to users having a parametrized role (PRBAC):

.. code-block:: json

    {
        "prbac": "http://vscht.cz/roles/administrator",
        "prbac_params": [
            {
                "name": "department",
                "value": "997"
            }
        ]
    }


Apply ACLs to existing resources
--------------------------------

List ACLs

.. code-block:: bash

    invenio invenio-acls list


Reindex a single ACL

.. code-block:: bash

    invenio invenio-acls reindex --acl=<acl_id>


Reindex documents in a single ES index

.. code-block:: bash

    invenio invenio-acls reindex --index=<index_name>


Reindex all documents

.. code-block:: bash

    invenio invenio-acls reindex


Reindex a single document

.. code-block:: bash

    invenio invenio-acls reindex --document=<document_id>

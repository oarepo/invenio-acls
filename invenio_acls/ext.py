# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CIS UCT Prague.
#
# CIS theses repository is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Flask extension for CIS theses repository."""

from __future__ import absolute_import, print_function

# noinspection PyUnresolvedReferences
import invenio_acls.signals
from invenio_acls.acl_handlers import ACLHandlers
from invenio_acls.api import AclAPI


class InvenioAcls(object):
    """ACLs for invenio extension."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions['invenio-acls'] = AclAPI(app, ACLHandlers())

    def init_config(self, app):
        """
            Initialize configuration.
        """
        app.config['INVENIO_ACLS_INDEX_NAME'] = 'invenio_acls-acl-v1.0.0'
        app.config['INVENIO_ACLS_DOCTYPE_NAME'] = 'acl-v1.0.0'
        app.config['INVENIO_ACLS_MIXIN_NAME'] = 'invenio-acl-mixin-v1.0.0'
        app.config['INVENIO_ACLS_DELAYED_REINDEX'] = False

#
# Copyright (c) 2019 UCT Prague.
#
# conftest.py is part of Invenio Explicit ACLs
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

"""Pytest configuration."""

from __future__ import absolute_import, print_function

import copy
import os
import shutil
import sys
import tempfile
import traceback
from collections import namedtuple

import pytest
from elasticsearch.exceptions import RequestError
from flask import Flask, current_app, make_response, url_for
from flask_login import LoginManager, current_user, login_user
from flask_principal import Identity, Principal, identity_changed
from helpers import set_identity
from invenio_access import InvenioAccess
from invenio_accounts.models import Role, User
from invenio_db import InvenioDB
from invenio_db import db as db_
from invenio_indexer import InvenioIndexer
from invenio_jsonschemas import InvenioJSONSchemas
from invenio_pidstore import InvenioPIDStore
from invenio_records import InvenioRecords
from invenio_records_rest import InvenioRecordsREST
from invenio_records_rest.utils import PIDConverter
from invenio_records_rest.views import create_blueprint_from_app
from invenio_rest import InvenioREST
from invenio_search import InvenioSearch, current_search, current_search_client
from sqlalchemy_utils.functions import create_database, database_exists

from invenio_explicit_acls.acl_records_search import ACLRecordsSearch
from invenio_explicit_acls.ext import InvenioExplicitAcls
from invenio_explicit_acls.record import SchemaEnforcingRecord

sys.path.insert(0, os.path.dirname(__file__))


class TestSearch(ACLRecordsSearch):
    """Test record search."""

    class Meta:
        """Test configuration."""

        index = 'records'
        doc_types = None

    def __init__(self, **kwargs):
        """Add extra options."""
        super(TestSearch, self).__init__(**kwargs)
        self._extra.update(**{'_source': {'excludes': ['_access']}})


@pytest.yield_fixture(scope='session')
def search_class():
    """Search class."""
    yield TestSearch


@pytest.yield_fixture()
def search_url():
    """Search class."""
    yield url_for('invenio_records_rest.recid_list')


def user_id_1_perm(record, *args, **kwargs):
    """Allow user with id 1."""
    def can(self):
        """Try to search for given record."""
        return current_user.is_authenticated and current_user.id == 1

    return type('User1Perm', (), {'can': can})()


@pytest.yield_fixture(scope="function")
def app(request, search_class):
    """Flask application fixture.

    Note that RECORDS_REST_ENDPOINTS is used during application creation to
    create blueprints on the fly, hence once you have this fixture in a test,
    it's too late to customize the configuration variable. You can however
    customize it using parameterized tests:
    .. code-block:: python
    @pytest.mark.parametrize('app', [dict(
        endpoint=dict(
            search_class='conftest:TestSearch',
        )
    def test_mytest(app, db, es):
        # ...
    This will parameterize the default 'recid' endpoint in
    RECORDS_REST_ENDPOINTS.
    Alternatively:
    .. code-block:: python
    @pytest.mark.parametrize('app', [dict(
        records_rest_endpoints=dict(
            recid=dict(
                search_class='conftest:TestSearch',
            )
        )
    def test_mytest(app, db, es):
        # ...
    This will fully parameterize RECORDS_REST_ENDPOINTS.
    """
    instance_path = tempfile.mkdtemp()
    app = Flask('testapp', instance_path=instance_path)
    from records import config

    es_hosts = [
        {
            'host': 'localhost',
            'port': int(os.environ.get('ES_PORT', 9200))
        }
    ]

    app.config.update(
        ACCOUNTS_JWT_ENABLE=False,
        INDEXER_DEFAULT_DOC_TYPE='record-v1.0.0',
        INDEXER_DEFAULT_INDEX=search_class.Meta.index,
        RECORDS_REST_ENDPOINTS=copy.deepcopy(config.RECORDS_REST_ENDPOINTS),
        RECORDS_REST_DEFAULT_CREATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_DELETE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_READ_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_UPDATE_PERMISSION_FACTORY=None,
        RECORDS_REST_DEFAULT_SEARCH_INDEX=search_class.Meta.index,
        SEARCH_ELASTIC_HOSTS=es_hosts,
        SERVER_NAME='localhost:5000',
        CELERY_ALWAYS_EAGER=True,
        CELERY_RESULT_BACKEND='cache',
        CELERY_CACHE_BACKEND='memory',
        CELERY_EAGER_PROPAGATES_EXCEPTIONS=True,
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            'SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db'
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=True,
        TESTING=True,
    )
    app.config['RECORDS_REST_ENDPOINTS']['recid']['search_class'] = \
        search_class

    app.config['RECORDS_REST_ENDPOINTS']['recid']['create_permission_factory_imp'] = \
        user_id_1_perm

    app.config['RECORDS_REST_ENDPOINTS']['recid']['record_class'] = \
        SchemaEnforcingRecord

    app.secret_key = 'changeme'

    # Parameterize application.
    if hasattr(request, 'param'):
        if 'endpoint' in request.param:
            app.config['RECORDS_REST_ENDPOINTS']['recid'].update(
                request.param['endpoint'])
        if 'records_rest_endpoints' in request.param:
            original_endpoint = app.config['RECORDS_REST_ENDPOINTS']['recid']
            del app.config['RECORDS_REST_ENDPOINTS']['recid']
            for new_endpoint_prefix, new_endpoint_value in \
                request.param['records_rest_endpoints'].items():
                new_endpoint = dict(original_endpoint)
                new_endpoint.update(new_endpoint_value)
                app.config['RECORDS_REST_ENDPOINTS'][new_endpoint_prefix] = \
                    new_endpoint

    app.url_map.converters['pid'] = PIDConverter

    InvenioDB(app)
    InvenioREST(app)
    InvenioRecords(app)
    schemas = InvenioJSONSchemas(app)
    indexer = InvenioIndexer(app)
    InvenioPIDStore(app)
    search = InvenioSearch(app)
    search.register_mappings(search_class.Meta.index, 'records.mappings')
    schemas._state.register_schemas_dir(os.path.join(os.path.dirname(__file__), 'records', 'jsonschemas'))
    InvenioRecordsREST(app)
    InvenioAccess(app)
    explicit_acls = InvenioExplicitAcls(app)
    principal = Principal(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def basic_user_loader(user_id):
        user_obj = User.query.get(int(user_id))
        return user_obj

    app.register_blueprint(create_blueprint_from_app(app))

    @app.route('/test/login/<int:id>', methods=['GET', 'POST'])
    def test_login(id):
        print("test: logging user with id", id)
        response = make_response()
        user = User.query.get(id)
        login_user(user)
        set_identity(user)
        return response

    with app.app_context():
        yield app

    # Teardown instance path.
    shutil.rmtree(instance_path)


@pytest.yield_fixture()
def db(app):
    """Database fixture."""
    if not database_exists(str(db_.engine.url)) and \
        app.config['SQLALCHEMY_DATABASE_URI'] != 'sqlite://':
        create_database(db_.engine.url)
    db_.create_all()

    yield db_

    db_.session.remove()
    db_.drop_all()


@pytest.yield_fixture()
def es(app):
    """Elasticsearch fixture."""
    # remove all indices and data to get to a well-defined state
    current_search_client.indices.refresh()
    current_search_client.indices.flush()
    for idx in current_search_client.indices.get('*'):
        try:
            print("Removing index", idx)
            current_search_client.indices.delete(idx)
        except:
            traceback.print_exc()
            pass
    current_search_client.indices.refresh()
    current_search_client.indices.flush()
    # just to make sure no index is left untouched
    for idx in current_search_client.indices.get('*'):
        try:
            print("Warning: leftover index", idx)
            current_search_client.indices.delete(idx)
        except:
            traceback.print_exc()
            pass
    try:
        list(current_search.create())
    except RequestError:
        list(current_search.delete(ignore=[404]))
        list(current_search.create(ignore=[400]))
    current_search_client.indices.refresh()
    yield current_search_client
    list(current_search.delete(ignore=[404]))


@pytest.yield_fixture()
def es_acl_prepare(app, es, db):
    """Prepares ACL index for records/record."""
    from invenio_explicit_acls.proxies import current_explicit_acls
    current_explicit_acls.prepare('records/record-v1.0.0.json')
    yield current_explicit_acls


TestUsers = namedtuple('TestUsers', ['u1', 'u2', 'u3', 'r1', 'r2'])


@pytest.fixture()
def test_users(app, db):
    """Returns named tuple (u1, u2, u3, r1, r2)."""
    with db.session.begin_nested():
        r1 = Role(name='role1')
        r2 = Role(name='role2')

        u1 = User(id=1, email='1@test.com', active=True, roles=[r1])
        u2 = User(id=2, email='2@test.com', active=True, roles=[r1, r2])
        u3 = User(id=3, email='3@test.com', active=True, roles=[r2])

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)

        db.session.add(r1)
        db.session.add(r2)

    return TestUsers(u1, u2, u3, r1, r2)

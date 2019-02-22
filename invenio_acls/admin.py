from __future__ import absolute_import, print_function

import json

import jsonschema
from elasticsearch import NotFoundError
from flask_admin.contrib.sqla import ModelView
from flask_admin.model import InlineFormAdmin
from flask_wtf import FlaskForm
from invenio_jsonschemas import current_jsonschemas
from invenio_search import current_search_client
from markupsafe import Markup
from wtforms.validators import StopValidation

from invenio_acls.proxies import acl_api
from .models import ACL, Index


def link(text, link_func):
    """Generate a object formatter for links.."""

    def object_formatter(v, c, m, p):
        """Format object view link."""
        return Markup('<a href="{0}">{1}</a>'.format(
            link_func(m), text))

    return object_formatter


def _(x):
    """Identity function for string extraction."""
    return x


class ACLModelView(ModelView):
    """ModelView for the locations."""

    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True
    column_formatters = dict(
    )
    column_details_list = (
        'id', 'name', 'record_selector', 'created', 'updated', 'database_operations')
    column_list = ('id', 'name', 'indices', 'record_selector', 'created', 'updated')
    column_labels = dict(
        id=_('ID'),
        database_operations=_('Operations')
    )
    column_filters = ('created', 'updated',)
    column_searchable_list = ('name', )
    column_default_sort = 'name'
    form_base_class = FlaskForm
    form_columns = ('name', 'indices', 'record_selector', 'database_operations')
    form_args = dict(
    )
    page_size = 25
    # inline_models = (Index,)

    def after_model_change(self, form, model, is_created):
        acl_api.index_acl(model)

    def after_model_delete(self, model):
        for index in model.indices:
            acl_api.unindex_acl(index.elasticsearch_index, model.id)

    def validate_form(self, form):
        if not super().validate_form(form):
            return False

        errors = False
        for fld in form._fields:
            method = getattr(self, f'validate_{fld}', None)
            if not method:
                continue
            try:
                method(form, getattr(form, fld))
            except StopValidation as e:
                getattr(form, fld).errors.append(str(e))
                errors = True

        return not errors

    def validate_index(self, form, field):
        index_name = field.data
        try:
            current_search_client.search(
                index=index_name, size=0,
                body={
                    'query': {
                        'match_all': {}
                    }
                }
            )
        except NotFoundError as e:
            indices = list(current_search_client.indices.get('*'))
            raise StopValidation("Index not found. Known indices: " + ', '.join(indices))

    def validate_database_operations(self, form, field):
        json_data = field.data
        # print(json_data, type(json_data))
        # load the json schema
        acl_schema = current_jsonschemas.get_schema('invenio-acls/acl-v1.0.0.json')
        acl_schema = {
            **acl_schema['definitions']['ACLOperations'],
            'definitions': acl_schema['definitions']
        }
        print(json.dumps(acl_schema, indent=4))
        try:
            jsonschema.validate(json_data, acl_schema)
        except Exception as e:
            raise StopValidation(str(e))

    def validate_record_selector(self, form, field):
        """Checks that the record selector is valid and we can use it to perform query in elasticsearch index"""
        indices = form.indices.data
        record_selector = field.data
        try:
            for index in indices:
                current_search_client.search(
                    index=index.elasticsearch_index, size=0, body={
                        'query': record_selector
                    }
                )
        except Exception as e:
            raise StopValidation(str(e))


aclset_adminview = dict(
    modelview=ACLModelView,
    model=ACL,
    category=_('ACLs'))

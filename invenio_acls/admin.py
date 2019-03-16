from __future__ import absolute_import, print_function

import json
import traceback
from html import escape

import jsonschema
from elasticsearch import NotFoundError
from flask import url_for
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask_wtf import FlaskForm
from invenio_indexer import current_record_to_index
from invenio_jsonschemas import current_jsonschemas
from invenio_records import Record
from invenio_search import current_search_client
from markupsafe import Markup
from wtforms import TextField, StringField, fields
from wtforms.validators import StopValidation

from invenio_acls.default_acls import DefaultACL
from invenio_acls.elasticsearch_acls.models import ElasticsearchACL
from invenio_acls.id_acls.models import IdACL
from invenio_acls.proxies import current_acls


class StringArrayField(fields.StringField):

    def _value(self):
        if isinstance(self.data, (list, tuple)):
            return u' '.join(v for v in self.data)
        elif self.data:
            return self.data
        else:
            return u''

    def process_formdata(self, valuelist):
        if valuelist:
            self.data = [v.strip() for v in valuelist[0].split(' ') if v.strip()]
        else:
            self.data = []


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


class ACLModelViewMixin(object):
    can_create = True
    can_edit = True
    can_delete = True
    can_view_details = True

    def after_model_change(self, form, model, is_created):
        try:
            current_acls.index_acl(model)
        except:
            traceback.print_exc()

    def after_model_delete(self, model):
        current_acls.unindex_acl(model)

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

    def validate_indices(self, form, field):
        for index_name in field.data:
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
        try:
            jsonschema.validate(json_data, acl_schema)
        except Exception as e:
            raise StopValidation(str(e))

    def on_model_change(self, form, model, is_created):
        print("model changed, adding originator", form, model, is_created)
        model.originator = current_user


class ElasticsearchACLModelView(ACLModelViewMixin, ModelView):
    """ModelView for the locations."""

    column_formatters = dict(
    )
    column_details_list = (
        'id', 'name', 'record_selector', 'created', 'updated', 'originator', 'database_operations', 'priority')
    column_list = ('id', 'name', 'indices', 'record_selector', 'priority', 'created', 'updated', 'originator')
    column_labels = dict(
        id=_('ACL ID'),
        database_operations=_('Operations')
    )
    column_filters = ('created', 'updated',)
    column_searchable_list = ('name',)
    column_default_sort = 'name'
    form_base_class = FlaskForm
    form_columns = ('name', 'priority', 'indices', 'record_selector', 'database_operations')
    form_args = dict(
    )
    page_size = 25
    form_extra_fields = {
        'indices': StringArrayField()
    }

    def validate_record_selector(self, form, field):
        """Checks that the record selector is valid and we can use it to perform query in elasticsearch index"""
        indices = form.indices.data
        record_selector = field.data
        if not record_selector:
            raise StopValidation(
                'Record selector must not be empty. If you want to match all resources, use {"match_all": {}}')
        try:
            for index in indices:
                current_search_client.search(
                    index=index, size=0, body={
                        'query': record_selector
                    }
                )
        except Exception as e:
            raise StopValidation(str(e))


def link_record(view, context, model, name):
    recid = model.record_id
    if recid:
        href = url_for('recordmetadata.details_view', id=recid)
        return Markup('<a href="{0}">{1}</a>'.format(
            href, escape(model.record_str)))
    else:
        return model.record_str


class IdACLModelView(ACLModelViewMixin, ModelView):
    """ModelView for the locations."""

    column_formatters = dict(
        record_str=link_record
    )
    column_details_list = (
        'id', 'name', 'record_str', 'indices', 'created', 'updated', 'originator', 'database_operations', 'priority')
    column_list = ('id', 'name', 'record_str', 'priority', 'created', 'updated', 'originator')
    column_labels = dict(
        id=_('ACL ID'),
        record_str = _('Record')
    )
    column_filters = ('created', 'updated',)
    column_searchable_list = ('name',)
    column_default_sort = 'name'
    form_base_class = FlaskForm
    form_columns = ('name', 'priority', 'record_id', 'indices', 'database_operations')
    form_args = dict(
    )
    page_size = 25
    form_extra_fields = {
        'indices': StringArrayField()
    }

    def validate_form(self, form):
        if not super().validate_form(form):
            return False
        if hasattr(form, 'indices'):
            indices = form.indices.data
            if not indices:

                record_id = form.record_id.data
                try:
                    rec = Record.get_record(record_id)
                except:
                    form.indices.errors.append('No indices defined and the record with the given does not exist yet')
                    return False

                form.indices.data = [
                    current_record_to_index(rec)[0]
                ]

        return True

class DefaultACLModelView(ACLModelViewMixin, ModelView):
    """ModelView for the locations."""

    column_formatters = dict(
        record_str=link_record
    )
    column_details_list = (
        'id', 'name', 'indices', 'created', 'updated', 'originator', 'database_operations', 'priority')
    column_list = ('id', 'name', 'indices', 'priority', 'created', 'updated', 'originator')
    column_labels = dict(
        id=_('ACL ID'),
    )
    column_filters = ('created', 'updated',)
    column_searchable_list = ('name',)
    column_default_sort = 'name'
    form_base_class = FlaskForm
    form_columns = ('name', 'priority', 'indices', 'database_operations')
    form_args = dict(
    )
    page_size = 25
    form_extra_fields = {
        'indices': StringArrayField()
    }

elasticsearch_aclset_adminview = dict(
    modelview=ElasticsearchACLModelView,
    model=ElasticsearchACL,
    category=_('ACLs'))

id_aclset_adminview = dict(
    modelview=IdACLModelView,
    model=IdACL,
    category=_('ACLs'))

default_aclset_adminview = dict(
    modelview=DefaultACLModelView,
    model=DefaultACL,
    category=_('ACLs'))

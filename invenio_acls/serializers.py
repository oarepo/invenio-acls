import json

from elasticsearch import JSONSerializer
from flask import current_app
from invenio_records_rest.serializers.base import PreprocessorMixin
from invenio_records_rest.utils import obj_or_import_string
from invenio_search import current_search
from invenio_search.utils import schema_to_index

from invenio_acls import ACLRecordsSearch, ACL_MATCHED_QUERY


class ACLSerializerMixin(PreprocessorMixin):
    acl_rest_endpoint = None
    """
    endpoint key from RECORDS_REST_ENDPOINTS of the resource that this serializer is about to serialize
    """

    acl_operations = ('get', 'update', 'delete')
    """
    set of acl operations that will be checked if user has access to them. For this to work the search_class
    defined on the rest endpoint must be inherited from ACLRecordsSearch
    """

    def preprocess_record(self, pid, record, links_factory=None, **kwargs):
        ret = super().preprocess_record(pid, record, links_factory, **kwargs)

        index_names = current_search.mappings.keys()
        index, doc_type = schema_to_index(record['$schema'], index_names=index_names)

        rest_configuration = current_app.config['RECORDS_REST_ENDPOINTS'][self.acl_rest_endpoint]

        SearchClazz = obj_or_import_string(rest_configuration.get('search_class', None), default=ACLRecordsSearch)

        sc = SearchClazz(index=index, doc_type=doc_type)

        rec = sc.acl_return_all(operation=self.acl_operations).get_record(str(record.id))
        rec = rec.execute()

        if rec.hits:
            matched_acls = getattr(rec.hits[0].meta, 'matched_queries', [])
            matched_acls = [x.replace(f'{ACL_MATCHED_QUERY}_', '') for x in matched_acls]
        else:
            matched_acls = []

        ret['invenio_acls'] = matched_acls

        return ret

    @staticmethod
    def preprocess_search_hit(pid, record_hit, links_factory=None, **kwargs):
        ret = PreprocessorMixin.preprocess_search_hit(pid, record_hit, links_factory=links_factory, **kwargs)
        matched_acls = record_hit.get('matched_queries', [])
        matched_acls = [x.replace(f'{ACL_MATCHED_QUERY}_', '') for x in matched_acls]
        ret['invenio_acls'] = matched_acls
        return ret


class ACLJSONSerializer(ACLSerializerMixin, JSONSerializer):
    pass

from elasticsearch_dsl.query import Bool, Nested, Term, Q
from flask_login import current_user
from invenio_search import RecordsSearch
from invenio_search.api import MinShouldMatch

ACL_MATCHED_QUERY = 'invenio_acls_match'


class ACLDefaultFilter:
    operations = ('get',)

    def __init__(self, operation=None):
        if operation and not isinstance(operation, tuple) and not isinstance(operation, list):
            operation = (operation,)
        self.operations = list(operation or ACLDefaultFilter.operations)

    def create_query(self, operation=None):
        query = []
        roles = []
        if operation and not isinstance(operation, tuple) and not isinstance(operation, list):
            operation = (operation,)
        operations = operation or self.operations

        # if anon
        if not current_user.is_anonymous:
            query.append(Q('term', _invenio_acls__users=current_user.id))
            roles.append('authenticated')
            for role in current_user.roles:
                roles.append(str(role.id))
        else:
            roles.append('anonymous')

        query.append(Q('terms', _invenio_acls__roles=roles))

        queries = []
        for operation in operations:
            queries.append(
                Nested(
                    path='_invenio_acls',
                    _name=f'{ACL_MATCHED_QUERY}_{operation}',
                    query=Bool(
                        must=[
                            Term(_invenio_acls__operation=operation),
                            Bool(
                                minimum_should_match=1,
                                should=query
                            )
                        ]
                    )
                )
            )

        return Bool(should=queries,
                    minimum_should_match=1)


class ACLRecordsSearch(RecordsSearch):

    def __init__(self, **kwargs):
        operation = kwargs.pop('operation', None)
        super().__init__(**kwargs)
        self.acl_operation = operation
        acl_filter = self._get_acl_filter()
        self.query = Bool(minimum_should_match=MinShouldMatch("100%"),
                          filter=acl_filter.create_query(operation=operation))

    def _get_acl_filter(self):
        acl_filter = getattr(self.Meta, 'acl_filter', None) or ACLDefaultFilter()
        return acl_filter

    def acl_return_all(self, operation=None):
        """
        Returns all the matched results regardless of their acls but mark those with matched ACLs
        (the default is to return only those resources for which ACLs match).
        Internally uses ES named query with name "invenio_acls_match", so the records with matched ACLs
        will contain the following element in "hits":

        "matched_queries": [
            "invenio_acls_match"
        ]
        :param operation:   optional operation if not specified in the constructor
        :return:    self to be used in pipes.

        Sample usage:

        resp = ACLRecordsSearch(...).acl_return_all(operation='get').query(Term(a=1)).execute()
        """
        acl_filter = self._get_acl_filter()
        self.query = Bool(minimum_should_match=MinShouldMatch(0),
                          should=acl_filter.create_query(operation=operation or self.acl_operation))
        return self

import json
from typing import List, Dict, Iterable

import elasticsearch
import elasticsearch.helpers
import pkg_resources
from invenio_records import Record
from invenio_search import current_search_client

from .models_acl import ACL


class ACLHandler:

    def handles(self, acl: ACL) -> bool:
        """
        returns if the handler is capable of handling the given ACL

        :param acl: acl
        :return:    True if capable of handling the ACL
        """

    def get_acl(self, id: str) -> ACL or None:
        """
        Returns acl instance for the given id

        :param id:  id of the ACL
        :return:    the ACL or None if the ACL is not handled by this handler
        """
        raise NotImplementedError("Must be implemented")

    def get_record_acls(self, record: Record) -> List[ACL]:
        """
        Returns a list of ACL objects applicable for the given record

        :param record: Invenio record
        :return:
        """
        raise NotImplementedError('Must be implemented')

    def get_matching_resources(self, acl) -> Iterable[str]:
        """
        Get resources that match given ACL

        :param acl: the acl
        :return:   iterable of resource ids
        """
        raise NotImplementedError('Must be implemented')

    def prepare(self, index_name, doc_type):
        """
        Prepare ACLs for the given index

        :param index_name: index in elasticsearch for which to prepare the ACLs
        """
        raise NotImplementedError('Must be implemented')

    def update(self, acl):
        """
        Update any internal representation / index for the acl

        :param acl:     the acl that has been created or changed
        """
        raise NotImplementedError('Must be implemented')

    def delete(self, acl):
        """
        Delete acl from any internal representation / index for the acl

        :param acl:     the acl that has been removed
        """
        raise NotImplementedError('Must be implemented')


class ACLHandlers:
    _handlers: Dict[str, ACLHandler] = None

    @property
    def handlers(self) -> Dict[str, ACLHandler]:
        if self._handlers:
            return self._handlers

        _handlers = {}
        for ep in pkg_resources.iter_entry_points(group='invenio_acls.handlers'):
            handler_clz = ep.load()
            _handlers[ep.name] = handler_clz()

        if not _handlers:
            raise Exception('No acl handlers defined. Please add them to setup.py entrypoints into invenio_acls.handlers group')

        self._handlers = _handlers
        return _handlers

    def get_handler(self, acl: ACL):
        for handler in self.handlers.values():
            if handler.handles(acl):
                return handler
        raise NotImplementedError('Handler for acl type %s is not registered. Known handlers: %s' %
                                  (type(acl), list(self.handlers.keys())))

    def get_record_acls(self, record: Record) -> Iterable[ACL]:
        """
        Returns a list of ACL objects applicable for the given record

        :param record: Invenio record
        :return:
        """
        applicable_acls = []
        for handler in self.handlers.values():
            applicable_acls.extend(handler.get_record_acls(record))

        # return those applicable acls with the highest priority
        if applicable_acls:
            max_priority = max([x.priority for x in applicable_acls])
            return [x for x in applicable_acls if x.priority == max_priority]

        return []

    def get_matching_resources(self, acl) -> Iterable[str]:
        """
        Get resources that match given ACL

        :param acl: the acl
        :return:   iterable of resource ids
        """
        return self.get_handler(acl).get_matching_resources(acl)

    def get_acl(self, id: str) -> ACL or None:
        """
        Returns acl instance for the given id

        :param id:  id of the ACL
        :return:    the ACL or None if the ACL is not handled by this handler
        """
        for handler in self.handlers.values():
            acl = handler.get_acl(id)
            if acl:
                return acl
        return None

    def prepare(self, index_name, doc_type):
        """
        Prepare ACLs for the given index

        :param index_name: index in elasticsearch for which to prepare the ACLs
        """
        for handler in self.handlers.values():
            handler.prepare(index_name, doc_type)

    def update(self, acl: ACL):
        """
        Update any internal representation / index for the acl

        :param acl:     the acl that has been created or changed
        """
        return self.get_handler(acl).update(acl)

    def delete(self, acl: ACL):
        """
        Delete acl from any internal representation / index for the acl

        :param acl:     the acl that has been removed
        """
        return self.get_handler(acl).delete(acl)

    def get_matching_resources_from_cache(self, acl, older_than_timestamp=None, indices=None) -> Iterable[str]:
        # return all resources in elasticsearch that were matching given ACL
        if isinstance(acl, str):
            acl_id = acl
            assert indices
        else:
            acl_id = acl.id
            assert not indices
            indices = acl.indices

        for index in indices:
            query = [
                {
                    "term": {
                        "_invenio_acls.id": str(acl_id)
                    }
                }
            ]
            if older_than_timestamp:
                query.append(
                    {
                        "range": {
                            "_invenio_acls.timestamp": {
                                "lt": older_than_timestamp
                            }
                        }
                    }
                )

            query = {
                "nested": {
                    "path": "_invenio_acls",
                    "score_mode": "min",
                    "query": {
                        "bool": {
                            "must": query
                        }
                    }
                }
            }

            print(index, json.dumps(query, indent=4))

            for doc in elasticsearch.helpers.scan(current_search_client,
                                                  query={"query": query},
                                                  index=index):
                yield doc['_id']

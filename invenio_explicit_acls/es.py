from elasticsearch import VERSION as ES_VERSION


def add_doc_type(doc_type):
    if ES_VERSION[0] >= 7:
        return {}
    else:
        return {
            'doc_type': doc_type
        }

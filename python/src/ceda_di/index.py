from elasticsearch import Elasticsearch


class BulkIndexer(object):
    """
    Indexes data into an ES installation by pooling documents and submitting
    in large bulk requests.
    """
    def __init__(self, host, port, index, threshold=1000):
        host_string = "%s:%d" % (host, port)

        self.index = index
        self.threshold = threshold
        self.es = Elasticsearch([host_string])
        self.doc_pool = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.submit_pools()

    def add_to_index_pool(self, mapping, document):
        """
        Add document to the correct pool, dependent on mapping type.
        """
        # Create the pool if it doesn't exist
        if mapping not in self.doc_pool:
            self.doc_pool[mapping] = []

        self.doc_pool[mapping].append(document)

        # If we've met the threshold, then submit all of the documents
        if len(self.doc_pool[mapping]) >= self.threshold:
            self.submit_pool(mapping)

    def submit_pool(self, mapping):
        """
        Submit current document grouping (grouped by mapping) to the
        appropriate mapping in the ElasticSearch index.
        """
        body = [{"index": body} for body in self.doc_pool[mapping]]
        self.es.bulk(body, index=self.index, doc_type=mapping)
        self.doc_pool[mapping] = []

    def submit_pools(self):
        """
        Submit all current document pools to the ElasticSearch index.
        """
        for mapping in self.doc_pool.keys():
            self.submit_pool(mapping)


if __name__ == "__main__":
    import json
    import os
    import sys
    documents = []
    for (root, dirs, files) in os.walk(sys.argv[1]):
        for fi in files:
            with open(os.path.join(root, fi), 'r') as f:
                documents.append(json.load(f))

    with BulkIndexer("fatcat-test.jc.rl.ac.uk", 9200, "test_index") as b:
        for doc in documents:
            b.add_to_index_pool("test_mapping", doc)

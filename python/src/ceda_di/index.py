from elasticsearch import Elasticsearch
from elasticsearch import ElasticsearchException


class BulkIndexer(object):
    """
    Context manager for indexing into an ES installation
    by pooling documents and submitting in large bulk requests when
    the document count reaches a certain threshold.
    """
    def __init__(self, es_host, es_port, es_index, threshold=1000):
        """
        :param str es_host: The Elasticsearch host.
        :param int es_port: The port that the Elasticsearch service runs on.
        :param str es_index: The index to submit bulk requests to.
        :param int threshold: The number of documents to hold in the buffer before indexing.
        """
        host_string = "%s:%d" % (es_host, es_port)

        self.index = es_index
        self.threshold = threshold
        self.es = Elasticsearch([host_string])

        # Dict containing key:value pairs of mapping:[list of documents]
        # That way, this class can handle indexing multiple types of documents
        self.doc_pool = {}

    def __enter__(self):
        return self

    def __exit__(self, exc_type, value, traceback):
        self.submit_pools()

    def add_to_index_pool(self, mapping, document):
        """
        Add document to the correct pool, dependent on mapping type.
        :param str mapping: The mapping to index the document into.
        :param object document: The JSON-serialisable object to index.
        """
        # Create the pool if it doesn't exist
        if mapping not in self.doc_pool:
            self.doc_pool[mapping] = []

        self.doc_pool[mapping].append(document)

        # If we've met the threshold, then submit all of the documents
        if len(self.doc_pool[mapping]) >= self.threshold:
            self.submit_pool(mapping)

    def index_directory(self, path, mapping):
        """
        Indexes all files in a given directory.
        :param str path: The path to the directory containing the data files.
        :param str mapping: The mapping type (doc type) for the document to be indexed as.
        """
        import os  # Only import in this method - it's not needed anywhere else
        for root, _, files in os.walk(path):
            for file_name in files:
                path = os.path.join(root, file_name)
                with open(path, 'r') as file_handle:
                    self.doc_pool[mapping].append(file_handle.read())

        # Make sure all documents are submitted to the index
        self.submit_pool(mapping)

    def submit_pool(self, mapping):
        """
        Submit current document grouping (grouped by mapping) to the
        appropriate mapping in the ElasticSearch index.
        :param str mapping: The mapping to submit a to index.
        """
        # Elasticsearch's Bulk API expects data in a strange format (see link)
        # http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/docs-bulk.html
        docs = []
        for doc in self.doc_pool[mapping]:
            docs.append({"index": True})
            docs.append(doc)

        # We want to see any errors that are thrown up by Elasticsearch
        response = self.es.bulk(docs, index=self.index, doc_type=mapping)
        if response["errors"] is True:
            raise ElasticsearchException(
                "Error response from Elasticsearch server: %s" % response)

        # Empty the list now that we've indexed all the docs from it
        self.doc_pool[mapping] = []

    def submit_pools(self):
        """
        Submit all current document pools to the ElasticSearch index.
        """
        for mapping in self.doc_pool.keys():
            if len(self.doc_pool[mapping]) > 0:
                self.submit_pool(mapping)

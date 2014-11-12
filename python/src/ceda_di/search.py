import re

from elasticsearch import Elasticsearch, ConnectionError
import dateutil.parser
import sys


class JsonQueryBuilder(object):

    def __init__(self):
        self.query_dict = {
            "query": {
                "filtered": {
                    "filter": {
                        "bool": {
                            "must": [],
                            "should": [],
                            "must_not": []
                        }
                    }
                }
            }
        }

    def build(self, extents_string=None):
        """
        Builds an Elasticsearch query dictionary from a given extents string
        :param extents_string: A string specifying temporal or spatial extents
        e.g. 't=[2014-10-12T12:13:14,2014-10-12T17:18:19]'
        :return: a dictionary which is valid Elasticsearch query JSON.
        """
        if extents_string is not None:
            self._validate_extents_string(extents_string)
            start, end = self._get_start_end_date(extents_string)
            start_constraint = {
                "range": {
                    "eufar.temporal.start_time": {
                        "lte": end
                    }
                }
            }
            end_constraint = {
                "range": {
                    "eufar.temporal.end_time": {
                        "gte": start
                    }
                }
            }
            self._add_to_query_filter("must", start_constraint)
            self._add_to_query_filter("must", end_constraint)
            return self.query_dict
        else:
            return self.query_dict

    def _get_start_end_date(self, string):
        """
        Extract a start date from an extents string
        :param string: Extents string (should contain temporal extent of form
        't=[2014-10-12T12:13:14,2014-10-12T17:18:19]')
        :return: Tuple (start, end), where start and end dates are dateutil valid timestamp strings
        """
        extents_regex = r't=\[([^\[\],]*),([^\[\],]*)\]'
        matches = re.search(extents_regex, string)
        start, end = matches.groups()
        for date_str in start, end:
            dateutil.parser.parse(date_str)  # Check that this is a valid date
        return start, end

    def _add_to_query_filter(self, filter_logic, filter_dict):
        """
        Add a filter dictionary to the overall query dictionary.
        :param filter_logic: Elasticsearch filter logic: one of 'must', 'must_not', 'should'.
        :param filter_dict: Filter dictionary (e.g {"range": {...}})
        :return: None
        """
        self.query_dict['query']['filtered']['filter']['bool'][filter_logic].append(filter_dict)

    def _validate_extents_string(self, extents_string):
        """
        Determine if a string is a valid extents string
        :param extents_string: A string specifying temporal or spatial extents
        e.g. 't=[2014-10-12T12:13:14,2014-10-12T17:18:19]'
        :return: True
        :raises: ValueError if validation fails
        """
        valid_regex = r't=\[([^\[\],]*),([^\[\],]*)\]'
        if not re.match(valid_regex, extents_string):
            raise ValueError("Invalid extents specified")
        return True


class ElasticsearchClientFactory(object):

    def get_client(self, config):
        host = config['es_host']
        port = config['es_port']
        return Elasticsearch(hosts=[{"host": host, "port": port}])


class Searcher(object):
    """
    Coordinates the searching of Elasticsearch nodes to output matching filepaths.
    """

    def __init__(self, config, json_query_builder=JsonQueryBuilder(),
                 elastic_search_client_factory=ElasticsearchClientFactory()):
        """
        Creates a new Searcher instance
        :param config: Configuration / command line args dictionary (includes the extents string)
        :param json_query_builder: Takes the user input extents string and converts it to Elasticsearch query DSL JSON
        :param elastic_search_client_factory: Creates appropriately configured Elasticsearch client instances
        :return: A new Searcher instance
        """
        self.elastic_search_client_factory = elastic_search_client_factory
        self.json_query_builder = json_query_builder
        self.config = config

    def run(self):
        """
        Run the search and output the results matching the configuration belonging to this instance
        :return: Outputs matching filenames to sys.stdout
        """
        extents = None
        if 'extents' in self.config:
            extents = self.config['extents']
        query = self.json_query_builder.build(extents)
        es = self.elastic_search_client_factory.get_client(self.config)
        try:
            results = es.search(index='badc', doc_type='eufar', body=query)
        except ConnectionError as ex:
            url = es.transport.seed_connections[0].host
            error_msg = "Couldn't connect to elastic search node at {url}. Exception was {exc}".format(url=url,
                                                                                                       exc=ex.message)
            print(error_msg)
            sys.exit(1)
        self._print_results(results)
        sys.exit(0)

    def _print_results(self, results):
        """
        Print the result's filepaths
        :param results: Elasticsearch query results JSON
        :return: Prints the results' filepaths to sys.stdout
        """
        hits = results['hits']['hits']
        for hit in hits:
            print(hit['_source']['file']['path'])

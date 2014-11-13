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
            },
            "size": 10
        }
        self.extent_handlers = [{'name': 'Datetime extents',
                                 'regex': r't=\[([^\[\],]*),([^\[\],]*)\]',
                                 'func': self.process_datetime_extents
                                },
                                {'name': 'Single datetime',
                                 'regex': r't=\[([^\[\],]*)\]',
                                 'func': self.process_single_datetime
                                }]

    def process_datetime_extents(self, start, end):
        for date_str in start, end:
            dateutil.parser.parse(date_str)
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

    def process_single_datetime(self, datetime):
        dateutil.parser.parse(datetime)
        start_constraint = {
            "range": {
                "eufar.temporal.start_time": {
                    "lte": datetime
                }
            }
        }
        end_constraint = {
            "range": {
                "eufar.temporal.end_time": {
                    "gte": datetime
                }
            }
        }
        self._add_to_query_filter("must", start_constraint)
        self._add_to_query_filter("must", end_constraint)

    def build(self, extents_string=None, max_results=None):
        """
        Builds an Elasticsearch query dictionary from a given extents string
        :param extents_string: A string specifying temporal or spatial extents
        e.g. 't=[2014-10-12T12:13:14,2014-10-12T17:18:19]'
        :return: a dictionary which is valid Elasticsearch query JSON.
        """
        if max_results is not None:
            self.query_dict['size'] = max_results
        if extents_string is not None:
            for handler in self.extent_handlers:
                regex = handler['regex']
                processing_func = handler['func']
                matches = re.search(regex, extents_string)
                if matches:
                    processing_func(*matches.groups())
        return self.query_dict

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

    def get_client(self, config_args):
        host = config_args['es_host']
        port = config_args['es_port']
        return Elasticsearch(hosts=[{"host": host, "port": port}])


class Searcher(object):
    """
    Coordinates the searching of Elasticsearch nodes to output matching filepaths.
    """

    def __init__(self, config_args, json_query_builder=JsonQueryBuilder(),
                 elastic_search_client_factory=ElasticsearchClientFactory()):
        """
        Creates a new Searcher instance
        :param config_args: Configuration / command line args dictionary (includes the extents string)
        :param json_query_builder: Takes the user input extents string and converts it to Elasticsearch query DSL JSON
        :param elastic_search_client_factory: Creates appropriately configured Elasticsearch client instances
        :return: A new Searcher instance
        """
        self._elastic_search_client_factory = elastic_search_client_factory
        self._json_query_builder = json_query_builder
        self._config_args = config_args

    def run(self):
        """
        Run the search and output the results matching the configuration belonging to this instance
        :return: Outputs matching filenames to sys.stdout
        """
        extents = self._config_args.get('extents')
        max_results = self._config_args.get('max-results')
        query = self._json_query_builder.build(extents, max_results=max_results)
        es = self._elastic_search_client_factory.get_client(self._config_args)
        try:
            results = es.search(index=self._config_args.get('es_index'), doc_type='eufar', body=query)
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

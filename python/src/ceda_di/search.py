import re

from elasticsearch import Elasticsearch, ConnectionError
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
                                },
                                {'name': 'Latitude extents',
                                 'regex': r'y=\[([^\[\],]*),([^\[\],]*)\]',
                                 'func': self.process_latitude_extents
                                },
                                {'name': 'Single latitude',
                                 'regex': r'y=\[([^\[\],]*)\]',
                                 'func': self.process_single_latitude
                                },
                                {'name': 'Longitude extents',
                                 'regex': r'x=\[([^\[\],]*),([^\[\],]*)\]',
                                 'func': self.process_longitude_extents
                                },
                                {'name': 'Single longitude',
                                 'regex': r'x=\[([^\[\],]*)\]',
                                 'func': self.process_single_longitude
                                }]

    def process_datetime_extents(self, start, end):
        """
        Process a datetime extents search filter and add it to the query dictionary.

        Will parse partial datetimes to maximise the search window - e.g. start=2009, end=2010 will find all results
        from 2009-01-01T00:00:00 to 2010-12-31T23:59:59
        :param start: Start datetime string
        :param end: End datetime string
        :return:
        """
        from jasmin_cis.parse_datetime import parse_partial_datetime
        try:
            start = parse_partial_datetime(start, True).isoformat()
            end = parse_partial_datetime(end, False).isoformat()
        except ValueError:
            raise ValueError("Couldn't parse datetimes '{start}' and '{end}': "
                             "use the ISO-8601 YYYY-MM-DDTHH:MM:SS format.".format(start=start, end=end))
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
        """
        Process a single datetime search filter and add it to the query dictionary.

        Will parse partial datetimes to maximise the search window - e.g. 2009 will find all results
        from 2009-01-01T00:00:00 to 2009-12-31T23:59:59
        :param datetime: Start datetime string
        :return:
        """
        self.process_datetime_extents(datetime, datetime)

    def process_latitude_extents(self, lat_1, lat_2):
        """
        Process latitude extents search filter and add it to the query dictionary.

        Will always include the region from the lowest latitude specified to the highest, regardless of the order in
        which they are passed to this function.
        :param lat_1: Latitude float in the range -90 to +90 degrees.
        :param lat_2: Latitude float in the range -90 to +90 degrees.
        :return:
        """
        try:
            lat1 = float(lat_1)
            lat2 = float(lat_2)
        except ValueError:
            raise ValueError("Couldn't parse latitude extents: '{start}' and '{end}'.".format(start=lat_1, end=lat_1))
        if not (-90 <= lat1 <= 90 and -90 <= lat1 <= 90):
            raise ValueError("Latitudes out of range: should be in -90 to 90, was {lat1} and {lat2}"
                             .format(lat1=lat1, lat2=lat2))
        # Sort them to the correct order
        bottom = min([lat1, lat2])
        top = max([lat1, lat2])
        lat_constraint = {
            "geo_shape": {
                "eufar.spatial.geometries.bbox": {
                    "shape": {
                        "type": "envelope",
                        "coordinates": [[-180, top], [180, bottom]]
                    }
                }
            }
        }
        self._add_to_query_filter("must", lat_constraint)

    def process_single_latitude(self, lat):
        """
        Process a single latitude search filter and add it to the query dictionary.

        :param lat: Latitude to filter by
        :return:
        """
        self.process_latitude_extents(lat, lat)

    def process_longitude_extents(self, start, end):
        """
        Process longitude extents search filter and add it to the query dictionary.

        Will automatically constrain start and end longitudes to be within the range -180 to +180 (so they may
        be specified e.g. as 370). The region searched is always the region from the start longitude to the end latitude
        :param start: Start latitude
        :param end: End latitude
        :return:
        """
        try:
            start = float(start)
            end = float(end)
        except ValueError:
            raise ValueError("Couldn't parse latitude extents: '{start}' and '{end}'.".format(start=start, end=end))
        start = self._confine_lon(start)
        end = self._confine_lon(end)
        lat_constraint = {
            "geo_shape": {
                "eufar.spatial.geometries.bbox": {
                    "shape": {
                        "type": "envelope",
                        "coordinates": [[start, 90], [end, -90]]
                    }
                }
            }
        }
        self._add_to_query_filter("must", lat_constraint)

    def process_single_longitude(self, lon):
        """
        Process a single longitude search filter

        Will automatically constrain to within the range -180 to +180 (so values of e.g. 370 are acceptable).
        :param lon: Longitude to filter by
        :return:
        """
        self.process_longitude_extents(lon, lon)

    def _confine_lon(self, lon):
        """
        Confine a longitude range to -180 -> +180
        :param lon: Longitude to confine
        :return: Confined longitude
        """
        while lon > 180:
            lon -= 360
        while lon < -180:
            lon += 360
        return lon

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


class ElasticsearchClientFactory(object):

    def get_client(self, config_args):
        """
        Return an appropriately configured Elasticsearch client.
        :param config_args: Configuration dictionary. Should contain an Elasticsearch hostname under key 'es_host'
        and an Elasticsearch port under the key 'es_port'.
        :return:
        """
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
            error_msg = "Couldn't connect to elastic search node at {url}. Exception was {exc}"\
                .format(url=url, exc=ex.info.args[1])
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

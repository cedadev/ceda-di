import re
import sys

import json

from elasticsearch import Elasticsearch, ConnectionError
from ceda_di.metadata.product import GeoJSONGenerator
from dateutil.parser import parse
import datetime


class JsonQueryBuilder(object):
    """
    Create a JSon Query Builder which can create an elastic search json query from extents and max results strings
    """

    def __init__(self, file_handler_factory):
        """
        Initialise
        :param file_handler_factory: factory used to get a file handler to return information on a file if needed
        :return: nothing
        """

        self.file_handler_factory = file_handler_factory

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
        self.extent_handlers = [
            {
                'name': 'Datetime extents',
                'regex': r't=\[([^\[\],]*),([^\[\],]*)\]',
                'func': self.process_datetime_extents
            },
            {
                'name': 'Single datetime',
                'regex': r't=\[([^\[\],]*)\]',
                'func': self.process_single_datetime
            },
            {
                'name': 'Latitude extents',
                'regex': r'y=\[([^\[\],]*),([^\[\],]*)\]',
                'func': self.process_latitude_extents
            },
            {
                'name': 'Single latitude',
                'regex': r'y=\[([^\[\],]*)\]',
                'func': self.process_single_latitude
            },
            {
                'name': 'Longitude extents',
                'regex': r'x=\[([^\[\],]*),([^\[\],]*)\]',
                'func': self.process_longitude_extents
            },
            {
                'name': 'Single longitude',
                'regex': r'x=\[([^\[\],]*)\]',
                'func': self.process_single_longitude
            },
            {
                'name': 'Bounding Box from a File',
                'regex': r'bb_from_file=\[([^\[\],]*)\]',  # filename inside square brackets e.g. [a filename.txt]
                'func': self.process_bounding_box_from_file
            },
            {
                'name': 'Times from a File',
                'regex': r'times_from_file=\[([^\[\],]*)\]',  # filename inside square brackets e.g. [a filename.txt]
                'func': self.process_times_from_file
            }
        ]

    def _add_region_to_query_filter(self, latitudes, longitudes, from_file):
        """
        Add a region query to the filter
        :param latitudes: the list of latitudes
        :param longitudes: the list of longitudes
        :param from_file: whether query was from a file (if so a polygon is created not just an envelope)
        :return: nothing
        """
        generator = GeoJSONGenerator(latitudes, longitudes)
        if from_file:
            bbox = generator._gen_bbox()
        else:
            bbox = generator._gen_envelope()
        if bbox is None:
            raise ValueError("No bounding box generated when reading the file.")
        constraint = {
            "geo_shape": {
                "eufar.spatial.geometries.bbox": {
                    "shape": bbox
                }
            }
        }
        self._add_to_query_filter("must", constraint)

    def _get_handler_for_file(self, action, filename):
        if len(filename.strip()) == 0:
            raise ValueError("No filename given when reading the file for %s." % action)
        try:
            handler = self.file_handler_factory.get_handler(filename)
        except Exception as ex:
            raise ValueError("An error occurred when determining the file format for the {action}. "
                             "Filename: '{filename}', error: '{error}'"
                             .format(filename=filename, error=ex, action=action))
        if handler is None:
            raise ValueError("File can not be read because format is not known, file: '{filename}'."
                             .format(filename=filename))
        return handler

    def process_bounding_box_from_file(self, filename):
        """
        Process bounding box from a file and add it to the query dictionary.

        Will automatically constrain start and end longitudes to be within the range -180 to +180 (so they may
        be specified e.g. as 370). The region searched is always the region from the start longitude to the end latitude
        :param filename: the filename to read the bounding box from
        """
        handler = self._get_handler_for_file("bounding box", filename)
        try:
            spatial = handler.get_geospatial()
            self._add_region_to_query_filter(spatial["lat"], spatial["lon"], False)
        except Exception as ex:
            raise ValueError("An error occurred when reading the file for the bounding box. Filename: '{filename}', "
                             "error: '{error}'".format(filename=filename, error=ex))

    def process_times_from_file(self, filename):
        """
        Process times from a file and add it to the query dictionary.

        :param filename: the filename to read the bounding box from
        """
        handler = self._get_handler_for_file("times", filename)
        try:
            temporal = handler.get_temporal()
        except Exception as ex:
            raise ValueError("An error occurred when reading the file for the times. Filename: '{filename}', "
                             "error: '{error}'".format(filename=filename, error=ex))
        try:
            self._add_temporal_query_to_filter(temporal["start_time"], temporal["end_time"])
        except KeyError:
            raise ValueError("No times found when reading the file. Filename: '{filename}'".format(filename=filename))

    def _add_temporal_query_to_filter(self, start, end):
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

    def process_datetime_extents(self, start, end):
        """
        Process a datetime extents search filter and add it to the query dictionary.

        Will parse partial datetimes to maximise the search window - e.g. start=2009, end=2010 will find all results
        from 2009-01-01T00:00:00 to 2010-12-31T23:59:59

        :param start: Start datetime string
        :param end: End datetime string
        """
        try:
            start = parse(start, default=datetime.datetime(1,1,1,0,0,0)).isoformat()
            end = parse(end, default=datetime.datetime(1,12,31,23,59,59)).isoformat()
        except ValueError:
            raise ValueError("Couldn't parse datetimes '{start}' and '{end}': "
                             "use the ISO-8601 YYYY-MM-DDTHH:MM:SS format.".format(start=start, end=end))
        self._add_temporal_query_to_filter(start, end)

    def process_single_datetime(self, datetime):
        """
        Process a single datetime search filter and add it to the query dictionary.

        Will parse partial datetimes to maximise the search window - e.g. 2009 will find all results
        from 2009-01-01T00:00:00 to 2009-12-31T23:59:59
        :param datetime: Start datetime string
        """
        self.process_datetime_extents(datetime, datetime)

    def process_latitude_extents(self, lat_1, lat_2):
        """
        Process latitude extents search filter and add it to the query dictionary.

        Will always include the region from the lowest latitude specified to the highest, regardless of the order in
        which they are passed to this function.

        :param lat_1: Latitude float in the range -90 to +90 degrees.
        :param lat_2: Latitude float in the range -90 to +90 degrees.
        """
        try:
            lat1 = float(lat_1)
            lat2 = float(lat_2)
        except ValueError:
            raise ValueError("Couldn't parse latitude extents: '{start}' and '{end}'.".format(start=lat_1, end=lat_1))
        if not (-90 <= lat1 <= 90 and -90 <= lat1 <= 90):
            raise ValueError("Latitudes out of range: should be in -90 to 90, was {lat1} and {lat2}"
                             .format(lat1=lat1, lat2=lat2))
        self._add_region_to_query_filter([lat1, lat2], [-180, 180], False)

    def process_single_latitude(self, lat):
        """
        Process a single latitude search filter and add it to the query dictionary.

        :param lat: Latitude to filter by
        """
        self.process_latitude_extents(lat, lat)

    def process_longitude_extents(self, start, end):
        """
        Process longitude extents search filter and add it to the query dictionary.

        Will automatically constrain start and end longitudes to be within the range -180 to +180 (so they may
        be specified e.g. as 370). The region searched is always the region from the start longitude to the end latitude
        :param start: Start latitude
        :param end: End latitude
        """
        try:
            start = float(start)
            end = float(end)
        except ValueError:
            raise ValueError("Couldn't parse latitude extents: '{start}' and '{end}'.".format(start=start, end=end))
        start = self._confine_lon(start)
        end = self._confine_lon(end)

        self._add_region_to_query_filter([-90, 90], [start, end], False)

    def process_single_longitude(self, lon):
        """
        Process a single longitude search filter.

        Will automatically constrain to within the range -180 to +180 (so values of e.g. 370 are acceptable).

        :param lon: Longitude to filter by
        """
        self.process_longitude_extents(lon, lon)

    def _confine_lon(self, lon):
        """
        Confine a longitude range to -180 -> +180.

        :param lon: Longitude to confine
        :returns: Confined longitude
        """
        while lon > 180:
            lon -= 360
        while lon < -180:
            lon += 360
        return lon

    def build(self, extents_string=None, max_results=None):
        """
        Build an Elasticsearch query dictionary from a given extents string.

        :param extents_string: A string specifying temporal or spatial extents, e.g. 't=[2014-10-12T12:13:14,2014-10-12T17:18:19]'.
        :returns: A dictionary which is valid Elasticsearch query JSON.
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
        """
        self.query_dict['query']['filtered']['filter']['bool'][filter_logic].append(filter_dict)


class ElasticsearchClientFactory(object):

    def get_client(self, config_args):
        """
        Return an appropriately configured Elasticsearch client.

        :param config_args: Configuration dictionary.
                            Should contain:
                                Elasticsearch hostname under key 'es-host'.
                                Elasticsearch user under key 'es-user'.
                                Elasticsearch password under key 'es-password'.

        :returns: A configured Elasticsearch instance
        """
        host = config_args['es-host']
        user = config_args["es-user"]
        password = config_args["es-password"]

        return Elasticsearch(
            [host],
            http_auth=(user, password),
            timeout=60
        )


class Searcher(object):
    """
    Coordinates the searching of Elasticsearch nodes to output matching filepaths.
    """

    def __init__(self, config_args, json_query_builder=None,
                 elastic_search_client_factory=ElasticsearchClientFactory()):
        """
        Create a new Searcher instance.

        :param config_args: Configuration / command line args dictionary (includes the extents string)
        :param json_query_builder: Takes the user input extents string and converts it to Elasticsearch query DSL JSON
        :param elastic_search_client_factory: Creates appropriately configured Elasticsearch client instances
        :returns: A new Searcher instance
        """
        from ceda_di.extract import HandlerFactory

        self._elastic_search_client_factory = elastic_search_client_factory

        if json_query_builder is not None:
            self._json_query_builder = json_query_builder
        else:
            try:
                handler_factory = HandlerFactory(config_args["handlers"])
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))
                raise SystemExit("Missing configuration option: %s\n\n" % str(k))
            self._json_query_builder = JsonQueryBuilder(handler_factory)

        self._config_args = config_args

    def run(self):
        """
        Run the search and output the results matching the configuration belonging to this instance.

        :returns: Outputs matching filenames to sys.stdout
        """
        extents = self._config_args.get('extents')
        max_results = self._config_args.get('max-results')
        query = self._json_query_builder.build(extents, max_results=max_results)
        es = self._elastic_search_client_factory.get_client(self._config_args)

        try:
            # XXX
            index = self._config_args.get('es-index')
            doc_type = self._config_args.get('es-mapping')
            results = es.search(index=index, doc_type=doc_type, body=query)
        except ConnectionError as ex:
            url = es.transport.seed_connections[0].host
            error_msg = "Couldn't connect to Elasticsearch node at {url}. Exception was {exc}" \
                .format(url=url, exc=str(ex))
            print(error_msg)
            sys.exit(1)

        if self._config_args.get('file-paths'):
            self._print_file_paths(results)
        else:
            self._print_json_results(results)

        sys.exit(0)

    def _print_file_paths(self, results):
        """
        Print the result's file paths.

        :param results: Elasticsearch query results JSON
        """
        hits = results['hits']['hits']
        for hit in hits:
            print(hit['_source']['file']['path'])

    def _print_json_results(self, results):
        """
        Print the results in JSON format.

        :param results: Elasticsearch query results.
        """
        hits = results['hits']['hits']
        print(json.dumps(hits, indent=4))

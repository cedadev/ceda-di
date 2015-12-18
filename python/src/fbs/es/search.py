import re
import sys

import simplejson as json

from elasticsearch import Elasticsearch, ConnectionError
from fbs_lib.geojson import GeoJSONGenerator

class ElasticsearchClientFactory(object):

    def get_client(self, config_args):
        """
        Return an appropriately configured Elasticsearch client.

        :param config_args: Configuration dictionary. Should contain an Elasticsearch hostname under key 'es-host' and an Elasticsearch port under the key 'es-port'.
        :returns: A configured Elasticsearch instance
        """
        host = config_args["es-configuration"]["es-host"]
        port = config_args["es-configuration"]["es-port"]
        return Elasticsearch(hosts=[{"host": host, "port": port}])
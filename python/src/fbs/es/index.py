import simplejson as json

from elasticsearch import Elasticsearch
from elasticsearch import ElasticsearchException
from elasticsearch.exceptions import TransportError


def _get_host_string(config):
    """
    Take appropriate elements from a config dictionary and convert them into
    a string of format 'host:port'.
    :param dict config: Application configuration dictionary, including ES config.
    """
    host = config["es-configuration"]["es-host"]
    port = config["es-configuration"]["es-port"]
    return "%s:%d" % (host, port)


def create_index(config, elasticsearch):
    """
    Set up an index in ElasticSearch, given a configuration file path.
    :param dict config: Application configuration dictionary, including ES config.
    :param str index_settings_path: Path to index settings JSON document.
    """
    index_settings_path = config["es-configuration"]["es-index-settings"]
    index_name = config["es-configuration"]["es-index"]

    import simplejson as json  # Import here as unused in rest of module
    with open(index_settings_path, 'r') as settings:
        index_settings = json.load(settings)

    elasticsearch.indices.create(index=index_name, body=index_settings)

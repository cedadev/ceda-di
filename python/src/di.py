#!/usr/bin/env python
"""
Usage:
    di.py (--help | --version)
    di.py index [options] <path-to-json-docs>
    di.py search <extents> [options] [--file-paths | --json]
    di.py extract [options] [--send-to-index]
                  [<input-path> (<output-path> | --no-create-files)]
    di.py test

Options:
    --help                     Show this screen.
    --version                  Show version.
    --config=<path>            Config file. [default: ../config/ceda_di.json]
    --host=<host>              Specify ElasticSearch host.
    --port=<port>              Specify ElasticSearch port.
    --index=<name>             Specify ElasticSearch index name.
    --send-to-index            Index metadata with ElasticSearch.
    --no-create-files          Don't create JSON metadata files.
    --max-results=<num>        Max number of results to return when searching
    --file-paths               Print out search results as file paths.
    --json                     Print out search results as pure JSON.

 <extents> for searching:
    one or more conditions that must be satisfied by the file:
    t=[<time>]                    contains <time>
    t=[<start time>, <end time>]  contains some data in the period
    times_from_file=[filename]    contains some data from the period in the file

    x=[<longitude>]               contains the longitude point
    x=[<start long>, <end long>]  contains some data in the longitude range
    y=[<latitude>]                contains the latitude point
    y=[<start lat>, <end lat>]    contains some data in the latitude range

    bb_from_file=[filename]       contains some data from the region in the file
"""

import os

from docopt import docopt

import ceda_di.util.cmd as cmd
from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract
from ceda_di.index import BulkIndexer
from ceda_di.search import Searcher


# Default configuration options
# These are overridden by the config file and command-line arguments
CONFIG = {
    "json-path": "json/",
    "log-path": "log/",
    "log-file": "log/",
    "logging": {
        "format": "[%(levelname)s] (%(name)s) %(message)s"
    }
}


def main():
    CONF_ARGS = cmd.sanitise_args(docopt(__doc__, version=__version__))
    if 'config' not in CONF_ARGS or not CONF_ARGS["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, '../../config/ceda_di.json')
        CONF_ARGS['config'] = conf_path

    CONF_FILE = cmd.read_conf(CONF_ARGS["config"])

    # Apply updates to CONFIG dictionary in priority order
    # Configuration priority: CONFIG < CONF_FILE < ARGS
    # (CONFIG being lowest, ARGS being highest)
    CONFIG.update(CONF_FILE)
    CONFIG.update(CONF_ARGS)

    if CONF_ARGS["extract"]:
        extract = Extract(CONFIG)
        extract.run()
    elif CONF_ARGS["index"]:
        # Opening the BulkIndexer as a context manager ensures all docs get
        # submitted properly to the index (all pools get submitted)
        with BulkIndexer(CONFIG) as index:
            index.index_directory(CONFIG["path-to-json-docs"])
    elif CONF_ARGS["search"]:
        searcher = Searcher(CONFIG)
        searcher.run()

if __name__ == "__main__":
    main()

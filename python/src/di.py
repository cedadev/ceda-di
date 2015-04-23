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


def main():
    conf_args = cmd.sanitise_args(docopt(__doc__, version=__version__))
    if 'config' not in conf_args or not conf_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../../config/ceda_di.json")
        conf_args["config"] = conf_path

    config = cmd.get_settings(conf_args["config"], conf_args)

    if conf_args["extract"]:
        extract = Extract(config)
        extract.run()
    elif conf_args["index"]:
        # Opening the BulkIndexer as a context manager ensures all docs get
        # submitted properly to the index (all pools get submitted)
        with BulkIndexer(config) as index:
            index.index_directory(config["path-to-json-docs"])
    elif conf_args["search"]:
        searcher = Searcher(config)
        searcher.run()

if __name__ == "__main__":
    main()

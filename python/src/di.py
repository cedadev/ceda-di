#!/usr/bin/env python
"""
Usage:
    di.py (--help | --version)
    di.py index [options] <path-to-json-docs>
                (--host=<host> --port=<port> --index=<name>)
    di.py query [options] <path-to-request-json>
                (--host=<host> --port=<port> --index=<name>)
    di.py search [options]
    di.py search <extents> [options]
    di.py extract [options] [--send-to-index]
                  [<input-path> (<output-path> | --no-create-files)]

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
"""

import json
import sys

from docopt import docopt

from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract
from ceda_di.search import Searcher


def sanitise_args(config):
    """
    Sanitise command-line configuration.
    :param config: Config dictionary (from docopt)
    :return dict: Config dictionary with all keys stripped of '<' '>' and '--'
    """
    sane_conf = {}
    for key, value in config.iteritems():
        if value is not None:
            key = key.lstrip("-><").rstrip("><")
            sane_conf[key] = value

    return sane_conf


def read_conf(conf_path):
    """
    Read configuration file into a dictionary.
    :param conf_path: Path to the JSON configuration file
    :return dict: Dict containing parsed JSON conf
    """
    try:
        with open(conf_path, "r") as conf:
            return json.load(conf)
    except IOError as ioe:
        sys.stderr.write(  # Continued on next line
            "Can't read configuration file\n%s\n\n" % str(ioe))
        return {}


def not_implemented(option):
    """
    Raise a NotImplementedError with a message saying "option" is unimplemented.
    :param str option: Name of the unimplemented command/option.
    """
    raise NotImplementedError(
        "The \"%s\" command has not been implemented yet.\n" % option)

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

if __name__ == "__main__":
    CONF_ARGS = sanitise_args(docopt(__doc__, version=__version__))
    CONF_FILE = read_conf(CONF_ARGS["config"])

    # Apply updates to CONFIG dictionary in priority order
    # Configuration priority: CONFIG < CONF_FILE < ARGS
    # (CONFIG being lowest, ARGS being highest)
    CONFIG.update(CONF_FILE)
    CONFIG.update(CONF_ARGS)

    # XXX Check for unimplemented functions and raise error
    UNIMPL = ["index", "query", "send-to-index", "no-create-files"]
    for cmd in UNIMPL:
        if cmd in CONF_ARGS and CONF_ARGS[cmd]:
            not_implemented(cmd)

    if CONF_ARGS["extract"]:
        E = Extract(CONFIG)
        E.run()

    if CONF_ARGS["search"]:
        searcher = Searcher(CONFIG)
        searcher.run()

    elif CONF_ARGS["test"]:
        # TODO Would be nice to run unit tests from here later on
        pass

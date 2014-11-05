#!/usr/bin/env python
"""
Usage:
    di.py (--help | --version)
    di.py index [options]
                (--host=<host> --port=<port> --index=<name>)
                <path-to-json-docs>
    di.py query [options]
                (--host=<host> --port=<port> --index=<name>)
    di.py extract [options] [--send-to-index] <input-path>
                  (<output-path> | --no-create-files)

Options:
    --help                     Show this screen.
    --version                  Show version.
    --config=<path>            Config file [default: ../config/ceda_di.json]
    --host=<host>              Specify ElasticSearch host
    --port=<port>              Specify ElasticSearch port
    --index=<name>             Specify ElasticSearch index name
    --send-to-index            Index metadata with ElasticSearch
    --no-create-files          Don't create JSON metadata files
"""

import json
import sys

from docopt import docopt

from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract


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
        return None


def not_implemented(option):
    """Write a message to sys.stderr and exit."""
    sys.stderr.write("The \"%s\" command has not been implemented!\n" % option)


if __name__ == "__main__":
    ARGS = docopt(__doc__, version=__version__)
    CONF = read_conf(ARGS["--config"])  # "--config" should ALWAYS exist as key

    if CONF:
        # Check for unimplemented functions and raise error
        UNIMPL = ["index", "query", "--send-to-index", "--no-create-files"]
        for cmd in UNIMPL:
            if cmd in ARGS and ARGS[cmd]:
                not_implemented(cmd)

        if ARGS["extract"]:
            print json.dumps(CONF, indent=4)
            E = Extract(CONF)
            E.run()

        elif ARGS["test"]:
            # TODO Would be nice to run unit tests from here as a "hidden" option
            pass

"""
Module containing useful functions for the command-line interfaces.
"""

import sys

import simplejson as json


def sanitise_args(config):
    """
    Sanitise command-line configuration.

    :param config: Config dictionary (from docopt)
    :returns: Config dictionary with all keys stripped of '<' '>' and '--'
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
    :returns: Dict containing parsed JSON conf
    """
    try:
        with open(conf_path, "r") as conf:
            return json.load(conf)
    except IOError as ioe:
        sys.stderr.write(  # Continued on next line
            "Can't read configuration file\n%s\n\n" % str(ioe))
        return {}

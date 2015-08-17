"""
Module containing useful functions for the command-line interfaces.
"""

import os
import sys
import csv

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
    except IOError:
        err_path = os.path.abspath(conf_path)
        sys.stderr.write(  # Continued on next line
            "Can't read configuration file\n%s\n\n" % err_path)
        return {}


def get_settings(conf_path, args):
    # Default configuration options
    # These are overridden by the config file and command-line arguments
    defaults = {
        "json-path": "json/",
        "log-path": "log/",
        "log-file": "log/",
        "logging": {
            "format": "[%(levelname)s] (%(name)s) %(message)s"
        }
    }

    conf_file = read_conf(conf_path)

    # Apply updates to CONFIG dictionary in priority order
    # Configuration priority: CONFIG < CONF_FILE < ARGS
    # (CONFIG being lowest, ARGS being highest)
    defaults.update(conf_file)
    defaults.update(args)

    return defaults


def build_file_list(path, followlinks=None):
    """
    :Return Directory 
    :return: A list of file paths
    """            
    file_list = []
    for root, _, files in os.walk(path, ("followlinks=false" if followlinks else "followlinks=True")):
        for each_file in files:
            file_list.append(os.path.join(root, each_file))

    return file_list

def write_list_to_file(file_list, file):
    f = open(file, 'w')
    
    for item in file_list:
        f.writelines(item)
        f.write("\n")
    
    f.close()
    
    
def find_dataset(file, dataset_id):
    """
    :Returns: The path of the given dataset id. 
    """
    vars = {}
    with open(file) as l_file:
        for line in l_file:
            name, var = line.partition("=")[::2]
            vars[name.strip()] = var.strip()
    
    return vars[dataset_id]   



#!/usr/bin/env python

"""
Usage:
  es_index_files.py -h | --help
  es_index_files.py --version
  es_index_files.py (-i <dataset>)
                    (-d <directory>)
  es_index_files.py (-i <dataset>)
                    (-l <list_file>)
Options:
  -h --help             Show this screen.
  --version             Show version.
  -i=<dataset>          Dataset to scan "faam", "eufar", "sentinel" or "ceda-eo" (for the combined index).
  -d=<directory>        Directory to scan. 
  -l=<list_file>        List of files.
 """

import sys
import getopt
import datetime
import subprocess
import os
import pipes
import shlex
import urllib2
import json
import time

# Default locations for script and virtual env.
# Get base directory from script location
BASE_DIR = "/".join(os.path.realpath(__file__).split("/")[:-5])
src_dir = os.path.join(BASE_DIR, "ceda-di/python/src")
virtual_env = os.path.join(BASE_DIR, "venv-ceda-di/bin/python2.7")
CONFIG_DIR = os.path.join(BASE_DIR, "ceda-di/python/config")


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


def execute_command(cmd, url):
    """
    Runs command `cmd` then calls URL `url` to report on the amount of
    records in the index.
    :cmd Scan command [string]
    :url URL to call Elastic search
    :return: None
    """
    print "Running command: %s" % cmd    

    try:
        subprocess.check_output(shlex.split(cmd), cwd=src_dir, env=os.environ.copy())
    except subprocess.CalledProcessError as exc:
        print "Error code:", exc.returncode, exc.output

    time.sleep(2)
    report_files(url) 


def construct_url(json_file):
    with open(json_file) as data_file:    
        data = json.load(data_file)

    url= "http://{}:{}/{}/_count?q=file.filename:*&pretty=true".format(data["es-host"], data["es-port"], data["es-index"])
    print "URL used: %s" % url
    return url


def report_files(url):
    content = urllib2.urlopen(url).read()
    print "\nFile count in index: %s" % content.split(",")[0].replace("{","")


def scan_dataset(dataset, directory):
    if dataset in ("faam", "eufar", "sentinel", "ceda-eo"):
        config_file = os.path.join(CONFIG_DIR, "ceda-di-%s.json" % dataset)
        cmd = "{}/di.py extract --no-create-files --config {} --send-to-index {}".format(src_dir, config_file, directory)
        url = construct_url(config_file)
        execute_command(cmd, url)
    else:
        print "Invalid 'dataset' argument: '%s'" % dataset


def scan_from_list_file(dataset, list_file):
    """
    Reads a set of paths from `list_file` file and scans
    each path specified.
    """
    with open(list_file) as fd:
        lines = fd.readlines()

    for line in lines:
        scan_dataset(dataset, line)


def main():
    """
    Main controller script.
    """
    # Get command line arguments.
    config = {"index": None, "directory": None, "file_list": None}
    args, dummy = getopt.getopt(sys.argv[1:], "d:i:l:")

    for k, v in args:
        if k == "-i":
            config["index"] = v
        elif k == "-d":
            config["directory"] = v
        elif k == "-l":
            config["file_list"] = v
            
    start = datetime.datetime.now()
    print "Script started at: %s" % start

    if config["index"] and config["file_list"]:
        scan_from_list_file(config["index"], config["file_list"])
    elif config["index"] and config["directory"]:
        scan_dataset(config["index"], config["directory"])
    else:
        print __doc__
        print "Arguments not recognised!"
    
    end = datetime.datetime.now()
    print "Script ended at: %s ; it ran for: %s seconds." % (str(end), str(end - start))


if __name__ == '__main__':
    main()

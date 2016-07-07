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
  -i=<dataset>          Dataset to scan "faam", "eufar" or "sentinel".
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
    print "Command used: " + cmd    
    subprocess.check_output(shlex.split(cmd), cwd=src_dir, env=os.environ.copy())

    try:
        subprocess.check_output(shlex.split(cmd), cwd=src_dir, env=os.environ.copy())
    except subprocess.CalledProcessError as grepexc:                                                                                                   
        print "Error code", grepexc.returncode, grepexc.output
    else:
        time.sleep(2)
        report_files(url) 


def construct_url(json_file):
    with open(json_file) as data_file:    
        data = json.load(data_file)

    url= "http://{}:{}/{}/_count?q=file.filename:*&pretty=true".format(data["es-host"], data["es-port"], data["es-index"])
    print "URL used: " + url
    return url


def report_files(url):
    content = urllib2.urlopen(url).read()
    print "Files in database:" + content.split(",")[0].replace("{","")


def scan_dataset(dataset, directory):
    if dataset in ("faam", "eufar", "sentinel"):
        config_file = os.path.join(CONFIG_DIR, "ceda-di-%s.json" % dataset)
        cmd = "{}/di.py extract --no-create-files --config {} --send-to-index {}".format(src_dir, config_file, directory)
        url = construct_url(config_file)
        execute_command(cmd, url)
    else:
        print "Invalid 'dataset' argument: '%s'" % dataset


def scan_file(dataset, list_file):
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
        print k, v
        if k == "-i":
            config["index"] = v
        elif k == "-d":
            config["directory"] = v
        elif k == "-l":
            config["file_list"] = v
            
    start = datetime.datetime.now()
    print "Script started at: %s" %(str(start))

    if config["index"] and config["file_list"]:
        scan_file(config["index"], config["file_list"])
    elif config["index"] and config["directory"]:
        scan_dataset(config["index"], config["directory"])
    else:
        print __doc__
        print "Arguments not recognised!"
    
    end = datetime.datetime.now()
    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))


if __name__ == '__main__':
    main()

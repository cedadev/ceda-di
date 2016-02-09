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

import docopt
import datetime
import subprocess
import os
import pipes
import shlex
import urllib2
import json
import time

#Default locations for script and virtual env.
python_script="/group_workspaces/jasmin/cedaproc/file_based_search/code/ceda-di/python/src/"
virtual_env="/group_workspaces/jasmin/cedaproc/file_based_search/venv/bin/python2.7"
configuration_file = {
                       "faam"    : "/group_workspaces/jasmin/cedaproc/file_based_search/code/ceda-di/python/config/ceda-di-faam.json",
                       "eufar"   : "/group_workspaces/jasmin/cedaproc/file_based_search/code/ceda-di/python/config/ceda-di-eufar.json",
                       "sentinel": "/group_workspaces/jasmin/cedaproc/file_based_search/code/ceda-di/python/config/ceda-di-sentinel.json"
                     }

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
    print "command used: " + cmd    
    #subprocess.Popen(shlex.split(cmd), cwd=python_script, shell=False, env=os.environ.copy())
    #print "time before subprocess:" + str(datetime.datetime.now())
    try:
        a=subprocess.check_output(shlex.split(cmd), cwd=python_script, env=os.environ.copy())
    except subprocess.CalledProcessError as grepexc:                                                                                                   
        print "error code", grepexc.returncode, grepexc.output
    else:
        time.sleep(2)
        report_files(url) 

def construct_url(json_file):
    with open(json_file) as data_file:    
        data = json.load(data_file)
    url= "http://{}:{}/{}/_count?q=filename:*&pretty=true".format( data["es-host"], data["es-port"], data["es-index"])
    print "url used: " + url
    return url

def report_files(url):
    #print "time before get: " + str(datetime.datetime.now())
    content = urllib2.urlopen(url).read()
    print "files in database:" + content.split(",")[0].replace("{","")

def scan_dataset(dataset, directory):
    if dataset == "faam":
        cmd = "{}di.py extract --no-create-files --config {} --send-to-index {}".format(python_script, configuration_file["faam"], directory)
        url=construct_url(configuration_file["faam"])
        execute_command(cmd, url)

    elif dataset == "eufar":
        cmd="{}di.py extract --no-create-files --config {} --send-to-index {}".format(python_script, configuration_file["eufar"], directory)
        url=construct_url(configuration_file["eufar"])
        execute_command(cmd, url)

    elif dataset == "sentinel":
        cmd="{}di.py extract --no-create-files --config {} --send-to-index {}".format(python_script, configuration_file["sentinel"], directory)
        url=construct_url(configuration_file["sentinel"])
        execute_command(cmd, url)
    else:
        print "invalid argument"

def scan_file(dataset, list_file):
    with open(list_file) as fd:
        lines = fd.readlines()

    for line in lines:
        #print line
        scan_dataset(dataset, line)

def main():

    """
    Relevant ticket : 
    """
    #Get command line arguments.
    com_args = sanitise_args(docopt.docopt(__doc__))

    #print com_args

    start = datetime.datetime.now()
    print "Script started at: %s" %(str(start))

    if "l" in com_args and "i" in com_args:
        scan_file(com_args["i"], com_args["l"])
    elif "d" in com_args and "i" in com_args:
        scan_dataset(com_args["i"], com_args["d"])
    elif "version" in com_args:
        print "V0.1"  

    end = datetime.datetime.now()
    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))


if __name__ == '__main__':
    main()

#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-f <filename> | --filename <filename>)
                  (-d <dataset_id> | --dataset <dataset_id> )
                  (-l <level> | --level <level>)
                  [-c <path_to_config_dir> | --config <path_to_config_dir>]
  scan_dataset.py (-f <filename> | --filename <filename>)
                  (-d <dataset_id> | --dataset <dataset_id>)
                  (-m <location> | --make-list <location>)
                  [-c <path_to_config_dir> | --config <path_to_config_dir>]
  scan_dataset.py (-f <filename> | --filename <filename>)
                  [-n <n_files> | --num-files <n_files>]
                  [-s <start_number> | --start <start_number>]
                  (-l <level> | --level <level>)
                  [-c <path_to_config_dir> | --config <path_to_config_dir>]

Options:
  -h --help                           Show this screen.
  --version                           Show version.
  -d --dataset=<dataset_id>           Dataset id.
  -f --filename=<filename>            File from where the dataset will
                                      be read [default: datasets.ini].
  -l --level=<level>                  Level of search:
                                      Level 1: File names and sizes
                                      Level 2: File names, sizes and
                                      phenomena (e.g. "air temperature")
                                      Level 3: File names, sizes, phenomena
                                      and geospatial metadata.
  -m --make-list=<location>           Stores the list of filenames to a file.
  -c --config=<path_to_config_dir>    Specify the main configuration directory.
  -n --num-files=<n_files>            Number of files to scan.
  -s --start=<start_number>           Starting point within the cache file
                                      containing filenames.
 """

import os

from docopt import docopt

import fbs_lib.util as util
from fbs import __version__  # Grab version from package __init__.py
from fbs.extract import ExtractSeq
import datetime
import fbs.constants.constants as constants
import signal, getpass, pwd


def sig_handler(signum, frame):

    """
    Catches SIGTERM, SIGINT, SIGHUP signals
    cleans tmp directoy 
    and terminates the process.
    """

    script_user = getpass.getuser()
    tmp_dir_files = util.build_file_list("/tmp")

    print "Signal {} received deleting tmp files:".format(signum)
    for filename in tmp_dir_files:

        if not os.path.exists(filename):
            continue
        stat_info = os.stat(filename)
        uid = stat_info.st_uid
        file_owner = pwd.getpwuid(uid)[0]

        if script_user == file_owner:
            print filename
            os.remove(filename)

    raise SystemExit(signum)

# Associate the handler with signals:
signal.signal(signal.SIGTERM, sig_handler)
signal.signal(signal.SIGINT, sig_handler)
signal.signal(signal.SIGHUP, sig_handler)

def ckeck_com_args_validity(config, status):

    """
    checks the validity of command line arguments
    """

    if status == constants.Script_status.STORE_DATASET_TO_FILE:
        return

    level = int(config.get("level"))

    if level < 1  or level > 3:
        raise ValueError("Level value is out of range, please \
                          use value between 1-3.")

def read_and_scan_dataset(conf, status):

    """
    Reads files from a specific directory in filesystem
    and outputs metadata to elastic search database.
    """
    extract = ExtractSeq(conf)
    extract.read_and_scan_dataset()

def store_dataset_to_file(conf, status):

    """
    Reads files from a specific directory in filesystem
    and stores their filenames and path to a file.
    """
    extract = ExtractSeq(conf)
    extract.store_dataset_to_file()

def read_dataset_from_file_and_scan(conf, status):

    """
    Reads file paths form a given file, extracts metadata
    for each file and posts results to elastic search.
    """

    extract = ExtractSeq(conf)
    extract.read_dataset_from_file_and_scan()

def get_stat_and_defs(com_args):

    """
    Set global variables that determine the operations to be performed.
    """

    status_and_defaults = []
    # Searches for the configuration file.
    if 'config' not in com_args or not com_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_fbs.ini")
        com_args["config"] = conf_path

    #Creates a dictionary with default settings some of them
    #where loaded from th edefaults file.
    config = util.get_settings(com_args["config"], com_args)


    #Set defaults if not supplied by user.
    if "start" not in config or not config["start"]:
        config["start"] = config["scanning"]["start"]

    if "num-files" not in config or not config["num-files"]:
        config["num-files"] = config["scanning"]["num-files"]

    status_and_defaults.append(config)

    if ("make-list" in config) and ("dataset" in config) \
       and  ("filename" in config):

        status_and_defaults.append(\
        constants.Script_status.STORE_DATASET_TO_FILE)

    elif ("dataset" in config) and  ("filename" in config) \
          and ("level" in config):

        status_and_defaults.append(\
        constants.Script_status.READ_AND_SCAN_DATASET)

    elif ("filename" in config) and ("start" in config) and \
          ("num-files" in config) and ("level" in config):

        status_and_defaults.append\
        (constants.Script_status.READ_DATASET_FROM_FILE_AND_SCAN)

    config["cf_tempdir"] = config["scanning"]["cf_tempdir"]

    return status_and_defaults

def main():

    """
    Relevant ticket : http://team.ceda.ac.uk/trac/ceda/ticket/23203
    """
    #Get command line arguments.
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))

    #Insert defaults
    status_and_defaults = get_stat_and_defs(com_args)

    config = status_and_defaults[0]
    status = status_and_defaults[1]

    #checks the validity of command line arguments.
    try:
        ckeck_com_args_validity(config, status)
    except ValueError as err:
        print err
        return


    start = datetime.datetime.now()
    print "Script started at: %s" %(str(start))


    #Manage the options given.
    if status == constants.Script_status.STORE_DATASET_TO_FILE:
        store_dataset_to_file(config, status)
    elif status == constants.Script_status.READ_AND_SCAN_DATASET:
        read_and_scan_dataset(config, status)
    elif status == constants.Script_status.READ_DATASET_FROM_FILE_AND_SCAN:
        read_dataset_from_file_and_scan(config, status)

    end = datetime.datetime.now()
    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))


if __name__ == '__main__':
    main()

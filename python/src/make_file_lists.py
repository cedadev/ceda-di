#!/usr/bin/env python

"""
Usage:
  make_file_lists.py -h | --help
  make_file_lists.py --version
  make_file_lists.py (-f <filename> | --filename <filename>)
                     (-m <location> | --make-list <location>)
                     [-p <number_of_processes> | --num-processes <number_of_processes>]
                     (--host <hostname>)

Options:
  -h --help                                  Show this screen.
  --version                                  Show version.
  -f --filename=<filename>                   File from where the dataset
                                             will be read
                                             [default: datasets.ini].
  -m --make-list=<location>                  Stores the list of filenames
                                             to a file.
  -p --num-processes=<number_of_processes>   Number of processes to use.
  --host=<hostname>                          The name of the host where
                                             the script will run.
 """

import os

from docopt import docopt
import fbs_lib.util as util
from fbs import __version__  # Grab version from package __init__.py
import datetime
from enum import Enum
import subprocess
import fbs_lib.util as util
import fbs.constants.constants as constants


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

    #Creates a dictionary with default settings some of
    #them where loaded from th edefaults file.
    config = util.get_settings(com_args["config"], com_args)

    if "num-processes" not in config or not config["num-processes"]:
        config["num-processes"] = config["scanning"]["num-processes"]

    status_and_defaults.append(config)

    if ("host" in config) and config["host"] == "localhost":
        status_and_defaults.append(constants.Script_status.RUN_SCRIPT_IN_LOCALHOST)
    else:
        status_and_defaults.append(constants.Script_status.RUN_SCRIPT_IN_LOTUS)


    return status_and_defaults

def store_datasets_to_files_in_lotus(status, config):

    """
    Finds and stores all files belonging to each dataset.
    """

    #Get file.
    filename = config["filename"]
    #Extract datasets ids and paths.
    datasets = util.find_dataset(filename, "all")
    datasets_ids = datasets.keys()
    num_datasets = len(datasets_ids)
    scan_commands = []
    current_dir = os.getcwd()
    directroy_to_save_files = config["make-list"]

    #Create the commands that will create the
    #files containing the paths to data files.
    for i in range(0, num_datasets):

        command = "python %s/scan_dataset.py -f %s -d  %s --make-list %s/%s.txt"\
                  %(current_dir, filename, datasets_ids[i],\
                  directroy_to_save_files, datasets_ids[i])

        scan_commands.append(command)


    lotus_max_processes = config["num-processes"]

    #Run each command in lotus.
    util.run_tasks_in_lotus(scan_commands, int(lotus_max_processes),\
                             user_wait_time=30)

def store_datasets_to_files_in_localhost(status, config):

    """
    Finds and stores all files belonging to each dataset.
    """

    #Get file.
    filename = config["filename"]
    #Extract datasets ids and paths.
    datasets = util.find_dataset(filename, "all")
    datasets_ids = datasets.keys()
    num_datasets = len(datasets_ids)
    scan_commands = []
    current_dir = os.getcwd()
    directroy_to_save_files = config["make-list"]

    #Create the commands that will create the
    #files containing the paths to data files.
    for i in range(0, num_datasets):

        command = "python %s/scan_dataset.py -f %s -d  %s --make-list %s/%s.txt" \
                  %(current_dir, filename, datasets_ids[i],  \
                  directroy_to_save_files, datasets_ids[i])

        print "executing : %s" %(command)

        subprocess.call(command, shell=True)

def main():

    """
    Relevant ticket : http://team.ceda.ac.uk/trac/ceda/ticket/23217
    """

    #Get command line arguments.
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))

    #Insert defaults
    status_and_defaults = get_stat_and_defs(com_args)



    start = datetime.datetime.now()
    print "Script started at: %s" %(str(start))

    status = status_and_defaults[1]
    config = status_and_defaults[0]


    if status == constants.Script_status.RUN_SCRIPT_IN_LOCALHOST:
        store_datasets_to_files_in_localhost(status, config)
    else:
        store_datasets_to_files_in_lotus(status, config)


    end = datetime.datetime.now()
    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))


if __name__ == '__main__':
    main()

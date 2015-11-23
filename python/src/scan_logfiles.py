#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-l <log_directory> | --log_directory <log_directory>)

Options:
  -h --help                           Show this screen.
  --version                           Show version.
  -l --log_directory=<log_directory>  Dataset id.
 """

import os

from docopt import docopt
import ceda_di.util.util as util
from ceda_di import __version__

import datetime


def main():

    """
    Relevant ticket : http://team.ceda.ac.uk/trac/ceda/ticket/23203
    """

    #Get command line arguments.
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))

    log_directory = com_args["log_directory"]
    print "scanning directory {}".format(log_directory)

    #find all files in log directroy.
    list_of_files = util.build_file_list(log_directory)
    no_files = len(list_of_files)

    print "Files found {}".format(list_of_files)

    summary_info = {}
    #open each file and exrtact info.
    for i in range(0, no_files):
        filename = list_of_files[i]
        print filename

        content_list = util.read_file_into_list(filename)
        record = util.find_in_list(content_list, "Summary")
        words_list = record.split(",")
        #dataset
        dataset = (words_list[1].split()[4].replace("(", "")).replace(")", "")
        #indexed
        indexed = int(words_list[2].split()[2])
        #database errors
        database_errors = int(words_list[3].split()[3])
        #properties errors
        properties_errors = int(words_list[4].split()[0])
        #total files
        total_files = int(words_list[5].split()[2])

        if dataset not in  summary_info:
            dataset_info = {}
            dataset_info["dataset"] = dataset
            dataset_info["indexed"] = indexed
            dataset_info["database_errors"] = database_errors
            dataset_info["properties_errors"] = properties_errors
            dataset_info["total_files"] = total_files

            summary_info[dataset] = dataset_info.copy()
            dataset_info = None
        else:
            dataset_info = {}
            dataset_info = summary_info[dataset]
            dataset_info["indexed"] = dataset_info["indexed"] + indexed
            dataset_info["database_errors"] = dataset_info["database_errors"] + database_errors
            dataset_info["properties_errors"] = dataset_info["properties_errors"] + properties_errors
            dataset_info["total_files"] = dataset_info["total_files"] + total_files
            dataset_info = None
    #At the end print all information.
    print summary_info

    start = datetime.datetime.now()
    print "Script started at: %s" %(str(start))

    end = datetime.datetime.now()

    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))


if __name__ == '__main__':
    main()

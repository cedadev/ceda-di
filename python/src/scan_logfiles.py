#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-l <log_directory> | --log_directory <log_directory>)
   (-f <filename> | --filename <filename>)

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

def parse_logs(com_args):

    log_directory = com_args["log_directory"]
    datasets_file = com_args["filename"]

    #find all files in log directroy.
    list_of_files = util.build_file_list(log_directory)
    no_files = len(list_of_files)

    summary_info = {}

    #open each file and exrtact info.
    for i in range(0, no_files):

        filename = list_of_files[i]
        content_list = util.read_file_into_list(filename)
        record = util.find_in_list(content_list, "Summary")

        if record is not None:
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
                #dataset_info["dataset"] = dataset
                dataset_info["indexed"] = indexed
                dataset_info["database_errors"] = database_errors
                dataset_info["properties_errors"] = properties_errors
                dataset_info["total_files"] = total_files
                dataset_info["dataset_dir"] = util.find_dataset(datasets_file, dataset)

                summary_info[dataset] = dataset_info.copy()
                dataset_info = None
            else:
                dataset_info = {}
                dataset_info = summary_info[dataset]
                dataset_info["indexed"] = dataset_info["indexed"] + indexed
                dataset_info["database_errors"] = dataset_info["database_errors"] + database_errors
                dataset_info["properties_errors"] = dataset_info["properties_errors"] + properties_errors
                #dataset_info["total_files"] = dataset_info["total_files"] + total_files
                dataset_info = None
        #At the end print all information.

    return summary_info

def validate_results(dict_data):

    for item in dict_data:
        dataset_info = {}
        dataset_info = dict_data[item]
        sum = dataset_info["indexed"] + dataset_info["database_errors"] + dataset_info["properties_errors"] 
        if dataset_info["total_files"] == sum:
            dataset_info["status"] = "ok"
        else:
            dataset_info["status"] = "errors"

def print_dict(dict_data):
    print "{a:<20} {b:<20} {c:<20} {d:<20} {e:<20} {g:<10} {f:<20}".format(a="Dataset",\
           b="Indexed", c="Total files", d="Properties errors", e="Database errors",\
           f="Dataset dir", g="Status")
    print "-------------------------------------------------------------------------------------------------------------------------------"

    for item in dict_data:
        print ("{a:<20} {p[indexed]:<20} {p[total_files]:<20} {p[properties_errors]:<20}" 
              " {p[database_errors]:<20} {p[status]:<10} {p[dataset_dir]:<20}").format(a=item, p=dict_data[item])

def main():

    """
    Relevant ticket : http://team.ceda.ac.uk/trac/ceda/ticket/23235
    """
    #Get command line arguments.
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))
    start = datetime.datetime.now()
    print "Script started at: {}".format(str(start))

    res = parse_logs(com_args)
    validate_results(res)
    print_dict(res)

    #Get command line arguments.
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))


    end = datetime.datetime.now()
    print "\nScript ended at : {} it ran for : {}".format(str(end), str(end - start))

if __name__ == '__main__':
    main()

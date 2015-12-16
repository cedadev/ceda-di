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
import ceda_fbs.util.util as util
from ceda_fbs import __version__

import datetime

def parse_logs(com_args):

    log_directory = com_args["log_directory"]
    datasets_file = com_args["filename"]

    #find all files in log directroy.
    list_of_files = util.build_file_list(log_directory)
    num_files = len(list_of_files)

    summary_info = {}

    #open each file and exrtact info.
    for i in range(0, num_files):

        filename = list_of_files[i]
        content_list = util.read_file_into_list(filename)
        summary = util.find_in_list(content_list, "Summary")

        if summary is not None:
            words_list = summary.split("Summary", 1)[1].split(",")
            #dataset
            dataset = (words_list[0].split())[5]
            #indexed
            indexed = int(words_list[1].split()[3])
            #database errors
            database_errors = int(words_list[2].split()[3])
            #properties errors
            properties_errors = int(words_list[3].split()[3])
            #total files
            total_files = int(words_list[4].split()[3])

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

    files_indexed_in_datasets = 0
    errors_in_datasets = 0
    total_files_in_datasets = 0

    for item in dict_data:
        dataset_info = {}
        dataset_info = dict_data[item]
        indexed_and_errors = dataset_info["indexed"] + dataset_info["database_errors"] + dataset_info["properties_errors"] 
        if dataset_info["total_files"] == indexed_and_errors:
            dataset_info["status"] = "ok"
        else:
            dataset_info["status"] = "errors"

        #Info for all datasets.
        files_indexed_in_datasets += dataset_info["indexed"]
        errors_in_datasets += dataset_info["database_errors"] + dataset_info["properties_errors"]
        total_files_in_datasets += dataset_info["total_files"]

    datasets_info = {}
    datasets_info["files_indexed_in_datasets"] = files_indexed_in_datasets
    datasets_info["errors_in_datasets"] = errors_in_datasets
    datasets_info["total_files_in_datasets"] = total_files_in_datasets

    dict_data["Totals"] = datasets_info.copy()

def print_dict(dict_data):
    print "{a:<20} {b:<20} {c:<20} {d:<20} {e:<20} {g:<10} {f:<20}".format(a="Dataset",\
           b="Indexed", c="Total files", d="Properties errors", e="Database errors",\
           f="Dataset dir", g="Status")

    print ("---------------------------------------------------------------"
           "----------------------------------------------------------------")

    for item in dict_data:
        if item != "Totals":
            print ("{a:<20} {p[indexed]:<20} {p[total_files]:<20} {p[properties_errors]:<20}" 
                " {p[database_errors]:<20} {p[status]:<10} {p[dataset_dir]:<20}").format(a=item, p=dict_data[item])

    print ("---------------------------------------------------------------"
           "----------------------------------------------------------------")

    #At the end print the totals:
    print ("{a:<20} {p[files_indexed_in_datasets]:<20} {p[total_files_in_datasets]:<20}"
           " {p[errors_in_datasets]:<20}").format(a="Totals:", p=dict_data["Totals"])


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

    end = datetime.datetime.now()
    print "\nScript ended at : {} it ran for : {}".format(str(end), str(end - start))

if __name__ == '__main__':
    main()

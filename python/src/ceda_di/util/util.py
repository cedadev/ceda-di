"""
Module containing useful functions for the command-line interfaces.
"""

import os
import sys
import csv
import subprocess

import simplejson as json
import time
from enum import Enum
import ConfigParser
import struct

#some globals.
Script_status = Enum("Script_status",
                     "SEARCH_AND_STORE_INFO_TO_FILE \
                      SEARCH_AND_STORE_INFO_TO_DB \
                      READ_PATHS_AND_STORE_INFO_TO_DB\
                      RUN_SCRIPT_IN_LOTUS \
                      RUN_SCRIPT_IN_LOCALHOST \
                      SCAN_SPECIFIC_DATASET_ID \
                      SCAN_ALL_DATASETS \
                      STAY_IDLE"
                    )


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
    Reads configuration file into a dictionary.

    :param conf_path: Path to the JSON configuration file.
    :returns: Dict containing parsed JSON conf.
    """
    try:
        with open(conf_path, "r") as conf:
            return json.load(conf)
    except IOError:
        err_path = os.path.abspath(conf_path)
        sys.stderr.write(  # Continued on next line
            "Can't read configuration file\n%s\n\n" % err_path)
        return {}

def cfg_read(filename):
    """
    Reads configuration file into a dictionary.

    :param conf_path: Path to the INI configuration file.
    :returns: Dict containing parsed ini conf.
    """
    #Read the config file
    config = ConfigParser.ConfigParser()
    config.read(filename)

    #get sections
    sections = config.sections()

    conf = {}
    section_options = {}
    handlers_sections = []

    for section in sections:

        if section in handlers_sections:
            continue

        options = config.options(section)

        for option in options:

            try:
                value = config.get(section, option)
                parsed_value = value.replace("\"", "")
                if section == "handlers":
                    handlers_sections.append(value)
                section_options[option] = parsed_value
                if section_options[option] == -1:
                    section_options[option] = None
            except:
                section_options[option] = None


        conf[section] = section_options.copy()
        section_options.clear()


    regx_details = {}
    regxs = {}
    for handler in handlers_sections:
        regx_pattern = config.get(handler, "regx")
        regx_details["class"] = config.get(handler, "class")
        regx_details["priority"] = config.get(handler, "priority")
        regxs[regx_pattern] = regx_details.copy()
        regx_details.clear()

    conf["handlers"] = regxs.copy()

    return  conf

def get_settings(conf_path, args):
    # Default configuration options
    # These are overridden by the config file and command-line arguments
    defaults = {}

    #conf_file = read_conf(conf_path)
    conf_file = cfg_read(conf_path)

    #print conf_file

    # Apply updates to CONFIG dictionary in priority order
    # Configuration priority: CONFIG < CONF_FILE < ARGS
    # (CONFIG being lowest, ARGS being highest)
    defaults.update(conf_file)
    defaults.update(args)

    return defaults

def build_file_list(path):
    """
    :param path : A file path
    :return: List of files contained withint he specified directory..
    """
    file_list = []
    for root, _, files in os.walk(path, followlinks=True):
        for each_file in files:
            file_list.append(os.path.join(root, each_file))

    return file_list

def write_list_to_file(file_list, filename):

    """
    :param file_list : A list of files.
    :param filename : Where the list of files is going to be saved.
    Saves content of a list to a file.
    """

    infile = open(filename, 'w')

    for item in file_list:
        infile.writelines(item)
        infile.write("\n")

    infile.close()

def get_file_header(filename):
    with open(filename, 'r') as f:
        first_line = f.readline()

    return first_line.replace("\n", "")

def get_bytes_from_file(filename, num_bytes):

    # open file in binary mode
    with open(filename, 'rb') as in_file:
        fmt = ">%ss" %(str(num_bytes))
        bytes = struct.unpack(fmt,  in_file.read(num_bytes))[0]

    return bytes


def find_dataset(filename, dataset_id):
    """
    :param filename : file containing dataset information.
    :param dataset_id : dataset to be searched.
    :returns: The path of the given dataset id.
    """
    var_dict = {}
    with open(filename) as l_file:
        for line in l_file:
            if not line.startswith("#"):
                name, var = line.partition("=")[::2]
                var_dict[name.strip()] = var.strip()
    if dataset_id == "all":
        return var_dict
    else:
        return var_dict[dataset_id]

def find_num_lines_in_file(filename):

    """
    :param filename : Name of the file to be read.
    :returns: The number of lines in the given file.
    """
    num_lines = 0

    with open(filename) as infp:
        for line in infp:
            num_lines += 1
    return num_lines

def get_number_of_submitted_lotus_tasks(max_number_of_tasks_to_submit):

    """
    :returns: Number of tasks submitted in lotus.
    """

    empty_task_queue_string = "No unfinished job found\n"
    non_empty_task_queue_string = "JOBID     USER    STAT  QUEUE      FROM_HOST   EXEC_HOST   JOB_NAME   SUBMIT_TIME"

    command_output = subprocess.check_output('bjobs', stderr=subprocess.STDOUT, shell=True)

    if command_output == empty_task_queue_string:
        num_of_running_tasks = 0
    elif command_output.startswith(non_empty_task_queue_string):
        num_of_running_tasks = command_output.count("\n") -1
    else:
        num_of_running_tasks = max_number_of_tasks_to_submit

    return num_of_running_tasks

def run_tasks_in_lotus(task_list, max_number_of_tasks_to_submit, user_wait_time=None, logger=None):

    """
    :param task_list : list of commands to run.
    :param max_number_of_tasks_to_submit : max number of jobs to be run in parallel.
    :param user_wait_time : polling time.
    :param logger : object used for logging.

    Submits the commands supplied in lotus making sure that
    max_number_of_jobs is not exceeded.
    """

    if user_wait_time is None:
        init_wait_time = 30
    else :
        init_wait_time = user_wait_time

    wait_time = init_wait_time
    dec = 1
    iterations_counter = 0


    info_msg = "Max number of jobs to submit in each step : %s.\
               \nTotal number commands to run : %s." \
               %(str(max_number_of_tasks_to_submit), str(len(task_list)))

    if logger is not None:
        logger.INFO(info_msg)
        logger.INFO("===============================")


    print info_msg
    print "==============================="


    while len(task_list) > 0 :

        #Find out if other jobs can be submitted.
        try:
            num_of_running_tasks = get_number_of_submitted_lotus_tasks(max_number_of_tasks_to_submit)
        except CalledProcessError:
            continue

        #num_of_running_tasks = 0
        num_of_tasks_to_submit = max_number_of_tasks_to_submit - num_of_running_tasks
        iterations_counter = iterations_counter + 1

        info_msg = "Iteration : %s." %(str(iterations_counter))
        if logger is not None:
            logger.INFO(info_msg)

        print info_msg

        info_msg = "Number of jobs running  : %s." %(str(num_of_running_tasks))
        if logger is not None:
            logger.INFO(info_msg)

        print info_msg

        info_msg = "Number of jobs to submit in this step : %s." %(str(num_of_tasks_to_submit))
        if logger is not None:
            logger.INFO(info_msg)

        print info_msg


        #Submit jobs according to availability.
        for i in range(0, num_of_tasks_to_submit):

            if len(task_list) == 0:
                break

            #Is there an extract op ?
            task = task_list[0]
            task_list.remove(task)

            command = "bsub %s" %(task)


            info_msg = "%s. Executng : %s" %(str(i +1), command)
            if logger is not None:
                logger.INFO(info_msg)

            print info_msg

            subprocess.call(command, shell=True)


        info_msg = "Number of tasks waiting to be submitted : %s." %(str(len(task_list)))
        if logger is not None:
            logger.INFO(info_msg)

        print info_msg

        #Wait in case some process terminates.
        info_msg = "Waiting for : %s secs." %(str(wait_time))
        if logger is not None:
            logger.INFO(info_msg)

        print info_msg
        time.sleep(wait_time)


        #If nothing can be submitted wait again.
        if num_of_tasks_to_submit == 0:
            wait_time = wait_time - dec
            if (wait_time == 0):
                wait_time = init_wait_time


        if logger is not None:
            logger.INFO("===============================")

        print "==============================="

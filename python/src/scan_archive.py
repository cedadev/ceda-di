#!/usr/bin/env python

"""
Usage:
  scan_archive.py --help
  scan_archive.py --version
  scan_archive.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>)  (-h <hostname> | --host <hostname>) [--num-processes <number_of_processes>] 
                  [-c <path_to_config_dir> | --config <path_to_config_dir>] 
 scan_archive.py  (-f <filename> | --filename <filename>) (-l <level> | --level <level>)  (-h <hostname> | --host <hostname>)
                  [--num-processes <number_of_processes>] [-n <n_files> | --num-files <n_files>] 
                  [-c <path_to_config_dir> | --config <path_to_config_dir>] 
                 
                  
                  
  
Options:
  --help                                     Show this screen.
  --version                                  Show version.
  -d --dataset=<dataset_id>                  Dataset id.
  -f --filename=<filename>                   File from where the dataset will be read [default: datasets.ini]. 
  -l --level=<level>                         Level of search:
                                             Level 1: File names and sizes
                                             Level 2: File names, sizes and phenomena (e.g. "air temperature")
                                             Level 3: File names, sizes, phenomena and geospatial metadata.
  -c --config=<path_to_config_dir>           Specify the main configuration directory.
  -n --num-files=<n_files>                   Number of files to scan.
  -h --host=<hostname>                       The name of the host where the script will run.
  --num-processes=<number_of_processes>   Number of processes to use.
 """

import os

from docopt import docopt

import ceda_di.util.util as util
from ceda_di import __version__  # Grab version from package __init__.py

import datetime   
from enum import Enum

import subprocess

Script_status = Enum( "Script_status",
                      "run_script_in_lotus \
                       run_script_in_localhost \
                       scan_specific_dataset_id \
                       scan_all_dataset_ids \
                       scan_filenames_from_file \
                       stay_idle"
                    )
 
def set_program_op_status_and_defaults(com_args):
    
    """
    Set global variables that determine the operations to be performed. 
    """
     
    status_and_defaults = []   
    # Searches for the configuration file.
    if 'config' not in com_args or not conf_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_di.json")
        com_args["config"] = conf_path

    #Creates a dictionary with default settings some of them where loaded from th edefaults file.
    config = util.get_settings(com_args["config"], com_args)

    status_and_defaults.append(config)
       
            
    if ("host" in config) and (config["host"] == "lotus"):
        status_and_defaults.append(Script_status.run_script_in_lotus)
    elif ("host" in config) and config["host"] == "localhost": 
        status_and_defaults.append(Script_status.run_script_in_localhost)
    else :
        status_and_defaults.append(Script_status.stay_idle)
       
    if ("level" in config) and not ("dataset" in config):
        status_and_defaults.append(Script_status.scan_filenames_from_file)       
    elif ("dataset" in config) and  config["dataset"] == "all" :
        status_and_defaults.append(Script_status.scan_all_dataset_ids)  
    elif ("dataset" in config) and  config["dataset"] != "all" :
        status_and_defaults.append(Script_status.scan_specific_dataset_id)
    else :
        status_and_defaults.append(Script_status.stay_idle)
       
    return status_and_defaults     
     
def scan_files_in_lotus(config, scan_status):
    
    #Get basic options.
    filename = config["filename"]
    level = config["level"]
    current_dir = os.getcwd() 
    number_of_processes  = config["num-processes"]
          
    #Manage the options given. 
    if scan_status == Script_status.scan_specific_dataset_id :
        dataset_id = config["dataset"]
        if ',' in dataset_id :
            dataset_ids_list = dataset_id.split(",")
            for dataset_id_item in dataset_ids_list: 
                command = "bsub" + " -n " + str(number_of_processes) + " python " + current_dir + "/scan_dataset.py -f "\
                          + filename + " -d " + dataset_id_item + " -l " + level 
                print "executng :" + command
                subprocess.call(command, shell=True)
        else:
            command = "bsub" + " -n " + str(number_of_processes) + " python " + current_dir + "/scan_dataset.py -f "\
                      + filename + " -d " + dataset_id + " -l " + level 
            print "executng :" + command
            subprocess.call(command, shell=True)      

    elif scan_status == Script_status.scan_all_dataset_ids :
        dataset_ids = util.find_dataset(filename, "all")
        
        for key, value in dataset_ids.iteritems():
            dataset_id = key
            command = "bsub" + " -n " + str(number_of_processes) + " python " + current_dir + "/scan_dataset.py -f "\
            + filename + " -d " + dataset_id + " -l " + level 
            print "executng :" + command
            subprocess.call(command, shell=True)
    
    elif scan_status == Script_status.scan_filenames_from_file :
        num_files = config["num-files"]
        start = config["start"]
        
        command = "bsub" + " -n " + str(number_of_processes) + " python " + current_dir + "/scan_dataset.py -f "\
                   + filename + " --num-files " +  str(num_files) + " --start " + str(start)  + " -l " + level 
        
        print "executng :" + command
        subprocess.call(command, shell=True)    

def scan_files_in_localhost(config, scan_status):
        
    #Get basic options.
    filename = config["filename"]
    level = config["level"]
    current_dir = os.getcwd()    
          
    #Manage the options given. 
    if scan_status == Script_status.scan_specific_dataset_id :
        dataset_id = config["dataset"]
        if ',' in dataset_id :
            dataset_ids_list = dataset_id.split(",")
            for dataset_id_item in dataset_ids_list: 
                command = "python " + current_dir + "/scan_dataset.py -f " + filename + " -d " + dataset_id_item + " -l " + level 
                print "executng :" + command
                subprocess.call(command, shell=True)
                #os.system(command)
        else :
            command = "python " + current_dir + "/scan_dataset.py -f " + filename + " -d " + dataset_id + " -l " + level 
            print "executng :" + command
            subprocess.call(command, shell=True)                  
                    
    elif scan_status == Script_status.scan_all_dataset_ids :
        dataset_ids = util.find_dataset(filename, "all")       
        
        for key, value in dataset_ids.iteritems():
            dataset_id = key
            command = "python " + current_dir + "/scan_dataset.py -f " + filename + " -d " + dataset_id + " -l " + level 
            print "executng :" + command
            subprocess.call(command, shell=True)   
    elif scan_status == Script_status.scan_filenames_from_file :
        num_files = config["num-files"]
        start = config["start"]
        
        command = "python " + current_dir + "/scan_dataset.py -f " + filename + " --num-files " +  str(num_files) + " --start " \
                  + str(start)  + " -l " + level 
        print "executng :" + command
        subprocess.call(command, shell=True) 
 
def main():
        
    """
    Relevant to ticket :
    http://team.ceda.ac.uk/trac/ceda/ticket/23204
    """   

    start = datetime.datetime.now()              
    print "Script started at:" +str(start) +".\n." 
        
    
    #Get command line arguments. 
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))        
  
  
    #Set default values and determione what operations the script will perform.
    status_and_defaults = set_program_op_status_and_defaults(com_args)      
    
    config_file = status_and_defaults[0] 
    run_status =  status_and_defaults[1]
    scan_status = status_and_defaults[2]
  
     #Calls appropriate functions. 
    if run_status == Script_status.run_script_in_lotus :
        scan_files_in_lotus(config_file, scan_status)
    elif run_status == Script_status.run_script_in_localhost :   
        scan_files_in_localhost(config_file, scan_status)
    else :
        print "Some options could not be recognized.\n"
        
    end = datetime.datetime.now()    
    print "Script ended at :" + str(end) + " it ran for :" + str(end - start) + ".\n"


if __name__ == '__main__':
    main()
#!/usr/bin/env python

"""
Usage:
  scan_archive.py --help
  scan_archive.py --version
  scan_archive.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>)  (-h <hostname> | --host <hostname>) [-p <number_of_processes> | --num-processes <number_of_processes>] 
                  [-c <path_to_config_dir> | --config <path_to_config_dir>] 
 scan_archive.py  (-f <filename> | --filename <filename>) (-l <level> | --level <level>)  (-h <hostname> | --host <hostname>)
                  [-p <number_of_processes> | --num-processes <number_of_processes>] [-n <n_files> | --num-files <n_files>] 
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
  -p --num-processes=<number_of_processes>   Number of processes to use.
 """

import os

from docopt import docopt

import ceda_di.util.util as util
from ceda_di import __version__  # Grab version from package __init__.py

import datetime   
from enum import Enum

import subprocess
import time

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


def scan_all_datasets_in_lotus(config):
    
    filename = config["filename"]
    level = config["level"]
    
    current_dir = os.getcwd() 
    
        
    dataset_ids = util.find_dataset(filename, "all")
    keys = dataset_ids.keys()
    number_of_datasets= len(keys)
    commands  = []      
        
        
    for i in range(0, number_of_datasets):
            
        command =  "python %s/scan_dataset.py -f  %s -d  %s  -l  %s" \
                   %(current_dir, filename, keys[i], level) 
                            
                                   
        print "created command :" + command
        commands.append(command)
    
    lotus_max_processes = config["num-processes"] 
    util.run_tasks_in_lotus(commands, int(lotus_max_processes), user_wait_time=5)        
    
            
def scan_specific_datasets_in_lotus(config):
    #Get basic options.
    filename = config["filename"]
    dataset_id = config["dataset"]
    level = config["level"]       
    current_dir = os.getcwd() 
            
    if ',' in dataset_id :
        dataset_ids_list = dataset_id.split(",")
        for dataset_id_item in dataset_ids_list: 
            
            command = "bsub python %s/scan_dataset.py -f %s -d %s -l %s" \
                      %(current_dir, filename, dataset_id_item, level) 
              
            print "executng : %s" %(command)
            subprocess.call(command, shell=True)
    else:
        command = "bsub python %s/scan_dataset.py -f %s -d  %s -l %s" \
                  %(current_dir, filename, dataset_id, level) 
        
                   
        print "executng : %s" %(command)
        subprocess.call(command, shell=True)
        

def scan_filenames_from_file_in_lotus(config):
    
    """
    basic algorithm:
    
    1. Go to the directory containing the files.
    2. Create a file list.
    3. Scan each file and determine the number of lines contained.
    4. create the appropriate commands.
    5. Store commands in a list.
    6. Go to the next file.
    7. Submit all commands in lotus.    
    """
        
    #Get basic options.
    filename_path = config["filename"]
    level = config["level"]
    num_files = config["num-files"]
    start = config["start"]
    current_dir = os.getcwd() 
    
    
    #Go to directory and create the file list.
    list_of_cache_files = util.build_file_list(filename_path)
    commands = []
    step = int(num_files)
    
    for file in list_of_cache_files :
        
        num_of_lines = util.find_num_lines_in_file(file) 
        
        if num_of_lines == 0 :
           continue
       
        #calculate number of jobs. 
        number_of_jobs = num_of_lines  / int(num_files)
        remainder = num_of_lines  % int(num_files)
    
        start = 0
        for i in range(0, number_of_jobs):
            
            command = " python %s/scan_dataset.py -f %s --num-files %s --start %d  -l %s" \
                        %(current_dir, file, num_files, start, level)
            
            start += step
            
            print "created command : %s" %(command)
            commands.append(command)
            
        #include remaning files
        command = " python %s/scan_dataset.py -f %s --num-files %d --start %d -l %s" \
                  %(current_dir, file, remainder, start, level)
        
        print "created command : %s" %(command)
        commands.append(command)
    
        
    #Run each command in lotus.
    lotus_max_processes = config["num-processes"] 
    util.run_tasks_in_lotus(commands, int(lotus_max_processes), user_wait_time=5)
        
          
def scan_files_in_lotus(config, scan_status):
    
    """
    Uses Lotus in order to scan files in the filesystem. 
    """
        
    #Scan given dataset ids  or file. 
    if scan_status == Script_status.scan_specific_dataset_id :
        scan_specific_datasets_in_lotus(config)      

    elif scan_status == Script_status.scan_all_dataset_ids :
        scan_all_datasets_in_lotus(config)
                                
    elif scan_status == Script_status.scan_filenames_from_file :
        scan_filenames_from_file_in_lotus(config)   
                 

def scan_filenames_from_file_in_localhost(config):
            
    #Get basic options.
    filename_path = config["filename"]
    level = config["level"]
    num_files = config["num-files"]
    start = config["start"]
    current_dir = os.getcwd() 
    
    
    #Go to directory and create the file list.
    list_of_cache_files = util.build_file_list(filename_path)
    commands = []
    step = int(num_files)
    
    for file in list_of_cache_files :
        
        num_of_lines = util.find_num_lines_in_file(file) 
        
        if num_of_lines == 0 :
           continue
       
        #calculate number of jobs. 
        number_of_tasks = num_of_lines  / int(num_files)
        remainder = num_of_lines  % int(num_files)
    
        start = 0
        for i in range(0, number_of_tasks):
            
            command = " python %s/scan_dataset.py -f %s --num-files %s  --start $d  -l %s"\
                      %(current_dir, file, num_files, start, level) 
               
            start += step
            
            print "created command :" + command
            commands.append(command)
            
        #include remaning files
        command = "python %s/scan_dataset.py -f %s --num-files %d  --start %d -l %s" \
                  %(current_dir, file, remainder, start,  level) 
        
        
        print "created command : %s" %(command)
        commands.append(command)
    
        
    #Run each command in localhost.
    number_of_commands = len(commands)
    for i in range(0, number_of_commands): 
        subprocess.call(command[i], shell=True) 
    
    

def scan_files_in_localhost(config, scan_status):
    
    """
    Uses localhost in order to scan files in the filesystem. 
    """
            
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
                command = "python %s/scan_dataset.py -f %s -d %s -l %s"\
                          %(current_dir, filename, dataset_id_item, level) 
                
                
                print "executng : %s" %(command)
                subprocess.call(command, shell=True)
                #os.system(command)
        else :
            command = "python %s/scan_dataset.py -f %s -d %s -l %s" \
                      %(current_dir, filename, dataset_id,  level) 
            
            
            print "executng : %s"  %(command)
            subprocess.call(command, shell=True)                  
                    
    elif scan_status == Script_status.scan_all_dataset_ids :
        dataset_ids = util.find_dataset(filename, "all")       
        
        for key, value in dataset_ids.iteritems():
            dataset_id = key
            command = "python  %s/scan_dataset.py -f %s -d  %s -l %s" %(current_dir, filename, dataset_id, level) 
            
            print "executng : %s" %(command)
            subprocess.call(command, shell=True)   
    elif scan_status == Script_status.scan_filenames_from_file :
        scan_filenames_from_file_in_localhost(config) 
        
 
def main():
        
    """
    Relevant to ticket :
    http://team.ceda.ac.uk/trac/ceda/ticket/23204
    """   

    start = datetime.datetime.now()    
    print "==============================="             
    print "Script started at: %s." %(str(start))
        
    
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
    print "Script ended at : %s  it ran for : %s." \
          %(str(end), str(end - start)) 
    print "==============================="   
    

if __name__ == '__main__':
    main()
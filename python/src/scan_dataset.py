#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>) [-c <path_to_config_dir> | --config <path_to_config_dir>]
  scan_dataset.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id>)
                  (-m <location> | --make-list <location>) [-c <path_to_config_dir> | --config <path_to_config_dir>] 
  scan_dataset.py (-f <filename> | --filename <filename>) (-n <n_files> | --num-files <n_files>) (-s <start_number> | --start <start_number>)
                  (-l <level> | --level <level>) [-c <path_to_config_dir> | --config <path_to_config_dir>] 
  
Options:
  -h --help                           Show this screen.
  --version                           Show version.
  -d --dataset=<dataset_id>           Dataset id.
  -f --filename=<filename>            File from where the dataset will be read [default: datasets.ini]. 
  -l --level=<level>                  Level of search:
                                      Level 1: File names and sizes
                                      Level 2: File names, sizes and phenomena (e.g. "air temperature")
                                      Level 3: File names, sizes, phenomena and geospatial metadata.
  -m --make-list=<location>           Stores the list of filenames to a file.
  -c --config=<path_to_config_dir>    Specify the main configuration directory.
  -n --num-files=<n_files>            Number of files to scan.
  -s --start=<start_number>           Starting point within the cache file containing filenames [default: 10].
  
 """

import os

from docopt import docopt

import ceda_di.util.util as util
from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract_seq
from ceda_di.index import BulkIndexer
from ceda_di.search import Searcher
from operator import or_

import glob
import logging
import logging.handlers
import datetime   
from enum import Enum



Script_status = Enum( "Script_status",
                      "search_dir_and_store_names_to_file \
                       search_dir_and_store_metadata_to_db \
                       read_file_paths_and_store_metadata_to_db\
                      "
                    )

def ckeck_args_validity(args_dict):
    
    """
    checks the validity of command line arguments
    :param dictionary containing ags.
    :returns:
    """
    level = int(args_dict.get("level"))
    if level < 1  or level > 3:
        raise NameError('value out of range')
 
    num_files = args_dict.get("num-files")
    if num_files:
        num_files = int(num_files)
         
    start_number = args_dict.get("start")
    if start_number:
        start_number = int(args_dict.get("start"))
       
    #TODO : Add more cases here...    

def scan_dir_and_store_metadata_to_db(conf):
    
    """
    Reads files from a specific directory in filesystem 
    and outputs metadata to elastic search database.    
    """     
    extract = Extract_seq(conf)
    extract.run_seq();
      
              
def scan_dir_and_store_filenames_to_file(conf):
    
    """
    Reads files from a specific directory in filesystem 
    and stores their filenames and path to a file.
    """ 
    extract = Extract_seq(conf)
    extract.store_filenames_to_file();         
                
        
def read_file_paths_and_store_metadata_to_db(conf) :
    
    """
    Reads file paths form a given file, extracts metadata 
    for each file and posts results to elastic search.  
    """
                          
    extract = Extract_seq(conf)
    extract.run_seq();      
      
        
def set_program_op_status_and_defaults(conf_args):
    
    """
    Set global variables that determine the operations to be performed. 
    """
     
    status_and_defaults = []   
    # Searches for the configuration file.
    if 'config' not in conf_args or not conf_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_di.json")
        conf_args["config"] = conf_path

    #Creates a dictionary with default settings some of them where loaded from th edefaults file.
    config = util.get_settings(conf_args["config"], conf_args)

    status_and_defaults.append(config)
       
    if ("make-list" in conf_args) and ("dataset" in conf_args) and  ("filename" in conf_args) :
        status_and_defaults.append(Script_status.search_dir_and_store_names_to_file)
    elif  ("dataset" in conf_args) and  ("filename" in conf_args) and ("level" in conf_args) :
        status_and_defaults.append(Script_status.search_dir_and_store_metadata_to_db)  
    elif  ("filename" in conf_args) and ("start" in conf_args) and \
          ("num-files" in conf_args) and ("level" in conf_args)  :     
        status_and_defaults.append(Script_status.read_file_paths_and_store_metadata_to_db)        
    
    
    return status_and_defaults 
    
    
def main():
        
    """
    Relevant to ticket :
    http://team.ceda.ac.uk/trac/ceda/ticket/23203
    """   
    start = datetime.datetime.now()              
    print "Script started at:" +str(start) +".\n." 
    
    
    #Get command line arguments. 
    conf_args = util.sanitise_args(docopt(__doc__, version=__version__))        
       
    #Insert defaults
    status_and_defaults = set_program_op_status_and_defaults(conf_args)      
    
    config_file = status_and_defaults[0] 
    status = status_and_defaults[1]
    
    #Manage the options given. 
    if status == Script_status.search_dir_and_store_names_to_file :
        scan_dir_and_store_filenames_to_file(config_file)
    elif status == Script_status.search_dir_and_store_metadata_to_db :
        scan_dir_and_store_metadata_to_db(config_file)     
    elif status == Script_status.read_file_paths_and_store_metadata_to_db :
        read_file_paths_and_store_metadata_to_db(config_file)           
     
    end = datetime.datetime.now()    
    print "Script ended at :" + str(end) + " it ran for :" + str(end - start) + ".\n"
        
if __name__ == '__main__':
    main()
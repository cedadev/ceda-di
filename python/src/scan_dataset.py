#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>) [-c <path_to_config_dir> | --config <path_to_config_dir>]
  scan_dataset.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id>)
                  (-m <location> | --make-list <location>) [-c <path_to_config_dir> | --config <path_to_config_dir>] 
  scan_dataset.py (-f <filename> | --filename <filename>) [-n <n_files> | --num-files <n_files>] [-s <start_number> | --start <start_number>]
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
  -s --start=<start_number>           Starting point within the cache file containing filenames.  
 """

import os

from docopt import docopt

import ceda_di.util.util as util
from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import ExtractSeq
from ceda_di.index import BulkIndexer
from ceda_di.search import Searcher
from operator import or_

import glob
import logging
import logging.handlers
import datetime   
from enum import Enum
import sys
from Cython.Shadow import NULL


def ckeck_com_args_validity(config, status):
    
    """
    checks the validity of command line arguments
    """
    
    if status == util.Script_status.search_dir_and_store_names_to_file :
        return
        
    level = int(config.get("level")) 
        
    if level < 1  or level > 3:
        raise ValueError("Level value is out of range, please use value between 1-3.")   
           
    
def scan_dir_and_store_metadata_to_db(conf, status):
    
    """
    Reads files from a specific directory in filesystem 
    and outputs metadata to elastic search database.    
    """     
    extract = ExtractSeq(conf, status)
    extract.run_seq();      
      
              
def scan_dir_and_store_filenames_to_file(conf, status):
    
    """
    Reads files from a specific directory in filesystem 
    and stores their filenames and path to a file.
    """ 
    extract = ExtractSeq(conf, status)
    extract.store_filenames_to_file();                
   
        
def read_file_paths_and_store_metadata_to_db(conf, status) :
    
    """
    Reads file paths form a given file, extracts metadata 
    for each file and posts results to elastic search.  
    """
                          
    extract = ExtractSeq(conf, status)
    extract.run_seq();      
    
        
def set_program_op_status_and_defaults(com_args):
    
    """
    Set global variables that determine the operations to be performed. 
    """
     
    status_and_defaults = []   
    # Searches for the configuration file.
    if 'config' not in com_args or not com_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_fbs.ini")
        com_args["config"] = conf_path

    #Creates a dictionary with default settings some of them where loaded from th edefaults file.
    config = util.get_settings(com_args["config"], com_args)
    
    
    #Set defaults if not supplied by user.
    if "start" not in config or not config["start"]:
        config["start"] = config["scanning"]["start"]        
    if "num-files" not in config or not config["num-files"]:
        config["num-files"] = config["scanning"]["num-files"]    
 
    status_and_defaults.append(config)
       
    if ("make-list" in config) and ("dataset" in config) and  ("filename" in config) :
        status_and_defaults.append(util.Script_status.search_dir_and_store_names_to_file)
    elif  ("dataset" in config) and  ("filename" in config) and ("level" in config) :
        status_and_defaults.append(util.Script_status.search_dir_and_store_metadata_to_db)  
    elif  ("filename" in config) and ("start" in config) and \
          ("num-files" in config) and ("level" in config)  :     
        status_and_defaults.append(util.Script_status.read_file_paths_and_store_metadata_to_db)        
    
    
    return status_and_defaults     
    
    
def main():
        
    """
    Relevant ticket : http://team.ceda.ac.uk/trac/ceda/ticket/23203
    """   
      
    #Get command line arguments. 
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))        
           
    #Insert defaults
    status_and_defaults = set_program_op_status_and_defaults(com_args)   
   
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
    if status == util.Script_status.search_dir_and_store_names_to_file :
        scan_dir_and_store_filenames_to_file(config, status)
    elif status == util.Script_status.search_dir_and_store_metadata_to_db :
        scan_dir_and_store_metadata_to_db(config, status)     
    elif status == util.Script_status.read_file_paths_and_store_metadata_to_db :
        read_file_paths_and_store_metadata_to_db(config, status)           
     
    end = datetime.datetime.now()    
    print "Script ended at : %s it ran for : %s" %(str(end), str(end - start))
        
        
if __name__ == '__main__':
    main()
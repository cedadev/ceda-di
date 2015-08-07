#!/usr/bin/env python

"""
Usage:
  scan_dataset.py -h | --help
  scan_dataset.py --version
  scan_dataset.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>) 
                  [-m | --make-list]  
                  [-c <path_to_config_dir> | --config <path_to_config_dir>] 
                  [-n <n_files> | --num-files <n_files>] 
                  [-s <start_number> | --start <start_number>]
  
Options:
  -h --help                           Show this screen.
  --version                           Show version.
  -d --dataset=<dataset_id>           Dataset id.
  -f --filename=<filename>            File from where the dataset will be read [default: datasets.ini]. 
  -l --level=<level>                  Level of search:
                                      Level 1: File names and sizes
                                      Level 2: File names, sizes and phenomena (e.g. "air temperature")
                                      Level 3: File names, sizes, phenomena and geospatial metadata.
  -m --make-list                      Stores the list of filenames to a file [default: file_lists.txt].
  -c --config=<path_to_config_dir>    Specify the main configuration directory.
  -n --num-files=<n_files>           Number of files to scan.
  -s --start=<start_number>           Starting point within the cache file containing filenames [default: 10].
  
 """

import os

from docopt import docopt

import ceda_di.util.cmd as cmd
from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract
from ceda_di.index import BulkIndexer
from ceda_di.search import Searcher
from operator import or_

import glob
import logging
import logging.handlers   


def sd_args_validity_ckeck(args_dict):
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

def sd_find_dataset(file, dataset_id):
    """
     Returns the path of the given dataset id. 
    """
    vars = {}
    with open(file) as l_file:
        for line in l_file:
            name, var = line.partition("=")[::2]
            vars[name.strip()] = var.strip()
    
    return vars[dataset_id]        

def sd_scan_and_store_to_db(conf_args):
    
    """
    Reads files from the filesystem and outputs metadata to database.
    """
         
    # Searches for the configuration file.
    if 'config' not in conf_args or not conf_args["config"]:
        direc = os.path.dirname(__file__)
        conf_path = os.path.join(direc, "../config/ceda_di.json")
        conf_args["config"] = conf_path

    #Creates a dictionary with default settings some of them where loaded from th edefaults file.
    config = cmd.get_settings(conf_args["config"], conf_args)

    # Finds the directory to be scanned 
    dataset_ids_file_path = conf_args.get("filename")
    dataset_id = conf_args.get("dataset")
    path = sd_find_dataset(dataset_ids_file_path, dataset_id) #derectory where the files to be searched are.
    
    # Extracts metadata and stores then in elastic search.
    search_level = conf_args.get("level")
    if dataset_ids_file_path and dataset_id and search_level :
        extract = Extract(config, path, "seq")
        extract.run_seq(search_level);    
    
def main():
    
    """
    Basic algorithm :
        Validate input
        Locate directory to be scanned
        Create file list
        Extract data
        Post data to elastic search.. 
    """            
   
    conf_args = cmd.sanitise_args(docopt(__doc__, version=__version__))
        
         
    try: 
        sd_args_validity_ckeck(conf_args)
    except ValueError as verr:
        log.error("Error in configuration.")
        return  
    except Exception as ex:
        log.error("Error in configuration")
        return 
            
    sd_scan_and_store_to_db(conf_args)    
               
        
if __name__ == '__main__':
    main()
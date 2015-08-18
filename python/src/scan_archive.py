#!/usr/bin/env python

"""
Usage:
  scan_archive.py --help
  scan_archive.py --version
  scan_archive.py (-f <filename> | --filename <filename>) (-d <dataset_id> | --dataset <dataset_id> ) 
                  (-l <level> | --level <level>)  (-h <hostname> | --host <hostname>) [--num-processes <number_of_processes>] 
                  [-n <n_files> | --num-files <n_files>] [-c <path_to_config_dir> | --config <path_to_config_dir>] 
                  
  
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
  --num-files=<n_files>                   Number of files to scan.
  -h --host=<hostname>                       The name of the host where the script will run.
  -n --num-processes=<number_of_processes>   Number of processes to use.
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


 
def main():
        
    """
    Relevant to ticket :
    http://team.ceda.ac.uk/trac/ceda/ticket/23204
    """   

    print "Script started.\n." 
    
    #Get command line arguments. 
    conf_args = util.sanitise_args(docopt(__doc__, version=__version__))        
  
    #Get command line arguments. 
    
    print "Script ended.\n"


if __name__ == '__main__':
    main()
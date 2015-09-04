#!/usr/bin/env python

"""
Usage:
  make_file_lists.py -h | --help
  make_file_lists.py --version
  make_file_lists.py (-f <filename> | --filename <filename>) (-m <location> | --make-list <location>)
                     [-p <number_of_processes> | --num-processes <number_of_processes>]  
Options:
  -h --help                                  Show this screen.
  --version                                  Show version.
  -f --filename=<filename>                   File from where the dataset will be read [default: datasets.ini]. 
  -m --make-list=<location>                  Stores the list of filenames to a file.
  -p --num-processes=<number_of_processes>   Number of processes to use.
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
import sys



Script_status = Enum( "Script_status",
                      "search_dir_and_store_names_to_file \
                       search_dir_and_store_metadata_to_db \
                       read_file_paths_and_store_metadata_to_db\
                      "
                    )


    
    
def main():
        
    """
    Relevant to ticket :
    http://team.ceda.ac.uk/trac/ceda/ticket/23217
    """   
   
    """
     Extract dataset paths from file
     Create list of commands needed in order to create the file containing the paths.
     submit commands to lotus. 
    """
    
   
    start = datetime.datetime.now()              
    print "Script started at:" +str(start) +".\n." 
   
   
    #Get command line arguments. 
    com_args = util.sanitise_args(docopt(__doc__, version=__version__))        
       
    #Insert defaults
    status_and_defaults = set_program_op_status_and_defaults(com_args)      
    
    
    config_file = status_and_defaults[0] 
    status = status_and_defaults[1]
    
     
    end = datetime.datetime.now()    
    print "Script ended at :" + str(end) + " it ran for :" + str(end - start) + ".\n"
        
        
if __name__ == '__main__':
    main()
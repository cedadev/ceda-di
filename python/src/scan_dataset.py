#!/usr/bin/env python
"""
Usage:
    scan_bataset.py (--help | --version)
    scan_dataset.py (-d | --dataset=<dataset_id>)
    scan_dataset.py (-l | --level=<level>)
    scan_dataset.py [-m | --make-list]
    scan_dataset.py [-c | --config=<path_to_config_dir>]
    scan_dataset.py [-n | --num-files=<n_files>]

Options:
    -h --help                 Show this screen.
    -d --dataset=<id>         Specify the dataset to be scanned wirhin the file datasets.ini.
    -l --level=<level>        Specify the Level of information being retrieved about the files in the dataset, as follows:     
                              Level 1: File names and sizes
                              Level 2: File names, sizes and phenomena (e.g. "air temperature")
                              Level 3: File names, sizes, phenomena and geospatial metadata 
                              <level> is an integer of value 1, 2 or 3. 
    -m --makelist=<m>         Make a list of files for the given dataset.
    -c --config=<name>        Specify the main configuration directory.
    -n --num-files=<n_files>  Specify the number of files to scan within each job.    
"""



import os

from docopt import docopt

import ceda_di.util.cmd as cmd
from ceda_di import __version__  # Grab version from package __init__.py
from ceda_di.extract import Extract
from ceda_di.index import BulkIndexer
from ceda_di.search import Searcher


def main():
    conf_args = cmd.sanitise_args(docopt(__doc__, version=__version__))
    
    if 'level' not in conf_args or not conf_args["level"]:
        quit
    else:
         for keys,values in conf_args.items():
             print(keys)
             print(values)  
        
if __name__ == '__main__':
    main()
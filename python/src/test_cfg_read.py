#!/usr/bin/env python

#29/09/2015 Test code delete after done.       
import netCDF4
import json
import os

import ConfigParser

from ceda_di.file_handlers.netcdf_file import NetCDFFile  
from elasticsearch import Elasticsearch
 
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
    options_dict = {}
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
                options_dict[option] = parsed_value
                if options_dict[option] == -1:
                    options_dict[option] = None
            except:
                options_dict[option] = None

        conf[section] = options_dict.copy()
        options_dict.clear()

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

def main():

    es = Elasticsearch()

    print "script started."


    conf_path2 =  "/home/kleanthis/Dev/python_dev/ceda-di/python/config/ceda_di.ini"
    conf = cfg_read(conf_path2)

    print conf

    #Repeat for the next file.
    #ob = NetCDFFile("/home/kleanthis/Dev/test_data_files/evspsblveg_Lmon_HadCM3_past1000_r1i1p1_085001-185012.nc")

    #doc = ob.get_properties_netcdf() 

    #res = es.index(index="test-index1", doc_type='test-type1', id=1, body=doc)


if __name__ == '__main__':
    main()
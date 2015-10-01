#!/usr/bin/env python

#29/09/2015 Test code delete after done.       
import netCDF4
import json

from ceda_di.file_handlers.netcdf_file import NetCDFFile  
from elasticsearch import Elasticsearch
 
def main():
    
    es = Elasticsearch()   
    
    print "script started."  
        
    #Create objecr.     
    ob = NetCDFFile("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc")
        
    #Get properties.    
    doc = ob.get_properties_netcdf()
              
    #Index properties.          
    res = es.index(index="test-index", doc_type='test-type', id=1, body=doc)
    
    
    #Repeat for the next file.
    ob = NetCDFFile("/home/kleanthis/Dev/test_data_files/evspsblveg_Lmon_HadCM3_past1000_r1i1p1_085001-185012.nc")
    
    doc = ob.get_properties_netcdf() 
            
    res = es.index(index="test-index1", doc_type='test-type1', id=1, body=doc)
       

if __name__ == '__main__':
    main()
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
    #ob = NetCDFFile("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc")
        
    #Get properties.    
    #doc = ob.get_properties_netcdf()
              
    #Index properties.     
    
    #basic info
    file_info = {}    
    file_info["file_size"]  = "some_size"
    file_info["location"] = "some_location"
    
    
    #nested section phenomeno 1:
    phenomeno1 = {}    
    phenomeno_parameters1  = {}
   
    #the phenomeno and its name.
    phenomeno1["name_of_phenomeno"]  = "some_phenomeno_name"
    
    phenomeno1_parameters_list = []
    phenomeno1_parameters1 = {}    
    phenomeno1_parameters2 = {}    
    phenomeno1_parameters3 = {}
            
    #the parameters of teh phenomeno.
    phenomeno1_parameters1["name_of_param1"] = "some_param_name1"
    phenomeno1_parameters1["value_of_param1"] = "some_param_name1"
    
    phenomeno1_parameters2["name_of_param2"] = "some_param_name2"
    phenomeno1_parameters2["value_of_param2"] = "some_param_name2"
    
    phenomeno1_parameters3["name_of_param3"] = "some_param_name3"
    phenomeno1_parameters3["value_of_param3"] = "some_param_name3"
   
   
    phenomeno1_parameters_list.append(phenomeno1_parameters1)
    phenomeno1_parameters_list.append(phenomeno1_parameters2)
    phenomeno1_parameters_list.append(phenomeno1_parameters3)
   
    phenomeno1["parameters"]  = phenomeno1_parameters_list
         
   
    #phenomeno 2 :
    #nested section
    phenomeno2   = {}
    phenomeno2_parameters  = {}
   
    #the phenomeno and its name.
    phenomeno2["name_of_phenomeno"]  = "some_phenomeno_name"
    
    phenomeno2_parameters_list = []
    phenomeno2_parameters1 = {}    
    phenomeno2_parameters2 = {}    
    phenomeno2_parameters3 = {}
            
    #the parameters of teh phenomeno.
    phenomeno2_parameters1["name_of_param1"] = "some_param_name1"
    phenomeno2_parameters1["value_of_param1"] = "some_param_name1"
    
    phenomeno2_parameters2["name_of_param2"] = "some_param_name2"
    phenomeno2_parameters2["value_of_param2"] = "some_param_name2"
    
    phenomeno2_parameters3["name_of_param3"] = "some_param_name3"
    phenomeno2_parameters3["value_of_param3"] = "some_param_name3"
   
         
    phenomeno2_parameters_list.append(phenomeno2_parameters1)
    phenomeno2_parameters_list.append(phenomeno2_parameters2)
    phenomeno2_parameters_list.append(phenomeno2_parameters3)
    
    
    phenomeno2["parameters"]  = phenomeno2_parameters_list
    
    all_phenomena = []  
    
    all_phenomena.append(phenomeno1) 
    all_phenomena.append(phenomeno2) 
    
    
    #final request   
    json_doc = {}  
    json_doc["info"] = file_info 
    json_doc["Phenomena"] = all_phenomena    
        
        
    doc = json.dumps(json_doc)
     
    print doc 
                
    res = es.index(index="archive_level_1", doc_type='file', id=1, body=doc)
    
    
    #Repeat for the next file.
    #ob = NetCDFFile("/home/kleanthis/Dev/test_data_files/evspsblveg_Lmon_HadCM3_past1000_r1i1p1_085001-185012.nc")
    
    #doc = ob.get_properties_netcdf() 
            
    #res = es.index(index="test-index1", doc_type='test-type1', id=1, body=doc)
       

if __name__ == '__main__':
    main()
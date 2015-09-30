#!/usr/bin/env python

#29/09/2015 Test code delete after done.       
import netCDF4
import json

from ceda_di.file_handlers.netcdf_file import NetCDFFile  
from elasticsearch import Elasticsearch
 
def main():
    
    es = Elasticsearch()   
    
    print "script started."  
         
    ob = NetCDFFile()
    
    doc_basic = ob.get_properties("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc")
    doc = ob.phenomena("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc") 
    
    final_dict = {}
    ext_dict = {}
    for item in doc:
         for inner_item in item.get() :
             key = inner_item["name"]
             value = inner_item["value"]
             ext_dict[key] = value
        
    final_dict["basic_file_info"] = doc_basic
    final_dict["variables_info"] = ext_dict 
    
       
    res = es.index(index="test-index", doc_type='test-type', id=1, body=final_dict)
    
    #print(res['created'])
    
    doc = ob.phenomena("/home/kleanthis/Dev/test_data_files/evspsblveg_Lmon_HadCM3_past1000_r1i1p1_085001-185012.nc") 
    
    final_dict = {}
    for item in doc:
         for inner_item in item.get() :
             key = inner_item["name"]
             value = inner_item["value"]
             final_dict[key] = value
        
    res = es.index(index="test-index1", doc_type='test-type1', id=1, body=final_dict)
    
    
    
    #res = es.search(index="test-index", body={"query": {"match_all": {}}})
    #print("Got %d Hits:" % res['hits']['total'])
    
    #for hit in res['hits']['hits']:
    #   print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
            
    #print "script ended" + str(res)


if __name__ == '__main__':
    main()
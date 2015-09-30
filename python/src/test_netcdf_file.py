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
    
    doc = ob.phenomena("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc") 
    
    res = es.index(index="test-index", doc_type='test-type', id=1, body=doc)
    
    print(res['created'])
    
    
    res = es.search(index="test-index", body={"query": {"match_all": {}}})
    print("Got %d Hits:" % res['hits']['total'])
    
    for hit in res['hits']['hits']:
        print("%(timestamp)s %(author)s: %(text)s" % hit["_source"])
            
    print "script ended" + str(res)


if __name__ == '__main__':
    main()
#!/usr/bin/env python

#29/09/2015 Test code delete after done.       
import netCDF4
import json

from ceda_di.file_handlers.netcdf_file import NetCDFFile  
 
def main():
    
    #29/09/2015 Test code delete after done.
    
    print "script started."  
         
    ob = NetCDFFile()
    
    res = ob.phenomena("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc") 
    
     
            
    print "script ended" + str(res)
    
    #TODO : traverse the res list.
    #       Create json or sent direclty to elastic search ?



if __name__ == '__main__':
    main()
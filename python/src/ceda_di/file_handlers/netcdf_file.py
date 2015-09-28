import logging
import os
import ntpath
import json
import netCDF4

from generic_file import GenericFile 
from ceda_di.metadata import product

class   NetCDFFile(GenericFile):
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self):             
        GenericFile.__init__(self) 
                
    def phenomena(self, ncdf):
    
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :returns list: List of metadata.product.Parameter objects
        """
        
        phens = []
        for v_name, v_data in ncdf.variables.iteritems():
            phen = product.Parameter(v_name, v_data.__dict__)
            phens.append(phen )

        return phens
        
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
    
    
def main():

    print "script started."  
         
    ob = NetCDFFile()
    
    with netCDF4.Dataset("/home/kleanthis/Dev/test_data_files/hus_cfDay_MPI-ESM-LR_1pctCO2_r1i1p1_19750101-19751231.nc") as ncdf:
        res = ob.phenomena(ncdf)        

    
            
    print "script ended"

if __name__ == '__main__':
    main()
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
         
                
    def phenomena(self, file_path):
    
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :returns list: List of metadata.product.Parameter objects
        """        
        
        with netCDF4.Dataset(file_path) as netcdf_object:
            phens = []
            for v_name, v_data in netcdf_object.variables.iteritems():
                phen = product.Parameter(v_name, v_data.__dict__)
                phens.append(phen)

        return phens        
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
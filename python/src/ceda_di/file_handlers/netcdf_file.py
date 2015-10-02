import logging
import os
import ntpath
import json

import netCDF4


from generic_file import GenericFile 
from ceda_di.metadata import product

class   NetCDFFile(GenericFile):
    """
    Simple class for returning basic information about a file about the content
    of an NetCDF file.
    """
              
    def __init__(self, file_path):             
        GenericFile.__init__(self,file_path)
        
    def phenomena(self):
    
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :returns list: List of metadata.product.Parameter objects
        """        
        
        with netCDF4.Dataset(self.file_path) as netcdf_object:
            phens = []
            for v_name, v_data in netcdf_object.variables.iteritems():
                phen = product.Parameter(v_name, v_data.__dict__)
                phens.append(phen)

        return phens  
    
    
    def get_properties_netcdf(self):
        """
           Returns a dict containig information about the properties of a netcdf file
           and its contents.            
        """
        
        file_info = self.get_properties()
        netcdf_phenomena = self.phenomena() 
                        
        all_param = []               
        for item in netcdf_phenomena :              
            for inet_item in item.get() :  
               all_param.append(inet_item)
               
               
                             
        summary_info = {}        
        summary_info["info"] = file_info
        
        
        summary_info["phenomena"] = all_param
    
       
        return summary_info      
              
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
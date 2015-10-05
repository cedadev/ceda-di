import logging
import os
import ntpath
import json

import netCDF4


from generic_file import GenericFile 
from ceda_di.metadata import product

class   NetCDFFile(GenericFile):
    """
    Simple class for returning basic information about the content
    of an NetCDF file.
    """
              
    def __init__(self, file_path):             
        GenericFile.__init__(self,file_path)
        
    def phenomena(self):
    
        """
        Construct list of Phenomena based on variables in NetCDF file.
        :returns : List of metadata.product.Parameter objects.
        """        
        
        with netCDF4.Dataset(self.file_path) as netcdf_object:
            phens = []
            for v_name, v_data in netcdf_object.variables.iteritems():
                phen = product.Parameter(v_name, v_data.__dict__)
                phens.append(phen)

        return phens  
    
    
    def get_properties_netcdf(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index.            
        """
        
        file_info = self.get_properties()
        netcdf_phenomena = self.phenomena() 
                        
        all_phenomena = []
        phenomeno_params_and_name = {}
               
        for item in netcdf_phenomena :                                      #get all parameter objects.            
              
            phenomeno_params_and_name["phenomeno_name"] = item.get_name()   #get phenomena name. 
            phenomeno_params_and_name["phenomeno_parameters"] = item.get()  #get phenomena params.
            
            all_phenomena.append(phenomeno_params_and_name.copy())
            phenomeno_params_and_name.clear()
        
                             
        summary_info = {}        
        summary_info["info"] = file_info        
        
        summary_info["phenomena"] = all_phenomena    
       
        return summary_info      
              
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
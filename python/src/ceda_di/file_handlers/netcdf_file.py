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
        
        doc_file_info    = self.get_properties()
        doc_content_info = self.phenomena() 
        unknown_vars = []    
            
        file_content_dict = {}
        for item in doc_content_info:
            for inner_item in item.get() :
                key = inner_item["name"]
                value = inner_item["value"]
                if key in self.netcdf_common_variables :
                    file_content_dict[key] = value
                else :
                    unknown_vars.append(key)
                    unknown_vars.append(" : ")    
                    unknown_vars.append(value)
                    unknown_vars.append(" ")
         
        if len(unknown_vars) > 0 :            
            unknown_vars_str = ""
                
            file_content_dict["unknown_vars"] = unknown_vars_str.join(unknown_vars)
            
                     
        file_summary_dict = {}        
        file_summary_dict["basic_file_info"] = doc_file_info
        file_summary_dict["netcdf_variables_info"] = file_content_dict 
    
       
        return file_summary_dict      
              
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
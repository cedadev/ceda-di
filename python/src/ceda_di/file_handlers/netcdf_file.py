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
    
    
    def get_properties_level2(self):
        """
        Wrapper for method phenomena().
        :returns:  A dict containing information compatible with current es index.            
        """
        
        file_info = self.get_properties_level1()
        netcdf_phenomena = self.phenomena() 
                        
        phenomena_list = []
         
        var_id_dict = {}
        phenomenon_parameters_dict = {}
               
        for item in netcdf_phenomena :                                      #get all parameter objects.            
              
            name = item.get_name()   #get phenomena name.             
                
            var_id_dict["name"] = "var_id"
            var_id_dict["value"] = name            
                
            list_of_phenomenon_parameters = item.get()
            list_of_phenomenon_parameters.append(var_id_dict.copy())            
            phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters 
                                   
            phenomena_list.append(phenomenon_parameters_dict.copy())
        
            var_id_dict.clear()
            phenomenon_parameters_dict.clear()
         
                             
        #summary_info = {}        
        #summary_info["info"] = file_info        
        #summary_info["phenomena"] = phenomena_list    
         
        file_info["phenomena"] = phenomena_list
              
        #doc = json.dumps(summary_info) 
        #print summary_info
              
        return file_info      
              
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
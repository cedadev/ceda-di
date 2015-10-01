import logging
import os
import ntpath
import json

class  GenericFile(object):
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self, file_path):      
        self.file_path = file_path
        
        self.netcdf_common_variables = set(
                                     [
                                       "_FillValue", 
                                       "associated_files",
                                       "axis", 
                                       "bounds",
                                       "calendar",
                                       "cell_measures",
                                       "cell_methods",
                                       "formula",
                                       "formula_terms",
                                       "history",
                                       "long_name",
                                       "missing_value",
                                       "positive",
                                       "standard_name",
                                       "units"
                                     ]
                                   )                  
                
                
    def get_properties(self):
        """
         Scans the given file and returns information about the file not the content.
        :returns: A dict containing a summary information.
        """         
                
        if self.file_path is None:
            return None
        
        #check if file still exists.  
        file_exists = os.path.isfile(self.file_path) 
        
        if not file_exists :
            return None      
                                               
        is_symlink = os.path.islink(self.file_path)
        
        #kltsa 16/09/2015 change for issue 23214 : symbolic link files will be ignored.
        if is_symlink :
            return None  
                
        doc = {}        
                
        #This is a regular file.       
        doc["directory"] = os.path.dirname(self.file_path)
        doc["format"] = "data file"
        doc["md5"] = ""
        
        filename = os.path.basename(self.file_path) #ntpath.basename(file_path)
        doc["name"] = filename 
        
        #self.subdoc[input] = filename
        
        #subval = json.dumps(self.subdoc)
             
        doc["name_auto"] = filename    
        
        
        size = os.path.getsize(self.file_path)
        size_h = size/(1024*1024.0)
        doc["size"] = size_h
        doc["type"] = "file"              
        
        return doc
              
              
              
    def get_properties_generic(self):           
        #Extra information.
        netcdf_file_content_dict = {}
        for item in set(self.netcdf_common_variables):
            netcdf_file_content_dict[item] = ""
               
        netcdf_file_content_dict["unknown_vars"] = ""       
        
        
        summary_info = {}        
        summary_info["basic_file_info"] = self.get_properties()
        summary_info["netcdf_variables_info"] = netcdf_file_content_dict 
    
                           
        return summary_info
        
                   
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
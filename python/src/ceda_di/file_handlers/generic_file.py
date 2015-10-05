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
                
        file_info = {}        
                
        #This is a regular file.       
        file_info["directory"] = os.path.dirname(self.file_path)
        file_info["format"] = "data file"
        file_info["md5"] = ""
        
        filename = os.path.basename(self.file_path) #ntpath.basename(file_path)
        file_info["name"] = filename 
        
        #self.subdoc[input] = filename
        
        #subval = json.dumps(self.subdoc)
             
        file_info["name_auto"] = filename    
        
        
        size = os.path.getsize(self.file_path)
        size_h = size/(1024*1024.0)
        file_info["size"] = size_h
        file_info["type"] = "file"              
        
        return file_info              
      
    def get_properties_generic(self):
        
        file_info = self.get_properties()          
          
        if file_info is None :
            return None
                                 
        summary_info = {}        
        summary_info["info"] = file_info
        
        phenomeno_params_and_name = {}        
        phenomeno_params_and_name["phenomeno_name"] = "File_without_phenomena"   
        phenomeno_params_and_name["phenomeno_parameters"] = [{"name" : "None", "value" : "None"}]  
                
        summary_info["phenomena"] = phenomeno_params_and_name 
            
        return summary_info    
            
                   
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
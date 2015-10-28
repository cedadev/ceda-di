import logging
import os
import ntpath
import json

class  GenericFile(object):
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self, file_path, level):      
        self.file_path = file_path
        self.level = level
        self.handler_id = None        
                
                
    def get_handler_id(self):
        return self.handler_id
                    
    def get_properties_generic_level1(self):
        """
         Scans the given file and returns information about the file not the content.
        :returns: A dict containing a summary information.
        """         
         
        self.handler_id = "Generic level 1." 
                
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
        info = {}        
                
        #This is a regular file.       
        info["directory"] = os.path.dirname(self.file_path)
        info["format"] = "data file"
        info["md5"] = ""
        
        filename = os.path.basename(self.file_path) #ntpath.basename(file_path)
        info["name"] = filename 
        
        #self.subdoc[input] = filename
        
        #subval = json.dumps(self.subdoc)
             
        info["name_auto"] = filename    
        
        
        size = os.path.getsize(self.file_path)
        size_h = size/(1024*1024.0)
        info["size"] = size_h
        info["type"] = "file"              
        
        file_info["info"] = info
         
        return file_info              
      
    def get_properties_generic_level2(self):
        
        """
         Wrapper for method get_properties().
        :returns: A dict containing information compatible with current es index.
        """ 
               
        file_info = self.get_properties_generic_level1()          
       
        self.handler_id = "Generic level 2."
            
        if file_info is None :
            return None
         
        #creates the nested json structure.        
        phenomenon_parameters_dict = {}
        var_id_dict = {}
        var_id_dict["name"] = "var_id"
        var_id_dict["value"] = "None"            
                
        list_of_phenomenon_parameters = []
        list_of_phenomenon_parameters.append(var_id_dict.copy())            
                                
        phenomenon_parameters_dict["phenomenon_parameters"] = list_of_phenomenon_parameters 
        phenomena_list = [] 
        phenomena_list.append(phenomenon_parameters_dict.copy())
           
         
        file_info["phenomena"] = phenomena_list 
                             
        return file_info    
    
    def get_properties(self):
        
        if self.level =="1" :
            return self.get_properties_generic_level1()  
        elif self.level  == "2" :
            return self.get_properties_generic_level2()
                   
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
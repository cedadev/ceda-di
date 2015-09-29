import logging
import os
import ntpath
import json

class  GenericFile(object):
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self):      
        self.doc={}
        self.subdoc={}        
                
    def get_properties(self, file_path):
        """
         Scans the given file and returns information about its properties and data.
        :returns: A dict containing a summary information.
        """         
                
        if file_path is None:
            return None
        else : 
            self.file_path = file_path
        
        #check if file still exists.  
        file_exists = os.path.isfile(file_path) 
        
        if not file_exists :
            return None      
                                               
        is_symlink = os.path.islink(file_path)
        
        #kltsa 16/09/2015 change for issue 23214 : symbolic link files will be ignored.
        if is_symlink :
            return None  
        
        #This is a regular file.       
        self.doc["directory"] = os.path.dirname(file_path)
        self.doc["format"] = "data file"
        self.doc["md5"] = ""
        
        filename = os.path.basename(file_path) #ntpath.basename(file_path)
        self.doc["name"] = filename 
        
        #self.subdoc[input] = filename
        
        #subval = json.dumps(self.subdoc)
             
        self.doc["name_auto"] = filename    
        
        
        self.size = os.path.getsize(file_path)
        self.size_h = self.size/(1024*1024.0)
        self.doc["size"] = self.size_h
        self.doc["type"] = "file"              
           
        return self.doc
        
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
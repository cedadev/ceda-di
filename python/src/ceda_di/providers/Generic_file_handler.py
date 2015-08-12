import logging
import os
import ntpath

class GENERIC:
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self):      
        self.doc={}
        
            
    def get_properties(self, file_path=None):
        """
        :returns: A dict containing a summary of the file's data.
        """         
        
        if file_path is None :
            return
        
        
        
        self.doc["directory"] = os.path.dirname(file_path)
        self.doc["format"] = "data file"
        self.doc["md5"] = ""
        
        filename = os.path.basename(file_path) #ntpath.basename(file_path)
        self.doc["name"] = filename 
        self.doc["autocomplete"] = filename
        
        self.size = os.path.getsize(file_path)
        self.size_h = self.size/(1024*1024.0)
        self.doc["size"] = self.size_h
        
        self.doc["type"] = ("simlink" if os.path.islink(file_path) else "file") 
         
         
                
        return self.doc
    
    def __enter__(self):
        return self
    
    
    def __exit__(self, *args):
        pass
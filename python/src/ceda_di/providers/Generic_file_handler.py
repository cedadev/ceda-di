import logging
import os

class GENERIC:
    """
    Simple class for returning basic information about a file.
    """
          
    def __init__(self, header_path, path=None):
        self.path = path
        self.id = 1
        self.doc={}
        
            
    def get_properties(self, file_path=None):
        """
        :returns: A dict containing a summary of the file's data.
        """         
        
        if file_path is None :
            return
        
        self.doc["directory"] = file_path
        self.doc["format"] = "file"
        self.doc["md5"] = ""
        self.doc["name"] = file_path
        self.size = os.path.getsize(file_path)
        self.doc["size"] = self.size
        self.doc["type"] = "file type"
         
         
                
        return self.doc
    
    def __enter__(self):
        return self
    
    
    def __exit__(self, *args):
        pass
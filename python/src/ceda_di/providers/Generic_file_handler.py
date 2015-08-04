import logging
import os

class GENERIC:
    """
    Class for returning basic file information.
    """
          
    def __init__(self, header_path, path=None):
        self.path = path
        self.id = 1
        self.doc={}
            
    def get_properties(self, file_path):
        """
        :returns: A dict containing a summary of the file's data.
        """
        
        self.doc["filename"] = file_path
        self.size = os.path.getsize(file_path)
        self.doc["size"] = self.size/(1024*1024)
                
        return self.doc
    
    def __enter__(self):
        return self
    
    
    def __exit__(self, *args):
        pass
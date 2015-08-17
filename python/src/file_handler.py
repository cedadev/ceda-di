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
         Scans the given file and returns information about its properties and data.
        :returns: A dict containing a summary information.
        """         
        
        #exclude tmp files.
        if (file_path is None):
            return None
                
        file_exists = True
        is_simlink = True
                        
        #check if file exists  
        is_simlink = os.path.islink(file_path)
        file_exists = os.path.isfile(file_path)
                
        
        if(file_exists or is_simlink):
            #if file exists.
            self.doc["directory"] = os.path.dirname(file_path)
            self.doc["format"] = "data file"
            self.doc["md5"] = ""
        
            filename = os.path.basename(file_path) #ntpath.basename(file_path)
            self.doc["name"] = filename 
            self.doc["autocomplete"] = filename
        
        
            if not is_simlink:
                self.size = os.path.getsize(file_path)
                self.size_h = self.size/(1024*1024.0)
                self.doc["size"] = self.size_h
                self.doc["type"] = "file"              
            else:                 
                self.doc["size"] = 0
                self.doc["type"] = "symlink" 
         
            return self.doc
        else :
            return None        
                
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
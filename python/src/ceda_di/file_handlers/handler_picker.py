import logging
import os
import ntpath
import json
import re
from ceda_di.metadata.product import FileFormatError
import ceda_di.file_handlers.generic_file as generic_file
import ceda_di.file_handlers.netcdf_file as netcdf_file
import magic as magic_number_reader


class  HandlerPicker(object):
    """
    Returns a handler for the supplied file..
    """
          
    def __init__(self, handler_map):      
        self.handler_map = handler_map
        self.handlers = {}
        self.handlers_and_dirs = {}
             
           
       
    def get_handler(self, filename):
        """
        :param filename : the filename to be scanned.
        :returns handler: Returns an appropriate handler 
        for the given file.
        """
        
        handler = None
        #Sanity check.
        #check if file still exists.  
        file_exists = os.path.isfile(filename) 
        
        file_dir = os.path.dirname(filename)
        
        if not file_exists :
            return None      
        
        """
        First use configured handlers then use handlers within 
        FBS project.
        """
            
        #Try configured handler.
        handler = self.get_configured_handler_class(filename)        
                
        if handler is not None :
            self.handlers_and_dirs[file_dir] = handler
            return handler        
        
        #Try returning a handler based on file extension.
        extension = os.path.splitext(filename)[1]
            
        if extension == ".nc" :
            handler = netcdf_file.NetCDFFile
             
            
        if handler is not None :
            self.handlers_and_dirs[file_dir] = handler
            return handler
                
        #Try returning a handler based on file's magic number.        
        res = magic_number_reader.from_file(filename)        
        
        if res  == "NetCDF Data Format data":        
            handler = netcdf_file.NetCDFFile   
            
                
        if handler is not None :
            self.handlers_and_dirs[file_dir] = handler
            return handler
           
        #Try to return last handler used in this directory.      
        handler = self.handlers_and_dirs[file_dir] = handler
        
        if handler is not None :
            return handler
                
        #Nothing worked, return the generic handler.      
        handler = generic_file.GenericFile        
        
        
        return handler            
                 
    
    def get_configured_handlers(self):
        
        for pattern, handler in self.handler_map.iteritems():
            handler_class = handler['class']
            priority = handler['priority']
            
            (module, _class) = handler_class.rsplit(".", 1)
            mod = __import__(module, fromlist=[_class])
            
            self.handlers[pattern] =\
            {
              "class": getattr(mod, _class),
              "priority": priority
            }  
            
    def get_configured_handler_class(self, filename):
        """
        Return the class of the correct file handler (un-instantiated).
        """
        handler_candidates = []  # All handlers whose file signatures match
        for pattern, handler in self.handlers.iteritems():
            if re.search(pattern, filename):
                handler_candidates.append(handler)

        # Sort by priority to ensure the correct class is returned
        # when files match multiple signatures
        handler_candidates.sort(key=lambda h: h['priority'])
        for handler in handler_candidates:
            handler_class = handler['class']
            try:
                handler_class.get_file_format(filename)
                return handler_class
            except FileFormatError as ex:
                self.logger.info("Not using handler {} because {}".format(handler_class, ex.message))
                pass
            except AttributeError:
                return handler_class
        return None          
            
                   
                   
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
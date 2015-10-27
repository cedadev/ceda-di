import os
import ntpath
import json
import re
from ceda_di.metadata.product import FileFormatError

import ceda_di.file_handlers.generic_file as generic_file
import ceda_di.file_handlers.netcdf_file as netcdf_file
import ceda_di.file_handlers.nasaames_file as nasaames_file

import magic as magic_number_reader

import util as util


class  HandlerPicker(object):
    """
    Returns a handler for the supplied file..
    """
          
    def __init__(self, handler_map):      
        self.handler_map = handler_map
        self.handlers = {}
        self.handlers_and_dirs = {}
        self.NETCDF_PYTHON_MAGIC_NUM_RES = "NetCDF Data Format data"
        self.ASCII_PYTHON_MAGIC_NUM_RES = "ASCII text"      
           
       
    def pick_best_handler(self, filename):
        """
        :param filename : the filename to be scanned.
        :returns handler: Returns an appropriate handler 
        for the given file.
        """
        
        handler = None
        """
        Sanity check.
        check if file still exists.  
        """
        
        file_exists = os.path.isfile(filename) 
        
        file_dir = os.path.dirname(filename)
        
        if not file_exists :
            return None                
            
            
        #Try configured handler.
        handler = self.get_configured_handler_class(filename)        
                
        if handler is not None :
            self.handlers_and_dirs[file_dir] = handler
            return handler        
        
        #Try returning a handler based on file extension.
        extension = os.path.splitext(filename)[1]
            
        if extension == ".nc":
            handler = netcdf_file.NetCDFFile
        elif extension == ".na":     
            handler = nasaames_file.NASAAmes 
            
        if handler is not None :
            self.handlers_and_dirs[file_dir] = handler
            return handler
                
        #Try returning a handler based on file's magic number.        
        res = magic_number_reader.from_file(filename)        
        
        if res  == self.NETCDF_PYTHON_MAGIC_NUM_RES:        
            handler = netcdf_file.NetCDFFile 
        elif res == self.ASCII_PYTHON_MAGIC_NUM_RES:
            #ok lets see if it is a na file.
            first_line = util.get_file_header(filename)
            tokens = first_line.split(" ")  
            if tokens[0].isdigit() and tokens[1].isdigit():
                handler = nasaames_file.NASAAmes  
            else:
                handler = generic_file.GenericFile                              
                
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
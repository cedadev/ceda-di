import logging
import os
import ntpath
import json

class  HandlerPicker(object):
    """
    Returns a handler for the supplied file..
    """
          
    def __init__(self, level, handler_map):      
        self.level = level
        self.handlers = {}
        
    def get_handler(self, filename):
        """
        :param filename : the filename to be scanned.
        :returns handler: Returns an appropriate handler 
        for the given file.
        """
        
        """
        First use configured handlers then use handlers within 
        FBS project.
        """
            
        extension = os.path.splitext(self.filename)[1]
                    
        if self.level is "1" :
            handle = generic_file.GenericFile(self.filename)
            return handle.get_properties_level1()
        elif self.level is "2" : 
            handler_class = self.get_handler_class(filename)
            if handler_class is not None:
                return handler_class(filename)    
            else :            
                if extension == ".nc" :
                    handle = netcdf_file.NetCDFFile(self.filename) 
                    #return handle.get_properties_netcdf()
                    return handle.get_properties_level2()
                else :
                    handle = generic_file.GenericFile(self.filename)
                    return handle.get_properties_level2()
            
        return None 
                 
    
    def get_configured_handlers(self, handler_map):
        
        for pattern, handler in handler_map.iteritems():
            handler_class = handler['class']
            priority = handler['priority']
            
            (module, _class) = handler_class.rsplit(".", 1)
            mod = __import__(module, fromlist=[_class])
            
            self.handlers[pattern] =\
            {
              "class": getattr(mod, _class),
              "priority": priority
            }         
                   
    def __enter__(self):
        return self
        
    def __exit__(self, *args):
        pass
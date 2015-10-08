import logging
import os
import ntpath
import json

class  HandlerPicker(object):
    """
    Returns a handler for the supplied file..
    """
          
    def __init__(self, level, handler_map):      
        self.handler_map = handler_map
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
            
        if self.level is "1" :
            handler = generic_file.GenericFile
            return handle
        elif self.level is "2" : 
            
            #Try configured handler:
            handler = get_configured_handler_class(filename)
         
            if handler is not None :
                return handler 
        
            #try to find a handler based on filename.
            else :
                extension = os.path.splitext(self.filename)[1]
            
                if extension == ".nc" :
                    handler = netcdf_file.NetCDFFile 
                    #return handle.get_properties_netcdf()
                    return handler
                else :
                    handler = generic_file.GenericFile
                    return handler
            
        return None 
                 
    
    def get_configured_handlers(self):
        
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
"""
'Extract' module - handles file crawling and metadata extraction.
"""

import datetime
import logging
import logging.config
import multiprocessing
import os
import sys
import re

#kltsa
import requests
import json
import hashlib
import socket
import ceda_di.util.util as util

########
from elasticsearch.exceptions import TransportError

from ceda_di.search import ElasticsearchClientFactory
from ceda_di import index
from ceda_di.metadata.product import FileFormatError
from mhlib import PATH


class HandlerFactory(object):
    """
    Factory for file handler classes.
    """
    def __init__(self, handler_map):
        self.logger = logging.getLogger(__name__)
        self.handlers = {}
        for pattern, handler in handler_map.iteritems():
            handler_class = handler['class']
            priority = handler['priority']
            (module, _class) = handler_class.rsplit(".", 1)
            mod = __import__(module, fromlist=[_class])
            self.handlers[pattern] = {
                "class": getattr(mod, _class),
                "priority": priority
            }

    def get_handler(self, filename):
        """
        Return instance of correct file handler class.
        """
        handler_class = self.get_handler_class(filename)
        if handler_class is not None:
            return handler_class(filename)
        
    def get_handler_by_level(self, level, filename = None):
        """
        Return instance of correct file handler class for 
        the specified level.
        """
        if level is "1" :
            handler = self.handlers[".$"]
            handler_class = handler['class']
            return handler_class() 
        else :
            return None                
        
        """
        handler_class = self.get_handler_class(filename)
        if handler_class is not None:
            return handler_class(filename)
        """
    def get_handler_class(self, filename):
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

class Extract(object):
    """
    File crawler and metadata extractor class.
    Part of core functionality of ceda_di.
    """
    def __init__(self, conf, path=None):
        if conf is None:
            return
        
        try: 
            self.make_dirs(conf)
            self.logger = self.prepare_logging()
            self.handler_factory = HandlerFactory(self.conf("handlers"))
            
            if path is None:
                self.file_list = self._build_file_list()
            else:
                self.file_list = path
        except KeyError as k:
            sys.stderr.write("Missing configuration option: %s\n\n" % str(k))

    def _build_file_list(self):
        """
        Return file list
        :return: A list of file paths
        """            
        path_l = self.conf("input-path")
        followlinks = True
        return util.build_file_list(path_l, followlinks)
          
    def conf(self, conf_opt):
        """
        Return configuration option or raise exception if it doesn't exist.
        :param str conf_opt: The name of the configuration option to find.
        """
        if conf_opt in self.configuration:
            return self.configuration[conf_opt]
        else:
            raise AttributeError(
                "Mandatory configuration option not found: %s" % conf_opt)

    def make_dirs(self, conf):
        """
        Create directories for output files.
        """
        if not conf["no-create-files"]:
            json_out = os.path.join(self.conf("output-path"),
                                    self.conf("json-path"))
            if not os.path.isdir(json_out):
                try:
                    os.makedirs(json_out)
                except OSError:
                    pass  # Directory already exists!

        log_out = os.path.join(self.conf("output-path"), self.conf("log-path"))
        if not os.path.isdir(log_out):
            try:
                os.makedirs(log_out)
            except OSError:
                pass  # Directory already exists!

    def prepare_logging(self):
        """
        Initial logging setup
        """
        log_fname = (self.conf("es-index") + "_" +
                     datetime.datetime.now().isoformat() + "_" +
                     ".log")
        fpath = os.path.join(self.conf("output-path"),
                             self.conf("log-path"),
                             log_fname)

        logging.basicConfig(filename=fpath,
                            format=self.conf("logging")["format"],
                            level=logging.INFO)

        log = logging.getLogger(__name__)        
        return log
           
    def process_file(self, filename):
        """
        Instantiate a handler for a file and extract metadata.
        """
        handler = self.handler_factory.get_handler(filename)
        if handler is not None:
            with handler as hand:
                if self.conf('send-to-index'):
                    self.index_properties(filename, hand)
                if not self.conf('no-create-files'):
                    self.write_properties(filename, hand)

    def index_properties(self, filename, handler):
        """
        Index the file in Elasticsearch
        """
        props = handler.get_properties()
        if props is not None:
            self.es.index(index=self.conf('es-index'),
                          doc_type=self.conf('es-mapping'),
                          body=str(props),
                          id=props.properties["_id"])

    def write_properties(self, fname, _geospatial_obj):
        """
        Write module properties to an output file.
        """
        # Construct JSON path
        fname = os.path.basename(fname)
        json_path = os.path.join(self.conf("output-path"), self.conf("json-path"))
        out_fname = "%s/%s.json" % (json_path, os.path.splitext(fname)[0])

        props = _geospatial_obj.get_properties()
        if props is not None:
            with open(out_fname, 'w') as j:
                j.write(str(props))
                
    def run(self):
        """
        Run main metadata extraction suite.
        """
        # Log beginning of processing
        start = datetime-bg_flat_0_aaaa.datetime.now()
        self.logger.info("Metadata extraction started at: %s",
                         start.isoformat())

        # Create index if necessary
        if self.conf("send-to-index"):
            es_factory = ElasticsearchClientFactory()
            self.es = es_factory.get_client(self.configuration)

            try:
                index.create_index(self.configuration, self.es)
            except TransportError as te:
                if te[0] == 400:
                    pass
                else:
                    raise TransportError(te)

        if len(self.file_list) > 0:
            # Process files
            pool = []

            for f in self.file_list:
                # HDF libraries don't seem to like unicode strings,
                # which the filenames will be if the configuration paths
                # loaded from JSON end up in unicode
                path = f
                if "raw" not in path:
                    p = multiprocessing.Process(target=self.process_file,
                                                args=(path,))
                    pool.append(p)
                    p.start()

                while len(pool) >= self.conf("num-cores"):
                    for p in pool:
                        if p.exitcode is not None:
                            pool.remove(p)

            for p in pool:
                p.join()

        # Log end of processing
        end = datetime.datetime.now()
        self.logger.info("Metadata extraction completed at: %s",
                         end.isoformat())
        self.logger.info("Start: %s, End: %s, Total: %s",
                         start.isoformat(), end.isoformat(), end - start)
    
            
  
#kltsa 14/08/2015 issue #23203.    
class Extract_seq(Extract):    
        
    """
    File crawler and metadata extractor class.
    Part of core functionality of ceda_di.
    """
    def __init__(self, conf):
        
        Extract.__init__(self, None)        
        
        self.configuration = conf
            
        if ("dataset" in self.configuration)  and ("filename" in self.configuration) \
            and ("level" in self.configuration):
            try:            
                self.logger = self.prepare_logging_seq()
                self.handler_factory = HandlerFactory(self.conf("handlers"))
                self.file_list = self._build_file_list_from_path()
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))        
            
        elif ("make-list" in self.configuration) :
            try:            
                self.logger = self.prepare_logging_seq()                         
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))
        
        elif ("start" in self.configuration ) and ("num-files" in self.configuration) :     
            try:            
                self.logger = self.prepare_logging_seq()
                self.handler_factory = HandlerFactory(self.conf("handlers"))
                self.file_list = self._build_list_from_file()
            
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))
    
                         
    def prepare_logging_seq(self):
        """
        Initial logging setup
        """
        
        log_fname = (self.conf("es-index") + "_" +
                     datetime.datetime.now().isoformat() + "_" +
                     socket.gethostname() +
                     ".log")
        
        log_fname_es = (self.conf("es-index") + "_" +
                     datetime.datetime.now().isoformat() + "_" +
                     socket.gethostname() + "_es" +
                     ".log")
        
        
        
        fpath = os.path.join(os.getcwd(),
                             log_fname)
        
        fpath_es = os.path.join(os.getcwd(),
                             log_fname_es)
        
        
        LEVELS = { 'debug'   : logging.DEBUG,
                   'info'    : logging.INFO,
                   'warning' : logging.WARNING,
                   'error'   : logging.ERROR,
                   'critical': logging.CRITICAL
                 }

        conf_log_level = self.conf("log-level")
        
        
        format = self.conf("logging")["format"]
        level = LEVELS.get(conf_log_level, logging.NOTSET)
        logging.basicConfig(filename=fpath,
                        format=format,
                        level=level)
        
        """
        #Also set log level in loger used by elastic search.       
        tracer = logging.getLogger('elasticsearch.trace')
        tracer.setLevel(level)
        tracer.addHandler(logging.FileHandler(fpath_es))
        """
          
        #Enable only logging from within this module.      
        es_log = logging.getLogger("elasticsearch")
        es_log.setLevel(logging.CRITICAL)
        #es_log.addHandler(logging.FileHandler(fpath_es))
        
        urllib3_log = logging.getLogger("urllib3")
        urllib3_log.setLevel(logging.CRITICAL)
        #urllib3_log.addHandler(logging.FileHandler(fpath_es))
        
        
        log = logging.getLogger(__name__)             
              
        return log 
   
    
    def  _build_file_list_from_path(self):
         # Finds the directory to be scanned 
         dataset_ids_file = self.conf("filename")
         dataset_id = self.conf("dataset")
         #derectory where the files to be searched are.
         path_to_files = util.find_dataset(dataset_ids_file, dataset_id) 
         
         return util.build_file_list(path_to_files)
                
        
    def _build_list_from_file(self):
        
        """
        Reads file paths form a given file, extracts metadata 
        for each file and posts results to elastic search.  
        """
            
        file_containing_paths = self.conf("filename")
        start_file = self.conf("start")
        num_of_files = self.conf("num-files")
        
        with open(file_containing_paths) as f:
            content = f.readlines()
            
        self.logger.info( str(len(content)) + " lines read from file " + "\"" + file_containing_paths + "\"." )   
       
        list_len = len(content)
        if int(start_file) < 0 or int(start_file) > list_len :
            self.logger.info("please correct start parameter value.")
            return
            
        end_file = int(start_file) + int(num_of_files)
    
        if end_file > list_len :
            self.logger.info("please correct num-files parameter value.")
            return
   
        file_list = content[int(start_file):end_file] 
    
        new_file_list = []
        for p in file_list:
            new_file_list.append(p.rstrip()) 
             
        return new_file_list       
   
            
    def index_properties_seq(self, body, id):
        """
        Index the file in Elasticsearch.
        """

        try:
            self.es.index(index=self.conf('es-index'),
                      doc_type=self.conf('es-mapping'),
                      body=body,
                      id=id) 
        except :
            return -1 
        
        return 1  
            
    def process_file_seq(self, filename, level):
        """
         Instantiates a handler for a file and is using it to 
         extracts metadata from the file.
        """
        
        handler = self.handler_factory.get_handler_by_level(level)  
          
        if handler is not None:
            with handler as hand:
                return handler.get_properties(filename)    
        else :
            return None       
    
    def store_filenames_to_file(self):
        """
        Reads files from a specific directory in filesystem 
        and stores their filenames and path to a file.
        """ 
              
        dataset_ids_file = self.conf("filename")
        dataset_id = self.conf("dataset")
        path_to_files = util.find_dataset(dataset_ids_file, dataset_id) 
        file_to_store_paths = self.conf("make-list")
        
        self.logger.info("Creating file \"" + file_to_store_paths + "\" with paths to files belonging to" + "\"" + dataset_id + "\" dataset." )
        file_list = util.build_file_list(path_to_files)
        
        util.write_list_to_file(file_list, file_to_store_paths)
        self.logger.info("file \"" + file_to_store_paths + "\" containing paths to files in given dataset has been created.")         
                                          
    def run_seq(self):      
        
        """
         Extracts metadata information from files within the file list
         and posts them in elastic search.
        """
              
        # Create index if necessary
        es_factory = ElasticsearchClientFactory()
        self.es = es_factory.get_client(self.configuration)

        try:
            index.create_index(self.configuration, self.es)
        except TransportError as te:
            if te[0] == 400:
                pass
            else:
                raise TransportError(te)
 
         
        
        doc = {}       
        level = self.conf("level")
        
        if len(self.file_list) > 0:
            
            for file in self.file_list:
                #file_path = f
                
                #self.logger.info("Metadata extraction started for file %s", file_path)
                start = datetime.datetime.now()
                
                doc = self.process_file_seq(file, level)    
                
                if doc is not None :
                                                               
                    es_query = json.dumps(doc)
                    id = hashlib.sha1(file).hexdigest()      
                
                    ret = self.index_properties_seq(es_query, id)
                    
                    end = datetime.datetime.now()
                    
                    self.logger.info( os.path.basename(file) + "|" + os.path.dirname(file)+ "|" 
                              + str(ret) + "|" + str(end - start) + "ms")
                       
                else :
                    end = datetime.datetime.now()
                    self.logger.info( os.path.basename(file) + "|" + os.path.dirname(file)+ "|" 
                              + "0" + "|" + str(end - start) + "ms")
                    continue   
         
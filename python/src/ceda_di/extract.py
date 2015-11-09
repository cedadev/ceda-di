"""
'Extract' module - handles file crawling and metadata extraction.
"""

import datetime
import logging
import logging.config
import os
import sys
import re

import hashlib
import socket
import ceda_di.util.util as util

import ceda_di.util.handler_picker as handler_picker

from elasticsearch.exceptions import TransportError

from ceda_di.search import ElasticsearchClientFactory
from ceda_di import index
from ceda_di.metadata.product import FileFormatError



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
                #pass
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
            self.configuration = conf
            self.make_dirs(conf)
            self.logger = self.prepare_logging()
            self.handler_factory_inst = HandlerFactory(self.conf("handlers"))

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
        return util.build_file_list(path_l)

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
        handler = self.handler_factory_inst.get_handler(filename)
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
        start = datetime.datetime.now()
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
                    #lets do that sequentially

                    self.process_file(path)

                    #p = multiprocessing.Process(target=self.process_file,
                    #                            args=(path,))
                    #pool.append(p)
                    #p.start()

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
class ExtractSeq(Extract):

    """
    File crawler and metadata extractor class.
    Part of core functionality of FBS.
    Files are scanned sequentially (one thread).
    """
    def __init__(self, conf, status):

        Extract.__init__(self, None)

        self.configuration = conf
        self.status = status
        self.logger = None
        self.handler_factory_inst = None
        self.file_list = None
        self.es = None
        #some constants
        self.FILE_PROPERTIES_ERROR = "0"
        self.FILE_INDEX_ERROR = "-1"
        self.FILE_INDEXED = "1"


    def prepare_run(self):

        """
         Prepares login and file list to be scanned.
        """
        if self.status == util.Script_status.SEARCH_AND_STORE_INFO_TO_FILE:
            try:
                self.logger = self.prepare_logging_seq()

                self.file_list = self.build_file_list_from_path()
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))
        elif self.status == util.Script_status.SEARCH_AND_STORE_INFO_TO_DB:
            try:
                self.logger = self.prepare_logging_seq()

                ###########################################################
                self.handler_factory_inst = handler_picker.HandlerPicker(self.conf("handlers"))
                self.handler_factory_inst.get_configured_handlers()
                ###########################################################

                self.file_list = self.build_file_list_from_path()
            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))
        elif self.status == util.Script_status.READ_PATHS_AND_STORE_INFO_TO_DB:
            try:
                self.logger = self.prepare_logging_seq()

                ###########################################################
                self.handler_factory_inst = handler_picker.HandlerPicker(self.conf("handlers"))
                self.handler_factory_inst.get_configured_handlers()
                ###########################################################

                self.file_list = self.build_list_from_file()

            except KeyError as k:
                sys.stderr.write("Missing configuration option: %s\n\n" % str(k))

    def prepare_logging_seq(self):

        """
        initializes  logging.
        """

        #Check if logging directory exists and if necessary create it.
        log_dir = self.conf("core")["log-path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #kltsa 15/09/2015 changes for issue :23221.
        if self.status == util.Script_status.READ_PATHS_AND_STORE_INFO_TO_DB:
            log_fname = "%s_%s_%s_%s_%s.log" \
                        %(self.conf("es-configuration")["es-index"], self.conf("filename").replace("/", "-"),\
                        self.conf("start"), self.conf("num-files"), socket.gethostname())
        else:
            log_fname = "%s_%s_%s.log" \
                        %(self.conf("es-configuration")["es-index"], self.conf("dataset"), socket.gethostname())


        #create the path where to create the log files.
        fpath = os.path.join(log_dir,
                             log_fname
                            )


        levels = {'debug'   : logging.DEBUG,
                  'info'    : logging.INFO,
                  'warning' : logging.WARNING,
                  'error'   : logging.ERROR,
                  'critical': logging.CRITICAL
                 }


        conf_log_level = self.conf("core")["log-level"]


        log_format = self.conf("core")["format"]
        level = levels.get(conf_log_level, logging.NOTSET)

        """
        ok, since this is the main module lets remove previously configured handlers
        and add the one used in this script.
        """
        logging.root.handlers = []

        """
        logging.basicConfig( filename=fpath,
                             filemode="a+",
                             format=log_format,
                             level=level
                           )
        """

        extract_logger = logging.getLogger(__name__)

        file_handler = logging.FileHandler(fpath)
        log_format = logging.Formatter(log_format)
        file_handler.setFormatter(log_format)


        extract_logger.addHandler(file_handler)
        extract_logger.setLevel(level)
        extract_logger.propagate = 0


        es_log = logging.getLogger("elasticsearch")
        es_log.setLevel(logging.ERROR)
        #es_log.addHandler(logging.FileHandler(fpath_es))


        nappy_log = logging.getLogger("nappy")
        nappy_log.setLevel(logging.ERROR)


        urllib3_log = logging.getLogger("urllib3")
        urllib3_log.setLevel(logging.ERROR)
        #urllib3_log.addHandler(logging.FileHandler(fpath_es))

        log = logging.getLogger(__name__)

        return log

    def  build_file_list_from_path(self):

        """
        Returns the files contained within a dataset.
        """

        dataset_ids_file = self.conf("filename")
        dataset_id = self.conf("dataset")
        #derectory where the files to be searched are.
        path_to_files = util.find_dataset(dataset_ids_file, dataset_id)

        return util.build_file_list(path_to_files)

    def build_list_from_file(self):

        """
        Reads file paths form a given file and returns a subset of them
        in a list.
        """

        file_containing_paths = self.conf("filename")
        start_file = self.conf("start")
        num_of_files = self.conf("num-files")

        #TODO: Make this a library function and make it more efficient.
        with open(file_containing_paths) as fd:
            content = fd.readlines()

        self.logger.info(("%s lines read from file \"%s\"."  %(str(len(content)), file_containing_paths)))

        list_len = len(content)
        if int(start_file) < 0 or int(start_file) > list_len:
            self.logger.info("please correct start parameter value.")
            return

        end_file = int(start_file) + int(num_of_files)

        if end_file > list_len:
            self.logger.info("please correct num-files parameter value.")
            return

        file_list = content[int(start_file):end_file]

        new_file_list = []
        for path in file_list:
            new_file_list.append(path.rstrip())

        return new_file_list

    def index_properties_seq(self, body, es_id):

        """
        Indexes metadata in Elasticsearch.
        """

        self.es.index(index=self.conf("es-configuration")["es-index"],\
                      doc_type=self.conf("es-configuration")["es-mapping"],\
                      body=body,\
                      id=es_id)

    def process_file_seq(self, filename, level):

        """
        Returns metadata from the given file.
        """

        handler = self.handler_factory_inst.pick_best_handler(filename)
        if handler is not None:
            handler_inst = handler(filename, level) #Can this done within the HandlerPicker class.
            metadata = handler_inst.get_properties()
            self.logger.info(("%s was read using handler \"%s\"." %(filename, handler_inst.get_handler_id())))
            return metadata
        else:
            self.logger.info(("%s could not be read by any handler." %(filename)))
            return None

    def store_filenames_to_file(self):
        """
        Stores filenames of files within a dataset to a file.
        """

        self.prepare_run()
        try :
            file_to_store_paths = self.conf("make-list")
            files_written = util.write_list_to_file(self.file_list, file_to_store_paths)
            self.logger.info(("Paths written in file: %s." %(str(files_written))))
            self.logger.info(("file \"%s\" containing paths to files in given dataset has been created." %(file_to_store_paths)))
        except Exception:
            self.logger.error("Could not save the python list of files to file...")


    def run_seq(self):

        """
         Extracts metadata information from files and posts them in elastic search.
        """

        #Create all data structures needed.
        self.prepare_run()

        #Sanity check.
        if self.file_list is None:
            self.logger.info("File list is empty.")
            return

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

            for filename in self.file_list:
                #file_path = f

                #self.logger.info("Metadata extraction started for file %s", file_path)
                start = datetime.datetime.now()

                doc = self.process_file_seq(filename, level)

                if doc is not None:

                    #es_query = json.dumps(doc)
                    es_id = hashlib.sha1(filename).hexdigest()

                    try:
                        self.index_properties_seq(doc, es_id)
                    except Exception as ex:
                        end = datetime.datetime.now()
                        self.logger.error(ex.message)
                        self.logger.error(("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                              self.FILE_INDEX_ERROR, str(end - start))))
                    else:
                        end = datetime.datetime.now()
                        self.logger.info(("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                             self.FILE_INDEXED, str(end - start))))

                else:
                    end = datetime.datetime.now()

                    self.logger.error("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                         self.FILE_PROPERTIES_ERROR, str(end - start)))
                    continue

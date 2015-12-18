"""
'Extract' module - handles file crawling and metadata extraction.
"""

import datetime
import logging
import os
import sys
import re
import hashlib
import socket
import fbs_lib.util as util
import fbs_lib.handler_picker as handler_picker
from elasticsearch.exceptions import TransportError
from fbs.es.search import ElasticsearchClientFactory
from fbs import index

#kltsa 14/08/2015 issue #23203.
class ExtractSeq(object):

    """
    File crawler and metadata extractor class.
    Part of core functionality of FBS.
    Files are scanned sequentially (one thread).
    """
    def __init__(self, conf):

        # Extract.__init__(self, None)

        self.configuration = conf
        #self.status = status
        self.logger = None
        self.handler_factory_inst = None
        self.file_list = []
        self.es = None
        self.dataset_id = None
        self.dataset_dir = None
        #some constants
        self.FILE_PROPERTIES_ERROR = "0"
        self.FILE_INDEX_ERROR = "-1"
        self.FILE_INDEXED = "1"
        #Varialbes for storing statistical information.
        self.database_errors = 0
        self.files_properties_errors = 0
        self.files_indexed = 0
        self.total_number_of_files = 0

    #***General purpose methods.***
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

    def read_dataset(self):

        """
        Returns the files contained within a dataset.
        """

        datasets_file = self.conf("filename")
        self.dataset_id = self.conf("dataset")
        #derectory where the files to be searched are.
        self.dataset_dir = util.find_dataset(datasets_file, self.dataset_id)
        if self.dataset_dir is not None:
            self.logger.debug("Scannning files in directory {}.".format(self.dataset_dir))
            return util.build_file_list(self.dataset_dir)
        else:
            return None

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
        try:
            handler = self.handler_factory_inst.pick_best_handler(filename)
            if handler is not None:
                handler_inst = handler(filename, level) #Can this done within the HandlerPicker class.
                metadata = handler_inst.get_properties()
                self.logger.debug("{} was read using handler {}.".format(filename, handler_inst.get_handler_id()))
                return metadata
            else:
                self.logger.error("{} could not be read by any handler.".format(filename))
                return None
        except Exception as ex:
            self.logger.error("Could not process file: {}".format(ex))
            return None

    def scan_dataset(self):

        """
         Extracts metadata information from files and posts them in elastic search.
        """
        #Sanity check.
        if self.file_list is None:
            self.logger.info("File list is empty.")
            return

        # Create index if necessary
        self.logger.debug("Setting elastic search index.")
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

        self.logger.debug("File list contains {} files.".format(len(self.file_list)))
        if len(self.file_list) > 0:

            for filename in self.file_list:
                #file_path = f

                #self.logger.info("Metadata extraction started for file %s", file_path)
                start = datetime.datetime.now()

                self.logger.debug("Scanning file {} at level {}.".format(filename, level))
                doc = self.process_file_seq(filename, level)


                if doc is not None:

                    #es_query = json.dumps(doc)
                    es_id = hashlib.sha1(filename).hexdigest()
                    self.logger.debug("Json for file {}: {} has is .".format(filename, doc, es_id))

                    try:
                        self.index_properties_seq(doc, es_id)
                    except Exception as ex:
                        end = datetime.datetime.now()
                        self.logger.error(("Database error: %s" %ex))
                        self.logger.error(("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                              self.FILE_INDEX_ERROR, str(end - start))))
                        self.database_errors = self.database_errors + 1
                    else:
                        end = datetime.datetime.now()
                        self.logger.debug(("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                             self.FILE_INDEXED, str(end - start))))
                        self.files_indexed = self.files_indexed + 1

                else:
                    end = datetime.datetime.now()

                    self.logger.error("%s|%s|%s|%s ms" %(os.path.basename(filename), os.path.dirname(filename), \
                                                         self.FILE_PROPERTIES_ERROR, str(end - start)))
                    self.files_properties_errors = self.files_properties_errors + 1
                    continue

            #At the end print some statistical info.
            logging.getLogger().setLevel(logging.INFO)
            self.logger.info("Summary information for Dataset id : %s, files indexed : %s, database errors : %s,"
                             " properties errors : %s, total files : %s "
                             % ( self.dataset_id, str(self.files_indexed), str(self.database_errors),
                             str(self.files_properties_errors), str(self.total_number_of_files))
                            )

    #***Functionality for traversing dataset dir and storing paths to file.***
    def prepare_logging_sdf(self):

        """
        initializes  logging.
        """

        #Check if logging directory exists and if necessary create it.
        log_dir = self.conf("core")["log-path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #kltsa 15/09/2015 changes for issue :23221.
        #if self.status == util.Script_status.READ_DATASET_FROM_FILE_AND_SCAN:
        #    log_fname = "%s_%s_%s_%s_%s.log" \
        #                %(self.conf("es-configuration")["es-index"], self.conf("filename").replace("/", "|"),\
        #                self.conf("start"), self.conf("num-files"), socket.gethostname())
        #else:
        log_fname = "%s_%s_%s.log" \
                    %(self.conf("es-configuration")["es-index"],\
                    self.conf("dataset"), socket.gethostname())


        #create the path where to create the log files.
        fpath = os.path.join(log_dir,
                             log_fname
                            )

        conf_log_level = self.conf("core")["log-level"]

        log_format = self.conf("core")["format"]
        level = util.log_levels.get(conf_log_level, logging.NOTSET)

        """
        ok, since this is the main module lets remove previously configured handlers
        and add the one used in this script.
        """
        logging.root.handlers = []


        logging.basicConfig( filename=fpath,
                             filemode="a+",
                             format=log_format,
                             level=level
                           )

        es_log = logging.getLogger("elasticsearch")
        es_log.setLevel(logging.ERROR)
        #es_log.addHandler(logging.FileHandler(fpath_es))


        nappy_log = logging.getLogger("nappy")
        nappy_log.setLevel(logging.ERROR)


        urllib3_log = logging.getLogger("urllib3")
        urllib3_log.setLevel(logging.ERROR)
        #urllib3_log.addHandler(logging.FileHandler(fpath_es))

        self.logger = logging.getLogger(__name__)

    def store_dataset_to_file(self):

        """
        Stores filenames of files within a dataset to a file.
        """
        self.prepare_logging_sdf()
        self.logger.debug("***Scanning started.***")
        self.file_list = self.read_dataset()
        if self.file_list is not None:
            file_to_store_paths = self.conf("make-list")
            try :
                files_written = util.write_list_to_file(self.file_list, file_to_store_paths)
            except Exception as ex:
                self.logger.error("Could not save the python list of files to file...{}".format(ex))
            else:
                self.logger.debug("Paths written in file: {}.".format(files_written))
                self.logger.debug("file {} ,containing paths to files in given dataset, has been created.".format(file_to_store_paths))

    #***Functionality for reading paths from file and then extracting metadata.***
    def prepare_logging_rdf(self):

        """
        initializes  logging.
        """

        #Check if logging directory exists and if necessary create it.
        log_dir = self.conf("core")["log-path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #kltsa 15/09/2015 changes for issue :23221.
        #READ_DATASET_FROM_FILE_AND_SCAN:
        log_fname = "%s_%s_%s_%s_%s.log" \
                    %(self.conf("es-configuration")["es-index"], self.conf("filename").replace("/", "|"),\
                    self.conf("start"), self.conf("num-files"), socket.gethostname())

        #create the path where to create the log files.
        fpath = os.path.join(log_dir,
                             log_fname
                            )

        conf_log_level = self.conf("core")["log-level"]


        log_format = self.conf("core")["format"]
        level = util.log_levels.get(conf_log_level, logging.NOTSET)

        logging.root.handlers = []

        logging.basicConfig( filename=fpath,
                             filemode="a+",
                             format=log_format,
                             level=level
                           )

        es_log = logging.getLogger("elasticsearch")
        es_log.setLevel(logging.ERROR)
        #es_log.addHandler(logging.FileHandler(fpath_es))


        nappy_log = logging.getLogger("nappy")
        nappy_log.setLevel(logging.ERROR)


        urllib3_log = logging.getLogger("urllib3")
        urllib3_log.setLevel(logging.ERROR)
        #urllib3_log.addHandler(logging.FileHandler(fpath_es))

        self.logger = logging.getLogger(__name__)

    def read_dataset_from_file_and_scan(self):
        """
        Reads file paths form a given file and returns a subset of them
        in a list.
        """

        #Set up logger and handler class.
        self.prepare_logging_rdf()
        self.logger.debug("***Scanning started.***")
        self.handler_factory_inst = handler_picker.HandlerPicker(self.conf("handlers"))
        self.handler_factory_inst.get_configured_handlers()


        file_containing_paths = self.conf("filename")
        start_file = self.conf("start")
        num_of_files = self.conf("num-files")

        self.logger.debug("Copying paths from file {} start is {} and number of lines is {}.".\
                          format(file_containing_paths, start_file, num_of_files))

        filename = os.path.basename(file_containing_paths)
        self.dataset_id = os.path.splitext(filename)[0]
        self.logger.debug("Dataset id is  {}.".format(self.dataset_id))

        content = util.read_file_into_list(file_containing_paths)

        self.total_number_of_files = len(content)
        self.logger.debug("{} lines read from file {}.".format((len(content)), file_containing_paths))

        if int(start_file) < 0 or int(start_file) > self.total_number_of_files:
            self.logger.error("Please correct start parameter value.")
            return

        end_file = int(start_file) + int(num_of_files)
        if end_file > self.total_number_of_files:
            self.logger.error("Please correct num-files parameter value because it is out of range.")
            return

        file_list = content[int(start_file):end_file]

        self.logger.debug("{} files copied in local file list.".format(len(file_list)))

        for path in file_list:
            self.file_list.append(path.rstrip())

        #at the end extract metadata.
        self.scan_dataset()

    #***Functionality for traversing dataset and then immediately extract metadata.***
    def prepare_logging_seq_rs(self):

        """
        initializes  logging.
        """

        #Check if logging directory exists and if necessary create it.
        log_dir = self.conf("core")["log-path"]

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        #kltsa 15/09/2015 changes for issue :23221.
        log_fname = "%s_%s_%s.log" \
                    %(self.conf("es-configuration")["es-index"],\
                    self.conf("dataset"), socket.gethostname())


        #create the path where to create the log files.
        fpath = os.path.join(log_dir,
                             log_fname
                            )

        conf_log_level = self.conf("core")["log-level"]


        log_format = self.conf("core")["format"]
        level = util.log_levels.get(conf_log_level, logging.NOTSET)

        """
        ok, since this is the main module lets remove previously configured handlers
        and add the one used in this script.
        """
        logging.root.handlers = []


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
        """

        es_log = logging.getLogger("elasticsearch")
        es_log.setLevel(logging.ERROR)
        #es_log.addHandler(logging.FileHandler(fpath_es))


        nappy_log = logging.getLogger("nappy")
        nappy_log.setLevel(logging.ERROR)


        urllib3_log = logging.getLogger("urllib3")
        urllib3_log.setLevel(logging.ERROR)
        #urllib3_log.addHandler(logging.FileHandler(fpath_es))

        self.logger = logging.getLogger(__name__)

    def read_and_scan_dataset(self):

        self.prepare_logging_seq_rs()
        self.logger.debug("***Scanning started.***.")
        self.handler_factory_inst = handler_picker.HandlerPicker(self.conf("handlers"))
        self.handler_factory_inst.get_configured_handlers()

        self.file_list = self.read_dataset()
        self.total_number_of_files = len(self.file_list)
        #at the end extract metadata.
        self.scan_dataset()

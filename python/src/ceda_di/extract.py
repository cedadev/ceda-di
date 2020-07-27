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
import hashlib

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

        for pattern, handler in handler_map.items():

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

        for pattern, handler in self.handlers.items():
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
                self.logger.info("Not using handler {} because {}".format(handler_class, ex))
                pass
            except AttributeError:
                return handler_class

        return None


class Extract(object):
    """
    File crawler and metadata extractor class.
    Part of core functionality of ceda_di.
    """

    def __init__(self, conf, file_list=None):

        self.configuration = conf

        try:
            self.make_dirs(conf)
            self.logger = self.prepare_logging()
            self.handler_factory = HandlerFactory(self.conf("handlers"))

            if file_list is None:
                self.file_list = self._build_file_list()
            else:
                self.file_list = file_list
        except KeyError as k:
            sys.stderr.write("Missing configuration option: %s\n\n" % str(k))

    def _build_file_list(self):
        """
        Return file list
        :return: A list of file paths
        """
        file_list = []
        for root, _, files in os.walk(self.conf("input-path"), followlinks=True):
            for each_file in files:
                file_list.append(os.path.join(root, each_file))

        return file_list

    def conf(self, conf_opt):
        """
        Return configuration option or raise exception if it doesn't exist.
        :param str conf_opt: The name of the configuration option to find.
        """
        if conf_opt in self.configuration:
            return self.configuration[conf_opt]
        else:
            raise AttributeError(
                f"Mandatory configuration option not found: {conf_opt}")

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
                     datetime.datetime.now().isoformat() +
                     ".log")
        fpath = os.path.join(self.conf("output-path"),
                             self.conf("log-path"),
                             log_fname)

        logging.basicConfig(filename=fpath,
                            format=self.conf("logging")["format"],
                            level=logging.WARNING)

        log = logging.getLogger(__name__)

        return log

    def process_file(self, filename):
        """
        Instantiate a handler for a file and extract metadata.
        """
        try:
            handler = self.handler_factory.get_handler(filename)
            if handler is not None:
                with handler as hand:
                    if self.conf('send-to-index'):
                        self.index_properties(filename, hand)
                    if not self.conf('no-create-files'):
                        self.write_properties(filename, hand)
        except Exception as exc:
            print(f"Failure in process_file for {filename}")
            raise

    def index_properties(self, filename, handler):
        """
        Index the file in Elasticsearch
        """
        try:
            props = handler.get_properties()
        except Exception as e:
            print(filename)
            raise e


        if props is not None:
            index = self.conf('es-index')
            body = str(props)
            doc_id = hashlib.sha1(filename.encode('utf-8')).hexdigest()

            try:
                self.es.index(index=index, body=body, id=doc_id)
            except Exception as err:
                print(f"FAILED to log: {filename}")
                print(f"FAILURE ERROR WAS: {str(err)}")


    def write_properties(self, fname, _geospatial_obj):
        """
        Write module properties to an output file.
        """
        # Construct JSON path
        fname = os.path.basename(fname)
        json_path = os.path.join(self.conf("output-path"), self.conf("json-path"))

        out_fname = f"{json_path}/{os.path.splitext(fname)[0]}.json"
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
        self.logger.info(f"Metadata extraction started at: {start.isoformat()}")

        # Create index if necessary
        if self.conf("send-to-index"):
            es_factory = ElasticsearchClientFactory()
            self.es = es_factory.get_client(self.configuration)

            index.create_index(self.configuration, self.es)

        if len(self.file_list) > 0:
            # Process files
            #pool = []
            #
            #for f in self.file_list:
            #    # HDF libraries don't seem to like unicode strings,
            #    # which the filenames will be if the configuration paths
            #    # loaded from JSON end up in unicode
            #    path = f
            #    if "raw" not in path:
            #        p = multiprocessing.Process(target=self.process_file,
            #                                    args=(path,))
            #        pool.append(p)
            #        p.start()
            #
            #    while len(pool) >= self.conf("num-cores"):
            #        for p in pool:
            #            if p.exitcode is not None:
            #                pool.remove(p)
            #
            #for p in pool:
            #    p.join()

            for f in self.file_list:
                path = f
                if "raw" not in path:
                    self.process_file(path)

        # Log end of processing
        end = datetime.datetime.now()
        self.logger.info("Metadata extraction completed at: %s",
                         end.isoformat())
        self.logger.info("Start: %s, End: %s, Total: %s",
                         start.isoformat(), end.isoformat(), end - start)

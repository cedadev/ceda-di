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


class HandlerFactory(object):
    """
    Factory for file handler classes.
    """
    def __init__(self, handler_map):
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
        if len(handler_candidates) > 0:
            handler_candidates.sort(key=lambda h: h['priority'])
            return handler_candidates[0]['class']


class Extract(object):
    """
    File crawler and metadata exractor class.
    Part of core functionality of ceda_di.
    """
    def __init__(self, conf):
        self.conf = conf
        try:
            self.make_dirs()
            self.logger = self.prepare_logging()

            self.numcores = self.conf["numcores"]
            self.datapath = self.conf["datapath"]
            self.outpath = self.conf["outputpath"]
            self.handler_factory = HandlerFactory(self.conf["handlers"])

            self.jsonpath = os.path.join(self.conf["outputpath"],
                                         self.conf["jsonpath"])
        except KeyError as k:
            sys.stderr.write("Missing configuration option: %s\n\n" % str(k))

    def make_dirs(self):
        """
        Create directories for output files.
        """
        conf = self.conf
        json_out = os.path.join(conf["outputpath"], conf["jsonpath"])
        if not os.path.isdir(json_out):
            os.makedirs(json_out)

        log_out = os.path.join(conf["outputpath"], conf["logpath"])
        if not os.path.isdir(log_out):
            os.makedirs(log_out)

    def prepare_logging(self):
        """
        Initial logging setup
        """
        fname = os.path.join(self.conf["outputpath"],
                             self.conf["logpath"],
                             self.conf["logfile"])

        logging.basicConfig(filename=fname,
                            format=self.conf["logging"]["format"],
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
                self.write_properties(filename, hand)

    def write_properties(self, fname, _geospatial_obj):
        """
        Write module properties to an output file.
        """

        fname = os.path.basename(fname)

        # Construct JSON path
        fname = "%s/%s.json" % (self.jsonpath, os.path.splitext(fname)[0])

        props = _geospatial_obj.get_properties()
        if props is not None:
            with open(fname, 'w') as j:
                j.write(str(props))

    def run(self):
        """
        Run main metadata extraction suite.
        """
        # Log beginning of processing
        start = datetime.datetime.now()
        self.logger.info("Metadata extraction started at: %s",
                         start.isoformat())

        # Build list of file paths
        data_files = []
        for root, _, files in os.walk(self.datapath, followlinks=True):
            for each_file in files:
                data_files.append((root, each_file))

        if len(data_files) > 0:
            # Process files
            pool = []

            for f in data_files:
                # HDF libraries don't seem to like unicode strings,
                # which the filenames will be if the configuration paths
                # loaded from JSON end up in unicode
                path = str(os.path.join(*f))
                if "raw" not in path:
                    p = multiprocessing.Process(target=self.process_file,
                                                args=(path,))
                    pool.append(p)
                    p.start()

            while len(pool) >= self.numcores:
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

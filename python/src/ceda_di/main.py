"""
Main script to handle processing of CEDA Data Index data.
"""

import datetime
import json
import logging
import logging.config
import multiprocessing
import os
import sys

from _dataset import _geospatial


class HandlerFactory(object):
    """
    Factory for file handler classes.
    """
    def __init__(self, handler_map):
        self.handlers = {}
        for pattern, handler in handler_map.iteritems():
            (module, hand) = handler.split(".", 1)
            mod = __import__(module, fromlist=[hand])
            self.handlers[pattern] = getattr(mod, hand)

    def get(self, filename):
        """
        Return instance of correct file handler class.
        """
        for pattern, handler in self.handlers.iteritems():
            if filename.endswith(pattern):
                return handler(filename)


class Main(object):
    """
    Main script to start processing of data files in ceda-di.
    """
    def __init__(self):
        try:
            self.conf = self.read_conf(sys.argv[1])
        except IndexError:
            # Try default configuration path if none provided
            self.conf = self.read_conf("../../config/ceda_di.json")

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

    def read_conf(self, conf_path):
        """
        Read the confuration file into a dictionary.
        :param fname: Path to the JSON confuration file
        :return dict: Dict containing parsed JSON conf
        """
        try:
            with open(conf_path, "r") as conf:
                return json.load(conf)
        except IOError as ioe:
            sys.stderr.write(  # Continued on next line
                "Can't read configuration, exiting.\n%s\n" % str(ioe))
            exit(1)

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
        handler = self.handler_factory.get(filename)
        with handler as hand:
            self.write_properties(filename, hand)

    def write_properties(self, fname, _geospatial_obj):
        """
        Write module properties to an output file.
        """
        fname = os.path.basename(fname)

        # Construct JSON path
        fname = "%s/%s.json" % (self.jsonpath, os.path.splitext(fname)[0])

        with open(fname, 'w') as j:
            props = str(_geospatial_obj.get_properties())
            j.write(props)

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
            pool = multiprocessing.Pool(self.numcores)
            pool.map(self.process_file, data_files)
            pool.close()
            pool.join()

        # Log end of processing
        end = datetime.datetime.now()
        self.logger.info("Metadata extraction completed at: %s",
                         end.isoformat())
        self.logger.info("Start: %s, End: %s, Total: %s",
                         start.isoformat(), end.isoformat(), end - start)


if __name__ == "__main__":
    MAIN = Main()
    MAIN.run()

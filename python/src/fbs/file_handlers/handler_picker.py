import os
import ntpath
import json
import re

from fbs_lib.util import FileFormatError
import generic_file as generic_file
import netcdf_file as netcdf_file
import nasaames_file as nasaames_file
import pp_file as pp_file
import grib_file as grib_file

import magic as magic_number_reader
import fbs_lib.util as util


class  HandlerPicker(object):
    """
    Returns a file handler for the supplied file.
    """

    def __init__(self, handler_map):
        self.handler_map = handler_map
        self.handlers = {}
        self.handlers_and_dirs = {}
        self.NETCDF_PYTHON_MAGIC_NUM_RES = "NetCDF Data Format data"
        self.ASCII_PYTHON_MAGIC_NUM_RES = "ASCII text"
        self.DATA_PYTHON_MAGIC_NUM_RES = "data"


    def pick_best_handler(self, filename):
        """
        :param filename : the file to be scanned.
        :returns handler: Returns an appropriate handler
        for the given file.
        """

        handler = None

        """
        Sanity check.
        check if file still exists.
        """
        if not os.path.isfile(filename):
            return None

        file_dir = os.path.dirname(filename)

        #Try configured handler.
        handler = self.get_configured_handler_class(filename)

        if handler is not None:
            self.handlers_and_dirs[file_dir] = handler
            return handler

        #Try returning a handler based on file extension.
        extension = os.path.splitext(filename)[1]

        if extension == ".nc":
            handler = netcdf_file.NetCdfFile
        elif extension == ".na":
            handler = nasaames_file.NasaAmesFile
        elif extension == ".pp":
            handler = pp_file.PpFile
        elif extension in (".grb", ".grib", ".GRB", ".GRIB"):
            handler = grib_file.GribFile

        if handler is not None:
            self.handlers_and_dirs[file_dir] = handler
            return handler


        #Try returning a handler based on file's magic number.
        try:
            res = magic_number_reader.from_file(filename)

            if res == self.NETCDF_PYTHON_MAGIC_NUM_RES:
                handler = netcdf_file.NetCdfFile
            elif res == self.ASCII_PYTHON_MAGIC_NUM_RES:
                #ok lets see if it is a na file.
                first_line = util.get_file_header(filename)
                tokens = first_line.split(" ")
                if len(tokens) >= 2:
                    if tokens[0].isdigit() and tokens[1].isdigit():
                        handler = nasaames_file.NasaAmesFile
                else:
                    handler = generic_file.GenericFile
            #This can be a grb file.
            elif res == self.DATA_PYTHON_MAGIC_NUM_RES:
                res = util.get_bytes_from_file(filename, 4)
                if res == "GRIB":
                    handler = grib_file.GribFile
                else:
                    handler = generic_file.GenericFile
        except: #catch everything... we do not want ifthere is an error just return the generic handler.
            handler = generic_file.GenericFile


        if handler is not None:
            self.handlers_and_dirs[file_dir] = handler
            return handler

        #Try to return last handler used in this directory.
        handler = self.handlers_and_dirs[file_dir] = handler

        if handler is not None:
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
            except FileFormatError: #as ex
                #self.logger.info("Not using handler {} because {}".format(handler_class, ex.message))
                pass
            except AttributeError:
                return handler_class
        return None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

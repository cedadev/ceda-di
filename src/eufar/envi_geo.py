"""
Interface for reading data from ENVI BSQ/BIL packed binary files.
Also contains methods for extracting metadata (geospatial/temporal).
"""

import logging

from io import envi
from metadata import product
from _dataset import _geospatial


class ENVI(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.logger = logging.getLogger()
        self.b = None  # Overridden by child classes
        self.data = None  # Overridden by child classes
        self.data_format = None  # Overridden by child classes
        self.extension = None  # Overridden by child classes
        self.parameters = None  # Overridden by child classes
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def _load_data(self):
        """
        Load data from the binary file into a class attribute "data"
        """
        if self.data is None:
            self.parameters = self.b.hdr
            self.data = self.b.read()

    def get_parameters(self):
        """
        Return a list of Parameter objects containing parameter information.
        """
        params = []
        for p_name in self.parameters:
            param = product.Parameter(p_name)
        params.append(param)

    def get_geospatial(self):
        """
        Read geospatial data parsed from binary file
        :return dict: A dict containing geospatial information
        """
        spatial = {
            "lat": self.data[1],
            "lon": self.data[2],
            "alt": self.data[3],
            "roll": self.data[4],
            "pitch": self.data[5],
            "heading": self.data[6]
        }

        return spatial

    def get_temporal(self):
        temporal = {
            "start_time": self.data[0][0],
            "end_time": self.data[0][-1],
        }

        return temporal

    def get_data_format(self):
        """
        Return file format information
        :return dict: A dict containing file format information
        """
        data_format = {
            "format": self.data_format,
        }

        return data_format

    def get_properties(self):
        """
        Return a metadata.product.Properties object describing
        the file's metadata.

        :return metadata.product.Properties: Metadata
        """
        file_level = super(ENVI, self).get_file_level(self.path)

        self._load_data()
        if "band names" in self.parameters:
            self.parameters = self.parameters["band names"]

        prop = product.Properties(file_level=file_level,
                                  temporal=self.get_temporal(),
                                  data_format=self.get_data_format(),
                                  spatial=self.get_geospatial(),
                                  parameters=self.get_parameters())
        return prop


class BIL(ENVI):
    """
    Sub-class of ENVI that uses the io.envi.BilFile class to read
    binary data from BIL files.
    """
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BIL, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bil"
        self.data_format = "ENVI BIL (Band Interleaved by Line)"

        # Construct file access object
        self.b = envi.BilFile(header_path=self.header_path,
                              path=self.path,
                              unpack_fmt=self.unpack_fmt)
        self.path = self.b.path

    def __enter__(self):
        self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        self._load_data()
        return self.data


class BSQ(ENVI):
    """
    Sub-class of ENVI that uses the io.envi.BsqFile class to read
    binary data from BSQ files.
    """
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BSQ, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bsq"
        self.data_format = "ENVI BSQ (Band Sequential)"

        # Construct file access object
        self.b = envi.BsqFile(header_path=self.header_path,
                              path=self.path,
                              unpack_fmt=self.unpack_fmt)
        self.path = self.b.path

    def __enter__(self):
        self.data = self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        self._load_data()
        return self.data

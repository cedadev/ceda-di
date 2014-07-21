from io import envi
from _dataset import _geospatial
import os


class ENVI(_geospatial):
    def __init__(self):
        raise NotImplementedError("Do not instantiate this class. Use BIL/BSQ.")

    def get_geospatial(self):
        """
        :param str header_fpath: Filename of header file
        :return dict: A dict containing geospatial and temporal information
        """

        self.data = self.b.read()
        flightline = {
            "lines": self.b.hdr["lines"],
            "time": self.data[0],
            "lat": self.data[1],
            "lon": self.data[2],
            "alt": self.data[3],
            "roll": self.data[4],
            "pitch": self.data[5],
            "heading": self.data[6],
        }

        return flightline

class BIL(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        """
        Used to set up file when used in context manager.
        :return self:
        """
        self.b = envi.BilFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def open(self):
        __enter__()

    def __exit__(self, *args):
        pass


class BSQ(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        """
        Used to set up file as context manager.
        :return self:
        """
        self.b = envi.BsqFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def open(self):
        __enter__()

    def __exit__(self):
        pass

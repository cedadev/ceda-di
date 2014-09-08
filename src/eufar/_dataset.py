"""Base class for metadata wrapper classes."""
import os


class _geospatial(object):
    """
    Base class used as interface for providing file-level metadata from
    geospatial and temporal metadata files.
    """
    def __init__(self):
        self.unimpl_base_class()

    @staticmethod
    def get_file_level(fpath):
        """Returns a dict containing filesystem information"""
        file_level = {
            "filename": os.path.basename(fpath),
            "path": fpath,
            "size": os.stat(fpath).st_size,
        }

        return file_level

    def get_geospatial(self):
        """Returns a dict containing geospatial information"""
        self.unimpl_base_class()

    def get_temporal(self):
        """Returns a dict containing temporal information"""
        self.unimpl_base_class()

    def get_parameters(self):
        """Returns a dict containing parameter information"""
        self.unimpl_base_class()

    @staticmethod
    def unimpl_base_class():
        """Throws relevant NotImplementedError."""
        exception = \
            "\"_geospatial\" is an abstract base class and is intended" + \
            "to be used as an OO interface for EUFAR data files ONLY."

        raise NotImplementedError(exception)


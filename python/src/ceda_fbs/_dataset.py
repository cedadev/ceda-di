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
    def get_filesystem(fpath):
        """Returns a dict containing filesystem information"""
        filesystem = {
            "filename": os.path.basename(fpath),
            "path": fpath,
            "size": os.stat(fpath).st_size,
            "symlinks": _geospatial.get_symlinks(fpath)
        }

        return filesystem

    @staticmethod
    def get_symlinks(path):
        """
        Return a list of all the levels of symlinks (if any).

        :param path: A string containing the path to examine.
        :returns pathlist: A list of file paths corresponding to symlinks.
        """
        paths_seen = []

        while os.path.islink(path) and path not in paths_seen:
            paths_seen.append(path)
            path = os.readlink(path)

        return paths_seen

    def get_geospatial(self):
        """Returns a dict containing geospatial information"""
        self.unimpl_base_class()

    def get_temporal(self):
        """Returns a dict containing temporal information"""
        self.unimpl_base_class()

    def get_parameters(self):
        """Returns a dict containing parameter information"""
        self.unimpl_base_class()

    def get_properties(self):
        """
        Return a ceda_di.metadata.product.Properties object populated with the
        file's metadata.

        :returns: A ceda_di.metadata.product.Properties object
        """
        self.unimpl_base_class()

    @staticmethod
    def unimpl_base_class():
        """Throws relevant NotImplementedError."""
        exception = \
            "\"_geospatial\" is an abstract base class and is intended" + \
            "to be used as an interface ONLY."

        raise NotImplementedError(exception)

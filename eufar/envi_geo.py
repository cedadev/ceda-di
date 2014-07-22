from io import envi
from _dataset import _geospatial


class ENVI(_geospatial):
    def __init__(self):
        self.header_path = None
        self.data_format = None
        self.path = None
        self.unpack_fmt = None
        raise NotImplementedError("Do not instantiate this class. Use BIL/BSQ.")

    def _load_data(self):
        if not self.data:
            self.b.read()

    def get_geospatial(self):
        """
        :return dict: A dict containing geospatial and temporal information
        """

        self._load_data()
        spatial = {
            "lat": data[1],
            "lon": data[2],
            "alt": data[3],
            "roll": data[4],
            "pitch": data[5],
            "heading": data[6]
        }

        return spatial

    def get_temporal(self):
        self._load_data()
        temporal = {
            "start_time": self.data[0][0],
            "end_time": self.data[0][-1],
        }

        return temporal

    def get_data_format(self):
        data_format = {
            "format": self.data_format,
        }

        return data_format


class BIL(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.data_format = "ENVI BIL (Band Interleaved by Line)"
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

    def __exit__(self, *args):
        pass


class BSQ(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.data_format = "ENVI BSQ (Band Sequential)"
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

    def __exit__(self):
        pass

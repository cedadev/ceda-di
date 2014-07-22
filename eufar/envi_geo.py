from io import envi
from metadata import product
from _dataset import _geospatial


class ENVI(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.b = None
        self.extension = None
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def read(self):
        raise NotImplementedError("Not implemented - this is a base class.")

    def _load_data(self):
        if not hasattr(self, "data"):
            self.data = self.b.read()

    def get_geospatial(self):
        """
        :return dict: A dict containing geospatial and temporal information
        """

        self._load_data()
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

    def get_properties(self):
        file_level = super(ENVI, self).get_file_level(self.b.path)
        prop = product.Properties(file_level=file_level,
                                  temporal=self.get_temporal(),
                                  data_format=self.get_data_format(),
                                  spatial=self.get_geospatial())
        return prop


class BIL(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BIL, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bil"
        self.data_format = "ENVI BIL (Band Interleaved by Line)"

    def __enter__(self):
        self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        if not hasattr(self, "data"):
            self.b = envi.BilFile(header_path=self.header_path,
                                  path=self.path,
                                  unpack_fmt=self.unpack_fmt)
            self.data = self.b.read()
        return self.data


class BSQ(ENVI):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        super(BSQ, self).__init__(header_path, path, unpack_fmt)
        self.extension = ".bsq"
        self.data_format = "ENVI BSQ (Band Sequential)"

    def __enter__(self):
        self.data = self.read()
        return self

    def __exit__(self, *args):
        pass

    def read(self):
        if not hasattr(self, "data"):
            self.b = envi.BsqFile(header_path=self.header_path,
                                  path=self.path,
                                  unpack_fmt=self.unpack_fmt)
            self.data = self.b.read()
        return self.data

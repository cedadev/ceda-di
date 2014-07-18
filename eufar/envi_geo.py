from io import envi
from _dataset import _geospatial


class BIL(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        self.b = envi.BilFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def __exit__(self):
        pass

    def get_geospatial(self):
        """
        :param str header_fpath: Filename of header file
        :return dict: A dict containing geospatial and temporal information
        """

        bil = self.b.read()
        swath_path = {
            "lines": self.b.hdr["lines"],
            "time": bil[0],
            "lat": bil[1],
            "lon": bil[2],
            "alt": bil[3],
            "roll": bil[4],
            "pitch": bil[5],
            "heading": bil[6]
        }

        return swath_path


class BSQ(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.header_path = header_path
        self.path = path
        self.unpack_fmt = unpack_fmt

    def __enter__(self):
        self.b = envi.BsqFile(self.header_path,
                              self.path,
                              self.unpack_fmt)
        return self

    def __exit__(self):
        pass

    def get_geospatial(self):
        """
        :param str header_fpath: Filename of header file
        :return dict: A dict containing geospatial and temporal information
        """

        bil = self.b.read()
        swath_path = {
            "lines": self.b.hdr["lines"],
            "time": bil[0],
            "lat": bil[1],
            "lon": bil[2],
            "alt": bil[3],
            "roll": bil[4],
            "pitch": bil[5],
            "heading": bil[6]
        }

        return swath_path

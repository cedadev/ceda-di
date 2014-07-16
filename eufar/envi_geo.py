from io import envi
from _dataset import _geospatial

class BIL(_geospatial):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        self.b = envi.BilFile(header_path, path, unpack_fmt)

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
        self.b = envi.BsqFile(header_path, path, unpack_fmt)
        
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

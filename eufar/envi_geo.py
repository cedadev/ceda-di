from io import envi
from _dataset import _geospatial


class BIL(_geospatial):
    def get_geospatial(self, header_fpath):
        """
        :param str header_fpath: Filename of header file
        :return dict: A dict containing geospatial and temporal information
        """

        b = envi.BilFile(header_fpath)
        bil = b.read_bil()

        swath_path = {
            "lines": b.hdr["lines"],
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
    def get_geospatial(self, header_fpath):
        raise NotImplementedError("Not implemented")

"""
Test module for eufar.envi_geo
"""

import unittest

from eufar.envi_geo import ENVI
from eufar.metadata.product import Parameter

class ENVIStub(object):
    """Stub ENVI object"""
    def __init__(self, **kwargs):
        self.hdr = {}

        for k, val in kwargs.iteritems():
            self.hdr[k] = val

    def read(self):
        # Returns 7x3 2-dimensional array of arbitrary data
        return [["start_time", "end_time"], ["lat"], ["lon"],
                ["alt"], ["roll"], ["pitch"], ["heading"]]

class TestENVI(unittest.TestCase):
    """Test class for eufar.exif_geo.EXIF"""
    def setUp(self):
        self.path = "/path/to/some/file"
        self.envi_stub = ENVIStub(path=self.path,
                                  velocity="unladen_swallow",
                                  spam="spammity_spam")

    def test_get_parameters(self):
        envi = ENVI(self.path, path=self.path)
        envi.b = self.envi_stub
        envi._load_data()

        assert envi.get_parameters()[0].__dict__ == \
                    Parameter("velocity").__dict__

    def test_get_geospatial(self):
        envi = ENVI(self.path, path=self.path)
        envi.b = self.envi_stub
        envi._load_data()

        geosp = envi.get_geospatial()
        assert geosp["lat"] == ["lat"]
        assert geosp["lon"] == ["lon"]

    def test_get_temporal(self):
        envi = ENVI(self.path, path=self.path)
        envi.b = self.envi_stub
        envi._load_data()

        temporal = envi.get_temporal()
        assert temporal["start_time"] == "start_time"
        assert temporal["end_time"] == "end_time"

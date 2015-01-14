"""
Test module for ceda_di.envi_geo
"""

import unittest

from ceda_di.envi_geo import BIL
from ceda_di.envi_geo import BSQ
from ceda_di.envi_geo import ENVI
from ceda_di.metadata.product import Parameter

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
    """Test class for ceda_di.exif_geo.EXIF"""
    def setUp(self):
        self.path = "/path/to/some/file"
        self.envi_stub = ENVIStub(velocity="unladen_swallow",
                                  spam="spammity_spam")

    def test_get_parameters(self):
        envi = ENVI(self.path)
        envi.b = self.envi_stub
        envi._load_data()

        assert envi.get_parameters()[0].__dict__ == \
                    Parameter("velocity").__dict__
        assert envi.get_parameters()[1].__dict__ == \
                    Parameter("spam").__dict__

    def test_get_geospatial(self):
        envi = ENVI(self.path)
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

    @unittest.skip
    def test_bil_get_data_format(self):
        bil = BIL(self.path)
        assert bil.get_data_format() == "ENVI BIL (Band Interleaved by Line)"

    @unittest.skip
    def test_bsq_get_data_format(self):
        bsq = BSQ(self.path)
        assert bsq.get_data_format() == "ENVI BSQ (Band Sequential)"

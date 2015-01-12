"""
Test module for ceda_di.metadata.product
"""

import unittest

from ceda_di.metadata.product import Properties, Parameter


class TestProperties(unittest.TestCase):
    def setUp(self):
        # Just some dummy data (totally arbitrary)
        fs = {"size": 3, "path": "/some/non/existent/path"}
        tmp = {"start_time": "2014-09-22T20:51:53Z",
               "end_time": "2014-09-22T20:51:53Z"}
        df = {"data_format": "spam"}
        sp = {"lat": [16.11321136, 36.8623985, -54.93456077],
              "lon": [-130.75576671, -170.2979817, -69.18607194]}
        par = [Parameter("test"), Parameter("spam")]

        self.prop = Properties(filesystem=fs, spatial=sp, temporal=tmp,
                               data_format=df, parameters=par, test="foo")

    def test_valid_lat(self):
        # Lovely lovely edge cases
        lats = [90, -90, 0, -91, 91]
        assert filter(Properties.valid_lat, lats) == [90, -90, 0]

    def test_valid_lon(self):
        # More lovely edge cases
        lons = [180, -180, 0, -181, 181]
        assert filter(Properties.valid_lon, lons) == [180, -180, 0]

    def test_gen_bbox(self):
        # Arbitrary data ahoy
        spatial = {
            "lat": [3, 4, 5],
            "lon": [5, 4, 3]
        }

        assert self.prop._gen_bbox(spatial) == {
            "type": "MultiPoint",
            "coordinates": [[3, 3], [3, 5], [5, 5], [5, 3]]
        }



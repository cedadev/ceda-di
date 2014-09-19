"""
Test module for hdf4_geo
"""

import unittest
from pyhdf.error import HDF4Error
from eufar.hdf4_geo import HDF4


class MockAttachedVData(object):
    def __init__(self, read_data):
        self.count = 0
        self.read_data = [read_data]

    def read(self):
        self.count += 1
        try:
            return [self.read_data[0][self.count - 1]]
        except IndexError:
            raise HDF4Error()

    def detach(self):
        pass


class MockVData(object):
    def __init__(self, read_data):
        self.read_data = read_data

    def find(self, k):
        return k

    def attach(self, k):
        return MockAttachedVData(self.read_data[k])


class TestHDF4(unittest.TestCase):
    def setUp(self):
        self.path = "/non/existent/path"

    def test_get_coords(self):
        # Mock an HDF4 VData object that supports reading
        hdf = HDF4(self.path)
        m = MockVData({
            "NVlat2": [[12345678]],
            "NVlng2": [[12345678]]
        })

        coords = hdf._get_coords(m, self.path)
        assert coords == {
            "lat": [1.2345678],
            "lon": [1.2345678]
        }

    def test_get_temporal(self):
        hdf = HDF4(self.path)

        m = MockVData({
            "MIdate": [[ord(x)] for x in "19/07/10"],
            "MIstime": [["100419"]],
            "MIetime": [["110101"]],
        })

        timestamps = hdf._get_temporal(m, self.path)
        print timestamps
        assert timestamps == {
            "start_time": "2010-07-19T10:04:19",
            "end_time": "2010-07-19T11:01:01",
        }

    def get_geospatial(self):
        pass

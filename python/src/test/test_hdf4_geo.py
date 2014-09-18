"""
Test module for hdf4_geo
"""

import unittest
from pyhdf.error import HDF4Error
from eufar.hdf4_geo import HDF4


class MockAttachedVData(object):
    def __init__(self, read_data):
        self.count = 0
        self.read_data = read_data

    def read(self):
        self.count += 1
        if self.count > 2:
            raise HDF4Error()
        return self.read_data

    def detach(self):
        pass


class MockVData(object):
    def __init__(self, read_data):
        self.read_data = read_data
    def find(self, k):
        return "Test"

    def attach(self, k):
        return MockAttachedVData(self.read_data)


class TestHDF4(unittest.TestCase):
    # Mock an HDF4 VData object that supports reading
    def setUp(self):
        self.path = "/non/existent/path"

    def test_get_coords(self):
        hdf = HDF4(self.path)
        coords = hdf._get_coords(MockVData([[12345678]]), self.path)
        assert coords == {
            "lat": [1.2345678, 1.2345678],
            "lon": [1.2345678, 1.2345678]
        }

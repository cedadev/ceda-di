"""
Test module for hdf4_geo
"""

import unittest
from pyhdf.error import HDF4Error
from ceda_di.hdf4_geo import HDF4


class StubAttachedVData(object):
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


class StubVData(object):
    def __init__(self, read_data):
        self.read_data = read_data

    def find(self, k):
        return k

    def attach(self, k):
        return StubAttachedVData(self.read_data[k])


class TestHDF4(unittest.TestCase):
    def setUp(self):
        self.path = "/non/existent/path"
        self.hdf = HDF4(self.path)

    def test_get_coords(self):
        # Stub an HDF4 VData object that supports reading
        m = StubVData({
            "NVlat2": [[12345678]],
            "NVlng2": [[12345678]]
        })

        coords = self.hdf._get_coords(m, self.path)
        assert coords == {
            "lat": [1.2345678],
            "lon": [1.2345678]
        }

    def test_parse_timestamps_ddmmyyy(self):
        # Test dd/mm/yyyy format
        time_dict = {
            "date": "01/01/1993",
            "start_time": ["101532"],
            "end_time": ["120212"]
        }

        assert self.hdf._parse_timestamps(time_dict) == {
                "start_time": "1993-01-01T10:15:32",
                "end_time": "1993-01-01T12:02:12"
        }

    def test_parse_timestamps_ddmmyy(self):
        # Test dd/mm/yy format
        time_dict = {
            "date": "01/01/93",
            "start_time": ["101532"],
            "end_time": ["120212"]
        }

        assert self.hdf._parse_timestamps(time_dict) == {
                "start_time": "1993-01-01T10:15:32",
                "end_time": "1993-01-01T12:02:12"
        }

    def test_parse_timestamps_bad(self):
        time_dict = {
            "date": "aa/bb/cccc",
            "start_time": ["101010"],
            "end_time": ["999999"]
        }

        self.assertRaises(UnboundLocalError,
                          self.hdf._parse_timestamps,
                          time_dict)

    def test_get_temporal(self):
        hdf = HDF4(self.path)

        m = StubVData({
            "MIdate": [[ord(x)] for x in "19/07/10"],
            "MIstime": [["100419"]],
            "MIetime": [["110101"]],
        })

        timestamps = self.hdf._get_temporal(m, self.path)
        assert timestamps == {
            "start_time": "2010-07-19T10:04:19",
            "end_time": "2010-07-19T11:01:01",
        }

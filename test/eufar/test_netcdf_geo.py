"""
Test module for eufar.netcdf_geo
"""

import os
import unittest

from eufar import netcdf_geo


class TestNetCDF(unittest.TestCase):
    """
    Test class for eufar.netcdf_geo.NetCDF
    """
    def setUp(self):
        # Hardwire in a test NetCDF filename
        path = os.path.abspath(
            "../data/nc/core-1Hz_safire-piper-aztec_20110625_r0_az110014.nc")
        self.netcdf = netcdf_geo.NetCDF(path)

    def test_get_netcdf_var_from_regex(self):
        pass

    def test_nc_var_from_list(self):
        pass

    def test_time_from_num_format(self):
        pass

    def test_time_from_str_format(self):
        pass

    def test_get_time_data(self):
        pass

    def test_get_geospatial(self):
        pass

    def test_get_properties(self):
        pass

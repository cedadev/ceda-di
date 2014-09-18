"""
Test module for eufar.netcdf_geo
"""

import re
import unittest
from mock import Mock

from eufar.netcdf_geo import NetCDF
from test import netCDF4

class TestNetCDF(unittest.TestCase):
    """
    Test class for eufar.netcdf_geo.NetCDF
    """
    def setUp(self):
        self.path = "/path/to/some/file"

    def test_nc_var_from_regex(self):
        # Uppercase
        with NetCDF(self.path) as ncdf:
            ncdf.variables = ["test", "TIME"]
            assert ncdf._nc_var_from_regex("time", ncdf,
                                           re.IGNORECASE) == "TIME"

        # Lowercase
        with NetCDF(self.path) as ncdf:
            ncdf.variables = ["test", "more test",
                              "time", "teeeeeeest"]
            assert ncdf._nc_var_from_regex("time", ncdf,
                                           re.IGNORECASE) == "time"

        # Error
        with NetCDF(self.path) as ncdf:
            ncdf.variables = ["brian", "spam", "error"]
            assert ncdf._nc_var_from_regex("time", ncdf,
                                           re.IGNORECASE) is None

    def test_nc_var_from_list(self):
        with NetCDF(self.path) as ncdf:
            possible_vars = ["pressure", "PRESSURE"]
            ncdf.variables = ["pressure", "something else"]
            assert ncdf._nc_var_from_list(possible_vars, ncdf) == "pressure"

        with NetCDF(self.path) as ncdf:
            possible_vars = ["altitude", "cheese", "ni"]
            ncdf.variables = ["height", "angular momentum"]
            self.assertRaises(AttributeError,
                ncdf._nc_var_from_list, possible_vars, ncdf)

    def test_get_time_data(self):
        param = {
            "name": "Brian"
        }

        mock = Mock(return_value=param)
        #with NetCDF(self.path) as ncdf:
        #    ncdf.get_time_data(mock)

    def test_get_parameters(self):
        param = {
            "name": "Brian"
        }

        mock = Mock(return_value=param)
        #with NetCDF(self.path) as ncdf:
        #    ncdf.get_time_data(mock)

    def test_time_from_num_format(self):
        pass

    def test_time_from_str_format(self):
        pass

    def test_get_geospatial(self):
        pass

    def test_get_properties(self):
        pass

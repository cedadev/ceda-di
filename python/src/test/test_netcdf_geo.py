"""
Test module for ceda_di.netcdf_geo
"""

import re
import unittest

from ceda_di.netcdf_geo import NetCDF
from ceda_di.metadata.product import Parameter

class TestNetCDF(unittest.TestCase):
    """
    Test class for ceda_di.netcdf_geo.NetCDF
    """
    def setUp(self):
        self.path = "/path/to/some/file"

    def test_nc_var_from_regex(self):
        with NetCDF(self.path) as ncdf:
            ncdf.variables = ["test", "TIME"]
            assert ncdf._nc_var_from_regex("time", ncdf,
                                           re.IGNORECASE) == "TIME"

        with NetCDF(self.path) as ncdf:
            ncdf.variables = ["test", "more test",
                              "time", "teeeeeeest"]
            assert ncdf._nc_var_from_regex("time", ncdf,
                                           re.IGNORECASE) == "time"

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

    def test_get_parameters(self):
        class Mock(object):
            __dict__ = {"thing": "Brian",
                        "something": "some other thing"}

        item = Mock()
        param = {"name": item}
        with NetCDF(self.path) as ncdf:
            ncdf.variables = param
            assert isinstance(ncdf.get_parameters(ncdf), list)
            assert isinstance(ncdf.get_parameters(ncdf)[0], Parameter)

    def test_time_from_num_format(self):
        pass

    def test_time_from_str_format(self):
        pass

    def test_get_time_data(self):
        #with NetCDF(self.path) as ncdf:
        #    ncdf.get_time_data(ncdf)
        pass

    def test_get_geospatial(self):
        pass

    def test_get_properties(self):
        pass

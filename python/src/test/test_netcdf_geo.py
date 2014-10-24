"""
Test module for ceda_di.netcdf_geo
"""

import unittest

from ceda_di.netcdf_geo import NetCDF_Base
from ceda_di.metadata.product import Parameter

class NetCDFStub(object):
    """Stub for netCDF4.Dataset"""

    class VarStub(object):
        """Parameter stub class"""
        def __init__(self, attributes):
            for key, value in attributes.iteritems():
                setattr(self, key, value)

        def __getitem__(self, key):
            return getattr(self, key)

    def __init__(self, fpath):
        self.fpath = fpath
        self.variables = {}

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def set(self, attr, value):
        """
        Set attribute on self.
        """
        setattr(self, attr, value)

    def add_variable(self, name, attributes):
        """Add a variable to self.variables"""
        self.variables[name] = self.VarStub(attributes)

class Test_NetCDF_Base(unittest.TestCase):
    """
    Test class for the main NetCDF_Base class.
    """
    def setUp(self):
        fpath = "/some/fake/file/here.nc"
        self.nc_stub = NetCDFStub(fpath)

    def test_get_params(self):
        self.nc_stub.add_variable("spam",
                             {"nobody expects": "the spanish inquisition"})

        assert NetCDF_Base.params(self.nc_stub)[0].__dict__ == {
            "name": "spam",
            "items": [{
                "name": "nobody expects",
                 "value": "the spanish inquisition"
            }]
        }

    @unittest.skip
    def test_get_temporal(self):
        self.nc_stub.add_variable(
            "time",
            {"units": "seconds since 1970-01-01 00:00:00"}
        )

        NetCDF_Base.temporal(self.nc_stub, "time")

    def test_find_var_by_standard_name(self):
        self.nc_stub.add_variable(
            "spam",
            {"standard_name": "spammity spam"}
        )

        assert NetCDF_Base.find_var_by_standard_name(
            self.nc_stub, "spammity spam"
        ) == "spam"

    def test_find_var_by_regex(self):
        self.nc_stub.add_variable(
            "spam",
            {"spam spam spam": "spammity spam"}
        )

        assert NetCDF_Base.find_var_by_regex(
            self.nc_stub,
            "SPAM{1,3}"
        ) == "spam"

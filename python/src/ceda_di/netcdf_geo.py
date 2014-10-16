"""
Metadata adapters for NetCDF files.
"""

import logging
import re

import netCDF4

from _dataset import _geospatial
from metadata import product

class NetCDFFactory(object):
    """
    Factory for checking, handling and returning an appropriate metadata
    extraction class.
    :param str fpath: Path to NetCDF file
    """
    @staticmethod
    def get(fpath):
        """
        Return correct metadata extraction class based on metadata format.
        """
        try:
            with netCDF4.Dataset(fpath) as ncdf:
                convention = ncdf.Conventions

            if "CF" in convention:
                return NetCDF_CF(fpath, convention)
            elif "RAF" in convention:
                return NetCDF_RAF(fpath)

        except AttributeError:
            # Try creating a NetCDF extractor with an unknown convention
            return NetCDF_Unknown(fpath)

class NetCDF_Base(_geospatial):
    """
    Base class - provides common NetCDF metadata extraction methods
    :param str fpath: Path to NetCDF file
    """
    @staticmethod
    def params(ncdf):
        """
        :return list: List of metadata.product.Parameter objects
        """
        params = []
        for v_name, v_data in ncdf.variables.iteritems():
            param = product.Parameter(v_name, v_data.__dict__)
            params.append(param)

        return params

    @staticmethod
    def geospatial(ncdf, lat_name, lon_name):
        """
        Returns a dict containing normalised and sanitised lat/lons.
        :param lat_name: Name of parameter containing latitude values
        :param lon_name: Name of parameter containing longitude values
        :return geospatial: Geospatial information as dict.
        """
        lats = ncdf.variables[lat_name][:].ravel()[10:-10]
        lons = ncdf.variables[lon_name][:].ravel()[10:-10]
        return {
            "lat": lats,
            "lon": lons
        }

class NetCDF_CF(_geospatial):
    """
    CF-compliant NetCDF metadata extraction class.
    """
    def __init__(self, fpath, convention):
        """
        :param str fpath: Path to NetCDF file
        """
        self.fpath = fpath
        self.logger = logging.getLogger(__name__)
        self.convention = convention

    def get_temporal(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            times = list(netCDF4.num2date(list(ncdf.variables["time"]),
                                          ncdf.variables["time"].units))
            return {
                "start_time": times[0].isoformat(),
                "end_time": times[-1].isoformat()
            }

    def get_parameters(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            return NetCDF_Base.params(ncdf)

    def get_geospatial(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            for key, value in ncdf.variables.iteritems():
                try:
                    if value.standard_name == "latitude":
                        lat_name = key
                    elif value.standard_name == "longitude":
                        lon_name = key
                except AttributeError:
                    continue

            if lat_name and lon_name:
                return NetCDF_Base.geospatial(ncdf, lat_name, lon_name)
            else:
                self.logger.info("Couldn't find lat/lon variables: %s" %
                                 self.fpath)

    def get_properties(self):
        """
        Return a metadata.product.Properties object populated with metadata.
        :return properties: Properties object populated with metadata
        """

        temporal = self.get_temporal()
        filesystem = self.get_filesystem(self.fpath)
        spatial = self.get_geospatial()
        data_format = {"format": ("NetCDF/%s" % self.convention)}
        parameters = self.get_parameters()

        return product.Properties(temporal=temporal,
                                  filesystem=filesystem,
                                  spatial=spatial,
                                  data_format=data_format,
                                  parameters=parameters)
class NetCDF_RAF(_geospatial):
    """
    :param str fpath: Path to NetCDF file
    """
    def __init__(self, fpath):
        pass

class NetCDF_Unknown(_geospatial):
    """
    A wrapper to extract NetCDF metadata that is stored using an unknown
    metadata convention.
    :param str fpath: Path to NetCDF file
    """
    def __init__(self, fpath):
        self.logger = logging.getLogger(__name__)
        self.logger.info("File \"%s\" has no associated metadata convention." %
                         fpath)
        pass

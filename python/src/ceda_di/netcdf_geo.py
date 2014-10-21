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
    def __init__(self, fpath):
        self.fpath = fpath

        try:
            with netCDF4.Dataset(self.fpath) as ncdf:
                self.convention = ncdf.Conventions
        except AttributeError:
            self.convention = None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_properties(self):
        """
        Return correct metadata extraction class based on metadata format.
        """
        if "CF" in self.convention:
            return NetCDF_CF(self.fpath, self.convention).get_properties()
        elif "RAF" in self.convention:
            return NetCDF_RAF(self.fpath, self.convention).get_properties()
        else:
            # Return a placeholder NetCDF extractor with no convention
            return NetCDF_Unknown(self.fpath).get_properties()

class NetCDF_Base(_geospatial):
    """
    Base class - provides common NetCDF metadata extraction methods
    :param str fpath: Path to NetCDF file
    """
    @staticmethod
    def params(ncdf):
        """
        Construct list of Parameters based on variables in NetCDF file.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
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
        Return a dict containing lat/lons from NetCDF file.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
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

    @staticmethod
    def temporal(ncdf, time_name):
        """
        Extract time values from Dataset using the variable name provided.
        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :param str time_name: Name of the time parameter
        """
        times = list(netCDF4.num2date(list(ncdf.variables[time_name]),
                                      ncdf.variables[time_name].units))
        return {
            "start_time": times[0].isoformat(),
            "end_time": times[-1].isoformat()
        }

    @staticmethod
    def find_var_by_standard_name(ncdf, standard_name):
        """
        Find a variable reference searching by CF standard name.
        :param Dataset ncdf: Reference to an opened netCDF4.Dataset object
        :param str standard_name: The CF standard name to search for
        """
        for key, value in ncdf.variables.iteritems():
            try:
                if value.standard_name.lower() == standard_name.lower():
                    return key
            except AttributeError:
                continue

        logger = logging.getLogger(__name__)
        logger.info("Could not find standard name variable: \"%s\"",
                     (standard_name))

    @staticmethod
    def find_var_by_regex(ncdf, regex):
        """
        Find a variable reference searching by regular expression.
        :param Dataset ncdf: Reference to an opened netCDF4.Dataset object
        :param re regex: Regular expression to match with variable name
        """
        for key in ncdf.variables.keys():
            if re.match(regex, key, flags=re.IGNORECASE):
                return key

        logger = logging.getLogger(__name__)
        logger.info("Could not find variable by regex: \"%s\"", regex)

class NetCDF_CF(_geospatial):
    """
    Metadata extraction class for CF-compliant NetCDF files.
    """
    def __init__(self, fpath, convention):
        self.fpath = fpath
        self.logger = logging.getLogger(__name__)
        self.convention = convention

    def get_temporal(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            time_name = NetCDF_Base.find_var_by_standard_name(ncdf, "time")
            return NetCDF_Base.temporal(ncdf, time_name)

    def get_parameters(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            return NetCDF_Base.params(ncdf)

    def get_geospatial(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            lat_name = NetCDF_Base.find_var_by_standard_name(ncdf, "latitude")
            lon_name = NetCDF_Base.find_var_by_standard_name(ncdf, "longitude")

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
        data_format = {"format": ("NetCDF/%s" % self.convention)}
        return product.Properties(temporal=self.get_temporal(),
                                  filesystem=self.get_filesystem(self.fpath),
                                  spatial=self.get_geospatial(),
                                  data_format=data_format,
                                  parameters=self.get_parameters())


class NetCDF_RAF(_geospatial):
    """
    Metadata extraction class for NCAR-RAF-compliant NetCDF.
    """
    def __init__(self, fpath, convention):
        self.fpath = fpath
        self.logger = logging.getLogger(__name__)
        self.convention = convention

    def get_temporal(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            time_name = NetCDF_Base.find_var_by_standard_name(ncdf, "time")
            return NetCDF_Base.temporal(ncdf, time_name)

    def get_parameters(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            return NetCDF_Base.params(ncdf)

    def get_geospatial(self):
        try:
            # Try finding corrected latitude and longitude
            with netCDF4.Dataset(self.fpath) as ncdf:
                return NetCDF_Base.geospatial(ncdf, "LATC", "LONC")
        except AttributeError:
            lat_name = NetCDF_Base.find_var_by_standard_name(ncdf, "latitude")
            lon_name = NetCDF_Base.find_var_by_standard_name(ncdf, "longitude")

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
        data_format = {"format": ("NetCDF/%s" % self.convention)}
        return product.Properties(temporal=self.get_temporal(),
                                  filesystem=self.get_filesystem(self.fpath),
                                  spatial=self.get_geospatial(),
                                  data_format=data_format,
                                  parameters=self.get_parameters())


class NetCDF_Unknown(_geospatial):
    """
    A wrapper to extract NetCDF metadata that is stored using an unknown
    metadata convention, or no known associated metadata convention.
    """
    def __init__(self, fpath):
        self.fpath = fpath
        self.logger = logging.getLogger(__name__)
        self.logger.info("No metadata convention: \"%s\"" % fpath)

    def get_properties(self):
        return None

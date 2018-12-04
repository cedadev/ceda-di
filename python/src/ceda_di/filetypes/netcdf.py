"""
Metadata adapters for NetCDF files.
"""

import logging
import re
import os

import numpy.ma
import netCDF4

from datetime import datetime, timedelta
from ceda_di._dataset import _geospatial
from ceda_di.metadata import product


class NetCDFFactory(object):
    """
    Factory for checking, handling and returning an appropriate metadata
    extraction class.

    :param str fpath: Path to NetCDF file
    """
    def __init__(self, fpath):
        self.fpath = fpath

        # Try fetching the 'Convention' global variable from the NetCDF header.
        # Some organisations don't capitalise "Convention" in accordance with
        # the CF/RAF spec, so a regular expression is needed...
        self.convention = None
        with netCDF4.Dataset(self.fpath) as ncdf:
            for attr in ncdf.ncattrs():
                if re.match(attr, "conventions", flags=re.IGNORECASE):
                    self.convention = getattr(ncdf, attr)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_properties(self):
        """
        Return correct metadata extraction class based on metadata format.
        """
        if not self.convention:
            # Return a placeholder NetCDF handler with no convention
            return NetCDF_Unknown(self.fpath).get_properties()
        elif "CF" in self.convention:
            return NetCDF_CF(self.fpath, self.convention).get_properties()
        elif "RAF" in self.convention:
            return NetCDF_RAF(self.fpath, self.convention).get_properties()
        else:
            # Return a placeholder NetCDF handler and log the unknown convention
            return NetCDF_Unknown(self.fpath, self.convention).get_properties()


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
        :returns list: List of metadata.product.Parameter objects
        """
        params = []
        for v_name, v_data in ncdf.variables.iteritems():
            param = product.Parameter(v_name, v_data.__dict__)
            params.append(param)

        return params

    @staticmethod
    def clean_coordinate(coord):
        """Return True if coordinate is valid."""
        try:
            # This filters out misconfigured "_FillValue" elements
            if coord == 0.0 or numpy.ma.is_masked(coord):
                return False

            int(coord)  # If this fails, "coord" is not a number!

            return True
        except ValueError:
            return False

    @staticmethod
    def geospatial(ncdf, lat_name, lon_name):
        """
        Return a dict containing lat/lons from NetCDF file.

        :param Dataset ncdf: Reference to an opened netcdf4.Dataset object
        :param lat_name: Name of parameter containing latitude values
        :param lon_name: Name of parameter containing longitude values
        :returns: Geospatial information as dict.
        """

        # Filter out items that are equal to "masked"
        lats = filter(NetCDF_Base.clean_coordinate,
                      ncdf.variables[lat_name][:].ravel())
        lons = filter(NetCDF_Base.clean_coordinate,
                      ncdf.variables[lon_name][:].ravel())
        return {
            "type": "track",
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
        try:

            times = list(netCDF4.num2date(list(ncdf.variables[time_name]),
                                          ncdf.variables[time_name].units))
            return {
                "start_time": times[0].isoformat(),
                "end_time": times[-1].isoformat()
            }
        except:
            return None

    @staticmethod
    def estimate_temporal_from_filename(fpath):

        pattern = r'(?P<year>[0-9]{4})(?P<month>[0-9]{2})(?P<day>[0-9]{2})(?P<hour>[0-9]{2})?(?P<minute>[0-9]{2})?'
        m = re.search(pattern, os.path.basename(fpath))
        key_list = ["year", "month", "day", "hour", "minute"]
        kwargs = {}
        for key in key_list:
            if m.group(key):
                kwargs[key] = int(m.group(key))

        start_date = datetime(**kwargs)
        end_date = datetime(kwargs["year"], kwargs["month"], kwargs["day"]) + timedelta(1)

        return {
            "start_time": start_date.isoformat(),
            "end_time": end_date.isoformat()
        }

    @staticmethod
    def find_var_by_standard_name(ncdf, fpath, standard_name):
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
        logger.warning("Could not find standard name variable \"%s\": %s, trying by regex." %
                     (standard_name, fpath))

        key = NetCDF_Base.find_var_by_regex(ncdf, fpath, "^%s$" % standard_name)
        if key:
            return key


    @staticmethod
    def find_var_by_regex(ncdf, fpath, regex):
        """
        Find a variable reference searching by regular expression.

        :param Dataset ncdf: Reference to an opened netCDF4.Dataset object
        :param re regex: Regular expression to match with variable name
        """
        for key in ncdf.variables.keys():
            if re.match(regex, key, flags=re.IGNORECASE):
                return key

        logger = logging.getLogger(__name__)
        logger.error("Could not find variable by regex: \"%s\": %s" % (regex, fpath))

    @staticmethod
    def get_flight_info(fname):
        """
        Return a dictionary populated with metadata about the flight that the
        given data file was captured on - flight number, organisation, etc.

        :return: A dict containing flight metadata.
        """
        patterns = {
            "faam": {
                "patterns": [

                    r"_(?P<flight_num>[a-z](\d{3}))"
                ]
            },
            "safire": {
                "patterns": [
                    r"_(?P<flight_num>((as|az|fs)\d{6}))"
                ]
            }
        }

        for org, info in patterns.iteritems():
            for pattern in info["patterns"]:
                match = re.search(pattern, fname)
                if match:
                    flight_info = {
                        "organisation": org,
                        "flight_num": match.group("flight_num")
                    }

                    return flight_info


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
            time_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "time")
            temporal = NetCDF_Base.temporal(ncdf, time_name)
            if temporal:
                return temporal
            else:
                # Can't read time data, approximate time from filename
                return NetCDF_Base.estimate_temporal_from_filename(self.fpath)

    def get_parameters(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            return NetCDF_Base.params(ncdf)

    def get_geospatial(self):
        with netCDF4.Dataset(self.fpath) as ncdf:
            lat_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "latitude")
            lon_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "longitude")

            if lat_name and lon_name:
                return NetCDF_Base.geospatial(ncdf, lat_name, lon_name)
            else:
                self.logger.error("Could not find lat/lon variables: %s" %
                                  self.fpath)

    def get_properties(self):
        """
        Return a metadata.product.Properties object populated with metadata.

        :returns: Properties object populated with metadata
        """
        data_format = {"format": ("NetCDF/%s" % self.convention)}
        filesystem = self.get_filesystem(self.fpath)
        flight_info = NetCDF_Base.get_flight_info(filesystem["filename"])
        return product.Properties(temporal=self.get_temporal(),
                                  filesystem=filesystem,
                                  spatial=self.get_geospatial(),
                                  data_format=data_format,
                                  parameters=self.get_parameters(),
                                  flight_info=flight_info)


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
            time_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "time")
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
            lat_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "latitude")
            lon_name = NetCDF_Base.find_var_by_standard_name(ncdf, self.fpath, "longitude")

            if lat_name and lon_name:
                return NetCDF_Base.geospatial(ncdf, lat_name, lon_name)
            else:
                self.logger.error("Couldn't find lat/lon variables: %s" %
                                  self.fpath)

    def get_properties(self):
        """
        Return a metadata.product.Properties object populated with metadata.

        :returns: Properties object populated with metadata
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
    def __init__(self, fpath, convention=None):
        self.fpath = fpath
        self.logger = logging.getLogger(__name__)

        if not convention:
            self.logger.error("Missing metadata convention: \"%s\"" % fpath)
        else:
            self.logger.error("Unrecognised metadata convention \"%s\": \"%s\"" %
                              (convention, fpath))

    def get_properties(self):
        return None

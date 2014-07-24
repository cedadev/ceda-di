# Adapted from Axel's KML script (axll@faam.ac.uk)

from datetime import timedelta, datetime as dt
import json
import logging
import numpy
import os
import re
import sys
import time

from netCDF4 import Dataset

from _dataset import _geospatial
from metadata import product

class NetCDF(_geospatial):
    TIME_FORMATS = ["seconds since %Y-%m-%d %H:%M:%S %z",
                    "seconds since %Y-%m-%d %H:%M:%S %Z",
                    "seconds since %Y-%m-%d %H:%M:%S 00:00 %Z",
                    "seconds since %Y-%m-%d %H:%M:%S 00:00:00 %Z"]

    LAT_NAMES = ["GPS_LAT", "LAT_GIN", "pos_lat_gps_25", "pos_lat_gps_1",
                 "pos_lat_airinspp_1", "GPS_LAT_NP", "Lat", "latitude"]

    LON_NAMES = ["GPS_LON", "LON_GIN", "pos_lon_gps_25", "pos_lon_gps_1",
                 "pos_lon_airinspp_1", "GPS_LON_NP", "Lon", "longitude"]

    ALT_NAMES = ["ALTITUDE", "ALT_GIN", "alt_alti_gps_25",
                 "alt_alti_gps_1", "alt_airinspp_1", "GPS_ALT_NP",
                 "Alt", "height_above_sea_level"]

    def __init__(self, fpath):
        self.logger = logging.getLogger(__name__)
        self.fpath = fpath

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def _get_netcdf_var_from_regex(self, regex, nc, flags=None):
        """
        Return the first matching variable from 'nc', that matches 'regex'.

        :param str(regex): Regex for variable name to match
        :param netCDF4.Dataset nc: NetCDF4 dataset to search for variables in
        :return str(var_name): The name of the first item from var_list in nc
        """
        for var in nc.variables:
            match = re.match(regex, var, flags=flags)
            if match is not None:
                return var

    def _nc_var_from_list(self, var_list, nc):
        """
        Return the first matching variable from 'var_list' that's in 'nc'.

        :param list(str) var_list: List of variable names
        :param netCDF4.Dataset nc: NetCDF4 dataset to search for variables in
        :return str(var_name): The name of the first item from var_list in nc
        """
        for var in var_list:
            if var in nc.variables:
                return var

        self.logger.error("No variables from '%s' could be found in %s" %
                     (str(var_list), self.fpath))
        raise AttributeError("Could not find attribute in list")

    def _time_from_num_format(self, nc, tm_var):
        """
        Return a flat list of timestamps from the NetCDF file, calculated
        from either epoch time, GPS time or Julian fractional time.

        :param netCDF4.Dataset nc: Dataset to extract timestamps from
        :param str tm_var: Variable name for "time" in nc
        :return list(datetime.datetime): List of datetime objects
        """
        # TODO Julian fractional time

        shape = nc.variables[tm_var].shape
        if len(shape) <= 1:
            tm_list = list(nc.variables[tm_var][:].ravel())
        elif len(shape) == 2 and shape[0] == 1:
            # Timestamp units in these files are "since midnight" which is
            # quite vague... Return blank list until I've implemented it
            self.logger.info("Timestamp format too vague: %s" % self.fpath)
            return []
        else:
            # If this is reached, the times are in a strange numpy.ndarray
            # Here, we convert to datetime objects (small loss of precision)
            times = list(nc.variables[tm_var][:].ravel(order='F'))
            tm_list = []
            for i in xrange(0, len(times), shape[0]):
                time = []
                for j in xrange(0, shape[0]):
                    time.append(int(times[i + j]))
                tm_list.append(dt(*time))

            return tm_list

        if hasattr(nc.variables[tm_var], "units"):
            # Try to parse from epoch time
            tm_str = nc.variables[tm_var].units
        elif hasattr(nc.variables[tm_var], "Units"):
            tm_str = nc.variables[tm_var].Units
        elif hasattr(nc, "date"):
            # Try to parse from GPS time
            nc_date = re.match(r"(\d{2})/(\d{2})/(\d{4})", nc.date).groups()
            tm_str = ("seconds since %s-%s-%s 00:00:00 UTC" %  # Continued
                     (nc_date[2], nc_date[1], nc_date[0]))
        else:
            tm_str = "seconds since 1970-01-01 00:00:00 00:00 UTC"
            self.logger.error("Unknown timestamp units in %s, assume epoch" %
                              (self.fpath))

        # Try converting the epoch/GPS timestamps to datetime objects here
        for f in self.TIME_FORMATS:
            try:
                base_time = dt.strptime(tm_str, f)
                timestamps = [base_time +
                              timedelta(seconds=float(sec))
                              for sec in tm_list]
                return timestamps
            except:
                continue

        # Couldn't work out what times were, return empty list
        return []

    def _time_from_str_format(self, nc, tm_var):
        """
        Return a flat list of timestamps from the NetCDF file, calculated
        from an ISO-style timestamp (e.g. 2011-08-04 00:00:00).

        :param netCDF4.Dataset nc: Dataset to extract timestamps from
        :param str tm_var: Variable name for "time" in nc
        :return list(datetime.datetime): List of datetime objects
        """
        for tm_str in self.TIME_FORMATS:
            try:
                tm_list = nc.variables[tm_var]
                base_time = dt.strptime(str(tm_list[0]), tm_str)
                timestamps = [base_time + timedelta(seconds=int(sec))  # Cont.
                              for sec in tm_list]
                return timestamps
            except ValueError:
                # Variable isn't in the format we tried, try next alternative
                continue

        # Raise error if list is exhausted
        self.logger.error("Couldn't match timestamp format: %s" % self.fpath)
        raise ValueError("Could not match format for time: %s" % tm_list[0])

    def get_time_data(self, nc):
        """
        Return a flat list of timestamps from the NetCDF file.

        :param netCDF4.Dataset nc: Dataset to extract timestamps from
        :param str tm_var: Variable name for "time" in nc
        :return list(datetime.datetime): List of datetime objects
        """
        # If base_time isn't in expected format, we may have to calculate it
        tm_var = self._get_netcdf_var_from_regex("time",
                                                 nc, flags=re.IGNORECASE)
        try:
            datum = nc.variables[tm_var][0]
        except KeyError:
            self.logger.error("No time variable: %s" % self.fpath)
            return []

        # If 'datum' is a numpy ndarray then check type of first item
        if isinstance(datum, numpy.ndarray):
            try:
                datum = datum.flat[0]
            except AttributeError:
                self.logger.error("Could not flatten array: %s" % self.fpath)
                return []

        # Is time a numeric time format? (epoch, GPS or Julian)
        if isinstance(datum, numpy.float32) or \
                isinstance(datum, numpy.float64):
            return self._time_from_num_format(nc, tm_var)

        # If string, then time is timestamp
        elif isinstance(datum, str):
            return self._time_from_str_format(nc, tm_var)

    def get_geospatial(self, netcdf_data):
        """
        Open specified NetCDF file and extract lat/lon/alt/timestamp data.
        :return dict: Dict with lat/lon/alt and timestamp lists for each file
        """

        try:
            lon_var = self._nc_var_from_list(self.LON_NAMES, netcdf_data)
            lon = netcdf_data.variables[lon_var][:].ravel()[10:-10]

            lat_var = self._nc_var_from_list(self.LAT_NAMES, netcdf_data)
            lat = netcdf_data.variables[lat_var][:].ravel()[10:-10]

            alt_var = self._nc_var_from_list(self.ALT_NAMES, netcdf_data)
            alt = netcdf_data.variables[alt_var][:].ravel()[10:-10]

            geospatial = {
                "lon": [float(x) for x in lon],
                "lat": [float(x) for x in lat],
                "alt": [float(x) for x in alt],
            }

            return geospatial
        except (KeyError, AttributeError) as err:
            self.logger.info("No GPS metadata: %s" % self.fpath)
            return None

    def get_properties(self):
        with Dataset(self.fpath, 'r') as netcdf_data:
            # Timestamps
            timestamps = self.get_time_data(netcdf_data)

            try:
                temporal = {
                    "start_time": dt.isoformat(timestamps[0]),
                    "end_time": dt.isoformat(timestamps[-1])
                }
            except (TypeError, IndexError):
                self.logger.info("No temporal metadata: %s" % self.fpath)
                temporal = None

            # File-level
            file_level = super(NetCDF, self).get_file_level(self.fpath)

            # Geospatial
            geospatial = self.get_geospatial(netcdf_data)

            # Data format
            data_format = {"format": "NetCDF"}

            # Create properties object
            props = product.Properties(temporal=temporal,
                                       file_level=file_level,
                                       spatial=geospatial,
                                       data_format=data_format)

            return props

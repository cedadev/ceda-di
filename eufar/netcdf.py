#! /usr/bin/env python
# Adapted from Axel's KML script (axll@faam.ac.uk)

from datetime import timedelta, datetime as dt
from netCDF4 import Dataset
import json
import numpy
import os
import re
import sys
import time
import tools.nc_dump

# TODO move this lot to a config file
TIME_FORMATS = ["seconds since %Y-%m-%d %H:%M:%S %z",
                "seconds since %Y-%m-%d %H:%M:%S %Z",
                "seconds since %Y-%m-%d %H:%M:%S 00:00 %Z"]

LAT_NAMES = ["GPS_LAT", "LAT_GIN", "pos_lat_gps_25", "pos_lat_gps_1",
             "pos_lat_airinspp_1", "GPS_LAT_NP", "Lat", "latitude"]

LON_NAMES = ["GPS_LON", "LON_GIN", "pos_lon_gps_25", "pos_lon_gps_1",
             "pos_lon_airinspp_1", "GPS_LON_NP", "Lon", "longitude"]

ALT_NAMES = ["ALTITUDE", "ALT_GIN", "alt_alti_gps_25", "alt_alti_gps_1",
             "alt_airinspp_1", "GPS_ALT_NP", "Alt", "height_above_sea_level"]


def _get_netcdf_var_from_regex(regex, nc, flags=None):
    """
    Return the first matching variable from 'nc', that matches 'regex'.

    :param str(regex): Regex for variable name to match
    :param netCDF4.Dataset nc: NetCDF4 dataset to search for variables in
    :return str(var_name): The name of the first variable from var_list in nc
    """
    for var in nc.variables:
        search = re.search(regex, var, flags=flags)
        if search is not None:
            return var


def _get_netcdf_var_from_list(var_list, nc):
    """
    Return the first matching variable from 'var_list' that's in 'nc'.

    :param list(str) var_list: List of variable names
    :param netCDF4.Dataset nc: NetCDF4 dataset to search for variables in
    :return str(var_name): The name of the first variable from var_list in nc
    """
    for var in var_list:
            if var in nc.variables:
                return var

    raise AttributeError("Could not find attribute in list: %s", var_list)


def _time_from_num_format(nc, tm_var):
    """
    Return a 1-dimensional list of timestamps from the NetCDF file, calculated
    from either epoch time, GPS time or Julian fractional time.
    
    :param netCDF4.Dataset nc: Dataset to extract timestamps from
    :param str tm_var: Variable name for "time" in nc
    :return list(datetime.datetime): List of datetime objects
    """
    # TODO Julian fractional time
    
    shape = nc.variables[tm_var].shape[0]
    if shape == 1:
        tm_list = list(nc.variables[tm_var][:].ravel())
    else:
        # If this is reached, the times are in a strange numpy.ndarray
        # Here, we convert to datetime objects (with a small loss of precision)
        times = list(nc.variables[tm_var][:].ravel(order='F'))
        tm_list = []
        for i in xrange(0, len(times), shape):
            time = []
            for j in xrange(0, shape):
                time.append(int(times[i + j]))
            tm_list.append(dt(*time))

        return tm_list

    if hasattr(nc.variables[tm_var], "units"):
        # Tries to parse from epoch time
        tm_str = nc.variables[tm_var].units
    elif hasattr(nc, "date"):
        # Tries to parse from GPS time
        nc_date = re.match(r"(\d{2})/(\d{2})/(\d{4})", nc.date).groups()
        tm_str = ("seconds since %s-%s-%s 00:00:00 UTC" %  # Continued
                 (nc_date[2], nc_date[1], nc_date[0]))

    try:
        # Try converting the epoch/GPS timestamps to datetime objects here
        base_time = dt.strptime(tm_str, TIME_FORMATS[1])
        timestamps = [base_time +
                      timedelta(seconds=float(sec))
                      for sec in tm_list]
        return timestamps
    except ValueError:
        # I tried :( couldn't work out what times were, return empty list
        return []


def _time_from_str_format(nc, tm_var):
    """
    Return a 1-dimensional list of timestamps from the NetCDF file, calculated
    from an ISO-style timestamp (e.g. 2011-08-04 00:00:00).
        
    :param netCDF4.Dataset nc: Dataset to extract timestamps from
    :param str tm_var: Variable name for "time" in nc
    :return list(datetime.datetime): List of datetime objects
    """
    for tm_str in TIME_FORMATS:
        try:
            tm_list = nc.variables[tm_var]
            base_time = dt.strptime(str(tm_list[0]), tm_str)
            timestamps = [base_time + timedelta(seconds=int(sec))  # Continued
                          for sec in tm_list]
            return timestamps
        except ValueError:
            # Variable isn't in the format we tried, so try next alternative
            continue

    # Raise error if list is exhausted
    raise ValueError("Could not match format for time: %s" % tm_list[0])


def get_time_data(nc):
    """
    Return a 1-dimensional list of timestamps from the NetCDF file.
    Uses helper methods to do so.
        
    :param netCDF4.Dataset nc: Dataset to extract timestamps from
    :param str tm_var: Variable name for "time" in nc
    :return list(datetime.datetime): List of datetime objects
    """
    # If base_time isn't in the format we expect, we may have to calculate it
    tm_var = _get_netcdf_var_from_regex("time", nc, flags=re.IGNORECASE)
    datum = nc.variables[tm_var][0]

    # If 'datum' is a numpy n-dimensional array then check type of first item
    if isinstance(datum, numpy.ndarray):
        datum = datum.flat[0]

    # Is time a numeric time format? (epoch, GPS or Julian)
    if isinstance(datum, numpy.float32) or isinstance(datum, numpy.float64):
        return _time_from_num_format(nc, tm_var)
    # If string, then time is timestamp
    elif isinstance(datum, str):
        return _time_from_str_format(nc, tm_var)


def get_geospatial(fname):
    """
    Open specified NetCDF file and extract lat/lon/alt/timestamp data.

    :param str fname: Filename of the NetCDF file to open
    :return dict: Dict with lists of lat/lon/alt and timestamps for each file
    """

    with Dataset(fname, 'r') as netcdf_data:
        timestamps = get_time_data(netcdf_data)
        try:
            lon_var = _get_netcdf_var_from_list(LON_NAMES, netcdf_data)
            lon = netcdf_data.variables[lon_var][:].ravel()[10:-10]

            lat_var = _get_netcdf_var_from_list(LAT_NAMES, netcdf_data)
            lat = netcdf_data.variables[lat_var][:].ravel()[10:-10]

            alt_var = _get_netcdf_var_from_list(ALT_NAMES, netcdf_data)
            alt = netcdf_data.variables[alt_var][:].ravel()[10:-10]

            finfo = {
                "filename": os.path.basename(fname),
                "length": len(timestamps),
                "lon": [float(x) for x in lon],
                "lat": [float(x) for x in lat],
                "alt": [float(x) for x in alt],
                "time": [dt.isoformat(x) for x in timestamps]
            }

            return finfo
        except KeyError as k:
            tools.nc_dump.dump(netcdf_data)
            raise("\nKeyError: %s (%s)" % (str(k), fname))


if __name__ == "__main__":
    for fname in sys.argv[1:]:
        gps_info = get_geospatial(fname)
        print(fname)

        root_fname = os.path.splitext(os.path.basename(fname))[0] + ".json"
        out_name = "out/" + root_fname
        with open(out_name, 'w') as f:
            f.write(json.dumps(gps_info, indent=4))

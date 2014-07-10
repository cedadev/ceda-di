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

TIME_FORMATS = ["seconds since %Y-%m-%d %H:%M:%S %z",
                "seconds since %Y-%m-%d %H:%M:%S %Z",
                "seconds since %Y-%m-%d %H:%M:%S 00:00 %Z"]

LAT_NAMES = ["LAT_GIN", "pos_lat_gps_25", "pos_lat_gps_1",
             "pos_lat_airinspp_1", "GPS_LAT_NP"]
LON_NAMES = ["LON_GIN", "pos_lon_gps_25", "pos_lon_gps_1",
             "pos_lon_airinspp_1", "GPS_LON_NP"]
ALT_NAMES = ["ALT_GIN", "alt_alti_gps_25", "alt_alti_gps_1",
             "alt_airinspp_1", "GPS_ALT_NP"]


def _get_netcdf_var_from_regex(regex, nc, flags=None):
    """
    Returns the first matching variable from 'nc', that matches 'regex'.

    :param str(regex): Regex for variable name to match
    :param NetCDF4.Dataset nc: NetCDF4 dataset to search for variables in
    :return str(var_name): The name of the first variable from var_list in nc
    """
    for var in nc.variables:
        search = re.search(regex, var, flags=flags)
        if search is not None:
            return var


def _get_netcdf_var_from_list(var_list, nc):
    """
    Returns the first matching variable from 'var_list' that's in 'nc'.

    :param list(str) var_list: List of variable names
    :param NetCDF4.Dataset nc: NetCDF4 dataset to search for variables in
    :return str(var_name): The name of the first variable from var_list in nc
    """
    for var in var_list:
            if var in nc.variables:
                return var
    return None


def _time_from_gps_format(nc, tm_var):
    tm_list = list(nc.variables[tm_var][:].ravel())

    nc_date = re.match(r"(\d{2})/(\d{2})/(\d{4})", nc.date).groups()
    tm_str = "seconds since %s-%s-%s 00:00:00 UTC" % (nc_date[2],
                                                      nc_date[1],
                                                      nc_date[0])
    base_time = dt.strptime(tm_str, TIME_FORMATS[1])
    secs_past_base_time = tm_list
    timestamps = [base_time +
                  timedelta(seconds=float(sec))
                  for sec in secs_past_base_time]

    return timestamps


def _time_from_str_format(nc, tm_var):
    for tm_str in TIME_FORMATS:
        try:
            base_time = dt.strptime(str(tm_list[0]), tm_str)
            secs_past_base_time = tm_list
            timestamps = [base_time +
                          timedelta(seconds=int(sec))
                          for sec in secs_past_base_time]

            return timestamps
        except ValueError:
            # Variable isn't in the format we tried, so try next alternative
            continue

    # Raise error if time couldn't be parsed
    raise ValueError("Could not match format for time: %s" % tm)


def get_time_data(nc):
    """
    """
    # If base_time isn't in the format we expect, we may have to calculate it
    tm_var = _get_netcdf_var_from_regex("time", nc, flags=re.IGNORECASE)
    datum = nc.variables[tm_var][0][0]

    if isinstance(datum, numpy.float32) or isinstance(datum, numpy.float64):
        return _time_from_gps_format(nc, tm_var)
    else:
        return _time_from_str_format(nc, tm_var)


def get_lat_lon_alt_data(nc):
    print "nope"


def raw_gps_safire(fname):
    """
    Opens specified NetCDF file and extracts lat/lon/alt/timestamp data.

    :param str fname: Filename of the NetCDF file to open
    :returns: dict with lists of lat/lon/alt and timestamps for each file
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
                "filename": fname,
                "length": len(timestamps),
                "lon": [float(x) for x in lon],
                "lat": [float(x) for x in lat],
                "alt": [float(x) for x in alt],
                "time": [dt.isoformat(x) for x in timestamps]
            }

            return finfo
        except KeyError as k:
            print("KeyError: %s (%s)" % (str(k), fname))


for fname in sys.argv[1:]:
    gps_info = raw_gps_safire(fname)
    print(fname)

    out_name = "out/" + os.path.splitext(os.path.basename(fname))[0] + ".json"
    with open(out_name, 'w') as f:
        f.write(json.dumps(gps_info, indent=4))

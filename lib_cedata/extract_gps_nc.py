#! /usr/bin/env python
# Adapted from Axel's KML script (axel@faam)

from datetime import timedelta, datetime as dt
from netCDF4 import Dataset
import json
import os
import re
import sys
import time


def _netcdf_var(var_list, nc):
    """
    Returns the first matching variable from 'var_list' that's in 'nc'.

    :param list(str) var_list: List of variable names
    :param NetCDF4.Dataset nc: NetCDF4 dataset to search for variables in
    :return str var_name: The name of the first variable from var_list in nc
    """
    for var in var_list:
        if var in nc.variables:
            return var
    return None


def raw_gps_safire(fname):
    """
    Opens the given SAFIRE NetCDF file and extracts lat/lon/alt/timestamp data.

    :param str fname: Filename of the NetCDF file to open
    :returns: dict with lists of lat/lon/alt and timestamps for each file
    """
    TIME_NAMES = ["time", "Time", "TIME"]
    TIME_STRINGS = ["seconds since %Y-%m-%d %H:%M:%S %z",
                    "seconds since %Y-%m-%d %H:%M:%S %Z",
                    "seconds since %Y-%m-%d %H:%M:%S 00:00 %Z"]

    LAT_NAMES = ["LAT_GIN", "pos_lat_gps_25", "pos_lat_gps_1",
                 "pos_lat_airinspp_1", "GPS_LAT_NP"]
    LON_NAMES = ["LON_GIN", "pos_lon_gps_25", "pos_lon_gps_1",
                 "pos_lon_airinspp_1", "GPS_LON_NP"]
    ALT_NAMES = ["ALT_GIN", "alt_alti_gps_25", "alt_alti_gps_1",
                 "alt_airinspp_1", "GPS_ALT_NP"]

    with Dataset(fname, 'r') as netcdf_data:
        tm_var = _netcdf_var(TIME_NAMES, netcdf_data)
        if tm_var is not None:
            tm = str(netcdf_data.variables[tm_var].units).strip()
            base_time = None

            for tm_str in TIME_STRINGS:
                try:
                    base_time = dt.strptime(tm, tm_str)
                except ValueError as ve:
                    # Variable isn't in NC file, so try next alternative
                    print tm
                    continue

            secs = int(netcdf_data.variables[tm_var][0])
            flight_num = (base_time +
                          timedelta(seconds=secs)).strftime('%Y%m%d')

            try:
                lon_var = _netcdf_var(LON_NAMES, netcdf_data)
                lon = netcdf_data.variables[lon_var][10:-10]

                lat_var = _netcdf_var(LAT_NAMES, netcdf_data)
                lat = netcdf_data.variables[lat_var][10:-10]

                alt_var = _netcdf_var(ALT_NAMES, netcdf_data)
                alt = netcdf_data.variables[alt_var][10:-10]

                secs_past_base_time = \
                    list(netcdf_data.variables[tm_var][:].ravel())

                timestamp = [base_time +
                             timedelta(seconds=int(sec))
                             for sec in secs_past_base_time]

                finfo = {
                    "filename": fname,
                    "length": len(timestamp),
                    "lon": [float(x) for x in lon],
                    "lat": [float(x) for x in lat],
                    "alt": [float(x) for x in alt],
                    "timestamp": [dt.isoformat(x) for x in timestamp]
                }

                return finfo
            except KeyError as k:
                print("KeyError: %s (%s)" % (str(k), fname))
        else:
            print("Error: %s" % fname)


def raw_gps_faam(netcdf_data):
        try:
            title = nc.title
            flight_number = re.search('[bB]\d\d\d', title).group(0)[1:]
            print("%s: %s" % (fname, flight_number))
        except AttributeError:
            print("No flight num: %s" % fname)


for fname in sys.argv[1:]:
    gps_info = raw_gps_safire(fname)
    print(fname)

    out_name = "out/" + os.path.splitext(os.path.basename(fname))[0] + ".json"
    with open(out_name, 'w') as f:
        f.write(json.dumps(gps_info, indent=4))

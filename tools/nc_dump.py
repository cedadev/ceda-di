#! /usr/bin/env python

import datetime
import json
import netCDF4
import os
import sys


def iter_attributes(nc):
    sep = ": "
    for i in nc.ncattrs():
        yield (i, sep, getattr(nc, i))
        
        
def dump(nc):
    print("NetCDF Variable Summary")
    for k, s, v in iter_attributes(nc):
            print k, s, v
            
    print "\n", ('-' * 20), "\n"
    for k, v in nc.variables.iteritems():
        print k, ": ", v


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        with netCDF4.Dataset(arg, 'r') as nc:
            dump(nc)

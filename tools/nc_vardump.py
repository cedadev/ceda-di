#! /usr/bin/env python

from netCDF4 import Dataset
import json
import os
import sys

for arg in sys.argv[1:]:
    output_fname = os.path.splitext(os.path.basename(arg))[0]
    output_fname += ".json"
    with open(output_fname, 'w') as f:
        with Dataset(arg, 'r') as nc:
            f.write(json.dumps(nc.variables,
                               indent=4,
                               sort_keys=True,
                               default=repr))
                               
            for k, v in nc.variables.iteritems():
                print k, type(v), v[0]

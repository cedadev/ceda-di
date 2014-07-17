from pyhdf.HDF import *
from pyhdf.V import *
from pyhdf.VS import *
import json
import sys


def dump_lat_lng(refnum, v, vs):
    vg = v.attach(refnum)

    if vg._name != "Navigation":
        vg.detach()
        return

    coords = {}
    for nav in ["NVlat2", "NVlng2"]:
        ref = vs.find(nav)
        vd = vs.attach(ref)
        coords[nav] = []
        while True:
            try:
                rec = vd.read()
                coords[nav].append(rec[0][0])
            except HDF4Error:
                break
        vd.detach()
    vg.detach()

    return coords

# Open HDF file and instantiate interfaces
hdf = HDF(sys.argv[1])
vs = hdf.vstart()
v = hdf.vgstart()

# Check all vgroups, dump relevant data
q = multiprocessing.Queue()
ref = -1
while True:
    try:
        ref = v.getid(ref)
        dump_lat_lng(ref, v, vs, q)
    except HDF4Error:
        break

# Close interfaces and HDF file
v.end()
vs.end()
hdf.close()

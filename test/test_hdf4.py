from eufar.hdf4_geo import *
import json

with open("files.txt", 'r') as f:
    files = f.readlines()[:5]
    files = map(str.rstrip, files)

finfo = {}
for f in files:
    with HDF4_geo(f) as hdf:
        finfo.update(hdf.get_geospatial())

with open("out.csv", 'w') as f:
    for k, v in finfo.iteritems():
        f.write("latitude,longitude\n")
        for i in xrange(0, len(v["lat"])):
            if (i % 2 == 0):
                f.write("%f,%f\n" % (v["lat"][i], v["lng"][i]))

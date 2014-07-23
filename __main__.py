import os
import sys
from eufar import envi_geo, netcdf_geo

def write_properties(_geospatial_obj):
    fname = "out/%s.json" % os.splitext(fname)[0]  # Create JSON path
    with open(fname, 'w') as j:
        props = str(_geospatial_obj.get_properties())
        j.write(props)


def process_bil(path):
    with eufar.envi_geo.BIL(path) as b:
        json_fn = write_properties(b)


def process_nc(path):
    with eufar.netcdf_geo.NetCDF(path) as nc:
        write_properties(nc)


if __name__ == "__main__":
    if not os.path.isdir("out"):
        os.mkdir("out")

    file_counter = 0
    start_path = "/badc/eufar/data/aircraft/"
    for root, dirs, files in os.walk(start_path, followlinks=True):
        for f in files:
            path = os.path.join(root, f)

            # BIL navigation files
            if f.endswith(".hdr") and "nav" in f and "qual" not in f:
                process_bil(path)
            if f.endswith(".nc"):
                process_nc(path)

import datetime
import logging
import logging.config
import os
import sys
from eufar import envi_geo, netcdf_geo


def write_properties(fname, _geospatial_obj):
    fname = os.path.basename(fname)
    fname = "out/%s.json" % os.path.splitext(fname)[0]  # Create JSON path
    with open(fname, 'w') as j:
        props = str(_geospatial_obj.get_properties())
        j.write(props)


def process_bil(path):
    with envi_geo.BIL(path) as b:
        json_fn = write_properties(path, b)


def process_nc(path):
    with netcdf_geo.NetCDF(path) as nc:
        write_properties(path, nc)


def prepare_logging():
    if not os.path.isdir("log"):
        os.mkdir("log")

    logging.config.fileConfig("logging.conf")
    logger = logging.getLogger("main")

    return logger


if __name__ == "__main__":
    # Stop HDF5 library complaining
    os.system("export HDF5_DISABLE_VERSION_CHECK=2")

    # Set up logging
    logger = prepare_logging()
    logger.info("Beginning script at %s" % str(datetime.datetime.now()))

    # Make output directory for JSON
    if not os.path.isdir("out"):
        os.mkdir("out")

    start_path = "/badc/eufar/data/aircraft/"
    for root, dirs, files in os.walk(start_path, followlinks=True):
        for f in files:
            path = os.path.join(root, f)

            # BIL navigation files
            if f.endswith(".hdr") and "nav" in f and "qual" not in f:
                process_bil(path)
            if f.endswith(".nc"):
                process_nc(path)

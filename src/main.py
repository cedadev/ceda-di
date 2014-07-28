"""
Main script to handle processing of EUFAR data.
"""

import logging
import logging.config
import multiprocessing
import os

from eufar import envi_geo, exif_geo, netcdf_geo


def write_properties(fname, _geospatial_obj):
    """Write module properties to an output file."""
    fname = os.path.basename(fname)
    fname = "out/%s.json" % os.path.splitext(fname)[0]  # Create JSON path
    with open(fname, 'w') as j:
        props = str(_geospatial_obj.get_properties())
        j.write(props)


def process_bil(fpath):
    """Process BIL files."""
    with envi_geo.BIL(fpath) as bil:
        write_properties(fpath, bil)


def process_nc(fpath):
    """Process NetCDF files."""
    os.putenv("HDF5_DISABLE_VERSION_CHECK", "2")
    with netcdf_geo.NetCDF(fpath) as netcdf:
        write_properties(fpath, netcdf)


def process_tiff(fpath):
    """Process TIFF files."""
    with exif_geo.EXIF(fpath) as exif:
        write_properties(fpath, exif)


def prepare_logging():
    """Initial logging setup"""
    if not os.path.isdir("log"):
        os.mkdir("log")

    logging.config.fileConfig("logging.conf")
    log = logging.getLogger("main")

    return log


if __name__ == "__main__":
    # Set up logging
    LOGGER = prepare_logging()

    # Make output directory for JSON
    if not os.path.isdir("out"):
        os.mkdir("out")

    START_PATH = "/badc/eufar/data/aircraft/"
    processes = []
    for root, dirs, files in os.walk(START_PATH, followlinks=True):
        for f in files:
            path = os.path.join(root, f)

            if f.endswith(".hdr") and "nav" in f and "qual" not in f:
                proc = multiprocessing.Process(target=process_bil,
                                               args=(path,))
                processes.append(proc)
                proc.start()
            elif f.endswith(".nc"):
                proc = multiprocessing.Process(target=process_nc,
                                               args=(path,))
                processes.append(proc)
                proc.start()
            elif f.endswith(".tif"):
                proc = multiprocessing.Process(target=process_tiff,
                                               args=(path,))
                processes.append(proc)
                proc.start()

            while len(processes) > 45:
                p = processes.pop()
                p.join()

    # End
    for proc in processes:
        proc.join()

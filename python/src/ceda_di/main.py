"""
Main script to handle processing of CEDA Data Index data.
"""

import datetime
import json
import logging
import logging.config
import multiprocessing
import os
import sys

from ceda_di import envi_geo, exif_geo, hdf4_geo, netcdf_geo


def get_config(fname="config/ceda_di.json"):
    """
    Reads the configuration file into a dictionary
    :param fname: Path to the JSON configuration file
    :return dict: Dict containing parsed JSON config
    """
    try:
        with open(fname, "r") as f:
            return json.load(f)
    except IOError as ioe:
        sys.stderr.write("ERR: can't read config.\n%s\n" % str(ioe))
        exit(1)


def make_dirs(conf):
    """Make all necessary directories."""

    json_out = os.path.join(conf["outputpath"], conf["jsonpath"])
    if not os.path.isdir(json_out):
        os.makedirs(json_out)

    log_out = os.path.join(conf["outputpath"], conf["logpath"])
    if not os.path.isdir(log_out):
        os.makedirs(log_out)


def write_properties(fname, _geospatial_obj):
    """Write module properties to an output file."""
    fname = os.path.basename(fname)

    # Construct JSON path
    fname = "%s/%s.json" % (jsonpath, os.path.splitext(fname)[0])

    with open(fname, 'w') as j:
        props = str(_geospatial_obj.get_properties())
        j.write(props)


def process_bil(fpath):
    """Process BIL files."""
    with envi_geo.BIL(fpath) as bil:
        write_properties(fpath, bil)


def process_hdf4(fpath):
    """Process HDF4 files."""
    with hdf4_geo.HDF4(str(fpath)) as hdf:
        write_properties(fpath, hdf)


def process_nc(fpath):
    """Process NetCDF files."""
    os.putenv("HDF5_DISABLE_VERSION_CHECK", "2")
    with netcdf_geo.NetCDF(fpath) as netcdf:
        write_properties(fpath, netcdf)


def process_tiff(fpath):
    """Process TIFF files."""
    with exif_geo.EXIF(fpath) as exif:
        write_properties(fpath, exif)


def process_file((base, fname)):
    """Process a data file."""
    fpath = os.path.join(base, fname)
    if "raw" not in fpath:
        if fname.endswith("_nav_post_processed.bil.hdr"):
            process_bil(fpath)
        elif fname.endswith(".nc"):
            process_nc(fpath)
        elif fname.endswith(".tif"):
            process_tiff(fpath)
        elif fname.endswith(".hdf"):
            process_hdf4(fpath)


def prepare_logging(conf):
    """Initial logging setup"""

    fname = os.path.join(conf["outputpath"],
                         conf["logpath"],
                         conf["logfile"])
    logging_config = {
        "filename": fname,
        "format": conf["logging"]["format"],
        "level": logging.INFO
    }

    logging.basicConfig(**logging_config)
    log = logging.getLogger(__name__)

    return log


jsonpath = ""

def main():
    if len(sys.argv) > 1:
        config = get_config(sys.argv[1])
    else:
        config = get_config()
        
    # Read useful sections from config
    try:
        make_dirs(config)
        logger = prepare_logging(config)
        numcores = config["numcores"]
        datapath = config["datapath"]
        outpath = config["outputpath"]
        jsonpath = os.path.join(outpath, config["jsonpath"])
    except KeyError as k:
        sys.stderr.write("Missing configuration option: %s\n\n" % str(k))

    # Log beginning of processing
    start = datetime.datetime.now()
    logger.info("Metadata extraction started at: %s", start.isoformat())

    # Build list of file paths
    data_files = []
    for root, dirs, files in os.walk(datapath, followlinks=True):
        for f in files:
            data_files.append((root, f))

    if len(data_files) > 0:
        # Process files
        pool = multiprocessing.Pool(numcores)
        pool.map(process_file, data_files)
        pool.close()
        pool.join()

    # Log end of processing
    end = datetime.datetime.now()
    logger.info("Metadata extraction completed at: %s", end.isoformat())
    logger.info("Start: %s, End: %s, Total: %s",
                start.isoformat(), end.isoformat(), end - start)


if __name__ == "__main__":
    main()

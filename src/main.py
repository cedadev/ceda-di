"""
Main script to handle processing of EUFAR data.
"""

import datetime
import json
import logging
import logging.config
import multiprocessing
import os
import sys

from eufar import envi_geo, exif_geo, hdf4_geo, netcdf_geo


def get_config(fname="config/eufar.json"):
    """
    Reads the configuration file into a dictionary
    :param fname: Path to the JSON configuration file
    :return dict: Dict containing parsed JSON config
    """
    try:
        with open(fname, "r") as f:
            return json.load(f)
    except IOError as ioe:
        sys.stderr.write("ERR: can't read config.\n\t%s\n" % str(ioe))
        exit(1)


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


def prepare_logging(conf):
    """Initial logging setup"""
    if not os.path.isdir(conf["logpath"]):
        os.makedirs(conf["logpath"])

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
if __name__ == "__main__":
    # Config
    if len(sys.argv) > 1:
        config = get_config(sys.argv[1])
    else:
        config = get_config()

    # File paths
    try:
        logger = prepare_logging(config)
        numcores = config["numcores"]
        datapath = config["datapath"]
        outpath = config["outputpath"]
        jsonpath = os.path.join(outpath, config["jsonpath"])

        if not os.path.isdir(jsonpath):
            os.makedirs(jsonpath)
    except KeyError as k:
        sys.stderr.write("Missing configuration option: %s" % str(k))

    start = datetime.datetime.now()
    logger.info("Metadata extraction started at: %s", start.isoformat())
    processes = []
    for root, dirs, files in os.walk(datapath, followlinks=True):
        for f in files:
            path = os.path.join(root, f)

            if "raw" not in path:
                if f.endswith("_nav_post_processed.bil.hdr"):
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
                elif f.endswith(".hdf"):
                    proc = multiprocessing.Process(target=process_hdf4,
                                                   args=(path,))
                    processes.append(proc)
                    proc.start()

            while len(processes) > numcores:
                for p in processes:
                    if p.exitcode is not None:
                        processes.remove(p)

    # End
    for proc in processes:
        proc.join()

    end = datetime.datetime.now()
    logger.info("Metadata extraction completed at: %s", end.isoformat())
    logger.info("Start: %s, End: %s, Total: %s",
                start.isoformat(),
                end.isoformat(),
                end - start)

#! /usr/bin/env python

from __future__ import division
from math import asin, atan2, cos, degrees, pi, radians, sin
from scipy.ndimage import gaussian_filter1d
from scipy.spatial import ConvexHull

import eufar.envi as envi
import matplotlib.pyplot as plt
import numpy as np

import multiprocessing
import os
import time


def reprint(line):
    """
    Print text on the same line as the previous print statement.
    :param str line: The text to print
    """
    # http://stackoverflow.com/a/12586667
    CURSOR_UP = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print("%s%s%s" % (CURSOR_UP, ERASE_LINE, line))


def get_bil_nav(header_fname, mm_dict):
    """
    :param str header_fname: Filename of header file
    :param multiprocessing.manager.dict mm_dict: Proc-safe dictionary
                                datatype provided by "multiprocessing"
    """
    
    b = envi.BilFile(header_fname)
    bil = b.read_bil()

    swath_path = {
        "lines": b.hdr["lines"],
        "time": bil[0],
        "lat": bil[1],
        "lon": bil[2],
        "alt": bil[3],
        "roll": bil[4],
        "pitch": bil[5],
        "heading": bil[6]
    }

    mm_dict[header_fname] = swath_path


def wait_for_processes(proc_list, nprocs=0):
    """
    :param list proc_list: List of active processes
    :param int n_procs: Number of processes desired in the list

    Wait for processes in proc_list to complete until there are 'n_procs'
    processes remaining.
    """
    while len(proc_list) > nprocs:
        proc_list = [x for x in proc_list if (x.is_alive())]
        time.sleep(0.1)


def gen_file_list(path):
    """
    :param str path: Path of directory to walk
    :returns: list -- List of files in tree

    Recursively walk a directory tree, returning a list of files.
    """
    data_files = []  # List of viable data files
    print("")
    for root, dirs, files in os.walk(path, topdown=True):
        if root.endswith("navigation"):
            for f in files:
                if (f.endswith(".hdr") and ("qual" not in f)):
                    header_fpath = os.path.join(root, f)
                    data_files.append(header_fpath)
                    reprint("%d file(s) indexed." % (len(data_files)))

    return data_files


def latlon_offset(lat_dec, lon_dec, d_metres, tc_deg):
    """
    :param float lat_dec: Decimal latitude of the point to offset
    :param float lon_dec: Decimal longitude of the point to offset
    :param float d_metres: Distance to offset the coordinate by (metres)
    :param float tc_deg: Direction to offset point (degrees)
    :return: (float, float) -- Offset decimal latitude and longitude

        Calculate coordinates of a point offset by a certain distance
        See: http://williams.best.vwh.net/avform.htm#LL
    """

    RADIUS_METRES = 6378137  # Constant, radius of earth

    # Convert parameters to radians
    tc_rad = radians(tc_deg)
    lat_rad = radians(lat_dec)
    lon_rad = radians(lon_dec)
    d = float(d_metres) / float(RADIUS_METRES)

    # Push converted params through formula
    lat = asin(((sin(lat_rad) * cos(d)) +
                (cos(lat_rad) * sin(d) * cos(tc_rad))))

    dlon = atan2((sin(tc_rad) * sin(d) * cos(lat_rad)),
                 (cos(d) - (sin(lat_rad) * sin(lat_rad))))

    lon = (((lon_rad - dlon + pi) % (2 * pi)) - pi)

    # Ta-da!
    return (degrees(lat), degrees(lon))


if __name__ == '__main__':
    # Indexing
    data_files = gen_file_list("/neodc/arsf/2011/")

    # Process the header files
    procs = []
    m = multiprocessing.Manager()
    fdata = m.dict()

    print("")
    for header_fpath in data_files:
        reprint("Processing: %s" % (os.path.basename(header_fpath)))
        p = multiprocessing.Process(target=get_bil_nav,
                                    args=(header_fpath, fdata,))

        wait_for_processes(procs, 4)
        procs.append(p)
        p.start()

    wait_for_processes(procs, 0)

    coords = []
    for key in fdata.keys():
        file_coords = zip(fdata[key]["lat"], fdata[key]["lon"])
        plt.plot(file_coords, 'ko')
        coords.extend(file_coords)
    np_coords = np.array(coords)

    c = ConvexHull(np_coords)
    for simplex in c.simplices:
        plt.plot(np_coords[simplex, 0], np_coords[simplex, 1], 'k--')

    plt.savefig("out.png")

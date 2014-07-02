#! /usr/bin/env python

from __future__ import division
import lib_cedata.bilfile as bilfile
from math import asin, atan2, cos, degrees, pi, radians, sin
import multiprocessing
import os
from scipy.ndimage import gaussian_filter1d
import time


def reprint(line):
    # http://stackoverflow.com/a/12586667
    CURSOR_UP = '\x1b[1A'
    ERASE_LINE = '\x1b[2K'
    print("%s%s%s" % (CURSOR_UP, ERASE_LINE, line))


def get_bil_nav(header_fname, multiproc_manager_dict):
    b = bilfile.BilFile(header_fname)
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

    multiproc_manager_dict[header_fname] = swath_path


def wait_for_processes(proc_list, nprocs=0):
    """
        :param list proc_list: List of active processes
        :param int n_procs: Number of processes desired in the list

        Waits for processes in proc_list to complete until there are 'n_procs'
        processes remaining.
    """
    while len(proc_list) > nprocs:
        proc_list = [x for x in proc_list if (x.is_alive())]
        time.sleep(0.1)


def gen_file_list(path):
    """
        :param str path: Path of directory to walk
        :returns: list -- List of files in tree

        Recursively walks a directory tree, returning a list of files.
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

                if len(data_files) >= 3:
                    return data_files

    return data_files


def latlon_offset(lat_dec, lon_dec, d_metres, tc_deg):
    """
        :param float lat_dec: Decimal latitude of the point to offset
        :param float lon_dec: Decimal longitude of the point to offset
        :param float d_metres: Distance to offset the coordinate by (metres)
        :param float tc_deg: Direction to offset point (degrees)
        :returns: (float, float) -- Offset decimal latitude and longitude

        Calculates coordinates of a point offset by a certain distance
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


def output_kml_placemark(coord_string, name):
    start = """  <Placemark>
    <name>"""+name+"""</name>"""+"""
    <LineString>
      <coordinates>"""

    end = """      </coordinates>
    </LineString>
  </Placemark>"""

    return start+coord_string+end


def output_kml_polygon(coord_string, name):
    start = """  <Placemark>
    <name>"""+name+"""</name>"""+"""
    <Polygon>
      <outerBoundaryIs>
        <LinearRing>
          <coordinates>"""

    end = """          </coordinates>
        </LinearRing>
      </outerBoundaryIs>
    </Polygon>
  </Placemark>"""

    return start+coord_string+end


def output_kml_header():
    return """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
<Document>
"""


def output_kml_end():
    return """</Document>
</kml>"""

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

    orig = []
    front = []
    back = []
    pos = fdata[fdata.keys()[1]]
    for i in xrange(0, int(pos["lines"])):
        if i % 50 == 0:
            front_latlon = latlon_offset(float(pos["lat"][i]),
                                         float(pos["lon"][i]),
                                         (0.34 * float(pos["alt"][i])),
                                         float(pos["heading"][i]))

            back_latlon = latlon_offset(float(pos["lat"][i]),
                                        float(pos["lon"][i]),
                                        (-0.34 * float(pos["alt"][i])),
                                        float(pos["heading"][i]))

            back.append(back_latlon)
            front.append(front_latlon)
            orig.append((pos["lat"][i], pos["lon"][i]))

    # Gaussian filter to smooth out bounds
    sigma = 5

    fr_lat = [x[0] for x in front]
    fr_lon = [x[1] for x in front]
    front = zip(gaussian_filter1d(fr_lat, sigma), gaussian_filter1d(fr_lon, sigma))

    bk_lat = [x[0] for x in back]
    bk_lon = [x[1] for x in back]
    back = zip(gaussian_filter1d(bk_lat, sigma), gaussian_filter1d(bk_lon, sigma))

with open("linestrings.kml", 'w') as f:
    f.write(output_kml_header())
    f.write(output_kml_placemark("\n".join([("%f, %f" % (x[1], x[0])) for x in orig]), "orig"))
    f.write(output_kml_placemark("\n".join([("%f, %f" % (x[1], x[0])) for x in front]), "front"))
    f.write(output_kml_placemark("\n".join([("%f, %f" % (x[1], x[0])) for x in back]), "back"))
    f.write(output_kml_end())

with open("polygon.kml", 'w') as f:
    f.write(output_kml_header())
    f.write(output_kml_polygon("\n".join([("%f, %f" % (x[1], x[0])) for x in front]) +
            "\n".join([("%f, %f" % (x[1], x[0])) for x in back]), "polygon"))
    f.write(output_kml_end())

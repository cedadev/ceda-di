#! /usr/bin/env python
# Taken and adapted from:
# arsf-dan.nerc.ac.uk/trac/attachment/ticket/287/data_handler.py
# Original author: Ben Taylor (benj)

from __future__ import division
import json
from multiprocessing import Process
import os
import stat
import struct
import sys


def process_hdr(fname):
    with open(fname, 'r') as fh:
        lines = fh.readlines()

    hdr = {}
    for line in lines:
        # Ignore comments
        if line.startswith(";"):
            continue

        # Load keys into dict
        split_ln = line.split("=")
        if len(split_ln) > 1:
            split_ln = [i.strip(" {}\r\n") for i in split_ln]
            hdr.update({
                split_ln[0]: split_ln[1]
            })

    for key in hdr.keys():
        # Substitute spaces for underscores
        key_repl = key.replace(" ", "_")
        if key_repl != key:
            hdr[key_repl] = hdr[key]
            del hdr[key]

    # Add bil filename into header
    hdr["filename"] = os.path.splitext(fname)[0]

    return hdr


def read_bil(filename, numlines, pixperline, numbands, unpack_fmt="<d"):
    try:  # Check given format string is valid
        bytesperpix = struct.calcsize(unpack_fmt)
    except:
        raise ValueError("Supplied format \"%s\" is invalid" % str(unpack_fmt))

    # Check file size matches with size attributes
    fileinfo = os.stat(filename)
    filesize = fileinfo[stat.ST_SIZE]

    checknum = int((((filesize / numbands) /
                   numlines) / bytesperpix) / pixperline)

    if (checknum != 1):
        raise ValueError("File size and supplied attributes do not match")

    # Open the file for reading in binary mode
    try:
        bil = open(filename, "rb")
    except:
        print("Failed to open BIL file %s" % (filename))
        raise

    # Create a list of bands containing an empty list for each band
    bands = [[] for i in xrange(0, numbands)]

    # BIL format so have to cycle through lines at top level rather than bands
    for linenum in xrange(0, numlines):
        for bandnum in xrange(0, numbands):
            if (linenum == 0):
                # For each band create an empty list of lines in the band
                bands[bandnum] = [[] for i in xrange(0, numlines)]

            for pixnum in xrange(0, pixperline):

                # Read one data item (pixel) from the data file.
                # No error checking - we want this to fall over if it fails.
                datum = bil.read(bytesperpix)

                # If we get a blank string then hit EOF early, raise an error
                if (datum == ""):
                    raise EOFError("Unexpected EOF :(")

                # If everything worked, unpack the binary value
                # and store it in the appropriate pixel value
                bands[bandnum][linenum].append(
                    struct.unpack(unpack_fmt, datum)[0])

    bil.close()

    return bands


def read_yb(bil_hdr, unpack_fmt="<d"):
    numbands = int(bil_hdr["bands"])
    numlines = int(bil_hdr["lines"])
    filetype = bil_hdr["interleave"]
    filename = bil_hdr["filename"]

    fileinfo = os.stat(filename)
    filesize = fileinfo[stat.ST_SIZE]

    # Check given format string is valid
    try:
        bytesperpix = struct.calcsize(unpack_fmt)
    except:
        raise ValueError("Supplied format \"%s\" is invalid" % str(unpack_fmt))

    pixperline = int((filesize / numbands) / numlines) / bytesperpix

    # Should be an integer, if not, then an attribute is wrong or file corrupt
    # is wrong or the file is corrupt
    if (numlines == int(numlines)):
        if (filetype == "bil"):
            return read_bil(filename,
                            int(numlines),
                            int(pixperline),
                            int(numbands),
                            unpack_fmt)
        else:
            raise ValueError("File type argument must be 'bil', got: %s"
                             % filetype)
    else:
        raise ValueError("File size and supplied attributes do not match")


def get_bil_nav(header_fname):
    header = process_hdr(header_fname)
    bil = read_yb(header)

    pre_json = []
    for l in xrange(int(header["lines"])):
        st_point = {
            "time": bil[0][l][0],
            "lat": bil[1][l][0],
            "lon": bil[2][l][0],
            "alt": bil[3][l][0],
            "roll": bil[4][l][0],
            "pitch": bil[5][l][0],
            "heading": bil[6][l][0]
        }
        pre_json.append(st_point)

    output = format("out/%s.json" %
                    (os.path.splitext(os.path.basename(header_fname))[0]))

    with open(output, 'w') as out:
        out.write(json.dumps(pre_json, indent=4))


if __name__ == '__main__':
    for root, dirs, files in os.walk(sys.argv[1]):
        for f in files:
            if (f.endswith(".hdr") and
                ("nav" in f) and
                    ("qual" not in f)):
                header_fname = os.path.join(root, f)
                print(header_fname)

                p = Process(target=get_bil_nav, args=(header_fname,))
                p.start()

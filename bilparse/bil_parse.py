#! /usr/bin/env python
# Taken and adapted from:
# arsf-dan.nerc.ac.uk/trac/attachment/ticket/287/data_handler.py
# Original author: Ben Taylor (benj)

import json
import os
import stat
import struct


def process_hdr(fname):

    with open(fname, 'r') as fh:
        lines = fh.readlines()

    hdr = {}
    for line in lines:
        print(line),
    return hdr


# Reads a BIL file and returns a list containing the data from the file
# dataformat: Format string for data, as Python struct definitionN
def readBil(filename, numlines, pixperline, numbands, dataformat="<d"):

    if (not os.path.isfile(filename)):
        raise ValueError("Supplied filename \"%s\" does not exist" %
                         (str(filename)))

    # Check given format string is valid
    try:
        bytesperpix = struct.calcsize(dataformat)
    except:
        raise ValueError("Supplied format \"%s\" is invalid" % str(dataformat))

    # Check file size matches with size attributes
    fileinfo = os.stat(filename)
    filesize = fileinfo[stat.ST_SIZE]
    checknum = ((((filesize / float(numbands)) / float(numlines)) /
                float(bytesperpix)) / pixperline)

    if (checknum != 1):
        raise ValueError("File size and supplied attributes do not match")

    # Open the file for reading in binary mode
    try:
        bilfile = open(filename, "rb")
    except:
        print "Failed to open BIL file " + filename
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
                dataitem = bilfile.read(bytesperpix)

                # If we get a blank string then hit EOF early, raise an error
                if (dataitem == ""):
                    raise EOFError("Unexpected EOF :(")

                # If everything worked, unpack the binary value
                # and store it in the appropriate pixel value
                bands[bandnum][linenum].append(
                    struct.unpack(dataformat, dataitem)[0])

    bilfile.close()

    return bands


# Wrapper function for readBil/readBsq that allows you to omit the number of
# pixels per line (works it out from the file size)
def readyb(filename, numlines, numbands, dataformat="<d", filetype="bil"):
    fileinfo = os.stat(filename)
    filesize = fileinfo[stat.ST_SIZE]

    # Check given format string is valid
    try:
        bytesperpix = struct.calcsize(dataformat)
    except:
        raise ValueError("Supplied format \"%s\" is invalid" % str(dataformat))

    pixperline = ((filesize / float(numbands)) /
                  float(numlines)) / float(bytesperpix)

    # Should be an integer, if it's not then one of the given attributes
    # is wrong or the file is corrupt
    if (numlines == int(numlines)):
        if (filetype == "bil"):
            return readBil(filename,
                           int(numlines),
                           int(pixperline),
                           int(numbands),
                           dataformat)
        else:
            raise ValueError("File type argument must be 'bil', got: %s"
                             % filetype)
    else:
        raise ValueError("File size and supplied attributes do not match")


# fn = "data/e134011b_nav_post_processed.bil"
# fn = "data/e319011b_nav_post_processed.bil"
fn = "data/e127a041b_nav_post_processed.bil"
hdr_fn = "data/e127a041b_nav_post_processed.bil.hdr"

print(json.dumps(process_hdr(hdr_fn), indent=4))

"""

nlns = 23343
nbands = 7
bil = readyb(fn, nlns, nbands)

pre_json = []
for l in xrange(nlns):
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
"""

#with open("out.txt", 'w') as out:
#    out.write(json.dumps(pre_json, indent=4))

x = """<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://earth.google.com/kml/2.0">
<Document>
  <name>KML Example file</name>
  <description>Simple markers</description>

  <Placemark>
    <name>ARSF Sample LineString</name>
    <description>Sample coordinates extracted from BIL file</description>
    <LineString>
      <coordinates>
"""

z = """      </coordinates>
    </LineString>
  </Placemark>
</Document>
</kml>
"""

#with open("out.kml", 'w') as out:
#    out.write(x)
#    for i in pre_json:
#        out.write(format("%f, %f, %fi\n" % (i["lon"], i["lat"], i["alt"])))
#    out.write(z)

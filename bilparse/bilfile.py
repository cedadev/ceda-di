#! /usr/bin/env python
# Taken and adapted from:
# arsf-dan.nerc.ac.uk/trac/attachment/ticket/287/data_handler.py
# Original author: Ben Taylor (benj)

from __future__ import division
import os
import stat
import struct


class BilFile:
    """
    BilFile constructor.
    Params:
        * header_path: Path to BIL header file.

        * bil_path:    Path to BIL file. Guessed from header if not provided.
                       Default: None

        * unpack_fmt:  C struct format string describing structure of data.
                       Default: "<d" - little-endian, double precision
    """
    def __init__(self, header_path, bil_path=None, unpack_fmt="<d"):
        self.hdr_path = header_path

        if bil_path:
            self.bil_path = bil_path
        else:
            self.bil_path = os.path.splitext(self.hdr_path)[0]

        self.unpack_fmt = unpack_fmt

        # Try loading the header file
        self.hdr = self.process_hdr()

    """
    Checks the format string for validity.

    Return:
        * The number of bytes for the data type specified in the format string.
    """
    def check_valid_fmt_string(self):
        try:  # Check given format string is valid
            num_bytes = struct.calcsize(self.unpack_fmt)
        except:
            raise ValueError("Supplied format \"%s\" is invalid" %
                             str(self.unpack_fmt))

        return num_bytes

    """
    Parses the provided header file.

    Return:
        * A dict, containing header file parsed into key/value pairs.
    """
    def process_hdr(self):
        with open(self.hdr_path, 'r') as fh:
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

        return hdr

    """
    Reads the BIL file binary data from information provided in the header.

    Return:
        * A 2-dimensional list containing the data from the BIL file.
    """
    def read_bil(self):
        filename = self.bil_path
        bands = int(self.hdr["bands"])
        lines = int(self.hdr["lines"])
        pixperline = int(self.hdr["pixperline"])

        try:
            filesize = self.hdr["filesize"]
            bytesperpix = self.hdr["bytesperpix"]
        except KeyError:
            filesize = os.stat(self.bil_path)[stat.ST_SIZE]
            bytesperpix = self.check_valid_fmt_string()

        # Check file size matches with size attributes
        checknum = int((((filesize / bands) /
                       lines) / bytesperpix) / pixperline)

        if (checknum != 1):
            raise ValueError("File size and supplied attributes do not match")

        with open(filename, 'rb') as bil:
            # Pre-allocate list
            bil_data = []
            for i in xrange(0, bands):
                bil_data.append([])
                bil_data[i] = [[] for j in xrange(0, lines)]

            for linenum in xrange(0, lines):
                for bandnum in xrange(0, bands):
                    for pixnum in xrange(0, pixperline):
                        # Read one data item (pixel) from the data file.
                        datum = bil.read(bytesperpix)

                        # If we get a blank string then we hit EOF unexpectedly
                        if (datum == ""):
                            raise EOFError("Unexpected EOF :(")

                        # If everything worked, unpack the binary value
                        # and store it in the appropriate pixel value
                        bil_data[bandnum][linenum] = \
                            struct.unpack(self.unpack_fmt, datum)[0]

        return bil_data

    """
    Calculates the number of pixels per line based on file size.
    """
    def calc_from_yb(self):
        bands = int(self.hdr["bands"])
        lines = int(self.hdr["lines"])

        filesize = os.stat(self.bil_path)[stat.ST_SIZE]
        bytesperpix = self.check_valid_fmt_string()
        pixperline = int((filesize / bands) / lines) / bytesperpix

        self.hdr["pixperline"] = pixperline
        self.hdr["bytesperpix"] = bytesperpix
        self.hdr["filesize"] = filesize

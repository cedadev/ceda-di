# Taken and adapted from:
# arsf-dan.nerc.ac.uk/trac/attachment/ticket/287/data_handler.py
# Original author: Ben Taylor (benj)

from __future__ import division
import os
import stat
import struct


class EnviFile(object):
    """
    x: Number of bands
    y: Number of lines
    z: Pixels per line
    """
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        """
        :param str header_path: Path to header file.
        :param str path: Path to file. Guessed from header if not provided.
        :param str unpack_fmt: Format string describing structure of data.
                               Default: "<d" - little-endian, double precision
        """
        self.hdr_path = header_path

        if path:
            self.path = path
        else:
            self.path = os.path.splitext(header_path)[0]

        self.unpack_fmt = unpack_fmt

        # Try loading the header file
        self.hdr = self.process_hdr()

        # Calculate pixels per line
        if not "pixperline" in self.hdr:
            self.calc_from_xy()

    def check_valid_fmt_string(self):
        """
        Check the format string for validity.
        :return int: Number of bytes needed for type in the format string
        """
        try:  # Check given format string is valid
            num_bytes = struct.calcsize(self.unpack_fmt)
        except:
            raise ValueError("Supplied format \"%s\" is invalid" %
                             str(self.unpack_fmt))

        return num_bytes

    def process_hdr(self):
        """
        Parse the provided header file.
        :return dict: Header file parsed into key/value pairs
        """
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

    def calc_from_xy(self):
        """
        Calculate the number of pixels per line based on file size.
        """
        bands = int(self.hdr["bands"])
        lines = int(self.hdr["lines"])

        filesize = os.stat(self.path)[stat.ST_SIZE]
        bytesperpix = self.check_valid_fmt_string()
        pixperline = int((filesize / bands) / lines) / bytesperpix

        self.hdr["bytesperpix"] = bytesperpix
        self.hdr["filesize"] = filesize
        self.hdr["pixperline"] = pixperline

    def read(self, x_size, y_size, z_size):
        """
        See class docstring for x/y/z mappings.
        """
        filename = self.path

        try:
            filesize = self.hdr["filesize"]
            bytesperpix = self.hdr["bytesperpix"]
        except KeyError:
            filesize = os.stat(self.path)[stat.ST_SIZE]
            bytesperpix = self.check_valid_fmt_string()

        # Check file size matches with size attributes
        bands = int(self.hdr["bands"])
        lines = int(self.hdr["lines"])
        pixperline = int(self.hdr["pixperline"])
        checknum = int((((filesize / bands) /
                       lines) / bytesperpix) / pixperline)
        if (checknum != 1):
            raise ValueError("File size and supplied attributes do not match")

        with open(filename, 'rb') as envi:
            # Pre-allocate list
            data = []
            for i in xrange(0, x_size):
                data.append([])
                data[i] = [[] for j in xrange(0, y_size)]

            for y in xrange(0, y_size):
                for x in xrange(0, x_size):
                    for z in xrange(0, z_size):
                        # Read one data item (pixel) from the data file.
                        datum = envi.read(bytesperpix)

                        # If we get a blank string then we hit EOF unexpectedly
                        if (datum == ""):
                            raise EOFError("Unexpected EOF :(")

                        # If everything worked, unpack the binary value
                        # and store it in the appropriate pixel value
                        data[x][y] = \
                            struct.unpack(self.unpack_fmt, datum)[0]

        return data


class BilFile(EnviFile):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        """
        Call superclass constructor with appropriate parameters.
        """
        super(BilFile, self).__init__(header_path, path, unpack_fmt)

    def read(self):
        """
        Read BIL file (reading bytes in correct order)
        """
        return super(BilFile, self).read(int(self.hdr["bands"]),
                                         int(self.hdr["lines"]),
                                         int(self.hdr["pixperline"]))
                                         
class BsqFile(EnviFile):
    def __init__(self, header_path, path=None, unpack_fmt="<d"):
        """
        Call superclass constructor with appropriate parameters.
        """
        super(BsqFile, self).__init__(header_path, path, unpack_fmt)
        
    def read(self):
        """
        Read BSQ file (reading bytes in correct order)
        """
        return super(BsqFile, self).read(int(self.hdr["lines"]),
                                         int(self.hdr["bands"]),
                                         int(self.hdr["pixperline"]))

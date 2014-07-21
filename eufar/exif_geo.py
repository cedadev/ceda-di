#! /usr/bin/env python

import exifread
import json
import xmltodict


class EXIF_geo(object):
    def __init__(self, fname):
        self.fname = fname

    def __enter__(self):
        """
        Context manager helper method.

        :return self:
        """
        with open(self.fname, 'rb') as f:
            tags = exifread.process_file(f, details=False, strict=True)

        # Set XML from EXIF file
        self.xml = xmltodict.parse(tags["Image ImageDescription"].values)

        return self

    def __exit__(self, *args):
        pass

    def get_geospatial(self):
        """
        Return a dictionary containing metadata and geospatial information
        :return dict: Dict containing metadata and geospatial information
        """
        finfo = {}
        finfo[self.fname] = {}

        # Position
        print json.dumps(self.xml, indent=4)
        pos = self.xml["Camera_Image"]["Plane_info"]
        pos = pos["Exterior_orientation"]["Position"]

        finfo[self.fname]["lat"] = pos["Latitude"]
        finfo[self.fname]["lon"] = pos["Longitude"]
        finfo[self.fname]["alt"] = pos["Height"]

        return finfo

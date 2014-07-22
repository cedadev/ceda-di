#! /usr/bin/env python

import datetime
import os

import exifread
import xmltodict

from _dataset import _geospatial
from metadata import product


class EXIF(_geospatial):
    def __init__(self, fname):
        """
        :param str fname: File name to construct EXIF_geo object from.
        """
        self.fname = fname

    def __enter__(self):
        """
        Context manager helper method.
        :return self:
        """
        with open(self.fname, 'rb') as f:
            tags = exifread.process_file(f, details=False, strict=True)

        # Set XML from EXIF file
        # TODO this may not work perfectly with JPGs
        self.xml = xmltodict.parse(tags["Image ImageDescription"].values)

        return self

    def __exit__(self, *args):
        pass

    def get_geospatial(self):
        """
        Return a dictionary containing metadata and geospatial information.
        :return dict: Dict containing metadata and geospatial information.
        """

        # Traverse XML
        pos = self.xml["Camera_Image"]["Plane_info"]
        pos = pos["Exterior_orientation"]["Position"]

        geospatial = {
            "lat": [float(pos["Latitude"])],
            "lon": [float(pos["Longitude"])],
            "alt": [float(pos["Height"])],
        }

        return geospatial

    def get_temporal(self):
        proj = self.xml["Camera_Image"]["Project_info"]

        year = int(proj["Year"])
        epoch = datetime.datetime(year=year, month=1, day=1)

        jul_day = int(proj["Flight_day_of_year"]) - 5  # Correction
        secs = float(proj["GPStime_of_week"])
        seconds = int(secs)
        milliseconds = (secs-seconds)

        delta = datetime.timedelta(days=jul_day,
                                   seconds=seconds,
                                   milliseconds=milliseconds)

        iso = (epoch + delta).isoformat()
        temporal = {
            "start_time": iso,
            "end_time": iso
        }

        return temporal

    def get_properties(self):
        file_level = super(EXIF, self).get_file_level(self.fname)
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()
        data_format = {
            "format": os.path.splitext(self.fname)[1][1:]
        }

        props = product.Properties(file_level=file_level,
                                   spatial=geospatial,
                                   temporal=temporal,
                                   data_format=data_format)

        return props

"""
Module containing classes to read and export XML metadata embedded in GeoTIFF
files using the EXIF standard.
"""

import datetime
import logging
import os

import exifread
import xmltodict
from xml.parsers.expat import ExpatError

from _dataset import _geospatial
from metadata import product


class EXIF(_geospatial):
    """
    Class that handles extraction and export of EXIF metadata from GeoTIFF
    image files.
    """
    def __init__(self, fname):
        """
        :param str fname: File name to construct EXIF_geo object from.
        """
        self.logger = logging.getLogger(__name__)
        self.fname = fname
        self.xml = None

    def __enter__(self):
        """
        Context manager entry method (e.g. "with" statement)
        :return self:
        """

        try:
            with open(self.fname, 'rb') as exif:
                tags = exifread.process_file(exif, details=False, strict=True)
            self.xml = xmltodict.parse(tags["Image ImageDescription"].values)
        except (IOError, KeyError, ExpatError):
            self.logger.warn("Could not parse XML from EXIF: %s" % self.fname)

        return self

    def __exit__(self, *args):
        """
        Context manager exit method (e.g. "with" statement)
        """
        pass

    def get_geospatial(self):
        """
        Return a dictionary containing geospatial extent metadata.
        :return dict: Dictionary containing geospatial extent metadata.
        """

        # Traverse XML
        pos = self.xml["Camera_Image"]["Plane_info"]
        if "Exterior_orientation" in pos:
            pos = pos["Exterior_orientation"]["Position"]
        elif "Position" in pos:
            pos = pos["Position"]

        geospatial = {
            "lat": [float(pos["Latitude"])],
            "lon": [float(pos["Longitude"])],
            "alt": [float(pos["Height"])],
        }

        return geospatial

    def get_temporal(self):
        """
        Return a dictionary containing temporal extent metadata
        :return dict: Dictionary containing temporal extent metadata
        """
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
        """
        Return a eufar.metadata.product.Properties object populated with the
        file's metadata.
        :return props: A eufar.metadata.product.Properties object
        """
        filesystem = super(EXIF, self).get_filesystem(self.fname)
        data_format = {
            "format": os.path.splitext(self.fname)[1][1:]
        }

        try:
            geospatial = self.get_geospatial()
            temporal = self.get_temporal()
        except KeyError:
            self.logger.warning("Could not extract metadata from EXIF XML: %s"
                                % self.fname)
            temporal = None
            geospatial = None

        props = product.Properties(filesystem=filesystem,
                                   spatial=geospatial,
                                   temporal=temporal,
                                   data_format=data_format)

        return props

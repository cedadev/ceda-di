"""
Module for holding and exporting file metadata as JSON documents.
"""

import json


class Properties(object):
    """
    A class to hold, manipulate, and export geospatial metadata at file level.
    """
    def __init__(self, file_level=None, spatial=None,
                 temporal=None, data_format=None, **kwargs):
        """
        Construct a 'eufar.metadata.Properties' ready to export as JSON or dict
        (see "doc/schema.json")

        :param dict file_level: File-level information about file
        :param dict spatial: Spatial information about file
        :param dict temporal: Temporal information about file
        :param dict data_format: Data format information about file
        :param **kwargs: Key-value pairs of any extra metadata describing file.
        """

        self.file_level = file_level
        self.spatial = spatial
        self.temporal = temporal
        self.data_format = data_format

        # Set other misc metadata
        if "parameters" in kwargs:
            self.parameters = kwargs["parameters"]
            del kwargs["parameters"]

        self.misc = kwargs

        self.properties = {
            "data_format": self.data_format,
            "file": self.file_level,
            "spatial": self.spatial,
            "temporal": self.temporal,
            "misc": self.misc,
        }

    @staticmethod
    def _to_wkt(spatial):
        """
        Convert lats and lons to a WKT linestring.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :return: A Python string representing a WKT linestring
        """
        lats = spatial["lat"]
        lons = spatial["lon"]

        coord_list = []
        for lat, lon in zip(lats, lons):
            coord_list.append("%f %f" % (lat, lon))

        sep = ',\n'
        coord_string = sep.join(coord_list)
        linestring = "LINESTRING (%s)" % coord_string

        return linestring

    def __str__(self):
        """
        Format file properties to JSON when coercing object to string.

        :return: A Python string containing JSON representation of object.
        """

        if self.spatial is not None:
            self.spatial = self._to_wkt(self.spatial)

        return json.dumps(self.properties, indent=4)

    def as_json(self):
        """
        Return metadata as JSON string.

        :return str: JSON document describing metadata.
        """
        return self.__str__()

    def as_dict(self):
        """
        Return metadata as dict object.

        :return dict: Dictionary describing metadata
        """
        return self.properties

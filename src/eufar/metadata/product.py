"""
Module for holding and exporting file metadata as JSON documents.
"""

from __future__ import division
import json
from pyhull.convex_hull import qconvex


class Properties(object):
    """
    A class to hold, manipulate, and export geospatial metadata at file level.
    """
    def __init__(self, file_level=None, spatial=None,
                 temporal=None, data_format=None, parameters=None,
                 **kwargs):
        """
        Construct a 'eufar.metadata.Properties' ready to export as JSON or dict
        (see "doc/schema.json")

        :param dict file_level: File-level information about file
        :param dict spatial: Spatial information about file
        :param dict temporal: Temporal information about file
        :param dict data_format: Data format information about file
        :param **kwargs: Key-value pairs of any extra relevant metadata.
        """

        self.file_level = file_level
        self.temporal = temporal
        self.data_format = data_format
        self.parameters = parameters
        self.spatial = spatial
        if self.spatial is not None:
            self.spatial = self._to_geojson(self.spatial)

        self.misc = kwargs
        self.properties = {
            "data_format": self.data_format,
            "file": self.file_level,
            "misc": self.misc,
            "parameters": self.parameters,
            "spatial": self.spatial,
            "temporal": self.temporal,
        }

    def _gen_bbox(self, spatial):
        """
        Generate and return a bounding box for the given geospatial data.
        :param dict spatial: Dictionary with "lat" and "lon" keys w/coordinates
        :return list bbox: A bounding-box list formatted in the GeoJSON style
        """
        lons = spatial["lon"]
        lats = spatial["lat"]

        lon_lo, lon_hi = self._get_min_max(lons)
        lat_lo, lat_hi = self._get_min_max(lats)

        return [lon_lo, lat_lo, lon_hi, lat_hi]

    @staticmethod
    def _get_min_max(item_list):
        """
        Return a tuple containing the (highest, lowest) values in the list.
        :param list item_list: List of comparable data items
        :return tuple: Tuple of (highest, lowest values in the list)
        """
        if len(item_list) < 1:
            return (None, None)

        high = max(item_list)
        low = min(item_list)

        return (high, low)

    @staticmethod
    def _to_wkt(spatial):
        """
        Convert lats and lons to a WKT linestring.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :return: A Python string representing a WKT linestring
        """
        lats = spatial["lat"]
        lons = spatial["lon"]

        coord_list = set()
        for lat, lon in zip(lats, lons):
            coord_list.add("%f %f" % (lat, lon))

        sep = ", "
        coord_string = sep.join(coord_list)
        linestring = "LINESTRING (%s)" % coord_string

        return linestring

    def _to_geojson(self, spatial):
        """
        Convert lats and lons to a GeoJSON-compatible type.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :return: A Python dict representing a GeoJSON-compatible coord array
        """
        lats = spatial["lat"]
        lons = spatial["lon"]

        if len(lats) > 0 and len(lons) > 0:
            geojson = {}
            coord_set = set()
            for lat, lon in zip(lats, lons):
                coord_set.add((lon, lat))

            coord_list = list(coord_set)
            geojson["geometries"] = {
                "type": "LineString",
                "bbox": self._gen_bbox(spatial),
                "coordinates": coord_list,
            }

            if len(coord_list) > 3:
                hull = qconvex('p', coord_list)
                new_hull = []
                for point in hull[2:]:
                    pt = point.split(" ")
                    new_hull.append((float(pt[0]), float(pt[1])))
                geojson["hull"] = new_hull

            return geojson
        return None

    def __str__(self):
        """
        Format file properties to JSON when coercing object to string.

        :return: A Python string containing JSON representation of object.
        """
        return json.dumps(self.properties, default=repr)

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

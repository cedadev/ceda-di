"""
Module for holding and exporting file metadata as JSON documents.
"""

from __future__ import division
import hashlib
import simplejson as json
import logging
import math
import numpy.ma as ma
import numpy as np


class FileFormatError(Exception):
    """
    Exception to raise if there is a error in the file format
    """
    pass


class GeoJSONGenerator(object):
    """
    A class to translate between different scientific data types and GeoJSON.

        * Flight tracks => GeoJSON "LineString"
        * Photography / stationary observation points => GeoJSON "Point"
        * Satellite swaths => GeoJSON "MultiPolygon"
    """
    def __init__(self, latitudes, longitudes, shape_type=None):
        self.longitudes, self.latitudes = self._sanitise_geometry(
            ma.array(longitudes),
            ma.array(latitudes)
        )
        self.shape_type = shape_type

    def get_elasticsearch_geojson(self):
        """
        Returns the specified GeoJSON object, constructed from the geometry
        supplied at construction-time. This can be provided from the
        "shape_type" parameter. Can be one of the following values:

            * None (returns a "LineString" type) [defaults to "track"]
            * "track" (returns a "LineString" type) [default]
            * "point" (returns a "Point" type)
            * "swath" (returns a "MultiPolygon" type)

        :return: Specified GeoJSON object.
        """
        geojson = None
        if len(self.latitudes) > 0 and len(self.longitudes) > 0:
            if self.shape_type == "point" or self._num_points() == 1:
                geojson = {
                    "geometries": {
                        "search": self._gen_point(),
                        "display": self._gen_point()
                    }
                }
            elif self.shape_type == "swath":
                geojson = {
                    "geometries": {
                       "search": self._gen_swath(),
                       "display": self._gen_track()
                    }
                }
            elif self.shape_type == "track" or self.shape_type is None:
                geojson = {
                    "geometries": {
                        "search": self._gen_track(),
                        "display": self._gen_track()
                    }
                }

        return geojson

    def _num_points(self):
        """
        Return the number of coordinates in the SHORTEST list out of:
            * self.latitudes
            * self.longitudes

        This returns the length of the SHORTEST list.

        :return int: The length of the shortest coordinate list.
        """
        len_lons = np.size(self.longitudes)
        len_lats = np.size(self.latitudes)

        if len_lons > len_lats:
            return len_lats
        else:
            return len_lons

    def _sanitise_geometry(self, lons, lats):
        """
        Sanitise geometry by removing any masked points.
        :param lons:
        :param lats:
        :return: A tuple containing arrays of (lon, lat)
        """
        sane_lons = lons[
            (lons >= -180) &
            (lons <= 180) &
            (lats >= -90) &
            (lats <= 90) &
            (ma.getmaskarray(lats) == False) &
            (ma.getmaskarray(lons) == False)
        ]

        sane_lats = lats[
            (lons >= -180) &
            (lons <= 180) &
            (lats >= -90) &
            (lats <= 90) &
            (ma.getmaskarray(lats) == False) &
            (ma.getmaskarray(lons) == False)
        ]

        return (sane_lons, sane_lats)

    def _gen_point(self):
        """
        Returns a GeoJSON 'Point' type.

        :return: A GeoJSON 'Point' type in a dictionary.
        """
        geojson = {
            "type": "Point",
            "coordinates": [self.longitudes[0], self.latitudes[0]]
        }

        return geojson

    def _gen_swath(self, num_polygons=30):
        """
        Returns a GeoJSON 'MultiPolygon' type.

        :return: A GeoJSON 'MultiPolygon' type in a dictionary.
        """
        geojson = {
            "type": "MultiPolygon",
            "coordinates": []
        }

        track = self._gen_track(num_polygons + 1)["coordinates"]
        for i in xrange(0, len(track) - 1):
            lo = track[i]
            hi = track[i + 1]

            polygon = self._gen_polygon(lo[0], lo[1], hi[0], hi[1])
            geojson["coordinates"].append(polygon["coordinates"])

        return geojson

    def _gen_track(self, num_points=30):
        """
        Creates a LineString from a summary of the file's latitudes and
        longitudes. Samples a coordinate every 'num_points'.

        :return: A GeoJSON LineString containing a sample of points from the
                  flight track.
        """
        track = {
            "type": "LineString"
        }

        point_count = self._num_points()
        if point_count <= num_points:
            track_lons = self.longitudes
            track_lats = self.latitudes
        else:
            step = int(math.ceil(point_count / num_points))
            track_lons = self.longitudes[::step]
            track_lats = self.latitudes[::step]

        track["coordinates"] = zip(track_lons, track_lats)

        return track

    def _gen_envelope(self):
        lon_left, lon_right = self._get_bounds(self.longitudes,
                                               wrapped_coords=True)
        lat_bottom, lat_top = self._get_bounds(self.latitudes)

        if (lon_left is None or lon_right is None or
                lat_bottom is None or lat_top is None):
            return None

        envelope = {
            "type": "envelope",
            "coordinates": [
                [lon_left, lat_top],
                [lon_right, lat_bottom]
            ]
        }

        return envelope

    def _gen_bbox(self):
        """
        Generate and return a bounding box for the given geospatial data.
        If there are no data points then bounding box is none

        :return: A bounding-box formatted as GeoJSON
        """
        lon_left, lon_right = self._get_bounds(self.longitudes,
                                               wrapped_coords=True)
        lat_bottom, lat_top = self._get_bounds(self.latitudes)

        if (lon_left is None or lon_right is None or
                lat_bottom is None or lat_top is None):
            return None

        bbox = self._gen_polygon(lon_left, lon_right, lat_bottom, lat_top)

        return bbox

    @staticmethod
    def _gen_polygon(lon_l, lon_r, lat_b, lat_t):
        """
        Generate and return a polygon from two provided sets of coordinates.

        :return: A GeoJSON bounding box
        """
        corners = [
            [
                [lon_r, lat_t],
                [lon_l, lat_t],
                [lon_l, lat_b],
                [lon_r, lat_b],
                [lon_r, lat_t]
            ]
        ]

        bbox = {
            "type": "polygon",
            "orientation": "counterclockwise",
            "coordinates": corners
        }

        return bbox

    @staticmethod
    def _get_bounds(item_list, wrapped_coords=False):
        """
        Return a tuple containing the first and secound bound in the list.
            * For 0 values it returns (None, None).
            * For 1 value it returns that value twice
            * For 2 values it returns those (low, high) for unwrapped
              co-ordinates or in the order given for wrapped
            * For Multiple values unwrapped, this returns min and max
            * For Multiple values wrapped co-ordinates, this
              returns the value around the largest gap in values

        :param list item_list: List of comparable data items
        :param wrapped_coords: is this a coordinate which wraps at 360 back to
                               0, e.g. longitude
        :return: Tuple of (first bound, second bound for values in the list)
        """
        items = ma.compressed(item_list)
        if len(items) < 1:
            return None, None

        if len(items) == 1:
            return items[0], items[0]

        if wrapped_coords:
            if len(items) is 2:
                first_bound_index = 0
                second_bound_index = 1
            else:
                # find the largest angle between closest points and exclude
                # this from the bounding box ensuring that this includes going
                # across the zero line
                items = sorted(items)
                first_bound_index = 0
                second_bound_index = len(items) - 1
                max_diff = (items[first_bound_index] -
                            items[second_bound_index]) % 360
                for i in range(1, len(items)):
                    diff = (items[i] - items[i-1]) % 360
                    if diff > max_diff:
                        max_diff = diff
                        first_bound_index = i
                        second_bound_index = i-1

            first_bound = items[first_bound_index]
            second_bound = items[second_bound_index]
        else:
            first_bound = min(items)
            second_bound = max(items)

        return float(first_bound), float(second_bound)


class Properties(object):
    """
    A class to hold, manipulate, and export geospatial metadata at file level.
    """
    def __init__(self, filesystem=None, spatial=None,
                 temporal=None, data_format=None, parameters=None,
                 index_entry_creation=None, **kwargs):
        """
        Construct 'ceda_di.metadata.Properties' ready to export.
        (for structure, see "doc/schema.json")

        :param dict filesystem: Filesystem information about file
        :param dict spatial: Spatial information about file
        :param dict temporal: Temporal information about file
        :param dict data_format: Data format information about file
        :param list parameters: Parameter objects in list
        :param index_entry_creation: the program that created the index entry
        :param **kwargs: Key-value pairs of any extra relevant metadata.
        """

        self.logger = logging.getLogger(__name__)
        self.filesystem = filesystem
        self.temporal = temporal
        self.data_format = data_format

        self.index_entry_creation = index_entry_creation

        if parameters is not None:
            self.parameters = [p.get() for p in parameters]
        else:
            self.parameters = None

        if spatial is None:
            self.spatial = None
        else:
            if "type" not in spatial:
                gj = GeoJSONGenerator(spatial["lat"], spatial["lon"])
            else:
                gj = GeoJSONGenerator(spatial["lat"], spatial["lon"],
                                      spatial["type"])
            self.spatial = gj.get_elasticsearch_geojson()

        self.misc = kwargs
        self.properties = {
            "_id": hashlib.sha1(self.filesystem["path"]).hexdigest(),
            "data_format": self.data_format,
            "file": self.filesystem,
            "misc": self.misc,
            "parameters": self.parameters,
            "spatial": self.spatial,
            "temporal": self.temporal,
        }

    def __str__(self):
        """
        Format file properties to JSON when coercing object to string.

        :returns: A Python string containing JSON representation of object.
        """
        return json.dumps(self.properties, default=repr)

    def as_json(self):
        """
        Return metadata as JSON string.

        :returns: JSON document describing metadata.
        """
        return self.__str__()

    def as_dict(self):
        """
        Return metadata as dict object.

        :returns: Dictionary describing metadata
        """
        return self.properties


class Parameter(object):
    """
    Placeholder/wrapper class for metadata parameters

    :param str name: Name of variable/parameter
    :param dict other_params: Optional - Dict containing other param metadata
    """
    def __init__(self, name, other_params=None):
        self.items = []
        self.name = name

        # Other arbitrary arguments
        if other_params:
            for key, value in other_params.iteritems():
                self.items.append(
                    self.make_param_item(key.strip(), unicode(value).strip()))

    @staticmethod
    def make_param_item(name, value):
        """
        Convert a name/value pair to dictionary (for better indexing in ES)

        :param str name: Name of the parameter item (e.g. "long_name_fr", etc)
        :param str value: Value of the parameter item (e.g. "Radiance")
        :return: Dict containing name:value information
        """
        return {"name": name,
                "value": value}

    def get(self):
        """Return the list of parameter items"""
        return self.items

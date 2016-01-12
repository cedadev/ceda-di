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


class GeoJSONGenerator(object):
    """
    A class to translate between different scientific data types and GeoJSON.

        * Flight tracks => GeoJSON "LineString"
        * Photography / stationary observation points => GeoJSON "Point"
        * Satellite swaths => GeoJSON "MultiPolygon"
    """
    def __init__(self, latitudes, longitudes, shape_type=None):
        self._sanitise_geometry(ma.array(longitudes), ma.array(latitudes))
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
            if (self.shape_type == "point" or
                    self._num_points(self.longitudes, self.latitudes) == 1):
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
                        "search": self._gen_envelope(),
                        "display": self._gen_track()
                    }
                }

        return geojson

    def _num_points(self, lons, lats):
        """
        Return the number of coordinates in the SHORTEST list out of:
            * self.latitudes
            * self.longitudes

        This returns the length of the SHORTEST list.

        :return int: The length of the shortest coordinate list.
        """
        len_lons = np.size(lons)
        len_lats = np.size(lats)

        if len_lons > len_lats:
            return len_lats
        else:
            return len_lons

    def __align_lons_lats(self, lons, lats):
        """
        Ensure "lons" and "lats" are the same length.
        """
        size = self._num_points(lons, lats)
        if np.size(lons) > size:
            lons = lons[0:size]
        elif np.size(lats) > size:
            lats = lats[0:size]

        return (lons, lats)

    def _sanitise_geometry(self, lons, lats):
        """
        Sanitise geometry by removing any masked points.
        :param lons:
        :param lats:
        :return: A tuple containing arrays of (lon, lat)
        """
        # Align the arrays
        lons, lats = self.__align_lons_lats(lons, lats)

        # Get masks
        lon_mask = ma.getmaskarray(lons)
        lat_mask = ma.getmaskarray(lats)

        # Filter the arrays
        self.longitudes = lons[
            (lons >= -180) &
            (lons <= 180) &
            (lats >= -90) &
            (lats <= 90) &
            (lon_mask == False) &
            (lat_mask == False)
        ]

        self.latitudes = lats[
            (lons >= -180) &
            (lons <= 180) &
            (lats >= -90) &
            (lats <= 90) &
            (lon_mask == False) &
            (lat_mask == False)
        ]

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

            polygon = self._gen_polygon(lo[0], hi[0], lo[1], hi[1])
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

        point_count = self._num_points(self.longitudes, self.latitudes)
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
        """
        Generate and return an Elasticsearch envelope type.
        :return: A bounding box as an envelope.
        """
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

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
    A class that can generate various geometric objects based on latitudes and longitudes
    """
    def __init__(self, latitudes, longitudes, shape_type=None):
        self.longitudes, self.latitudes = self._sanitise_geometry(
            ma.array(longitudes),
            ma.array(latitudes)
        )

        self.shape_type = shape_type

    def _sanitise_geometry(self, lons, lats):
        """
        Sanitise geometry by removing any masked points.
        :param lons:
        :param lats:
        :returns: A tuple containing arrays of (lon, lat)
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

    def calc_spatial_geometries(self):
        """
        Calculate the spatial geometries geojson
        :return: geojson object
        """
        if len(self.latitudes) > 0 and len(self.longitudes) > 0:
            geojson = {
                "geometries": {
                    "bbox": self.generate_bounding_box(False),
                    "summary": self._gen_coord_summary()
                }
            }

            return geojson
        return None

    def _gen_coord_summary(self, num_points=30):
        """
        Pull 30 evenly-spaced coordinates

        :returns: A summary formatted in the GeoJSON style
        """
        summ = {
            "type": "LineString"
        }

        lon_values, lat_values = self._sanitise_geometry(self.longitudes, self.latitudes)
        point_count = np.size(lon_values)
        if point_count <= num_points:
            summary_lons = lon_values
            summary_lats = lat_values
        else:
            step = int(math.ceil(point_count / num_points))
            summary_lons = lon_values[::step]
            summary_lats = lat_values[::step]

        summ["coordinates"] = zip(summary_lons, summary_lats)

        return summ

    def generate_bounding_box(self, generate_polygon):
        """
        Generate and return a bounding box for the given geospatial data.
        If there are no data points then bounding box is none

        :param generate_polygon: if True bounding box is for a polygon, otherwise for an envelope
        :returns: A bounding-box formatted as GeoJSON
        """
        lon_left, lon_right = self._get_bounds(self.longitudes, wrapped_coords=True)
        lat_bottom, lat_top = self._get_bounds(self.latitudes)

        if lon_left is None or lon_right is None or lat_bottom is None or lat_top is None:
            return None

        if generate_polygon:
            corners = [
                [
                    [lon_right, lat_top],
                    [lon_left, lat_top],
                    [lon_left, lat_bottom],
                    [lon_right, lat_bottom],
                    [lon_right, lat_top]
                ]
            ]

            bbox = {
                "type": "polygon",
                "orientation": "counterclockwise",
                "coordinates": corners
            }
        else:
            corners = [
                [lon_left, lat_top],
                [lon_right, lat_bottom]
            ]

            bbox = {
                "type": "envelope",
                "coordinates": corners
            }

        return bbox

    @staticmethod
    def _get_bounds(item_list, wrapped_coords=False):
        """
        Return a tuple containing the first and secound bound in the list.
        For No values it returns None, None
        For One value it returns the that value twice
        For Two values it returns those low, high for unwrapped co-ordinates or in the order given for wrapped
        For Multiple values unwrapped co-ordinates this returns min and max
        For Multiple values wrapped co-ordinates it returns the value around the largest gap in values

        :param list item_list: List of comparable data items
        :param wrapped_coords: is this a coordinate which wraps at 360 back to 0, e.g. longitude
        :returns: Tuple of (first bound, second bound for values in the list)
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
                # find the largest angle between closest points and exclude this from the bounding box ensuring that
                # this includes going across the zero line
                items = sorted(items)
                first_bound_index = 0
                second_bound_index = len(items) - 1
                max_diff = (items[first_bound_index] - items[second_bound_index]) % 360
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
            geo_json_generator = GeoJSONGenerator(spatial["lat"], spatial["lon"])
            self.spatial = geo_json_generator.calc_spatial_geometries()

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

    @staticmethod
    def _to_wkt(spatial):
        """
        Convert lats and lons to a WKT linestring.

        :param dict spatial: A dict with keys 'lat' and 'lon' (as lists)
        :returns: A Python string representing a WKT linestring
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
        :returns: Dict containing name:value information
        """
        return {"name": name,
                "value": value}

    def get(self):
        """Return the list of parameter items"""
        return self.items

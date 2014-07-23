import json


class Properties(object):
    def __init__(self, file_level=None, spatial=None,
                 temporal=None, parameters=None, data_format=None):
        """
        Construct a 'eufar.metadata.Properties' object with data
        conforming to Steve Donegan's FatCat JSON metadata structure.
        (see "doc/schema.json")
        """
        # TODO document parameters

        self.file_level = file_level
        self.spatial = spatial
        self.temporal = temporal
        self.parameters = parameters
        self.data_format = data_format

    def _to_wkt(self, spatial):
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

        linestring = "LINESTRING (%s)" % ', '.join(coord_list)
        return linestring

    def __str__(self):
        """
        Format file properties to JSON when coercing object to string.
        :return: A Python string containing JSON representation of object.
        """

        if self.spatial is not None:
            self.spatial = self._to_wkt(self.spatial)

        properties = {
            "data_format": self.data_format,
            "file": self.file_level,
            "parameters": self.parameters,
            "spatial": self.spatial,
            "temporal": self.temporal,
        }
        return json.dumps(properties, indent=4)

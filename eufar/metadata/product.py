import json


class Properties(object):
    def __init__(self, file_level=None, spatial=None,
                 temporal=None, parameters=None, data_format=None):
        """
        Construct a eufar.metadata.Properties object with data conforming to
        Steve Donegan's FatCat JSON metadata structure.
        (see "arsf-geo-map/doc/schema.json")
        """

        self.file_level = file_level
        self.spatial = spatial
        self.temporal = temporal
        self.parameters = parameters
        self.data_format = data_format
        
    def _geospatial_list_to_wkt(self):
        raise NotImplementedError("Not implemented yet.")

    def __str__(self):
        properties = {
            "file": {
                "properties": self.file_level,
            },
            "spatial": {
                "properties": self.spatial,
            },
            "temporal": {
                "properties": self.temporal,
            },
            "parameters": {
                "properties": self.parameters,
            },
            "data_format": {
                "properties": self.data_format,
            },
        }
        return json.dumps(properties, indent=4)

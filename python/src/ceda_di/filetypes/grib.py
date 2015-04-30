import iris

from ceda_di.dataset import _geospatial
from ceda_di.metadata import product

class GRIB(_geospatial):
    def __init__(self, fname):
        """
        :param str fname: Filesystem path to GRIB file.
        """
        self.fname = fname
        self.cubes = iris.load(self.fname)

        self.param_properties = ["origin", "long_name",
                               "standard_name", "var_name"]

    def get_temporal(self):
        return {}

    def get_geospatial(self):
        return {}

    def get_data_format(self):
        data_format = {
            "format": "GRIB"
        }

    def get_parameters(self):
        def _get_param_meta(obj):
            param_info = {}
            for key in param_properties:
                try:
                    value = getattr(obj, key)
                    if value is not None:
                        param_info[key] = value
                except AttributeError:
                    pass  # Ignore the error, the property doesn't exist
            return param_info

        params = []
        for cube in self.cubes:
            for coords in cube.coords():
                other_params = _get_param_meta(coords, self.param_properties)
                param = product.Parameter(coords.name(),
                                          other_params=other_params)

    def get_properties(self):
        """
        :return dict: A dictionary containing the GRIB file's properties.
        """
        properties = product.Properties(
            filesystem=self.get_filesystem(self.fname),
            temporal=self.get_temporal(),
            data_format=self.get_data_format(),
            spatial=self.get_geospatial(),
            parameters=self.get_parameters()
        )

        return properties

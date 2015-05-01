import iris

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product

class GRIB_PP(_geospatial):
    def __init__(self, fname):
        """
        :param str fname: Filesystem path to GRIB file.
        """
        self.fname = fname
        self.cubes = iris.load(self.fname)
        self.param_properties = ["origin", "long_name",
                                 "standard_name", "var_name"]
        self.unit_properties = ["origin", "name", "symbol", "definition"]

    def get_temporal(self):
        return {}

    def get_geospatial(self):
        return {}

    def get_data_format(self):
        data_format = {
            "format": "GRIB"
        }

    def get_parameters(self):
        def _get_meta(obj):
            """
            Helper function to help extract variable names and unit metadata.
            """
            names = ["long_name", "standard_name", "var_name"]

            metadata = {}
            for key in names:
                try:
                    value = getattr(obj, key)
                    if value is not None:
                        metadata[key] = value
                except AttributeError:
                    pass  # This attribute doesn't exist, ignore

            # Try to get unit information, too
            try:
                units = obj.units
                units_meta = {
                    "origin": units.origin,
                    "name": units.name,
                    "symbol": units.symbol,
                    "definition": units.definition
                }
            except AttributeError:
                units_meta = None

            if units_meta is not None:
                metadata.update(units_meta)

            return product.Parameter(name=obj.name(unknown="unknown"),
                                     other_params=metadata)

        params = []
        for cube in self.cubes:
            params.append(_get_meta(cube))
            for coords in cube.coords():
                params.append(_get_meta(coords))

        return params

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

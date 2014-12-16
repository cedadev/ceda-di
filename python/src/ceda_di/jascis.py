"""
Contains class which use the JASMIN CIS tool to extract metadata from specific data formats
"""

import coards
from jasmin_cis.data_io.products.AProduct import get_coordinates, get_variables, get_data

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product
from ceda_di.metadata.product import Parameter


class JasCisDataProduct(_geospatial):
    """
    Use a JASMIN CIS data product to read the data from a file
    """

    def __init__(self, filename):
        """
        Initiate the reader
        :param filename: filename to read
        :return: nothing
        """
        super(JasCisDataProduct, self).__init__()
        self._filenames = [filename]

    def __enter__(self):
        """
        Entry for with
        :return: self
        """
        return self

    def __exit__(self, *args):
        """
        exit for with
        :param args: arguments
        :return: nothing
        """
        pass

    def get_geospatial(self):
        """
        Returns a dict containing geospatial information
        """

        coords = get_coordinates(self._filenames)
        lat = coords.coord(standard_name='latitude')
        lon = coords.coord(standard_name='longitude')

        return {
            'lat': lat.points,
            'lon': lon.points
        }

    def get_temporal(self):
        """
        Returns a dict containing temporal information
        """

        coords = get_coordinates(self._filenames)
        time = coords.coord(standard_name='time')
        start_time = coards.parse(min(time.points), time.units)
        end_time = coards.parse(max(time.points), time.units)
        return {"start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()}

    def get_parameters(self):
        """
        Returns a dict containing parameter information
        """

        variables = get_variables(self._filenames)
        parameters = []
        for variable in variables:
            variable_data = get_data(self._filenames, variable)
            param = Parameter(variable_data.name(), variable_data.metadata.__dict__)
            parameters.append(param)
        return parameters

    def get_properties(self):
        """
        return product properties
        :return: products properties
        """
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()
        filesystem = self.get_filesystem(self._filenames[0])
        parameters = self.get_parameters()
        data_format = {
            "format": "CloudSat HDF",
        }

        props = product.Properties(spatial=geospatial,
                                   temporal=temporal,
                                   filesystem=filesystem,
                                   data_format=data_format,
                                   parameters=parameters)

        return props

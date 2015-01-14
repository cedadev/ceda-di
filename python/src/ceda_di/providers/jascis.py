"""
Contains class which use the JASMIN CIS tool to extract metadata from specific data formats
"""

import coards
from jasmin_cis.exceptions import ClassNotFoundError
from jasmin_cis.exceptions import FileFormatError as jasmin_cis_FileFormatError
from jasmin_cis.data_io.products.AProduct import get_coordinates, get_variables, get_data, get_file_format, \
    get_product_full_name, ProductPluginException
from jasmin_cis.time_util import convert_std_time_to_datetime

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product
from ceda_di.metadata.product import Parameter, FileFormatError
import numpy as np

# noinspection PyMissingConstructor
class JasCisDataProduct(_geospatial):
    """
    Use a JASMIN CIS data product to read the data from a file
    """

    @staticmethod
    def get_file_format(filename):
        try:
            get_file_format([filename])
        except ClassNotFoundError:
            raise FileFormatError("No reader from CIS could be found")
        except jasmin_cis_FileFormatError as ex:
            message = ".".join(ex.error_list)
            raise FileFormatError(message)
        except ProductPluginException as ex:
            raise FileFormatError("There was a problem with CIS %s" % ex.message)

    def __init__(self, filename):
        """
        Initiate the reader
        :param filename: filename to read
        :return: nothing
        """
        self._filenames = [filename]
        self._coords = None

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


    def _get_coords(self):
        """
        Return the coordinates, loading them first if needed
        :return: the coordinate list
        """
        if self._coords is None:
            self._coords = get_coordinates(self._filenames)
        return self._coords

    def get_geospatial(self):
        """
        Returns a dict containing geospatial information
        """

        coords = self._get_coords()
        lat = coords.get_coordinates_points().latitudes
        lon = coords.get_coordinates_points().longitudes
        return {
            'lat': lat,
            'lon': lon
        }

    def get_temporal(self):
        """
        Returns a dict containing temporal information
        """

        coords = self._get_coords()
        time = coords.get_coordinates_points().times
        start_time = convert_std_time_to_datetime(np.amin(time))
        end_time = convert_std_time_to_datetime(np.amax(time))
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
            "format": get_file_format(self._filenames)
        }

        indexer = get_product_full_name(self._filenames)
        index_entry_creation = {
            "indexer": indexer
        }

        props = product.Properties(spatial=geospatial,
                                   temporal=temporal,
                                   filesystem=filesystem,
                                   data_format=data_format,
                                   parameters=parameters,
                                   index_entry_creation=index_entry_creation)

        return props

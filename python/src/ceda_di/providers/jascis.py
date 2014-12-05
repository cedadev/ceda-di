"""
Contains classes whuch use the JASMIN CIS tool to extract metadata from specific data formats
"""

import coards
from jasmin_cis.data_io.products.products import CloudSat as CisCloudSat

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product
from ceda_di.metadata.product import Parameter


class CloudSat(_geospatial):
    """
    Extracts metadata from the CloudSat data format:
    http://www.cloudsat.cira.colostate.edu/dataHome.php
    Uses the JASMIN CIS tool to understand the CloudSat data format
    """

    def __init__(self, filename):
        self.cis_cloud_sat = CisCloudSat()
        self.filename = filename

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get_geospatial(self):
        """Returns a dict containing geospatial information"""
        coords = self.cis_cloud_sat.create_coords([self.filename])
        lat = coords.coord(standard_name='latitude')
        lon = coords.coord(standard_name='longitude')

        return {
            'lat': lat.points,
            'lon': lon.points
        }

    def get_temporal(self):
        """Returns a dict containing temporal information"""
        coords = self.cis_cloud_sat.create_coords([self.filename])
        time = coords.coord(standard_name='time')
        start_time = coards.parse(min(time.points), time.units)
        end_time = coards.parse(max(time.points), time.units)
        return {"start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()}

    def get_parameters(self):
        """Returns a dict containing parameter information"""
        variables = self.cis_cloud_sat.get_variable_names(self.filename).keys()
        parameters = []
        for variable in variables:
            variable_data = self.cis_cloud_sat.create_data_object([self.filename],variable)
            param = Parameter(variable_data.name(), variable_data.metadata.__dict__)
            parameters.append(param)
        return parameters

    def get_properties(self):
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()
        filesystem = self.get_filesystem(self.filename)
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

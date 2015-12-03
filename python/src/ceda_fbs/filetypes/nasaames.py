import datetime

import nappy

from ceda_fbs._dataset import _geospatial
from ceda_fbs.metadata import product


class NASAAmes(_geospatial):
    def __init__(self, fname):
        """
        :type fname: Filesystem path to the NASA Ames file
        """
        self.fname = fname
        self.na = nappy.openNAFile(self.fname)
        self._data_in_memory = False

    def _read_data(self):
        """
        """
        if not self._data_in_memory:
            self.na.readData()
            self._data_in_memory = True

    def _find_variable(self, search_string):
        """
        """
        search_string = search_string.lower()
        for i, v in enumerate(self.na.getVariables()):
            if search_string in v[0].lower():
                return i
        return None

    def _find_attribute(self, search_string):
        search_string = search_string.lower()
        for k, v in self.na.getNADict().iteritems():
            if search_string in k.lower():
                return (k, v)

        return (None, None)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def get_temporal(self):
        date = self._find_attribute("DATE")
        rdate = self._find_attribute("RDATE")

        if rdate:
            time_var = rdate[1]
        elif date:
            time_var = date
        else:
            return None

        return {
            "start_time": datetime.datetime(*time_var).isoformat(),
            "end_time": datetime.datetime(*time_var).isoformat()
        }

    def get_geospatial(self):
        """
        Extract geospatial data (if any exists)
        """
        spatial = {
            "type": "track",
            "lat": [],
            "lon": []
        }

        # Try to find the variables containing latitude/longitude
        lat_var = self._find_variable("latitude")
        lon_var = self._find_variable("longitude")
        if lat_var and lon_var:
            self._read_data()  # Read the data into memory if it isn't already
            vd = self.na.getNADict()["V"]  # Get variables and data

            for lat, lon in zip(vd[lat_var], vd[lon_var]):
                spatial["lat"].append(lat)
                spatial["lon"].append(lon)

            return spatial

        return None

    def get_data_format(self):
        data_format = {
            "format": "NASA Ames"
        }

        return data_format

    def get_parameters(self):
        """
        :return:
        """
        variables = {}
        for v in self.na.getVariables():
            variables.update({
                v[0]: {
                    "name": v[0],
                    "units": v[1]
                }
            })

        variables = [product.Parameter(k, other_params=v) for (k, v) in variables.iteritems()]
        return variables

    def get_properties(self):
        """
        :return:
        """
        properties = product.Properties(
            filesystem=self.get_filesystem(self.fname),
            temporal=self.get_temporal(),
            data_format=self.get_data_format(),
            spatial=self.get_geospatial(),
            parameters=self.get_parameters()
        )

        return properties
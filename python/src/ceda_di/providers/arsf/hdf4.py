"""
Interface to extract and generate JSON from HDF4 EUFAR metadata
"""

import datetime

from pyhdf.HDF import HDF
from pyhdf.VS import VS
from pyhdf.V import V
from pyhdf.error import HDF4Error

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product
from ceda_di.providers import arsf


class HDF4(_geospatial):
    """
    HDF4 context manager class.
    """
    hdf = None
    vs = None
    v = None

    def __init__(self, fname):
        """
        :param str fname: The path of the HDF4 file.
        """
        self.fname = str(fname)

    def __enter__(self):
        """
        Open HDF file and interfaces for use as context manager.

        :returns: Self.
        """
        self.hdf = HDF(self.fname)
        self.vs = self.hdf.vstart()
        self.v = self.hdf.vgstart()

        return self

    def __exit__(self, *args):
        """
        Close interfaces and HDF file after finishing use in context manager.
        """
        self.v.end()
        self.vs.end()
        self.hdf.close()

    def _get_coords(self, vs, fn):
        """
        Iterate through vgroup and return a list of coordinates (if existing).

        :param HDF4.V.vs vs: VData object
        :param str fn: Path to the data file
        :returns: Dict containing geospatial information.
        """
        mappings = {
            "NVlat2": "lat",
            "NVlng2": "lon",
        }

        coords = {}
        for k, v in mappings.iteritems():
            ref = vs.find(k)
            vd = vs.attach(ref)

            coords[v] = []
            while True:
                try:
                    coord = float(vd.read()[0][0]) / (10**7)
                    coords[v].append(coord)
                except HDF4Error:  # End of file
                    break

            vd.detach()
        return coords

    def _get_temporal(self, vs, fn):
        """
        Return start and end timestamps (if existing)

        :param HDF4.V.vs vs: VData object
        :param str fn: Path to the data file
        :returns: Dict containing temporal information.
        """
        mappings = {
            "MIdate": "date",
            "MIstime": "start_time",
            "MIetime": "end_time",
        }

        timestamps = {}
        for k, v in mappings.iteritems():
            ref = vs.find(k)
            vd = vs.attach(ref)

            timestamps[v] = []
            while True:
                try:
                    timestamps[v].append(vd.read()[0][0])
                except HDF4Error:  # EOF
                    break

            vd.detach()

        # This list comprehension basically converts from a list of integers
        # into a list of chars and joins them together to make strings
        # ...
        # If unclear - HDF text data comes out as a list of integers, e.g.:
        # 72 101 108 108 111 32 119 111 114 108 100 (this means "Hello world")
        # Those "char" numbers get converted to strings with this snippet.
        dates = [chr(x) for x in timestamps["date"] if x != 0]
        timestamps["date"] = ''.join(dates)

        return self._parse_timestamps(timestamps)

    def _parse_timestamps(self, tm_dict):
        """
        Parse start and end timestamps from an HDF4 file.

        :param dict tm_dict: The timestamp to be parsed
        :returns: Dict containing start and end timestamps
        """
        st_base = ("%s %s" % (tm_dict["date"], tm_dict["start_time"][0]))
        et_base = ("%s %s" % (tm_dict["date"], tm_dict["end_time"][0]))

        for t_format in ["%d/%m/%y %H%M%S", "%d/%m/%Y %H%M%S"]:
            try:
                start_time = datetime.datetime.strptime(st_base, t_format)
                end_time = datetime.datetime.strptime(et_base, t_format)
            except ValueError:
                # ValueError will be raised if strptime format doesn't match
                # the actual timestamp - so just try the next strptime format
                continue

        return {"start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()}

    def get_geospatial(self):
        """
        Search through HDF4 file, returning a list of coordinates from the
        'Navigation' vgroup (if it exists).

        :returns: Dict containing geospatial information.
        """
        ref = -1
        while True:
            try:
                ref = self.v.getid(ref)
                vg = self.v.attach(ref)

                if vg._name == "Navigation":
                    geospatial = self._get_coords(self.vs, self.fname)
                    geospatial["type"] = "track"  # Type annotation
                    vg.detach()
                    return geospatial

                vg.detach()
            except HDF4Error:  # End of file
                # This is a weird way of handling files, but this is what the
                # pyhdf library demonstrates...
                break

        return None

    def get_temporal(self):
        """
        Search through HDF4 file, returning timestamps from the 'Mission'
        vgroup (if it exists)

        :returns: List containing temporal metadata
        """
        ref = -1
        while True:
            try:
                ref = self.v.getid(ref)
                vg = self.v.attach(ref)

                if vg._name == "Mission":
                    temporal = self._get_temporal(self.vs, self.fname)
                    vg.detach()
                    return temporal

                vg.detach()
            except HDF4Error:  # End of file
                # This 'except at end of file' thing is some pyhdf weirdness
                # Check the pyhdf documentation for clarification
                break

        return None

    def get_properties(self):
        """
        Returns ceda_di.metadata.properties.Properties object
        containing geospatial and temporal metadata from file.

        :returns: Metadata.product.Properties object
        """
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()
        filesystem = super(HDF4, self).get_filesystem(self.fname)
        data_format = {
            "format": "HDF4",
        }

        instrument = arsf.Hyperspectral.get_instrument(filesystem["filename"])
        flight_info = arsf.Hyperspectral.get_flight_info(filesystem["filename"])
        props = product.Properties(spatial=geospatial,
                                   temporal=temporal,
                                   filesystem=filesystem,
                                   data_format=data_format,
                                   instrument=instrument,
                                   flight_info=flight_info)

        return props

"""
Interface to extract and generate JSON from Generic Flight JSON metadata files.
"""

import os
import pprint
import json

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product


class GenericFlight(_geospatial):
    """
    Generic Flight scanner class.
    """

    def __init__(self, fname):
        """
        :param str fname: The path of the data file.
        """
        self.fname = str(fname)
        self.flight_metadata_file = str(fname)

    def __enter__(self):
        """
        Open file and interfaces for use as context manager.
        :returns: Self.
        """
        self._parse_content()
        return self

    def __exit__(self, *args):
        """
        Close interfaces and file after finishing use in context manager.
        """
        pass

    def _parse_content(self):
        """
        Parses content of input file.
        """
        with open(self.flight_metadata_file) as reader:
            self.content = json.load(reader)

    def get_geospatial(self):
        """
        Return coordinates.
        :returns: Dict containing geospatial information.
        """
        return self.content["spatial"]

    def get_temporal(self):
        """
        Returns temporal window.
        :returns: List containing temporal metadata
        """
        return self.content["temporal"]

    def _update_extra_metadata(self, extra_metadata):
        """
        Set extra content from existing content and filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        pass

    def _update_filesystem_metadata(self, metadata):
        """
        Takes the dictionary file info `metadata` and maps from the JSON
        content to the actual data file(s).
        """
        metadata_file = self.fname

        # Test for presence and size of data file
        data_file = self.content["file"]["path"]
        directory = os.path.dirname(data_file)

        if os.path.isfile(data_file):
            location = 'on_disk'
            data_file_size = os.path.getsize(data_file)
        else:
            location = 'on_tape'
            data_file_size = 0

        # Add to metadata dictionary
        item_map = {'directory': directory, 'metadata_file': metadata_file,
                    'data_file': data_file, 'location': location,
                    'path': data_file, 'data_file_size': data_file_size}

        for key, value in item_map.items():
            metadata[key] = value


    def get_properties(self):
        """
        Returns ceda_di.metadata.properties.Properties object
        containing geospatial and temporal metadata from file.
        :returns: Metadata.product.Properties object
        """
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()

        # File system metadata
        filesystem = super(GenericFlight, self).get_filesystem(self.fname)
        self._update_filesystem_metadata(filesystem)

        data_format = self.content["data_format"]

        # Gather up extra metadata
        extra_metadata = self.content["misc"]

        # Set extra content from existing content and filename
        self._update_extra_metadata(extra_metadata)

        props = product.Properties(spatial=geospatial,
                                   temporal=temporal,
                                   filesystem=filesystem,
                                   data_format=data_format,
                                   **extra_metadata)

        return props



def check_match(d1, d2):
    "Raises an exception if any part of dictionary `d1` is not in `d2`."
    for (key, value) in d1.items():
        if key not in d2:
            raise Exception("Cannot find key '%s' in response: %s" % (key, d1))

        if isinstance(value, dict):
            check_match(value, d2[key])
        else:
            if value != d2[key]:
                raise Exception("Value ('%s') for key '%s' does not match expected value: '%s'" % (
                    value, key, d2[key]))


def test_parser():
    "Tests parsing of an S1 and S2 file and searches for content."

    # Prescribe content to test that find it in the output
    eg1_content = { 
        "parameters": None,
        "temporal": { "start_time": "2010-07-14T09:06:00", "end_time": "2010-07-14T09:10:00" },
        "misc": { "instrument": { "name": "AHS" },
                  "flight_info": {} },
        "data_format": { "format": "ENVI" },
        "file": {
            "symlinks": [],
            "path": "/badc/eufar/data/projects/t-mapp-fp7/intacasa-rs_20100714_tmappfp7/AHS_100714/calibrated_data/AHS_100714_0906Z_P01BD_L00120_PT34.raw",
            "data_file_size": 325762500,
            "data_file": "/badc/eufar/data/projects/t-mapp-fp7/intacasa-rs_20100714_tmappfp7/AHS_100714/calibrated_data/AHS_100714_0906Z_P01BD_L00120_PT34.raw",
            "filename": "AHS_100714_0906Z_P01BD_L00120_PT34_flight_info.json"},
        "spatial": { "geometries": {
                          "search": { "type": "envelope", "coordinates": [ [ 5.89465972914, 43.4594775347 ],
                                      [ 6.14033684529, 43.6369635359 ] ] }, 
                          "display": { "type": "LineString", "coordinates": [ [ 6.12232674111, 43.4616328513 ],
                                      [ 6.11255187452, 43.4712461593 ], [ 6.1024392898, 43.4805513577 ],
                                      [ 6.08997609085, 43.4880096416 ], [ 6.08042651581, 43.4977054382 ],
                                      [ 6.06911713789, 43.506531062 ], [ 6.05848106284, 43.5156247128 ],
                                      [ 6.0478394764, 43.5245961952 ], [ 6.03703713626, 43.5334094282 ],
                                      [ 6.02626535295, 43.5421158156 ], [ 6.01614534177, 43.5511805934 ],
                                      [ 6.00511710801, 43.5597240913 ], [ 5.99462202391, 43.5684783045 ],
                                      [ 5.98459808396, 43.5778107996 ], [ 5.97303684431, 43.5864057393 ],
                                      [ 5.96192136246, 43.5946957934 ], [ 5.95243423057, 43.6042764919 ],
                                      [ 5.94155636607, 43.6130881335 ], [ 5.92994012069, 43.621407286 ],
                                      [ 5.91992467846, 43.6310218526 ], [ 5.90821272709, 43.6394892214 ] ] } }
                   }
         }

    source_files = [
        "/badc/eufar/data/projects/t-mapp-fp7/intacasa-rs_20100714_tmappfp7/metadata/AHS_100714_0906Z_P01BD_L00120_PT34_flight_info.json"
    ]

    test_files = [
        ("GenericFlight: eg1",
         "../../eg_files/generic_flight/AHS_100714_0906Z_P01BD_L00120_PT34_flight_info.json",
         eg1_content)
    ]

    for (test, filepath, to_match) in test_files[:]:

        print("\n\nTesting: %s" % test)
        print("With: %s\n" % filepath)

        cls = eval("%s" % test.split(":")[0])
        with cls(filepath) as handler:
            resp = handler.get_properties().as_dict()
            pprint.pprint(resp)
            check_match(to_match, resp)


if __name__ == "__main__":

    test_parser()

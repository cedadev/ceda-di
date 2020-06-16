"""
Interface to extract and generate JSON from Landsat MTL metadata
"""

from glob import glob
import os
import pprint

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product


# Define mappings dictionary of key words to sections we are capturing
def get_mappings(cls):
    product_info = {}
    mappings = {
        "platform": {
            "properties": {
                "Satellite": "SPACECRAFT_ID",
                "Instrument Abbreviation": "SENSOR_ID",
                "Instrument Mode": "SENSOR_MODE"
            },
        },
        "spatial": {
            "transformers": {
                # Defines method name used to convert string of coordinates
                # into list of tuples containing floats
                "Coordinates": "_package_coordinates",
            },
            "properties": {
                "Coordinates": ['CORNER_UL_LAT_PRODUCT',
                                'CORNER_UL_LON_PRODUCT',
                                'CORNER_UR_LAT_PRODUCT',
                                'CORNER_UR_LON_PRODUCT',
                                'CORNER_LR_LAT_PRODUCT',
                                'CORNER_LR_LON_PRODUCT',
                                'CORNER_LL_LAT_PRODUCT',
                                'CORNER_LL_LON_PRODUCT',
                                'CORNER_UL_LAT_PRODUCT',
                                'CORNER_UL_LON_PRODUCT'
                               ]
            },
        },
        "product_info": product_info,
        "acquisition_period": {
            "transformers": {
                # Defines method name used to convert a date and a time into a
                # datetime
                "Start Time": "_package_datetime",
            },
            "properties": {
                "Start Time": ['DATE_ACQUIRED', 'SCENE_CENTER_TIME'],
            }
        },

        "quality_info": {
            "transformers": {
                # Defines method name used to convert a float
                "Cloud Coverage Assessment": "_to_float",
            },
            "properties": {
                "Cloud Coverage Assessment": "CLOUD_COVER",
            }
        }
    }

    return mappings


class LandsatBase(_geospatial):
    """
    Landsat MTL context manager class.
    """

    def __init__(self, fname):
        """
        :param str fname: The path of the data file.
        """
        self.fname = str(fname)
        self.manifest = str(fname)
        self.mappings = get_mappings(self.__class__)

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
        manifest_properties = {}
        with open(self.manifest) as myfile:
            for line in myfile:
                name, var = line.partition("=")[::2]
                manifest_properties[name.strip()] = var.strip().strip('"')

        self.sections = {}
        for section_id, content_dict in self.mappings.items():
            if not content_dict:
                continue

            self.sections[section_id] = {}
            for item_name, property_name in content_dict["properties"].items():
                if property_name != "":
                    try:
                        if isinstance(property_name, str):
                            value = manifest_properties[property_name]
                        else:
                            multi_value = []
                            for name in property_name:
                                multi_value.append(manifest_properties[name])
                            value = ",".join(multi_value)

                        if item_name in content_dict.get("transformers", {}):
                            transformer = (
                                getattr(self, content_dict["transformers"][item_name]))
                            value = transformer(value)

                        self.sections[section_id][item_name] = value
                    except:
                        pass

    def _package_coordinates(self, coords_string):
        """
        Converts a coordinates string into a dictionary of lats and lons.

        :param string coords_string: a string of lat,lon pairs
                     (separated by commas or spaces)
        :returns: Dictionary of: {"lats": <list of lats>,
                                  "lons": <list of lons>}
        """
        values = [float(x)
                  for x in coords_string.strip().replace(",", " ").split()]
        if len(values) % 2 != 0:
            raise Exception("Number of values for coordinates is not even.")

        return {"lat": values[0::2], "lon": values[1::2],
                "type": "polygon",
                "do_sanitise_geometries": False}

    def _package_datetime(self, datetime_string):
        value = datetime_string.replace(",", "T")
        return value

    def _to_float(self, item):
        return float(item)

    def get_geospatial(self):
        """
        Return coordinates.

        :returns: Dict containing geospatial information.
        """
        return self.sections["spatial"]["Coordinates"]

    def get_temporal(self):
        """
        Returns temporal window.

        :returns: List containing temporal metadata
        """
        ap = self.sections["acquisition_period"]
        return {"start_time": ap["Start Time"],
                "end_time": ap.get("Stop Time", ap["Start Time"])}

    def _add_filename_metadata(self, extra_metadata):
        """
        Adds extra metadata extracted from the filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """

        # Make sure product_info section exists
        extra_metadata.setdefault('product_info', {})

        file_name = os.path.basename(self.fname)

        # Add file/scan name
        extra_metadata['product_info']['Name'] = file_name.split('_')[0]

    def _derive_extra_metadata(self, extra_metadata):
        """
        Derives extra fields from the existing fields.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        # Add/ update platform data
        satellite = self.sections['platform']['Satellite']
        extra_metadata['platform']['Mission'] = "Landsat"
        extra_metadata['platform']['Satellite'] = satellite.replace('_', '-')
        extra_metadata['platform']['Platform Family Name'] = (
            satellite.split('_')[0])
        extra_metadata['platform']['Family'] = (
            extra_metadata['platform']['Platform Family Name'])

    def _update_extra_metadata(self, extra_metadata):
        """
        Set extra content from existing content and filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        self._add_filename_metadata(extra_metadata)
        self._derive_extra_metadata(extra_metadata)

    def _update_filesystem_metadata(self, metadata):
        """
        Takes the dictionary file info `metadata` and does some MTL specific
        searching for the '.TIF' and '.jpg' files to report on their existence
        in the output dictionary by adding to `metadata`.
        """
        directory, fname = os.path.split(self.fname)
        fbase = fname.split('_')[0]

        # Test for presence and size of tif file
        os.listdir(directory)
        tiff_files = glob(os.path.join(directory, '{}*.TIF'.format(fbase)))

        if len(tiff_files) > 0:
            location = 'on_disk'
            tiff_files.sort()
            _, data_file = os.path.split(tiff_files[0])
            data_file_size = os.path.getsize(
                os.path.join(directory, data_file))
            tiff_names = []
            tiff_sizes = []
            for tiff in tiff_files:
                _, tiff_name = os.path.split(tiff)
                tiff_names.append(tiff_name)
                tiff_sizes.append(str(os.path.getsize(tiff)))
            tiff_names = ",".join(tiff_names)
            tiff_sizes = ",".join(tiff_sizes)
        else:
            location = 'on_tape'
            data_file_size = 0
            data_file = ""

        # Test for presence of quick look PNG file
        quicklook_file = fbase + '_VER.jpg'
        quicklook_path = os.path.join(directory, quicklook_file)

        if not os.path.isfile(quicklook_path):
            quicklook_file = ''

        # Add to metadata dictionary
        item_map = {'directory': directory, 'metadata_file': fname,
                    'data_file': data_file, 'location': location,
                    'data_file_size': data_file_size,
                    'quicklook_file': quicklook_file}

        if len(tiff_files) > 0:
            item_map.update({'data_files': tiff_names,
                             'data_file_sizes': tiff_sizes})

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
        filesystem = super(LandsatBase, self).get_filesystem(self.fname)
        self._update_filesystem_metadata(filesystem)

        data_format = {"format": "GeoTIFF"}

        # Gather up extra metadata
        extra_metadata = {}
        for key in ("platform", "product_info", "quality_info"):
            if self.sections.get(key):
                extra_metadata[key] = self.sections[key]

        # Set extra content from existing content and filename
        self._update_extra_metadata(extra_metadata)

        props = product.Properties(spatial=geospatial,
                                   temporal=temporal,
                                   filesystem=filesystem,
                                   data_format=data_format,
                                   **extra_metadata)

        return props


# Define specific classes for different Landsat missions
class Landsat5(LandsatBase):
    pass


class Landsat7(LandsatBase):
    pass


class Landsat8(LandsatBase):
    pass


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
    lt5_content = {'data_format': {'format': 'GeoTIFF'},
                   'file': {'data_file': 'LT50300432008315EDC00_B1.TIF',
                            'data_file_size': 10,
                            'data_files': 'LT50300432008315EDC00_B1.TIF,LT50300432008315EDC00_B2.TIF',
                            'data_file_sizes': '10,0',
                            'directory': '../../eg_files/landsat',
                            'filename': 'LT50300432008315EDC00_MTL.txt',
                            'location': 'on_disk',
                            'metadata_file': 'LT50300432008315EDC00_MTL.txt',
                            'path': '../../eg_files/landsat/LT50300432008315EDC00_MTL.txt',
                            'quicklook_file': 'LT50300432008315EDC00_VER.jpg',
                            'size': 5415},
                   'misc': {'platform':
                            {'Family': 'LANDSAT',
                             'Instrument Abbreviation': 'TM',
                             'Instrument Mode': 'BUMPER',
                             'Mission': 'Landsat',
                             'Platform Family Name': 'LANDSAT',
                             'Satellite': 'LANDSAT-5'},
                            'product_info': {'Name': 'LT50300432008315EDC00'},
                            'quality_info': {'Cloud Coverage Assessment': 39.00}},
                   'spatial': {'geometries':
                               {'display':
                                {'coordinates': [[[-105.04975, 25.483609999999999], [-102.6985, 25.46557], 
                                             [-102.73269999999999, 23.575849999999999], 
                                             [-105.04901, 23.592390000000002], 
                                             [-105.04975, 25.483609999999999]]],
                                 'type': 'Polygon'}}},
                   'temporal': {'end_time': '2008-11-10T17:06:17.5690940Z',
                                'start_time': '2008-11-10T17:06:17.5690940Z'}
                   }

    le7_content = {'data_format': {'format': 'GeoTIFF'},
                   'file': {'data_file': '',
                            'data_file_size': 0,
                            'directory': '../../eg_files/landsat',
                            'filename': 'LE70200492009223EDC00_MTL.txt',
                            'location': 'on_tape',
                            'metadata_file': 'LE70200492009223EDC00_MTL.txt',
                            'path': '../../eg_files/landsat/LE70200492009223EDC00_MTL.txt',
                            'quicklook_file': '',
                            'size': 6856},
                   'misc': {'platform':
                            {'Family': 'LANDSAT',
                             'Instrument Abbreviation': 'ETM',
                             'Instrument Mode': 'BUMPER',
                             'Mission': 'Landsat',
                             'Platform Family Name': 'LANDSAT',
                             'Satellite': 'LANDSAT-7'},
                            'product_info': {'Name': 'LE70200492009223EDC00'},
                            'quality_info': {'Cloud Coverage Assessment': 76.00}},
                   'spatial': {'geometries':
                               {'display':
                                {'coordinates': [[[-91.599530000000001, 16.850989999999999], 
                                      [-89.371549999999999, 16.823699999999999], 
                                      [-89.404989999999998, 14.95064], 
                                      [-91.612470000000002, 14.97475], 
                                      [-91.599530000000001, 16.850989999999999]]],
                                 'type': 'Polygon'}}},
                   'temporal': {'end_time': '2009-08-11T16:13:53.3465278Z',
                                'start_time': '2009-08-11T16:13:53.3465278Z'}
                   }

    lc8_content = {'data_format': {'format': 'GeoTIFF'},
                   'file': {'data_file': '',
                            'data_file_size': 0,
                            'directory': '../../eg_files/landsat',
                            'filename': 'LC81940122016126LGN00_MTL.txt',
                            'location': 'on_tape',
                            'metadata_file': 'LC81940122016126LGN00_MTL.txt',
                            'path': '../../eg_files/landsat/LC81940122016126LGN00_MTL.txt',
                            'quicklook_file': '',
                            'size': 7898},
                   'misc': {'platform':
                            {'Family': 'LANDSAT',
                             'Mission': 'Landsat',
                             'Platform Family Name': 'LANDSAT',
                             'Satellite': 'LANDSAT-8'},
                            'product_info': {'Name': 'LC81940122016126LGN00'},
                            'quality_info': {'Cloud Coverage Assessment': 19.38}},
                   'spatial': {'geometries':
                               {'display':
                                {'coordinates': [[[20.023389999999999, 69.426270000000002], 
                                        [26.441880000000001, 69.343649999999997], 
                                        [25.92662, 67.071219999999997], 
                                        [20.116320000000002, 67.144850000000005], 
                                        [20.023389999999999, 69.426270000000002]]],
                                 'type': 'Polygon'}}},
                   'temporal': {'end_time': '2016-05-05T10:03:58.0056090Z',
                                'start_time': '2016-05-05T10:03:58.0056090Z'}
                   }

    source_files = [
        "/neodc/landsat5/data/TM/2008/11/10/030/043/Level1/LPGS_12.5.0/LT50300432008315EDC00_B1.TIF",
        "/neodc/landsat5/data/TM/2008/11/10/030/043/Level1/LPGS_12.5.0/LT50300432008315EDC00_MTL.txt",
        "/neodc/landsat5/data/TM/2008/11/10/030/043/Level1/LPGS_12.5.0/LT50300432008315EDC00_VER.jpg",
        "/neodc/landsat7etm/p020/r049/LE70200492009223EDC00/LE70200492009223EDC00_MTL.txt",
        "/neodc/landsat8/data/OLI_TIRS/2016/05/05/194/012/Level1/LPGS_2.6.2/LC81940122016126LGN00_MTL.txt",
    ]

    test_files = [
        ("Landsat5: LT5",
         "../../eg_files/landsat/LT50300432008315EDC00_MTL.txt",
         lt5_content),
        ("Landsat7: LE7",
         "../../eg_files/landsat/LE70200492009223EDC00_MTL.txt",
         le7_content),
        ("Landsat8: LC8",
         "../../eg_files/landsat/LC81940122016126LGN00_MTL.txt",
         lc8_content),
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

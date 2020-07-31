'''Interface to handle extraction and generation of JSON from Sentinel ARD data'''

import datetime, os, pprint
import xml.etree.cElementTree as ET

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product

# Set up name spaces for use in XML paths
namespaces = {
'gmd': 'http://www.isotc211.org/2005/gmd',
    "gml": "http://www.opengis.net/gml",
    'gco': 'http://www.isotc211.org/2005/gco',
    "xfdu": "urn:ccsds:schema:xfdu:1",
    'gmx': 'http://www.isotc211.org/2005/gmx'
}

def get_mappings(cls):

    product_info = {}

    ns = {key: value for key, value in namespaces.items()}

    #iso19115 format xml
    east_bdc = '{%(gmd)s}eastBoundLongitude/{%(gco)s}Decimal' % ns
    west_bdc = '{%(gmd)s}westBoundLongitude/{%(gco)s}Decimal' % ns
    north_bdc = '{%(gmd)s}northBoundLatitude/{%(gco)s}Decimal' % ns
    south_bdc = '{%(gmd)s}southBoundLatitude/{%(gco)s}Decimal' % ns

    # Generic mappings
    mappings = {
        "spatial": {
            "common_prefix":
                "{%(gmd)s}identificationInfo/{%(gmd)s}MD_DataIdentification/{%(gmd)s}extent/{%(gmd)s}EX_Extent/{%(gmd)s}geographicElement/{%(gmd)s}EX_GeographicBoundingBox/" % ns,
            "transformers": {
                # Defines method name used to convert string of coordinates into list of tuples containing floats
                "Coordinates": "_package_coordinates",
            },
            "properties": {'Coordinates':
                               {'eastbc': east_bdc, 'westbc':west_bdc, 'southbc': south_bdc, 'northbc': north_bdc}
                           },
        },
        "acquisition_period": {
            "common_prefix":
                "{%(gmd)s}identificationInfo/{%(gmd)s}MD_DataIdentification/{%(gmd)s}extent/{%(gmd)s}EX_Extent/{%(gmd)s}temporalElement/{%(gmd)s}EX_TemporalExtent/{%(gmd)s}extent/{%(gml)s}TimePeriod/" % ns,
            "properties": {
                "Start Time": "{%(gml)s}beginPosition" % ns,
                "End Time": "{%(gml)s}endPosition" % ns
            }
        }
    }

    return mappings

class Sentinel_ARD_Base(_geospatial):

    def __init__(self, fname):
        """
        :param str fname: The path of the data file.
        """
        self.fname = str(fname)
        self.manifest = os.path.splitext(self.fname)[0] + ".xml"
        self.mappings = get_mappings(self.__class__)

    def __enter__(self):
        """
        Open file and interfaces for use as context manager.

        :returns: Self.
        """
        self.root = ET.parse(self.manifest).getroot()
        self._parse_content()

        return self

    def __exit__(self, *args):
        """
        Close interfaces and file after finishing use in context manager.
        """
        pass

    def _get_content_by_type(self, elem, attr_name=None):
        """
        Return the content of an element as "text" (if `attr_name` is None) or
        as an attribute if `attr_name` is set.
        """
        if not attr_name:
            resp = elem.text
        else:
            resp = elem.get(attr_name, "")

        return resp.strip()

    def _parse_content(self):
        self.sections = {}

        for section_id, content_dict in self.mappings.items():
            if not content_dict: continue

            self.sections[section_id] = {}
            prefix = content_dict["common_prefix"]
            multiple_element_props = content_dict.get("multiples", [])

            for item_name, xml_path_details in content_dict["properties"].items():

                # Decide how to treat the xml path and work out if we need to get the element content or attribute
                if type(xml_path_details) == str:
                    xml_path = prefix + xml_path_details
                    attr_name = None

                elif type(xml_path_details) == dict:
                    xml_path = {}
                    for key,value in xml_path_details.items():
                        xml_path[key ] = prefix + xml_path_details[key]

                    #for ard set this to none - don't think we'll be needing it from the basic iso19115 xml
                    attr_name = None
                else:
                    xml_path = prefix + xml_path_details[0]
                    attr_name = xml_path_details[1]

                try:
                    # Handle multiple element case - concatenate them into a comma-separated string
                    if type(xml_path) != dict:
                        if item_name in multiple_element_props:
                            value = ",".join([self._get_content_by_type(elem, attr_name=attr_name) for elem in
                                              self.root.findall(xml_path)])
                        else:  # single element only
                            value = self._get_content_by_type(self.root.find(xml_path), attr_name=attr_name)

                        if item_name in content_dict.get("transformers", {}):
                            transformer = getattr(self, content_dict["transformers"][item_name])
                            value = transformer(value)

                        self.sections[section_id][item_name] = value

                    else:
                        d={}
                        for key,value in xml_path.items():
                            xml_path[key] = self._get_content_by_type(self.root.find(value), attr_name=attr_name)

                        #todo - convert the coords now into the expected string used th etransformer method
                        if item_name in content_dict.get("transformers", {}):
                            transformer = getattr(self, content_dict["transformers"][item_name])

                        value = transformer(xml_path)

                        self.sections[section_id][item_name] = value

                except:
                    pass

    def _package_coordinates(self, coords_string):
        """
        Converts a coordinates string into a dictionary of lats and lons.

        :param string coords_string: a string of lat,lon pairs
                     (separated by commas or spaces)
        :returns: Dictionary of: {"lats": <list of lats>, "lons": <list of lons>}
        """

        # parse the westbc etc here {'eastbc': '6.284688', 'westbc': '1.942106', 'southbc': '51.834194', 'northbc': '53.745213'}
        # seems to be in required order: BL - TL - TR - BR based on example from SAFE parsing
        latitudes_in_order = [coords_string['southbc'], coords_string['northbc'], coords_string['northbc'], coords_string['southbc']]
        longitudes_in_order = [coords_string['westbc'], coords_string['westbc'], coords_string['eastbc'], coords_string['eastbc']]

        # Convert strings to floats
        latitudes_in_order = [float(x) for x in latitudes_in_order]
        longitudes_in_order = [float(x) for x in longitudes_in_order]

        return {"lat": latitudes_in_order, "lon": longitudes_in_order, "type": "polygon", "do_sanitise_geometries": False}

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


    def _derive_extra_metadata(self, extra_metadata):
        """
        Derives extra fields from the existing fields.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        extra_metadata['platform']['Family'] = extra_metadata['platform']['Platform Family Name']

        # Add platform number if derivable from file
        if self.__class__ is not Sentinel_ARD_Base:
            extra_metadata['platform']['Family'] += "-%s" % extra_metadata['platform']['Platform Number']


    def _update_extra_metadata(self, extra_metadata):
        """
        Set extra content from existing content and filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        self._add_filename_metadata(extra_metadata)
        #self._derive_extra_metadata(extra_metadata)

        #if type(self) == SAFESentinel3:
        #    self._extract_metadata_from_zipfile(extra_metadata)


    def _add_filename_metadata(self, extra_metadata):
        """
        Adds extra metadata extracted from the filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """

        #todo parse the platform A or B here and anything else from the filename here

        # Make sure product_info section exists
        extra_metadata.setdefault('product_info', {})

        file_name = os.path.basename(self.fname)
        fn_comps = file_name.split("_")

        # Add file/scan name
        extra_metadata['product_info']['Name'] = os.path.splitext(file_name)[0]

        # Add Satellite and Mission from the file path
        extra_metadata['platform'] = {}
        comp_1 = fn_comps[0].upper()
        extra_metadata['platform']['Mission'] = f"Sentinel-{comp_1[1]}"
        extra_metadata['platform']['Satellite'] = f"Sentinel-{comp_1[1:]} ARD"


    def _update_filesystem_metadata(self, metadata):
        """
        Takes the dictionary file info `metadata` and does some ESA SAFE specific searching for
        the '.zip' and '.png' files to report on their existence in the output dictionary by
        adding to `metadata`.
        """
        directory, fname = os.path.split(self.fname)
        fbase = os.path.splitext(fname)[0].replace('_meta','')

        # Test for presence and size of zip file
        zip_file = fbase + '.tif'
        zip_path = os.path.join(directory, zip_file)

        if os.path.isfile(zip_path):
            location = 'on_disk'
            data_file_size = os.path.getsize(zip_path)
        else:
            location = 'on_tape'
            data_file_size = 0

        quicklook_file = ''

        # Add to metadata dictionary
        item_map = {'directory': directory, 'metadata_file': fname,
                    'data_file': zip_file, 'location': location,
                    'data_file_size': data_file_size, 'quicklook_file': quicklook_file}

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
        filesystem = super(Sentinel_ARD_Base, self).get_filesystem(self.fname)
        self._update_filesystem_metadata(filesystem)

        data_format = {"format": "ARD"}

        # Gather up extra metadata
        extra_metadata = {}
        for key in ("platform", "product_info", "orbit_info"):
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


class SentinelARDSentinel2(Sentinel_ARD_Base):
    mission = "Sentinel1"


class SentinelARDSentinel1(Sentinel_ARD_Base):
    mission = "Sentinel2"



def test_parser():

    s1b_ard_content = {'misc': {'platform': {'Platform Family Name': 'SENTINEL-1',
                                         'Family': 'SENTINEL-1', 'Instrument Abbreviation': 'SAR',
                                         'Mission': 'Sentinel-1', 'Satellite': 'Sentinel-1B'},
                            'product_info': {'Product Type': 'ARD',
                                             'Name': 'S1B_20200202_110_desc_055728_055753_VVVH_G0_GB_OSGB_RTCK_SpkRL'
                                             }}}

    source_files = ["/neodc/sentinel_ard/data/sentinel_1/2020/02/02/S1B_20200202_110_desc_055728_055753_VVVH_G0_GB_OSGB_RTCK_SpkRL_meta.xml"]

    test_files_S1_ARD = [
        ("Sentinel1",
         "../../../../../eg_files/sentinel_ard/S1B_20200202_110_desc_055728_055753_VVVH_G0_GB_OSGB_RTCK_SpkRL_meta.xml",
         s1b_ard_content)]

    test_files = test_files_S1_ARD

    for (test, filepath, to_match) in test_files[:]:
        ("\n\nTesting: %s" % test)
        print("With: %s\n" % filepath)

        #cls_name = "SAFE%s" % test.split(":")[0]
        cls_name = 'Sentinel_ARD_Base'
        cls = eval(cls_name)
        print("Using class: {0}".format(cls_name))

        try:
            with cls(filepath) as handler:
                resp = handler.get_properties().as_dict()
                pprint.pprint(resp)
                # check_match(to_match, resp)
        except Exception as ex:
            print (ex)

if __name__ == "__main__":


    test_parser()


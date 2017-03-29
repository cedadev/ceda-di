"""
Interface to extract and generate JSON from ESA SAFE Sentinel metadata
"""

import datetime, os, pprint
import xml.etree.cElementTree as ET

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product
from ceda_di.providers.esa import sentinel2


# Set up name spaces for use in XML paths
namespaces = {
    "gml": "http://www.opengis.net/gml",
    "gx": "http://www.google.com/kml/ext/2.2",
    "s1": "http://www.esa.int/safe/sentinel-1.0/sentinel-1",    
    "s1sar": "http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar",
    "s1sarl1": "http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-1",
    "s1sarl2": "http://www.esa.int/safe/sentinel-1.0/sentinel-1/sar/level-2",
    "safe_1_0": "http://www.esa.int/safe/sentinel-1.0",    
    "safe_1_1": "http://www.esa.int/safe/sentinel/1.1",
    "xfdu": "urn:ccsds:schema:xfdu:1",
}


def get_mappings(cls):

    ns = {key: value for key, value in namespaces.items()}
    ns["safe"] = ns[cls.namespace]

    if cls == SAFESentinel1:
        product_info = {
          "multiples": ["Polarisation"],
          "common_prefix":
            "./metadataSection/metadataObject[@ID='generalProductInformation']/metadataWrap/xmlData/",
          "properties": {
             "Product Class": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}productClass" % ns,
             "Product Class Description": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}productClassDescription" % ns,
             "Timeliness Category": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}productTimelinessCategory" % ns,
             "Product Composition": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}productComposition" % ns,
             "Product Type": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}productType" % ns,
             "Polarisation": "{%(s1sarl1)s}standAloneProductInformation/{%(s1sarl1)s}transmitterReceiverPolarisation" % ns,
           }
        }
    else:
        product_info = {}

    # Generic mappings
    mappings = {
        "platform": {
           "common_prefix": 
               "./metadataSection/metadataObject[@ID='platform']/metadataWrap/xmlData/",
           "properties": {
               "Platform Family Name": "{%(safe)s}platform/{%(safe)s}familyName" % ns, 
               "NSSDC Identifier": "{%(safe)s}platform/{%(safe)s}nssdcIdentifier" % ns,
               "Instrument Family Name": "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}familyName" % ns,
               "Instrument Abbreviation": ("{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}familyName[@abbreviation]"  % ns, "abbreviation")
           },
        },    
        "spatial": {
           "common_prefix":
               "./metadataSection/metadataObject[@ID='measurementFrameSet']/metadataWrap/xmlData/",
           "transformers": {
               # Defines method name used to convert string of coordinates into list of tuples containing floats
               "Coordinates": "_package_coordinates",
           },
           "properties": {},  
        },
        "product_info": product_info,
        "orbit_info": {
           "common_prefix":
               "./metadataSection/metadataObject[@ID='measurementOrbitReference']/metadataWrap/xmlData/",
           "properties": {
               "Start Relative Orbit Number": "{%(safe)s}orbitReference/{%(safe)s}relativeOrbitNumber[@type='start']" % ns,
               "Start Orbit Number": "{%(safe)s}orbitReference/{%(safe)s}orbitNumber[@type='start']" % ns,
           },
        },
        "acquisition_period": {
           "common_prefix":
               "./metadataSection/metadataObject[@ID='acquisitionPeriod']/metadataWrap/xmlData/",
           "properties": {
               "Start Time": "{%(safe)s}acquisitionPeriod/{%(safe)s}startTime" % ns,
           }
        }    
    }

    if cls == SAFESentinel1:
        mappings["platform"]["properties"]["Instrument Mode"] = "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}extension/{%(s1sarl1)s}instrumentMode/{%(s1sarl1)s}mode" % ns

        mappings["orbit_info"]["properties"]["Stop Relative Orbit Number"] = "{%(safe)s}orbitReference/{%(safe)s}relativeOrbitNumber[@type='stop']" % ns
        mappings["orbit_info"]["properties"]["Phase Identifier"] = "{%(safe)s}orbitReference/{%(safe)s}phaseIdentifier" % ns

        mappings["orbit_info"]["properties"]["Pass Direction"] = "{%(safe)s}orbitReference/{%(safe)s}extension/{%(s1)s}orbitProperties/{%(s1)s}pass" % ns
        mappings["orbit_info"]["properties"]["Cycle Number"] = "{%(safe)s}orbitReference/{%(safe)s}cycleNumber" % ns

        mappings["orbit_info"]["properties"]["Stop Orbit Number"] = "{%(safe)s}orbitReference/{%(safe)s}orbitNumber[@type='stop']" % ns

        mappings["spatial"]["properties"]["Coordinates"] = "{%(safe)s}frameSet/{%(safe)s}frame/{%(safe)s}footPrint/{%(gml)s}coordinates" % ns
        mappings["acquisition_period"]["properties"]["Stop Time"] = "{%(safe)s}acquisitionPeriod/{%(safe)s}stopTime" % ns

    elif cls == SAFESentinel2:
        mappings["platform"]["properties"]["Instrument Mode"] = "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}mode" % ns
        mappings["platform"]["properties"]["Platform Number"] = "{%(safe)s}platform/{%(safe)s}number" % ns
        mappings["spatial"]["properties"]["Coordinates"] = "{%(safe)s}frameSet/{%(safe)s}footPrint/{%(gml)s}coordinates" % ns

    elif cls == SAFESentinel3:
        mappings["platform"]["properties"]["Instrument Mode"] = "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}mode" % ns
        mappings["platform"]["properties"]["Platform Number"] = "{%(safe)s}platform/{%(safe)s}number" % ns
        mappings["spatial"]["properties"]["Coordinates"] = "{%(safe)s}frameSet/{%(safe)s}footPrint/{%(gml)s}posList" % ns

    else:
        raise Exception("Class {0} not recognised.".format(cls.__name__))

    return mappings


class SAFESentinelBase(_geospatial):
    """
    ESA SAFE Sentinel context manager class.
    """

    def __init__(self, fname):
        """
        :param str fname: The path of the data file.
        """
        self.fname = str(fname)
        self.manifest = os.path.splitext(self.fname)[0] + ".manifest"
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
                else:
                    xml_path = prefix + xml_path_details[0]
                    attr_name = xml_path_details[1]
                    
                try:
                    # Handle multiple element case - concatenate them into a comma-separated string
                    if item_name in multiple_element_props:
                        value = ",".join([self._get_content_by_type(elem, attr_name=attr_name) for elem in self.root.findall(xml_path)])
                    else: # single element only
                        value = self._get_content_by_type(self.root.find(xml_path), attr_name=attr_name)

                    if item_name in content_dict.get("transformers", {}):
                        transformer = getattr(self, content_dict["transformers"][item_name])
                        value = transformer(value)
                    
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
        values = [float(x) for x in coords_string.strip().replace(",", " ").split()]

        if len(values) % 2 != 0:
            raise Exception("Number of values for coordinates is not even.")
 
        return {"lat": values[0::2], "lon": values[1::2], "type": "polygon", "do_sanitise_geometries": False}


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
        fn_comps = file_name.split("_")
        
        if self.__class__ == SAFESentinel1:
            component = fn_comps[2]
            if len(component) < 4: 
                resolution = 'N/A'
            else:
                resolution = component[-1]
                
            extra_metadata['product_info']['Resolution'] = resolution
        
        # Add file/scan name        
        extra_metadata['product_info']['Name'] = os.path.splitext(file_name)[0]
        
        # Add Satellite and Mission from the file path
        comp_1 = fn_comps[0].upper()
        extra_metadata['platform']['Mission'] = "Sentinel-%s" % comp_1[1]
        extra_metadata['platform']['Satellite'] = "Sentinel-%s" % comp_1[1:]


    def _derive_extra_metadata(self, extra_metadata):
        """
        Derives extra fields from the existing fields.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        extra_metadata['platform']['Family'] = extra_metadata['platform']['Platform Family Name']

        # Add platform number if derivable from file
        if self.__class__ is not SAFESentinel1:
            extra_metadata['platform']['Family'] += "-%s" % extra_metadata['platform']['Platform Number']

            
    def _extract_metadata_from_zipfile(self, extra_metadata):
        """
        Set extra metadata extracted from the zip file.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.       
        """
        try:
            zip_metadata = sentinel2.Sentinel2Scan(self.fname).sentinel_metadata 
        except:
            return 
            
        datatake_attr = "Datatake Type"
        if hasattr(zip_metadata, datatake_attr):
            extra_metadata["product_info"][datatake_attr] = getattr(zip_metadata, datatake_attr)

        cloud_attr = "Cloud Coverage Assessment"
        if hasattr(zip_metadata, cloud_attr):
            extra_metadata["quality_info"] = {cloud_attr: float(getattr(zip_metadata, cloud_attr))}

            
    def _update_extra_metadata(self, extra_metadata):
        """
        Set extra content from existing content and filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.       
        """
        self._add_filename_metadata(extra_metadata)
        self._derive_extra_metadata(extra_metadata)
        
        if self.__class__ == SAFESentinel2:
            self._extract_metadata_from_zipfile(extra_metadata)


    def _update_filesystem_metadata(self, metadata):
        """
        Takes the dictionary file info `metadata` and does some ESA SAFE specific searching for 
        the '.zip' and '.png' files to report on their existence in the output dictionary by 
        adding to `metadata`.
        """
        directory, fname = os.path.split(self.fname)
        fbase = os.path.splitext(fname)[0]
        
        # Test for presence and size of zip file
        zip_file = fbase + '.zip'
        zip_path = os.path.join(directory, zip_file)
        
        if os.path.isfile(zip_path):
            location = 'on_disk'
            data_file_size = os.path.getsize(zip_path)
        else:
            location = 'on_tape'
            data_file_size = 0
            
        # Test for presence of quick look PNG file
        quicklook_file = fbase + '.png'
        quicklook_path = os.path.join(directory, quicklook_file)
        
        if not os.path.isfile(quicklook_path):
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
        filesystem = super(SAFESentinelBase, self).get_filesystem(self.fname)
        self._update_filesystem_metadata(filesystem)

        data_format = {"format": "SAFE"}

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


# Define specific classes for different Sentinel missions
class SAFESentinel1(SAFESentinelBase): 
    namespace = "safe_1_0"


class SAFESentinel2(SAFESentinelBase): 
    namespace = "safe_1_1"


class SAFESentinel3(SAFESentinelBase):
    namespace = "safe_1_1"


def check_match(d1, d2):
    "Raises an exception if any part of dictionary `d1` is not in `d2`."
    for (key, value) in d1.items():
        if key not in d2:
            raise Exception("Cannot find key '%s' in response: %s" % (key, d1))
            
        if isinstance(value, dict):
            check_match(value, d2[key])
        else:
            if value != d2[key]:
                raise Exception("Value ('%s') for key '%s' does not match expected value: '%s'" % (value, key, d2[key]))            

                
def test_parser():
    "Tests parsing of an S1 and S2 file and searches for content."

    # Prescribe content to test that find it in the output
    s1a_content = {'misc': {'platform': {'Instrument Mode': 'EW', 'Platform Family Name': 'SENTINEL-1',
                                        'Family': 'SENTINEL-1', 'Instrument Abbreviation': 'SAR',
                                        'Mission': 'Sentinel-1', 'Satellite': 'Sentinel-1A'},
                          'product_info': {'Product Type': 'GRD', 'Resolution': 'M',
                                           'Name': 'S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF',
                                           'Polarisation': 'HH,HV'}}}

    s1b_content = {'misc': {'platform': {'Instrument Mode': 'IW', 'Platform Family Name': 'SENTINEL-1',
                                        'Family': 'SENTINEL-1', 'Instrument Abbreviation': 'SAR',
                                        'Mission': 'Sentinel-1', 'Satellite': 'Sentinel-1B'},
                          'product_info': {'Product Type': 'SLC', 
                                           'Name': 'S1B_IW_SLC__1SSV_20161101T010312_20161101T010340_002758_004AB5_B6E7',
                                           'Polarisation': 'VV'}}}

    s2_1_content = {'misc': {'platform': {'Platform Family Name': 'SENTINEL', 'Platform Number': '2A',
                                        'Family': 'SENTINEL-2A', 'Mission': 'Sentinel-2', 'Satellite': 'Sentinel-2A',
                                        'Instrument Abbreviation': 'MSI'},
                           'product_info': {'Name': 'S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305'}}}

    s2_2_content = {'misc': {'platform': {'Platform Family Name': 'SENTINEL', 'Platform Number': '2A',
                                        'Family': 'SENTINEL-2A', 'Mission': 'Sentinel-2', 'Satellite': 'Sentinel-2A',
                                        'Instrument Abbreviation': 'MSI'},
                           'product_info': {'Name': 'S2A_OPER_PRD_MSIL1C_PDMC_20160801T072514_R073_V20160801T000734_20160801T000734',
                                            'Datatake Type': 'INS-NOBS'},
                           'quality_info': {'Cloud Coverage Assessment': 27.67777777777778}},
                    'spatial': {'geometries': {'search': {'coordinates': 
                          [[[154.81522194202373,
                             -10.849976483467962],
                            [151.7477474521766,
                             -10.849976483467962],
                            [151.7477474521766,
                             -12.762291212286028],
                            [154.81522194202373,
                             -12.762291212286028],
                            [154.81522194202373,
                             -10.849976483467962]]]
                        }}}
                    }

    s2_3_content = {'misc': {'product_info': {'Datatake Type': 'INS-NOBS',
                                              'Name': 'S2A_MSIL1C_20170221T233801_N0204_R001_T53CMQ_20170221T233758'},
                             'quality_info': {'Cloud Coverage Assessment': 0.0}}
                   }

    s3a_content = {'file': {'data_file': 'S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.zip',
                            'data_file_size': 0,
                            'directory': '../../eg_files/sentinel',
                            'filename': 'S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.manifest',
                            'location': 'on_tape',
                            'metadata_file': 'S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.manifest',
                            'path': '../../eg_files/sentinel/S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.manifest',
                            'quicklook_file': '',
                            'size': 197442},
                   'misc': {'orbit_info': {'Start Orbit Number': '4082',
                                           'Start Relative Orbit Number': '259'},
                   'platform': {'Family': 'Sentinel-3-A',
                                'Instrument Abbreviation': 'SLSTR',
                                'Instrument Family Name': 'Sea and Land Surface Temperature Radiometer',
                                'Instrument Mode': 'Earth Observation',
                                'Mission': 'Sentinel-3',
                                'NSSDC Identifier': '0000-000A',
                                'Platform Family Name': 'Sentinel-3',
                                'Platform Number': 'A',
                                'Satellite': 'Sentinel-3A'},
                   'product_info': {'Name': 'S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002'}},
                    }
                           
    source_files = [
         "/neodc/sentinel1a/data/EW/L1_GRD/m/IPF_v2/2016/01/01/S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF.manifest",
         "/neodc/sentinel1b/data/IW/L1_SLC/IPF_v2/2016/11/01/S1B_IW_SLC__1SSV_20161101T010312_20161101T010340_002758_004AB5_B6E7.manifest",
         "/neodc/sentinel2a/data/L1C_MSI/2016/07/03/S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305.manifest",
         "/neodc/sentinel2a/data/L1C_MSI/2016/08/01/S2A_OPER_PRD_MSIL1C_PDMC_20160801T072514_R073_V20160801T000734_20160801T000734.manifest",       
         "/neodc/sentinel2a/data/L1C_MSI/2017/02/21/S2A_MSIL1C_20170221T233801_N0204_R001_T53CMQ_20170221T233758.manifest",
         "/neodc/sentinel3a/data/SLSTR/L1_RBT/2016/11/29/S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.manifest"]
        
    test_files_S1 = [
        ("Sentinel1",
         "../../eg_files/sentinel/S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF.manifest",
         s1a_content),
        ("Sentinel1: S1B",
         "../../eg_files/sentinel/S1B_IW_SLC__1SSV_20161101T010312_20161101T010340_002758_004AB5_B6E7.manifest",
         s1b_content)
        ]

    test_files_S2 = [
        ("Sentinel2: 1",
         "../../eg_files/sentinel/S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305.manifest",
         s2_1_content),
        ("Sentinel2: 2",
         "../../eg_files/sentinel/S2A_OPER_PRD_MSIL1C_PDMC_20160801T072514_R073_V20160801T000734_20160801T000734.manifest",
         s2_2_content), 
        ("Sentinel2: 3 MSIL1C version (different zip)",
         "../../eg_files/sentinel/S2A_MSIL1C_20170221T233801_N0204_R001_T53CMQ_20170221T233758.manifest",
         s2_3_content)
        ]        

    test_files_S3 = [
        ("Sentinel3: S3A",
         "../../eg_files/sentinel/S3A_SL_1_RBT____20161129T002703_20161129T003003_20161129T030545_0179_011_259_0900_SVL_O_NR_002.manifest",
         s3a_content),
        ]

    test_files = test_files_S1 + test_files_S2 + test_files_S3
        
    for (test, filepath, to_match) in test_files[:]:
  
        print "\n\nTesting: %s" % test
        print "With: %s\n" % filepath
 
        cls_name = "SAFE%s" % test.split(":")[0]
        cls = eval(cls_name)
        print "Using class: {0}".format(cls_name)

        with cls(filepath) as handler: 
            resp = handler.get_properties().as_dict() 
            pprint.pprint(resp)
            check_match(to_match, resp)
            

if __name__ == "__main__":

    test_parser()

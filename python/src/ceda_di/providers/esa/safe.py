"""
Interface to extract and generate JSON from ESA SAFE Sentinel metadata
"""

import datetime, os, pprint
import xml.etree.cElementTree as ET

from ceda_di._dataset import _geospatial
from ceda_di.metadata import product


# Set up name spaces for use in XML paths
ns = {
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

# Define mappings dictionary of XML paths to sections we are capturing
def get_namespace_mappings(cls):
    """
    Return a dictionary of mappings according to the class being used.
    """
    if cls == SAFESentinel1a:
        ns["safe"] = ns["safe_1_0"]
        
    else: # if SafeSentinel2a
        ns["safe"] = ns["safe_1_1"]

    return get_mappings(ns)


def get_mappings(ns):

    if ns["safe"] == ns["safe_1_0"]:
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

    mappings = {
        "platform": {
           "common_prefix": 
               "./metadataSection/metadataObject[@ID='platform']/metadataWrap/xmlData/",
           "properties": {
               "Platform Family Name": "{%(safe)s}platform/{%(safe)s}familyName" % ns, 
               "NSSDC Identifier": "{%(safe)s}platform/{%(safe)s}nssdcIdentifier" % ns,
               "Instrument Family Name": "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}familyName" % ns,
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

    if ns["safe"] == ns["safe_1_0"]:
        mappings["platform"]["properties"]["Instrument Mode"] = "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}extension/{%(s1sarl1)s}instrumentMode/{%(s1sarl1)s}mode" % ns

        mappings["orbit_info"]["properties"]["Stop Relative Orbit Number"] = "{%(safe)s}orbitReference/{%(safe)s}relativeOrbitNumber[@type='stop']" % ns
        mappings["orbit_info"]["properties"]["Phase Identifier"] = "{%(safe)s}orbitReference/{%(safe)s}phaseIdentifier" % ns

        mappings["orbit_info"]["properties"]["Pass Direction"] = "{%(safe)s}orbitReference/{%(safe)s}extension/{%(s1)s}orbitProperties/{%(s1)s}pass" % ns
        mappings["orbit_info"]["properties"]["Cycle Number"] = "{%(safe)s}orbitReference/{%(safe)s}cycleNumber" % ns

        mappings["orbit_info"]["properties"]["Stop Orbit Number"] = "{%(safe)s}orbitReference/{%(safe)s}orbitNumber[@type='stop']" % ns

        mappings["spatial"]["properties"]["Coordinates"] = "{%(safe)s}frameSet/{%(safe)s}frame/{%(safe)s}footPrint/{%(gml)s}coordinates" % ns
        mappings["acquisition_period"]["properties"]["Stop Time"] = "{%(safe)s}acquisitionPeriod/{%(safe)s}stopTime" % ns
    else: # Sentinel 2
        mappings["platform"]["properties"]["Instrument Mode"] = "{%(safe)s}platform/{%(safe)s}instrument/{%(safe)s}mode" % ns
        mappings["platform"]["properties"]["Platform Number"] = "{%(safe)s}platform/{%(safe)s}number" % ns
        mappings["spatial"]["properties"]["Coordinates"] = "{%(safe)s}frameSet/{%(safe)s}footPrint/{%(gml)s}coordinates" % ns

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
        self.mappings = get_namespace_mappings(self.__class__)
              
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

    def _parse_content(self):
        self.sections = {}
       
        for section_id, content_dict in self.mappings.items():
            if not content_dict: continue

            self.sections[section_id] = {}
            prefix = content_dict["common_prefix"]
            multiple_element_props = content_dict.get("multiples", [])

            for item_name, xml_path_end in content_dict["properties"].items():
                xml_path = prefix + xml_path_end
                    
                try:
                    # Handle multiple element case - concatenate them into a space-separated string
                    if item_name in multiple_element_props:
                        value = " ".join([elem.text.strip() for elem in self.root.findall(xml_path)])
                    else: # single element only
                        value = self.root.find(xml_path).text.strip()

                    if item_name in content_dict.get("transformers", {}):
                        transformer = getattr(self, content_dict["transformers"][item_name])
                        value = transformer(value)
                    
                    self.sections[section_id][item_name] = value
                    #print "SUCCESS: %s --> %s" % (section_id, xml_path)
                except:
                    #print "FAILED: %s  -->  %s" % (section_id, xml_path)
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
 
        return {"lat": values[0::2], "lon": values[1::2], "type": "swath"}

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
        
        if self.__class__ == SAFESentinel1a:
            component = os.path.basename(self.fname).split("_")[2]
            if len(component) < 4: 
                resolution = 'N/A'
            else:
                resolution = component[-1]
                
            extra_metadata['product_info']['Resolution'] = resolution
        
        # Add mission name abbreviation        
        extra_metadata['product_info']['Name'] = os.path.splitext(os.path.basename(self.fname))[0]

    def _derive_extra_metadata(self, extra_metadata):
        """
        Derives extra fields from the existing fields.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.
        """
        extra_metadata['platform']['Family'] = extra_metadata['platform']['Platform Family Name']

        # Add number if derived from Sentinel2
        if self.__class__ == SAFESentinel2a:
            extra_metadata['platform']['Family'] += "-%s" % extra_metadata['platform']['Platform Number']
        
    def _update_extra_metadata(self, extra_metadata):
        """
        Set extra content from existing content and filename.
        Dictionary `extra_metadata` is changed in place.
        Returns nothing.       
        """
        self._add_filename_metadata(extra_metadata)
        self._derive_extra_metadata(extra_metadata)

    def get_properties(self):
        """
        Returns ceda_di.metadata.properties.Properties object
        containing geospatial and temporal metadata from file.

        :returns: Metadata.product.Properties object
        """
        geospatial = self.get_geospatial()
        temporal = self.get_temporal()
        filesystem = super(SAFESentinelBase, self).get_filesystem(self.fname)
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
class SAFESentinel1a(SAFESentinelBase): pass

class SAFESentinel2a(SAFESentinelBase): pass


def check_match(d1, d2):
    "Raises an exception if any part of dictionary `d1` is not in `d2`."
    for (key, value) in d1.items():
        if key not in d2:
            raise Exception("Cannot find key '%s' in response: %s" % (key, d1))
            
        if isinstance(value, dict):
            check_match(value, d2[key])
        else:
            if value != d2[key]:
                raise Exception("Value for key '%s' does not match expected value: '%s'" % (key, d2[key]))            

                
def test_parser():
    "Tests parsing of an S1 and S2 file and searches for content."

    # Prescribe content to test that find it in the output
    s1_content = {'misc': {'platform': {'Instrument Mode': 'EW', 'Platform Family Name': 'SENTINEL-1',
                                        'Family': 'SENTINEL-1'},
                          'product_info': {'Product Type': 'GRD', 'Resolution': 'M',
                                           'Name': 'S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF',
                                           'Polarisation': 'HH HV'}}}
    s2_content = {'misc': {'platform': {'Platform Family Name': 'SENTINEL', 'Platform Number': '2A',
                                        'Family': 'SENTINEL-2A'},
                           'product_info': {'Name': 'S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305'}}}
                          
    test_files = [
        ("Sentinel1a",
         "/neodc/sentinel1a/data/EW/L1_GRD/m/IPF_v2/2016/01/01/S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF.zip",
         s1_content),
        ("Sentinel2a",
         "/neodc/sentinel2a/data/L1C_MSI/2016/07/03/S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305.zip",
         s2_content)
        ]       
        
    test_files = [
        ("Sentinel1a",
         "../../eg_files/sentinel/S1A_EW_GRDM_1SDH_20160101T144136_20160101T144236_009302_00D6FE_49DF.zip",
         s1_content),
        ("Sentinel2a",
         "../../eg_files/sentinel/S2A_OPER_PRD_MSIL1C_PDMC_20160703T192815_R095_V20160703T124305_20160703T124305.zip",
         s2_content)
        ]        

        
    for (sat, filepath, to_match) in test_files:
  
        print "\n\nTesting: %s" % sat 
        print "With: %s" % filepath
 
        cls = eval("SAFE%s" % sat)
        with cls(filepath) as handler: 
            resp = handler.get_properties().as_dict() 
            #resp['spatial']['geometries']['display'] = resp['spatial']['geometries']['search'] = "dummy"
            pprint.pprint(resp)
            check_match(to_match, resp)
            

if __name__ == "__main__":

    test_parser()
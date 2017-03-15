import os, sys
import zipfile
import xml.etree.ElementTree as ET
import datetime


class SentinelMetadata(object):
    '''
    Set up an object to just hold information on required info
    '''
    
    def __init__(self, **kwargs):
        
        # Record as a dict for writing final version once full of details
        self.metadata_dict = {}
        
        for key, value in kwargs.iteritems():
            setattr(self, key, value)
            self.metadata_dict[key] = value
    
    
    def add_details(self, varname, varval):
        '''
        Add information on ingestion date, manifest file etc - just add given value as a self variable
        '''
        try:
            setattr(self, varname, varval)
        except:
            raise Exception("Cannot add %s" % varname)

            
    def return_dict(self):
        return self.metadata_dict
            
    
class Sentinel2Scan(object):

    def __init__(self, manifest_file, ingestdt = None):
        
        if not os.path.exists(manifest_file):
            raise Exception( "ERROR: Cannot find manifest file%s "% manifest_file)
        
        self.zip_filename = manifest_file.replace('.manifest', '.zip')
    
        if not os.path.exists(self.zip_filename):
            raise Exception ("ERROR: Cannot find data file file%s " % self.zip_filename)
        
        self.xpath_info()
        self.safe_metadata = self.extract_from_zip(self.zip_filename)
       
        self.extract_metadata()
                
        # Add extra information if needed
        if ingestdt is None:
            
            # Default time to now
            self.add_details('ingestion_date', datetime.datetime.now())
            
        else:
            self.add_details('ingestion_date', ingestdt)
            
        # Manifest_file
        self.add_details('manifest_file', manifest_file)
        
        # Zipfile loc
        self.add_details('datafile_file', self.zip_filename)
    
        # Get the object to hold the values
        self.sentinel_metadata = SentinelMetadata(**self.extracted_info)
    

    def xpath_info(self):
        '''
        Put here all info required to be extracted via xpath
            
        Note namespace used is https://psd-13.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd
        '''
        
        self.info_to_extract = {}
        self.info_to_extract['Datatake Type'] = "{https://psd-13.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}General_Info/Product_Info/Datatake/DATATAKE_TYPE"
        
        self.info_to_extract['Cloud Coverage Assessment'] = "{https://psd-13.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}Quality_Indicators_Info/Cloud_Coverage_Assessment"
        self.info_to_extract['product_type'] = "{https://psd-13.sentinel2.eo.esa.int/PSD/User_Product_Level-1C.xsd}General_Info/Product_Info/PRODUCT_TYPE"
    
    def zip_archive_info(self, filename):
        '''
        Calculate where to find the correct xml metadata file in the S2 zip.
        '''
        # Work out name of archive member we want to extract
        fname = os.path.basename(filename)
        sentinel_metadata_zip_dir = fname.replace('.zip', '.SAFE')

        if 'S2A_OPER_PRD_MSIL1C' in fname: 
            sentinel_metadata_zip_file = sentinel_metadata_zip_dir.replace('SAFE', 'xml').replace('PRD_MSIL1C', 'MTD_SAFL1C')
        elif 'S2A_MSIL1C' in fname:
            sentinel_metadata_zip_file = 'MTD_MSIL1C.xml'
        else: 
            raise Exception("Could not extract sentinel metadata zip file info for: %s" % filename)

        ziploc = os.path.join(sentinel_metadata_zip_dir, sentinel_metadata_zip_file)
        return ziploc
        
    
    def extract_from_zip(self, filename):
        '''
        Open the zip and return the extracted xml as a string object.
        '''
        try: 
            zf = zipfile.ZipFile(filename)
        except Exception as ex:
            raise Exception("ERROR: Cannot open zip archive: %s" % ex)
            
        try:
            safe_metadata = zf.read(self.zip_archive_info(filename))
        except KeyError as ex:
            raise Exception('ERROR: Cannot find metadata in target zip file (%s)' % ex)
            sys.exit()
            
        if type(safe_metadata) is str:
            return safe_metadata
        else:
            raise Exception ('ERROR: Cannot extract metadata properly')
                    
    
    def extract_metadata(self):
        '''
        Method to extract information and return as a dict with the original key values
        '''
        self.extracted_info = {}
        
        try:
            tree = ET.fromstring(self.safe_metadata)
        except Exception as ex:
            raise Exception("ERROR: Could not access xml structure for %s (%s)" % (file, ex)) 
                
        for element in self.info_to_extract.keys():
            
            xpath = self.info_to_extract[element]
            
            try:
                value = tree.find(xpath)
                if value is not None:
                    self.extracted_info[element] = value.text
                
            except Exception as ex:
                print "WARNING: Could not access information for %s (%s)" % (element, ex)
                self.extracted_info[element] = None
    
    
    def add_details(self, varname, varval):
        '''
        Add information on ingestion date, manifest file etc - just add given value as a self variable
        '''
        try:
            self.extracted_info[varname] = varval
        except:
            raise Exception("Cannot add %s" % varname)
    
    
    def write_metadata_file(self, output_filename):
        '''
        Write to output file as a key:value structure based on the dict
        '''
        
        # Open output file
        try:
            output_file = open(output_filename, 'w+')
            write_vals = self.sentinel_metadata.return_dict()
                       
            for key,value in write_vals.items():
                output_file.write("%s = %s\n" % (key, value))
                
            output_file.close()
            
        except Exception as ex:
            print "ERROR: Problem generating metadata output file: %s (%s)" % (output_filename, ex)
            sys.exit()
            
        if os.path.exists(output_filename):
            return True    
        else:
            return False
        
        
    def write_metadata(self):
        
        try:
            output_file = os.path.join(outputdir, os.path.basename(scan.zip_filename).replace('zip', 'metadata'))
            
            if self.write_metadata_file(output_file):
                print "INFO: Created metadata file: %s" % output_file
            else:
                print "ERROR: Unable to create metadata file: %s" % output_file
                
        except Exception:
            print "ERROR: Could not write metadata file"
            
                
if __name__ == '__main__':

    manifest_file = sys.argv[1]
    outputdir = sys.argv[2]
    
    try:
        scan = Sentinel2Scan(manifest_file)
                
    except Exception as ex:
        print "Error: %s" % ex
        sys.exit()
    
    # Write metadata
    if outputdir is not None:
        scan.write_metadata()
    
    
        

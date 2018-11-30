import os
import sys
import zipfile
from netCDF4 import Dataset
from tempfile import NamedTemporaryFile
import shutil
from sentinel2 import SentinelMetadata

sentinel3_zip_mapping = {
    "solar_zenith_nadir": "geometry_tn.nc",
    "solar_zenith_oblique": "geometry_to.nc",

}


class Sentinel3Scan(object):

    def __init__(self, manifest_file):

        if not os.path.exists(manifest_file):
            raise Exception("ERROR: Cannot find manifest file: %s" % manifest_file)

        self.zip_filename = manifest_file.replace('.manifest', '.zip')
        # self.zip_mapping = sentinel3_zip_mapping

        if not os.path.exists(self.zip_filename):
            raise Exception("ERROR: Cannot find data file: %s" % self.zip_filename)

        self.extract_metadata()

    def get_solar_zenith_range(self, data_file_extn, variable_name, archive_obj):

        # Manipulate the file name
        filename = os.path.basename(self.zip_filename)
        fname = filename.replace('.zip', data_file_extn)
        fopen = archive_obj.open(fname)

        # Create temporary file
        tmp = NamedTemporaryFile(delete=False)
        shutil.copyfileobj(fopen, tmp)
        fopen.close()
        tmp.close()

        # Read the contents
        d = Dataset(tmp.name)
        v = d.variables[variable_name]

        # Delete temporary file
        os.unlink(tmp.name)

        return v[:].min(), v[:].max()

    def extract_solar_zenith(self):

        # Open archive file object
        try:
            zf = zipfile.ZipFile(self.zip_filename)
        except Exception as ex:
            raise Exception("ERROR - Cannot open zip archive: {}".format(ex))

        # Extract nadir zenith range
        min_nadir, max_nadir = self.get_solar_zenith_range('.SEN3/geometry_tn.nc', 'solar_zenith_tn', zf)

        # Extract oblique zenith range
        min_oblique, max_oblique = self.get_solar_zenith_range('.SEN3/geometry_to.nc', 'solar_zenith_to', zf)

        extracted_info = {
            "nadir": {
                "max": max_nadir,
                "min": min_nadir,
                "range": {
                    "gte": min_nadir,
                    "lte": max_nadir
                }
            },
            "oblique": {
                "max": max_oblique,
                "min": min_oblique,
                "range":{
                    "gte": min_oblique,
                    "lte": max_oblique
                }
            }
        }

        self.sentinel_metadata = SentinelMetadata(**extracted_info)

    def extract_metadata(self):
        # Extract data from zipfile
        self.extract_solar_zenith()


if __name__ == '__main__':

    manifest_file = sys.argv[1]
    outputdir = sys.argv[2]

    try:
        scan = Sentinel3Scan(manifest_file).scan()

    except Exception as ex:
        print "Error: %s" % ex
        sys.exit()

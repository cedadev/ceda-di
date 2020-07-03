import os

import ceda_di.filetypes.netcdf


class FAAMNetCDF(object):
    """
    NetCDF metadata extraction wrapper for FAAM metadata.
    """
    def __init__(self, fpath):
        self.fpath = fpath
        self.nc_from_fac = ceda_di.filetypes.netcdf.NetCDFFactory(fpath)
        self.readme = self.get_readme(fpath)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_readme(self, fpath):
        """
        Goes several levels up the directory tree, looking for a README file.

        @param fpath The path to the input file
        @returns A list of keywords in the top line of the README
        """
        readme_name = "00README"
        fpath = os.path.split(fpath)[0]  # Chop off filename

        # Look at (maximum) 3 levels up directory tree for a "README"
        for i in range(0, 3):
            fpath = os.path.split(fpath)[0]
            readme_loc = os.path.join(fpath, readme_name)

            if os.path.isfile(readme_loc):
                with open(readme_loc, "r") as readme_file:
                    return readme_file.readline().rstrip().split(" ")

        return None

    def get_properties(self):
        """
        Return the NetCDF file's properties, also adding in metadata from the
        README file if one is available.

        @returns A metadata.product.Properties object populated with metadata.
        """
        props = self.nc_from_fac.get_properties()
        if props:
            properties = props.as_dict()
            if "misc" not in properties:
                props["misc"] = {}

            properties["misc"].update({
                "readme": self.readme
            })
            props.properties = properties

        return props


def test_parser():
    "Run a test with a test file."
    fpath = "/badc/faam/data/2016/b989-oct-20/core_processed/core_faam_20161020_v004_r0_b989_1hz.nc"
    test = FAAMNetCDF(fpath) 
    print(test.get_properties())

if __name__ == "__main__":

    test_parser()

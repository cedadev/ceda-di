import os

import ceda_di.filetypes.netcdf


class FAAMNetCDF(object):
    """
    NetCDF metadata extraction wrapper for FAAM metadata.
    """
    def __init__(self, fpath):
        self.nc = netcdf.NetCDFFactory(fpath)
        self.readme = self.get_readme(fpath)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return None

    def get_readme(self, fpath):
        """
        Goes several levels up the directory tree, looking for a README file.
        """
        readme_name = "00README"
        fpath = os.path.split(fpath)[0]  # Chop off filename

        # Look at (maximum) 3 levels up directory tree for a "README"
        for i in xrange(0, 3):
            fpath = os.path.split(fpath)[0]
            readme_loc = os.path.join(fpath, readme_name)

            if os.path.isfile(readme_loc):
                with open(readme_loc, "r") as readme_file:
                    return readme_file.readline().rstrip().split(" ")

        return None

    def get_properties(self):
        props = self.nc.get_properties()
        print props
        exit(1)
        if "misc" not in props:
            props["misc"] = {}

        props["misc"].update({
            "readme": self.readme
        })

        return props

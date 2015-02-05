import os

import ceda_di.filetypes.netcdf as nc


class FAAMNetCDF(object):
    def __init__(self, fpath):
        self.nc = nc.NetCDFFactory(fpath)
        # TODO some way of combining the main metadata with the README
        self.readme = self.get_readme(fpath)


    def get_readme(self, fpath):
        readme_name = "00README"

        fpath = os.path.split(fpath)[0]  # Chop off filename
        for i in xrange(0, 3):
            fpath = os.path.split(fpath)[0]
            readme_loc = os.path.join(fpath, readme_name)

            if os.path.isfile(readme_loc):
                with open(readme_loc, "r") as readme_file:
                    return readme_file.readline()

        return None

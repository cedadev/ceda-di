from eufar import netcdf_geo
import json
import sys

n = netcdf_geo.NetCDF(sys.argv[1])
with open(sys.argv[1]+".json", 'w') as f:
    f.write(json.dumps(n.get_geospatial(), indent=4))

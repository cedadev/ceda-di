from pyhdf.HDF import *
from pyhdf.V import *
from pyhdf.VS import *

class HDF4_geo(object):
    """
    ARSF/EUFAR HDF4 Geospatial context manager
    """
    def __init__(self, fname):
        self.fname = fname
        
    def __enter__(self):
        # Open HDF file and interfaces
        self.hdf = HDF(self.fname)
        self.vs = self.hdf.vstart()
        self.v = self.hdf.vgstart()
        
        return self

    def __exit__(self, *args):
        # Close interfaces and HDF file
        self.v.end()
        self.vs.end()
        self.hdf.close()        

    def get_coords(self, v, vs, fn):
        mappings = {
            "NVlat2": "lat",
            "NVlng2": "lng",
        }
    
        coords = {}
        coords[fn] = {}
        for k, v in mappings.iteritems():
            ref = vs.find(k)
            vd = vs.attach(ref)
            
            coords[fn][v] = []
            while True:
                try:
                    coord = float(vd.read()[0][0]) / (10**7)
                    coords[fn][v].append(coord)
                except HDF4Error:  # End of file
                    break

            vd.detach()
        return coords
        
    def get_geospatial(self):
        ref = -1
        while True:
            try:
                ref = self.v.getid(ref)
                vg = self.v.attach(ref)
                
                if vg._name == "Navigation":
                    finfo = self.get_coords(self.v, self.vs, self.fname)
                    vg.detach()
                    return finfo
                    
                vg.detach()
            except HDF4Error:
                break

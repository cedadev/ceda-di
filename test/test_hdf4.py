from pyhdf.HDF import *
from pyhdf.V   import *
from pyhdf.VS  import *
from pyhdf.SD  import *
import json
import sys

def describevg(refnum):
    # Open vgroup in read mode.
    vg = v.attach(refnum)
    
    if vg._name != "Navigation":
        vg.detach()
        return
    
    # Read the contents of the vgroup.
    members = vg.tagrefs()

    lats, lngs = ([], [])

    # Display info about each member.
    index = -1
    for tag, ref in members:
        index += 1
        # Vdata tag
        if tag == HC.DFTAG_VH:
            vd = vs.attach(ref)
            nrecs, intmode, fields, size, name = vd.inquire()
            
            if "NVlat2" == name:
                while True:
                    try:
                        rec = vd.read()       # read next record
                        lats.append(rec[0][0])
                    except HDF4Error:             # end of vdata reached
                        break
                        
            elif "NVlng2" == name:
                while True:
                    try:
                        rec = vd.read()       # read next record
                        lngs.append(rec[0][0])
                    except HDF4Error:             # end of vdata reached
                        break
           
            vd.detach()
            
            nav_stuff = {
                "lats": lats,
                "lngs": lngs,
            }
            
            with open("out.json", 'w') as f:
                f.write(json.dumps(nav_stuff, indent=4))

    # Close vgroup
    vg.detach()

# Open HDF file in readonly mode.
filename = sys.argv[1]
hdf = HDF(filename)

# Initialize the SD, V and VS interfaces on the file.
sd = SD(filename)
vs = hdf.vstart()
v  = hdf.vgstart()

# Scan all vgroups in the file.
ref = -1
while 1:
    try:
        ref = v.getid(ref)
        describevg(ref)
            
    except HDF4Error as msg:    # no more vgroup
        break
    

# Terminate V, VS and SD interfaces.
v.end()
vs.end()
sd.end()

# Close HDF file.
hdf.close()

import os
import eufar


for root, dirs, files in os.walk("/badc/eufar/data/aircraft/"):
    if files.endswith(".hdr") and "nav" in files and "qual" not in files:
        try:
            b = eufar.envi_geo.BIL(files)
            print(str(b.get_properties()))
        except:
            print(os.path.join(root, files))

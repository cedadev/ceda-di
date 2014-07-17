import eufar.envi_geo as envi
import json

bil = envi.BIL("/home/ccnewey/Downloads/e098021b_nav_post_processed.bil.hdr")

with open("out.json", 'w') as j:
    j.write(json.dumps(bil.get_geospatial(), indent=4))

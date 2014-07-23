import os
import sys
from eufar import envi_geo


def process_bil(path):
    with envi_geo.BIL(path) as b:
        json_fn = ["out/", os.path.splitext(f)[0], ".json"]
        with open(''.join(json_fn), 'w') as j:
            j.write(str(b.get_properties()))


process_counter = 0
for root, dirs, files in os.walk("/badc/eufar/data/aircraft/", followlinks=True):
    for f in files:
        if f.endswith(".hdr") and "nav" in f and "qual" not in f:
            path = os.path.join(root, f)
            process_bil(path)

            process_counter += 1
            if (process_counter % 100) == 0:
                sys.stdout.write("%d files processed\n" % process_counter)

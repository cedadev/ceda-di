import os
import sys
from eufar import envi_geo


def write_properties(fname, _geospatial_obj):
    fname = "out/%s.json" % os.splitext(fname)[0]  # Create JSON path
    with open(fname, 'w') as j:
        props = str(_geospatial_obj.get_properties())
        j.write(props)


def process_bil(path):
    with envi_geo.BIL(path) as b:
        json_fn = write_properties(f)


if __name__ == "__main__":
    if not os.path.isdir("out"):
        os.mkdir("out")

    file_counter = 0
    start_path = "/badc/eufar/data/aircraft/"
    for root, dirs, files in os.walk(start_path, followlinks=True):
        for f in files:
            # BIL navigation files
            if f.endswith(".hdr") and "nav" in f and "qual" not in f:
                path = os.path.join(root, f)
                process_bil(path)

                file_counter += 1
                if not (file_counter % 20):
                    sys.stdout.write("%d files processed\n" % file_counter)

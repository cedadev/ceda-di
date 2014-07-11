#! /usr/bin/env python

import exifread
import json
import os
import sys

with open(sys.argv[1], 'rb') as f:
    tags = exifread.process_file(f)

fname = "%s.exif" % os.path.splitext(
                         os.path.basename(
                              sys.argv[1]))[0]
with open(fname, 'w') as f:
    f.write(json.dumps(tags, indent=4, sort_keys=True, default=repr))

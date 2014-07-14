#! /usr/bin/env python

import exifread
import json
import os
import sys
import xml.dom.minidom as md

with open(sys.argv[1], 'rb') as f:
    tags = exifread.process_file(f, details=False, strict=True)
    
x = md.parseString(tags["Image ImageDescription"].values)
print(x.toprettyxml())

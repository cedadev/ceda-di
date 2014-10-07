ceda-di
=======

Python backend for extracting geospatial and temporal extent information
from various scientific data formats, including:

* ENVI BIL
* ENVI BSQ
* NetCDF
* GeoTIFF (using EXIF metadata)
* and others

The Python backend extracts the required data and outputs it as JSON documents,
ready for ingest into CEDA's FatCat system and an ElasticSearch platform.

This data (once indexed), can then be used to draw bounding polygons of flight
campaigns or even individual flights.

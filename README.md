ceda-di
=======

The ceda-di project is a suite of Python scripts and tools to extract
JSON metadata from various scientific data formats, including:

* ENVI BIL/BSQ
* NetCDF
* GeoTIFF (EXIF metadata)
* HDF

The Python backend is designed to be run on a system with a large number of CPU
cores. It extracts metadata from scientific data files and outputs it as
platform-independent JSON documents.

This JSON metadata can then be stored in a NoSQL data store such as 
ElasticSearch. This repository contains some example applications of the
toolkit, including an Ansible playbook to set up and configure an ElasticSearch
cluster. This repo also contains a sample web interface that allows for 
real-time faceted search (including full-text, temporal, and geospatial facets)
and live display of data files on a map.


Guide to This Repository
========================

* "elasticsearch"
    * Ansible playbook for setting up an ES cluster
    * Schema for JSON metadata
    * ElasticSearch mapping for JSON metadata
    * Sample ElasticSearch queries
* "examples"
    * Simple Python script to plot the output of a request to ElasticSearch
    * A Google Maps demonstration interface
* "lotus"
    * Helper scripts for running the Python suite on a cluster
* "python"
    * The main Python backend for metadata extraction

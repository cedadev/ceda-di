Welcome to ceda_di's documentation!
========================================

Introduction
------------

The ceda_di module is a Python backend to interface with a wide range of historical scientific data formats.

Within this project, you will find:

* Library interfaces to common scientific data formats (focusing mostly on data formats within the BADC archive), including:
    * NetCDF
    * HDF4
    * GeoTIFF
    * ENVI BIL/BSQ
* Interfaces to the file format modules, to enable extraction of domain-specific metadata (including geospatial/temporal metadata)
* A command-line interface to a suite of tools designed to be run on a multi-core system with filesystem access to scientific data. This includes:
    * A tool to extract metadata from common scientific data formats
    * A tool to index metadata into an Elasticsearch installation
    * A suite of tools to query and visualise the data stored within Elasticsearch

Project Goals
-------------

The metadata extraction toolkit was developed with following goals:

* Extract geospatial, temporal and parameter metadata from a historical dataset with homogenous data stored in various file formats
* Generate JSON documents from the readable files containing geospatial and temporal metadata
* Ingest the created JSON documents into an enterprise full-text search system (ElasticSearch)
* Build a query system around the ElasticSearch module

Module Contents:
================

.. toctree::
    modules

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

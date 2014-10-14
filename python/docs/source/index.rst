Welcome to ceda_di's documentation!
========================================

Introduction
------------

The ceda_di module is a Python backend to interface with a wide range of historical scientific data formats.

Within this module, you will find:

* Library interfaces to common scientific data file formats (focusing mostly on data formats within the ceda_di archive), including:
    * NetCDF
    * HDF4
    * GeoTIFF
    * ENVI BIL/BSQ
* Interfaces to the file format modules, to enable extraction of domain-specific metadata (including geospatial/temporal metadata)
* A main file discovery/parsing script - designed to be run in parallel on a multi-core processor with access to the CEDA archive

Project Goals
-------------

This module set was developed with focus on a particular project - this project included the following goals:

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

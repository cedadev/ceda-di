ceda-di (CEDA Data Index)
=========================

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


Command-line Usage
==================

Usage string
------------

The usage string for the command-line application is as follows:

.. literalinclude:: ../../src/di.py
    :language: python
    :lines: 2-21
    :linenos:


Sample usage
------------

**Note:** This is not a comprehensive guide! Please refer to the :doc:`commandline`
documentation for a more thorough explanation.

.. code-block:: bash

    # Extracts metadata from files in /path/to/input
    # Outputs data to Elasticsearch (--send-to-index)
    # Outputs JSON files to /path/to/output
    di.py extract --send-to-index /path/to/input /path/to/output

    # Extracts metadata from files in /path/to/input
    # Outputs data to Elasticsearch (--send-to-index)
    # Does not create JSON documents (--no-create-files)
    di.py extract --no-create-files --send-to-index /path/to/input

    # Finds all JSON documents in /path/to/json and sends to Elasticsearch
    di.py index /path/to/json

    # Run unit tests
    di.py test


More information
----------------

For more information, see the section on the :doc:`commandline`.


Configuration File
==================

Format
------

The configuration for the command-line interface for ``di.py`` is written in a JSON file with various nested elements for various options.

More information
----------------

For a full summary of all configuration options, read the section on the :doc:`configuration`.


Module Contents
================

.. toctree::
    commandline
    configuration

Indices and Tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

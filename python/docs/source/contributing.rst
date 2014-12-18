Contributing or Extending ``ceda-di``
=====================================

Introduction
------------

This section should provide a brief guide to extending the functionality of
``ceda-di`` - with particular regard to developing custom metadata handler
classes. In this way, you will be able to write a simple Python interface to
a particular filetype or dataset that is capable of extracting the type of
metadata that you require.


Handler Design Choices
======================

Per-filetype
------------

This is how ``ceda-di`` is structured by default. This assumes a fully
machine-readable dataset, structured in such a way that (if they exist), any
sidecar files or extraneous metadata files are  parsed by Python easily.

For example, the standard metadata extraction classes provided with ``ceda-di``
are:

* exif-geo
* hdf4-geo
* netcdf4-geo
* etc

Each of these metadata extraction classes (also referred to as ``handlers`` or
``handler classes``) will interpret data from a specific filetype.

The design choice you will need to make for your *handlers* vastly depends
on the structure of your dataset or archive.


Per-dataset
-----------

This design choice is probably more appropriate for more heterogeneous datasets
in that the directory structure (and layout of metadata files) may make it
a little more difficult to extract metadata.

For an example, there is a particular type of scientific hyperspectral data
in a format known as ENVI BIL (which stands for "band interleaved by line").
These data are *not* stored in single files!
They comprise of a header file which contains some metadata and parameter
information, and they also have an accompanying binary file which contains the
imaging information and any other navigational information.
If these two files (for each BIL header file must have an accompanying binary
file - and vice versa) are stored in separate directories or in non-standard
ways, it can pose a problem for the per-filetype scripts tring to interpret
the data.

In this way, it can be more useful to write metadata collection scripts on a
per-dataset basis.

For example, imagine the following directory tree:

.. code-block:: bash

    tree -d ../
        ├── data
        │   ├── binary
        │   └── doc
        │       ├── flightpath
        │       ├── some-photographs
        │       └── other-important-metadata
        └── headers

It's quite difficult to ensure that all of the files
in the ``binary`` directory are correctly matched with the headers in the
``headers`` directory if you use the generic scripts included with ``ceda-di``
- you will probably need to roll your own.


Metadata Handler API
====================

Geospatial
----------

.. function:: get_geospatial()

    Returns a dictionary of geospatial information, including a 30-coordinate
    flight summary and a bounding box.

    The dictionary should be formatted like so (as an example):

    .. code-block:: python

        "spatial": {
            "lat": [
                1.0293,
                8.4756
            ],
            "lon": [
                1.2345,
                9.8765
            ]
        }


Temporal
--------

.. function:: get_temporal()

    Returns a dictionary of temporal information, including start and end times
    for time-series data.

    The dictionary should be formatted like so (as an example):

    .. code-block:: python

        "temporal": {
            # MUST use ISO8601 datetimestamps
            "start_time": "2014-11-28T16:14:05+00:00",
            "end_time": "2014-11-28T16:42:40+00:00"
        }


Parameters
----------

.. function:: get_parameters()

    Returns a multi-level nested dictionary describing various elements of the
    parameters.

    The dictionary should be formatted like so (as an example):

    .. code-block:: python

        "parameters": [
            [
                {
                    "name": "long_name",
                    "value": "time of measurement"
                },
                {
                    "name": "standard_name",
                    "value": "time"
                },
            ],
            [
                {
                    "name": "long_name",
                    "value": "Air speed"
                },
                {
                    "name": "standard_name",
                    "value": "platform_speed_wrt_air"
                }
            ]
        ]

    Please note that for this dictionary type, "name" refers to the name of the
    parameter property - for example, "long_name" or "standard_name". "value"
    refers to the value extracted from the file (e.g. "time").
    

Properties
----------

.. function:: get_properties()

    Returns a dictionary containing metadata from all of the above functions.

File Format Check
-----------------

.. function:: get_file_format(filename):

   When choosing the correct handler this static function will be called if it exists. If it raises a FileFormatError
   then the handler will be ignore; just as if it did not match the regular expression for the file type

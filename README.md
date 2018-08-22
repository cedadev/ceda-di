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


Documentation Status
====================

[![Documentation Status](https://readthedocs.org/projects/ceda-di/badge/?version=latest)](https://readthedocs.org/projects/ceda-di/?badge=latest)


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
    
Setting up the environment
==========================

Get and install ceda-fbs code from Git (with install script)

```
$ wget https://raw.githubusercontent.com/cedadev/ceda-di/master/python/src/scripts/install-ceda-di.sh
$ .  ./install-ceda-di.sh
```

This will build you a `virtualenv` locally so your environment should look like:

```
$ ls
ceda-di  install-ceda-fbs.sh  venv-ceda-fbs
```

## Create a little setup script

```
$ cat setup_env.sh
export BASEDIR=/group_workspaces/jasmin/cedaproc/$USER/ceda-di
export PYTHONPATH=$BASEDIR/ceda-di/python:$BASEDIR/ceda-di/python/src/ceda-di:$PYTHONPATH
export PATH=$PATH:$BASEDIR/ceda-di/python/src/scripts
. venv-ceda-di/bin/activate
```

Example usage
=============

Set up environment first (not covered here).

Add a directory of files to an index:

```
$ cd ceda-di/python/src/
$ python di.py extract --no-create-files --config /home/badc/software/datasets/ceda-eo-prod/ceda-di/python/config/ceda-di-ceda-eo.json --send-to-index /neodc/sentinel2a/data/L1C_MSI/2017/01/14/
```

Add a single file to an index:

```
$ file_to_add=/neodc/sentinel2a/data/L1C_MSI/2017/01/14/S2A_MSIL1C_20170114T191501_N0204_R027_T01CDQ_20170114T191458.manifest
$ echo $file_to_add > to_index.txt
$ di.py extract --no-create-files --config /home/badc/software/datasets/ceda-eo-prod/ceda-di/python/config/ceda-di-ceda-eo.json --send-to-index --file-list-file to_index.txt
```

Check which `.manifest` files in the `ceda-eo` index have been indexed from directory `/neodc/sentinel2a/data/L1C_MSI/2017/01/14`:

```
$ ./scripts/find_indexed_files.py -i ceda-eo -e manifest -d /neodc/sentinel2a/data/L1C_MSI/2017/01/14
```

This writes an output file of all missing files, called: `files_not_found.txt`
```

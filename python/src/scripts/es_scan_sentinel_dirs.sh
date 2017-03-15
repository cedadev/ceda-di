#!/bin/bash

# Basic wrapper for Sentinel data
# All command-line args are directories to scan

DIRS=$@

export CEDA_DI_PROJECT=ceda-eo
cd /home/badc/software/datasets/ceda-eo/ceda-di/python/src
./scripts/wrap_es_index_files.sh $DIRS

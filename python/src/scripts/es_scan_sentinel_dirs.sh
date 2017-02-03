#!/bin/bash

# Basic wrapper for Sentinel data
# All command-line args are directories to scan

DIRS=$@

cd /home/badc/software/datasets/sentinel/ceda-di-sentinel/ceda-di/python/src
./scripts/wrap_es_index_files.sh $DIRS

#!/bin/bash

cd /home/badc/software/datasets/sentinel/ceda-di-sentinel
. setup_env.sh

DIRS=$@

for dr in $DIRS; do
    python scripts/es_index_files.py -i sentinel -d $dr
done

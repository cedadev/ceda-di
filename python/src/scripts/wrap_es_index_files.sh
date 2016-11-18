#!/bin/bash

cd /home/badc/software/datasets/faam/elasticsearch
. setup_env.sh

DIRS=$@

# Get project name from CEDA_DI_PROJECT environment variable
if [ ! $CEDA_DI_PROJECT ]; then
    echo "Please set CEDA_DI_PROJECT environment variable to use this script."
    echo "E.g.: $ export CEDA_DI_PROJECT=faam"
    exit
fi

proj=$CEDA_DI_PROJECT
echo "Working on project: $proj"

for dr in $DIRS; do
    python scripts/es_index_files.py -i $proj -d $dr
done

#!/bin/bash

if [ ! -f scripts/wrap_es_index_files.sh ]; then
    echo "You must run this script from the 'ceda-di/python/src/' directory for it to work."
    exit
fi

# Get project name from CEDA_DI_PROJECT environment variable
if [ ! $CEDA_DI_PROJECT ]; then
    echo "Please set CEDA_DI_PROJECT environment variable to use this script."
    echo "E.g.: $ export CEDA_DI_PROJECT=faam"
    exit
fi


BASEDIR=$PWD/../../..
. $BASEDIR/setup_env.sh $CEDA_DI_PROJECT

DIRS=$@

proj=$CEDA_DI_PROJECT
echo "Working on project: $proj"

for dr in $DIRS; do
    python scripts/es_index_files.py -i $proj -d $dr
done

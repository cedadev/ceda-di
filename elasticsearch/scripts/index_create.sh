#! /bin/bash

# Configure these to suit your ElasticSearch setup
MASTER_LOCATION="fatcat-test.jc.rl.ac.uk"
MASTER_PORT="9200"

# Begin script, check arguments
if [ "$#" -lt "3" ]
then
    echo "Usage:"
    echo "    ./es_create.sh <index_name> <mapping_name> <mapping path> <data path (optional)>"
    echo "        e.g.: ./es_create.sh badc ./custom_analyzers.json eufar ./mapping.json /path/to/data"
    exit
fi

# Set variables from parameters
INDEX_NAME="$1"
ANALYZER_NAME="$2"
MAPPING_NAME="$2"
MAPPING_PATH="$3"
DATA_PATH="$4"

# Construct the base URL for ES index
BASE_URL="http://$MASTER_LOCATION:$MASTER_PORT"

echo "=== Deleting existing index \"$INDEX_NAME\"..."
curl -XDELETE "$BASE_URL/$INDEX_NAME"

# Create main index and add the correct mapping
echo
echo "=== Creating index \"$INDEX_NAME\"..."
curl -XPUT "$BASE_URL/$INDEX_NAME" -d @$ANALYZER_NAME
echo
echo "=== Creating mapping \"$MAPPING_NAME\"..."
curl -XPUT "$BASE_URL/$INDEX_NAME/_mapping/$MAPPING_NAME" -d @$MAPPING_PATH

if [ "$#" -eq 5 ]
then
    # Index data from file path
    echo; echo;
    echo "=== Indexing data from \"$DATA_PATH\"..."
    for i in $DATA_PATH/*
    do
        echo
        echo "$i"
        curl -XPOST "$BASE_URL/$INDEX_NAME/$MAPPING_NAME/" -d @$i
    done
fi

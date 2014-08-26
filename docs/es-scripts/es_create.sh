#! /bin/bash

# Configure these to suit your ElasticSearch setup
MASTER_LOCATION="127.0.0.1"
MASTER_PORT="9200"

# Begin script, check arguments
if [ "$#" -ne "4" ]
then
    echo "Usage:"
    echo "    ./es_create.sh <index_name> <mapping_name> <mapping path> <data path>"
    echo "        e.g.: ./es_create.sh badc eufar ./mapping.txt ./data_folder/"
    exit
fi

# Set variables from parameters
INDEX_NAME="$1"
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
curl -XPUT "$BASE_URL/$INDEX_NAME"
echo
echo "=== Creating mapping \"$MAPPING_NAME\"..."
curl -XPUT "$BASE_URL/$INDEX_NAME/_mapping/$MAPPING_NAME" -d @$MAPPING_PATH

# Index data from file path
echo; echo;
echo "=== Indexing data from \"$DATA_PATH\"..."
for i in $DATA_PATH/*
do
    echo
    echo "$i"
    curl -XPOST "$BASE_URL/$INDEX_NAME/$MAPPING_NAME/" -d @$i
done

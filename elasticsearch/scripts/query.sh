#! /bin/bash

# Configure these to suit your ElasticSearch setup
MASTER_LOCATION="http://jasmin-es1.ceda.ac.uk"
MASTER_PORT="9200"
INDEX="eufar"
MAPPING="geospatial"
QUERY="$1"

# Begin script, check arguments
if [ "$#" -lt "1" ]
then
    echo "Usage:"
    echo "    ./es_create.sh <query json>"
    echo "        e.g.: ./es_create.sh ../query.json"
    exit
fi

BASE_URL="$MASTER_LOCATION:$MASTER_PORT"

if [ ! -z $INDEX ] && [ ! -z $MAPPING ]
then
    BASE_URL="$BASE_URL/$INDEX"
    BASE_URL="$BASE_URL/$MAPPING"
fi

BASE_URL="$BASE_URL/_search/?pretty=true"
echo $BASE_URL

# curl -XGET "$BASE_URL" -d @"$QUERY"

#! /bin/bash

# Configure these to suit your ElasticSearch setup
MASTER_LOCATION="http://fatcat-test.jc.rl.ac.uk"
MASTER_PORT="9200"
INDEX="badc"
MAPPING="eufar"
QUERY="$1"

# Begin script, check arguments
if [ "$#" -lt "1" ]
then
    echo "Usage:"
    echo "    ./es_create.sh <query json>"
    echo "        e.g.: ./es_create.sh ../query.json"
    exit
fi

BASE_URL="$MASTER_LOCATION:$MASTER_PORT/$INDEX/$MAPPING/_search/?pretty=true"
curl -XGET "$BASE_URL" -d @"$QUERY"

#!/bin/bash

if [ ! -f scripts/wrap_es_index_files.sh ]; then
    echo "You must run this script from the 'ceda-di/python/src/' directory for it to work."
    exit
fi

# Set project
export CEDA_DI_PROJECT=eufar

wd=$PWD
cd $wd

today=$(date +%Y-%m-%d)
outdir=$wd/outputs/$today
mkdir -p $outdir

dirs=/neodc/eufar

for dr in $dirs; do

    # Get years and do most recent first
    yrs=$(ls $dr | grep -v READ | grep -v raw | grep -v docs | sort -r)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        path=$dr/$yr
        job=${ds}-${yr}

        cmd="./scripts/wrap_es_index_files.sh $path"
#        cmd="bsub -q ingest -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
        echo "Running: $cmd"
        $cmd

    done
done

echo
echo "You can count the number of records with this line:"
echo "curl jasmin-es1.ceda.ac.uk:9200/${CEDA_DI_PROJECT}/_count ; echo"

echo 
echo "...and check the number of actual 'manifest' files with:"
echo "find $dirs -follow -type f -name "*.manifest" | wc -l"

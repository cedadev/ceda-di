#!/bin/bash

if [ ! -f scripts/wrap_es_index_files.sh ]; then
    echo "You must run this script from the 'ceda-di/python/src/' directory for it to work."
    exit
fi

wd=$PWD
cd $wd

today=$(date +%Y-%m-%d)
outdir=$wd/outputs/$today
mkdir -p $outdir

dirs="/neodc/landsat8/data/OLI_TIRS"

for dr in $dirs; do

    yrs=$(ls $dr | grep 20)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        ydr=$dr/$yr

        mdirs=$(ls $ydr/)
    
        for mon in $mdirs; do
            path=$ydr/$mon
            job=${ds}-${yr}-${mon}

            cmd="bsub -q ingest -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
            echo "Running: $cmd"
            $cmd

        done
    done
done

echo
echo "You can count the number of records with this line:"
echo "curl jasmin-es1.ceda.ac.uk:9200/${CEDA_DI_PROJECT}/_count ; echo"

echo
echo "...and check the number of actual 'MTL' files with:"
echo "find $dirs -follow -type f -name "*_MTL.txt" | wc -l"

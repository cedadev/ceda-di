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

dirs="/neodc/sentinel3a/data/SLSTR/L1_RBT"


for dr in $dirs; do

    yrs=$(ls $dr | grep 20)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        if [ $yr -ne 2017 ] ; then
           continue
        fi

        ydr=$dr/$yr

        mdirs=$(ls $ydr/)
    
        for mon in $mdirs; do
            if [ $mon != "06" ] ; then
               continue
            fi

            path=$ydr/$mon
            job=${ds}-${yr}-${mon}

            cmd="bsub -q ingest -W 72:00 -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
            echo "Running: $cmd"
            $cmd

        done
    done
done

echo
echo "You can count the number of records with this line:"
echo "curl jasmin-es1.ceda.ac.uk:9200/${CEDA_DI_PROJECT}/_count ; echo"

echo
echo "...and check the number of actual 'manifest' files with:"
echo "find $dirs -follow -type f -name "*.manifest" | wc -l"

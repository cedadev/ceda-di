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

dirs="/neodc/sentinel_ard/data/sentinel_1 /neodc/sentinel_ard/data/sentinel_2"


for dr in $dirs; do

    yrs=$(ls $dr | grep 20)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        ydr=$dr/$yr

        mdirs=$(ls $ydr/)
    
        for mon in $mdirs; do
            path=$ydr/$mon
            job=${ds}-${yr}-${mon}

            cmd="sbatch -p long-serial -t 72:00:00 -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
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

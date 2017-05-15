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

dirs="/neodc/landsat7etm/p020 /neodc/landsat7etm/p021 /neodc/landsat7etm/p022 /neodc/landsat7etm/p030 /neodc/landsat7etm/p031 /neodc/landsat7etm/p032 /neodc/landsat7etm/p041 /neodc/landsat7etm/p042"

for dr in $dirs; do

    yrs=$(ls $dr)
    ds=$(echo $dr | cut -d/ -f3)

    for yr in $yrs; do
        path=$dr/$yr

        job=${ds}-${yr}

        cmd="bsub -q ingest -o $outdir/${job}.out -e $outdir/${job}.err ./scripts/wrap_es_index_files.sh $path"
        echo "Running: $cmd"
        $cmd

    done
done

echo
echo "You can count the number of records with this line:"
echo "curl jasmin-es1.ceda.ac.uk:9200/${CEDA_DI_PROJECT}/_count ; echo"

echo
echo "...and check the number of actual 'MTL' files with:"
echo "find $dirs -follow -type f -name "*_MTL.txt" | wc -l"

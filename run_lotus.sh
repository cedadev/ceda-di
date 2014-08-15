#!/bin/bash
#BSUB -x
#BSUB -n 8
#BSUB -W 1:30
#BSUB -o /work/scratch/ccnewey/arsf-geo-map/%J.out
#BSUB -e /work/scratch/ccnewey/arsf-geo-map/%J.err
#BSUB -q lotus

cd ~ccnewey/arsf-geo-map
source bin/activate
cd ~ccnewey/arsf-geo-map/src
python main.py 8

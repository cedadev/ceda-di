#!/bin/bash
#BSUB -n 45
#BSUB -W 1:15
#BSUB -M 1048576
#BSUB -q lotus-smp
#BSUB -N charles.newey@stfc.ac.uk
#BSUB -o %J.out

cd ~ccnewey/arsf-geo-map
source bin/activate
cd ~ccnewey/arsf-geo-map/src
python main.py

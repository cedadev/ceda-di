#!/bin/bash
#BSUB -n 48
#BSUB -W 1:00
#BSUB -M 1048576
#BSUB -N charles.newey@stfc.ac.uk
#BSUB -o arsf-geo-map-%J.out

cd ~ccnewey/arsf-geo-map
source bin/activate
python main.py

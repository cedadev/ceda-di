#!/bin/bash
#BSUB -n 10
#BSUB -W 2:45
#BSUB -q lotus

cd ~ccnewey/arsf-geo-map
source bin/activate
cd ~ccnewey/arsf-geo-map/src
python main.py

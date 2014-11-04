#!/bin/bash
#BSUB -n 24
#BSUB -W 1:30
#BSUB -o /work/scratch/ccnewey/ceda-di/%J.smp.out
#BSUB -e /work/scratch/ccnewey/ceda-di/%J.smp.err
#BSUB -q lotus-smp

cd ~ccnewey/ceda-di
source bin/activate
cd ~ccnewey/ceda-di/src
python -m ceda_di.main

#!/bin/bash

rm /work/scratch/ccnewey/ceda_di/log/*
rm /work/scratch/ccnewey/ceda_di/out/*
find src/ceda_di/ -name "*.pyc" -exec rm {} \;

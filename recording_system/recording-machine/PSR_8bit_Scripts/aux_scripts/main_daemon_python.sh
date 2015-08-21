#!/bin/bash

cd ~/PSR_8bit_Scripts/

python processPulsars.py -s -t 8 -res -L 0 -U 55 /media/scratch/observer/LuMP &
python processPulsars.py -s -t 3 -pres -L 56 /media/scratch/observer/LuMP

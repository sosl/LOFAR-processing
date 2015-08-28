#!/bin/bash

for generation in b c d
do
  for node in $(seq 1 4)
  do
    echo running on lofar${generation}${node}
    ssh lofar${generation}${node} bash -c "'
    . ~/PSR_8bit_Scripts/setup.sh
    cd /media/scratch/observer/LuMP_DE60?_reduced/B*/2*/
    . ~/PSR_8bit_Scripts/setup.sh
    ~/PSR_8bit_Scripts/zap.psh -ez B*ar
    ls B*z | xargs -L 1 pazi 
    rm B*z
    '"
  done
done

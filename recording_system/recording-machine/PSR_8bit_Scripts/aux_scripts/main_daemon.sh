#!/bin/bash

if [ $# -ne 1 ]
then
   echo usage: $0 station
   echo e.g.: $0 DE603
   exit
fi

trap "killall run_process_highdm_pulsars.sh" SIGINT SIGTERM

station=$1

~/PSR_8bit_Scripts/aux_scripts/run_process_highdm_pulsars.sh $station &
~/PSR_8bit_Scripts/aux_scripts/run_process_normal_pulsars.sh $station  

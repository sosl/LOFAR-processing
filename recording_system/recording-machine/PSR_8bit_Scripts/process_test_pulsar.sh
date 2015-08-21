#!/bin/bash

. ~/PSR_8bit_Scripts/setup.sh

if [ $# -ne 3 ]
then
	echo usage: $0 PSR STATION THREADS
	exit
fi

PSR=$1
STATION=$2
THREADS=$3

DATE="$(date +%Y-%m-%d)*"

cd /media/scratch/observer/LuMP_${STATION}_reduced/${PSR}/${DATE}
pwd
#touch process_test_pulsar_was.HERE
#~/PSR_8bit_Scripts/AnalyseLuMP_${NODE_DUALITY}.sh ${STATION} ${PSR} ${THREADS}
~/PSR_8bit_Scripts/zap.psh -ez ${PSR:0:1}*ar

for zapped in $(ls ${PSR:0:1}*z)
do
	psrplot -c flux:below:r='$snr' -pF ${zapped} -j DTp -D ${zapped}.png/PNG
done

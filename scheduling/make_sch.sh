#!/bin/bash

if [ $# -ne 4 ]
then
  echo usage: $0 BEGIN_DAY BEGIN_TIME END_DAY END_TIME
  echo format: '{BEGIN,END}_DAY' mm.dd.yy
  echo         '{BEGIN,END}_TIME' hh:mm
  exit
fi

set -o nounset

for station in DE601 DE602 DE603 DE605
do
	python observePulsars.py -v 0 -b $1 $2 -d $3 $4 -s ${station} -o ${station}.sch -D 5000 -I 200 pulsars_${station}.dat
	mv gantt.svg ${station}.svg
done

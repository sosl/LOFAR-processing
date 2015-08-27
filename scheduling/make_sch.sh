#!/bin/bash

echo 'did you remember to set the dates (UTC!!)?'
#format: MM.DD.YY HH:MM

#for station in DE601 DE603 DE605
#for station in DE601 DE602 DE603 DE605 DE609
for station in DE601 
do
	python observePulsars.py -v 0 -b '08.14.15 09:45' -d '08.17.15 08:45' -s ${station} -o ${station}.sch -D 5000 -I 200 pulsars_${station}.dat
	mv gantt.svg ${station}.svg
done

echo now run convert.sh to create .list files

#!/bin/bash

overlap() {
	station_A=$1
	station_B=$2

	TMP1=`mktemp`
	TMP2=`mktemp`

	join -j 1 pulsars_${station_A}.dat pulsars_${station_B}.dat | awk '{print $1,$2,$4}' > overlap_${station_A}_${station_B}.dat
	echo for ${station_A} and ${station_B} found:
	echo OVERLAP_COUNT DURATION_A DURATION_B
	awk '{SUM_A+=$2;SUM_B+=$3}END{print NR,int((SUM_A+0.5)/60),int((SUM_B+0.5)/60)}' overlap_${station_A}_${station_B}.dat

	# clean-up:
	rm $TMP1 $TMP2

	if [ $? -ne 0 ]
	then
		echo failed '(exist status' $?')' to remove files $TMP1 and $TMP2
	fi
}

overlap DE601 DE602 
echo
overlap DE601 DE603 
echo
overlap DE601 DE605 
echo
overlap DE602 DE603 
echo
overlap DE602 DE605 
echo
overlap DE603 DE605 
echo

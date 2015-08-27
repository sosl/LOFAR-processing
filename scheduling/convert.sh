#!/bin/bash

if [ "$1" = "-h" ]
then
	echo usage: $0 [date]
	echo format: YYYY-MM-DD
	exit
fi

if [ $# -eq 1 ]
then
	date_str=$1
else
	date_str=`date +%Y-%m-%d`
fi

#for station in DE601 DE603 DE605 DE609
for station in DE601 DE602 DE603 DE605 
do
	awk '{if (NR>2) {print "#", $1,"LST: ",substr($10,0,5), "UTC: ", $3,substr($4,0,5); print $1,int($2*24*60+0.5)-2,$3,substr($4,0,5)}}' ${station}.sch > ${date_str}_${station}.list
done

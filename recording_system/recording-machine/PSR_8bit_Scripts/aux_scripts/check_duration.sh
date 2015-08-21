#!/bin/bash

if [ $# -ne 1 ]
then
	echo usage: $0 list_file
	echo ; echo this script will compare the desired and actual observing times
	exit
fi
list_file=$1
topdir="/media/scratch/observer/LuMP_reduced"

# Determine the host and thus lanes
Node=`hostname | awk '{print substr($1,length($1))}'`

if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
then 
	lanes="[3,4]"
else
	lanes="[1,2]"
fi

cd $topdir

for psr in `find . -mindepth 1 -maxdepth 1 -type d -name '[B,J]*' | awk -F/ '{print $2}' | sort`
do
	expected_length=`grep $psr $list_file | awk '{print $2}'`
	echo -n $psr ${expected_length}" "
	for archive in `find $psr -name $psr'*lofar?.ar'`
	do
		length=`psredit -qQ -c length $archive | awk '{print int($1/60+0.5)}'`
		echo -n ${length}" "
	done
	echo
done

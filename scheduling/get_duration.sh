#!/bin/bash

sufix=$1

for x in 1 2 3 5 9
do
	echo -n "DE60${x} "
        awk '{if (substr($1,1,1)!="#") SUM+=$2}END{print SUM/60}' pulsars_DE60${x}.dat${sufix}
done

#!/bin/bash

# Copyright (C) 2015 by Stefan Oslowski
# Licensed under the Academic Free License version 3.0
# This script is a heavily modified version of a previous script
# Based on a script by Aris Noutsos
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work

# Note that since the script uses GNU parallel you must either
# cite the relevant reference or pay 10000 EUR to O. Tange

if [[ $# -lt 6 ]] || [[ "$1" = "-h" ]] || [[ $# -gt 7 ]]
then
        echo
        echo "  Usage:  $0 <MODEL> <ARCHIVE> <PREFIX> <THREADS> <SUBBANDWIDTH> <BANDFILTER> [--inv]"
        echo
        echo "  Example:$0 Hamaker test.ar test.ar 4 195.3125 HBA_110_190 [--inv]"
        echo " the SUBBANDWIDTH and BANDFILTER above are for HBA observations"
        echo
        echo You need to point to mscorpol with the MSCORPOL_PYPATH variable
        echo
        echo This script comes with ABSOLUTELY NO WARRANTY.
        echo
        exit
fi

if [ -z ${MSCORPOL_PYPATH+x} ]
then
  echo "MSCORPOL_PYPATH is not set. Aborting"
  exit
fi

which psrcat >&/dev/null
if [ $? -eq 1 ]
then
  echo "psrcat not found. Aborting"
  exit
fi

which psredit >&/dev/null
if [ $? -eq 1 ]
then
  echo "psredit not found. Aborting"
  exit
fi

which parallel >&/dev/null
if [ $? -eq 1 ]
then
  echo "GNU parallel not found. Aborting"
  exit
fi

if [[ ! -s ${MSCORPOL_PYPATH}/add_freq.awk ]]
then
  echo "add_freq.awk not present in ${MSCORPOL_PYPATH}. Aborting"
  exit
fi

if [[ ! -s "$2" ]]
then
  echo Input archive "$2" not found. Aborting
  exit
fi

mypath=`pwd`
pypath=${MSCORPOL_PYPATH}
tmpfile=$(mktemp)
tmpfile2=$(mktemp)
tmpfile3=$(mktemp)
tmpfile4=$(mktemp)
TMPFREQS=$(mktemp)

trap "rm -f ${tmpfile}* ${tmpfile2}* ${tmpfile3}* ${tmpfile4}* ${TMPFREQS}" SIGINT SIGTERM EXIT

model=$1
archive=$2
out_prefix=$3
threads=$4
clock=$(echo $5 | awk '{print $1/1000.0}')
bandf=$(echo $6 | awk -F _ '{print $2}')

#get some meta data about the archive

tmp=( $(psredit -Qq -c name,nsubint $archive) )
psr=${tmp[0]}
last_subint=$((${tmp[1]}-1))

tmp=( $(psredit -Qq -c 'int[0]:mjd,int['$last_subint']:mjd,int[1]:duration,site' $archive) ) #better to use int[1] as sometimes the first subint can be shorter
# this is an approximation, will be bad for tscrunched data
UTC_START=$( getMJD -m ${tmp[0]} 2>&1 | tail -n1 | awk -F- '{OFS="-"; print $1,$2,$3" "$4}')
UTC_END=$(   getMJD -m ${tmp[1]} 2>&1 | tail -n1 | awk -F- '{OFS="-"; print $1,$2,$3" "$4}')
tstep=${tmp[2]}
station=${tmp[3]:0:5}

source_info=( $(psrcat -all -o short -nohead -nonumber -c "raj decj" $psr ) )
pos_rad=( $(echo ${source_info[0]} ${source_info[1]} | sed s/\\:/" "/g | awk -v pi=3.1415926535 '{printf "%.6f %.6f\n",(($1+(($2+($3/60.0))/60.0))/24.0)*2*pi,(($4+(($5+($6/60.0))/60.0))/360.0)*2*pi}') )
RA_RAD=${pos_rad[0]}
DEC_RAD=${pos_rad[1]}
if [ "${DEC_RAD:0:1}" = "-" ]
then
  DEC_RAD="-n ${DEC_RAD:1}"
fi

#create a list of frequencies
for x in $(psredit -c 'int[0]:freq' -Qq -d '\n' $archive)
do
  echo $(echo $x'*1000000' | bc| awk -F. '{print $1}') >> ${TMPFREQS}
done

nfreqs=$(wc -l ${TMPFREQS})

startt_label=$UTC_START
stopt_label=$UTC_END

durs="$(echo $(date --date="$stopt_label" +%s)'-'$(date --date="$startt_label" +%s)'+('$tstep'/2.)' | bc )"

echo "MODEL=$model STATION=$station  SUBBANDS=$nfreqs DURATION=$durs RA=$RA_RAD DEC=$DEC_RAD tstep=$tstep"

mode=`echo | awk '{if('$clock'==0.195312)print "200MHz"; else print "160MHz"}'`

if [ "$mode" = "200MHz" ]
then
 low_edge=`echo | 
 awk '{if('$bandf'>=200)print "200"; else if('$bandf'<200 && '$bandf'>=100)print "100"; else print "0.0"}'` 
elif [ "$mode" = "160MHz" ]
then
 low_edge=`echo | 
 awk '{if('$bandf'>=160)print "160"; else if('$bandf'<160 && '$bandf'>=80)print "80"; else print "0.0"}'` 
else
 low_edge=0
fi

echo "CLOCK = $clock MHz   |   ZONE=$mode   |   FILTER = $bandf MHz  |   LOW_EDGE = $low_edge MHz "

rm -f ${tmpfile}* ${tmpfile3}*

# It is remarkably difficult to add awk to a parallel command chain. Thus, I decided to use an external awk script which works well but has the increased cost of having more files
 parallel -j ${threads} ${pypath}/antennaJones.py $model $station '"'$startt_label'"' $durs $tstep $RA_RAD $DEC_RAD {} '| awk -v freq='{}' -f '${pypath}'/add_freq.awk > ' ${tmpfile3}_{} :::: ${TMPFREQS}

for file in $(ls -1 ${tmpfile3}_* | sort -gt_ -k2,2)
do
  cat $file >> ${tmpfile}
done

sort -g -k1,1 ${tmpfile} > ${tmpfile2}

if [ "$7" = "--inv" ]
then
  python $pypath/invertJones.py $tmpfile2 > ${out_prefix}_bbs.jones
else
  mv $tmpfile2 ${out_prefix}_bbs.jones
fi

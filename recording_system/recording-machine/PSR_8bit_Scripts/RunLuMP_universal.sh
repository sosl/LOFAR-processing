#!/bin/bash

#
# Written by Stefan Oslowski, November 2014
# Original script by Joris P.W. Verbiest, December 2012.
# Based on guidelines by James Anderson from MPIFR's LOFAR deki.
#

if [[ $# -ne 7 ]]
then
    echo usage: $0 PSR Tint datadir starttime station lane verbosity_level
    echo Tint is in minutes
    exit
fi

verbose=$7

PSR=$1

[[ $verbose -gt 0 ]] && echo "Will observe Pulsar " $PSR

TINT=$(echo $2 | awk '{print $1*60}')
[[ $verbose -gt 0 ]] && echo "... for " $TINT " seconds."

export PYTHONPATH
export USE_LUMP_PULSAR_STUFF=1
. /opt/lump/lump_2.0/SETUP.sh
. /opt/pulsar-stuff/pulsar-init.sh

datadir="./"$3
starttime=$4

station=$5
if [[ ${#station} -ne 5 ]]
then
	echo station must be a 5 character string
	echo e.g.: DE601
	exit 16
fi

station_no=${station:(-3)}

lane=$6
if [[ $lane -gt 4 || $lane -lt 1 ]]
then
	echo lane needs to be between 1 and 4
	exit 16
fi
# set up auxiliary per-lane information
beamlet_start=$(( ($lane-1)*122 ))
beamlet_end=$(( ($lane)*122 ))
subband_start=$(( ($lane-1)*122 + 12 ))
subband_end=$(( ($lane)*122 + 12 ))
[[ $verbose -gt 0 ]] && echo determined beamlet_start _end and subband_start _end: $beamlet_start $beamlet_end $subband_start $subband_end

port=$(( 10000 + ${station_no}*10 + $lane ))
[[ $verbose -gt 0 ]] && echo station: $station with number $station_no and lane $lane thus port $port

RAJR=$(psrcat -all -x -c RAJD $PSR | awk '{print $1/180*3.141592654}')
if [[ $RAJR -eq 0 ]]
then 
    echo "PROBLEM: Source not in catalogue!!"
    exit 16
fi
DECJR=$(psrcat -all -x -c DECJD $PSR | awk '{print $1/180*3.141592654}')


mkdir -p /media/scratch/observer/LuMP_${station}/
cd /media/scratch/observer/LuMP_${station}/
mkdir -p $PSR
cd $PSR
  
    Basic_LuMP_Recorder.py --port=${port} --clock_speed=200 --beamlets_per_lane=122 --datadir=${datadir} --data_type_in=L_intComplex16_t --station_name=${station} --writer_type=LuMP1 --physical_beamlet_array='['${beamlet_start}':'${beamlet_end}']' --rcumode_array='[5]*122' --epoch_array='[J2000]*122' --verbose --duration=${TINT} --subband_array='['${subband_start}':'${subband_end}']' --filename_base=${PSR}_${lane} --sourcename_array="[$PSR]*122" --rightascension_array="[$RAJR]*122" --declination_array="[$DECJR]*122" --start_date=${starttime} --recorder_num_cores=2

[[ $verbose -gt 0 ]] && echo "Finished observation."

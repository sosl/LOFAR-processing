#!/bin/bash

#
# Simple script to record data with LuMP, based on the user guidelines
# provided on the MPIfR deki by James Anderson.
#
# This script by Joris P.W. Verbiest, December 2012.
# Modified by Stefan Oslowski, September 2014
#

if [[ $# != 6 ]]
then
    echo usage: $0 PSR TINT OBSEPOCH STARTTIME STATION LANE
    #echo e.g.: $0 B0329+54
    exit
endif

PSR=$1
TINT=`echo $2 | awk '{print $1*60}'`
date=$3
starttime=$4
station=$5
lane=$6

datadir="./"${date}
station_number=$( echo $station | tr -d '[:alpha:]')
port=1${station_number}${lane}

echo script not finished exiting
exit

export PYTHONPATH
export USE_LUMP_PULSAR_STUFF 1
. /opt/lump/lump_2.0/SETUP.sh

cd /media/scratch/observer/LuMP_reduced/
mkdir -p $PSR
cd $PSR

RAJR=`psrcat -x -c RAJD $PSR | awk '{print $1/180*3.141592654}'`
if [ $RAJR == 0 ]
then 
    echo "PROBLEM: Source not in catalogue!!"
fi
DECJR=`psrcat -x -c DECJD $PSR | awk '{print $1/180*3.141592654}'`

## NOTE: The following line is node-specific!!
set port = 4346
  
    Basic_LuMP_Recorder.py --port=${port} --clock_speed=200 --beamlets_per_lane=122 --datadir=${datadir} --data_type_in=L_intComplex16_t --data_type_process=L_intComplex16_t --data_type_out=L_intComplex16_t --station_name=DE602 --writer_type=LuMP2 --physical_beamlet_array='[0:122]' --rcumode_array='[5]*122' --epoch_array='[J2000]*122' --verbose --duration=${TINT} --subband_array='[12:134]' --filename_base=${PSR}_1 --sourcename_array="[$PSR]*122" --rightascension_array="[$RAJR]*122" --declination_array="[$DECJR]*122" --start_date=${starttime} --extra_string_option_0='dspsr -A -D 26.833 -c 0.714519699726 -L 10 -F %d:D -U minX1 -O '${PSR}'.'${date}'lofar1 %s' --extra_string_option_1=1 --extra_string_option_3='test_dog.log'
                                                                 

echo "Finished observation."

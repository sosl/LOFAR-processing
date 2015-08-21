#!/bin/bash

#
# Simple script to process LuMP single-station pulsar data. 
#
# Joris P.W. Verbiest, MPIfR, December 2012.
#

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ $# -gt 4 ]
then
    echo "Need station id and pulsar name. Optionally number of threads as an argument:"
    echo "e.g.: RunLuMP.csh B0329+54 [threads]"
    exit
elif [ $# -eq 2 ]
then
    station=$1
    PSR=$2
    threads=20
    channels=122
elif [ $# -eq 3 ]
then
    station=$1
    PSR=$2
    threads=$3
    channels=122
elif [ $# -eq 4 ]
then
    station=$1
    PSR=$2
    threads=$3
    channels=$4
fi

high_dm_threads=`echo $threads | awk '{print int('$threads'*0.4)}'`
if [ "$high_dm_threads" == "0" ]
then
    high_dm_threads=1
fi

echo "Will analyse Pulsar " $PSR

export PYTHONPATH
#export USE_LUMP_PULSAR_STUFF=1
. /opt/lump/lump_2.0/SETUP.sh
. /opt/pulsar-stuff/pulsar-init.sh 

# Get the par file
if [ -e ~/PSR_parfiles/${PSR}.par ]
then
  cp ~/PSR_parfiles/${PSR}.par ./eph.par
  chmod -w eph.par
else
  psrcat -e $PSR > eph.par
fi

# Obtain the vital information from the par file
datum=`date +%Y-%m-%d-%H:%M`
#set RA = `psrcat -c RAJ -x $PSR | awk '{print $1}'`
RA=`grep RAJ eph.par | awk '{print $2}'`
#set DEC = `psrcat -c DECJ -x $PSR | awk '{print $1}'`
DEC=`grep DECJ eph.par | awk '{print $2}'`

# Catch for ecliptic coordinates
if [[ $RA == "" ]] || [[ $DEC == "" ]]
then
    RA=`psrcat -c RAJ -x $PSR | awk '{print $1}'`
    DEC=`psrcat -c DECJ -x $PSR | awk '{print $1}'`
fi

#set P0 = `psrcat -c P0 -x $PSR | awk '{print $1}'`
P0=`grep F0 eph.par | awk '{print 1/$2}'`
#set DM = `psrcat -c DM -x $PSR | awk '{print $1}'`
DM=`grep DM eph.par | grep -v DMEPOCH | grep -v DM1 | grep -v DM2 | grep -v DM3 |  awk '{print $2}'`

if [[ $RA == "" ]] || [[ $DEC == "" ]] || [[ $P0 == "" ]] || [[ $DM == "" ]]
then
    echo "================================================================"
    echo "ERROR! -- couldn't find all necessary parameters in par file."
    echo $PSR
    echo "Have:" 
    cat eph.par
    echo "================================================================"
    exit
fi

# Determine the host 
Node=`hostname | awk '{print substr($1,length($1))}'`

lanes="1 2 3 4"

for lane in $lanes
do
  LuMP_Pulsar_Cleanup.py --source_name=${PSR} --source_RA=${RA} --source_Dec=${DEC} --telescope=${station} --filename_base=${PSR}_${lane}.00 

  mkdir -p SubBands_${lane}
  mkdir -p ToThrow_${lane}
  for file in ` ls -1 ${PSR}_${lane}*.0*raw`
  do
      small_DM=`echo $DM | awk '{if ($1 < 65 ) print "1"; else print "0"}'`
      if  [ $small_DM -eq 1 ]
      then
          dspsr -F ${channels}:D -A -E eph.par -L 10 -t $threads -minram 1 -O ${file}.ar $file -fft-bench
      else
          echo "High DM. Slowing down..."
          dspsr -F ${channels}:D -A -E eph.par -L 10 -U minX2 -t $high_dm_threads -minram 1 -O ${file}.ar $file #-fft-bench
      fi
      mv ${file}.ar.ar SubBands_${lane}/
      mv $file ToThrow_${lane}/
      prefix=`basename $file .raw`
      mv ${prefix}* ToThrow_${lane}/
      mkdir -p Logs_${lane}
      mv *log Logs_${lane}
      mv SubBands_${lane}/*ar ${PSR}.${datum}.lofar${lane}.ar
      rmdir SubBands_${lane}
  done

  #mv *_${lane}* ToThrow_${lane}/
  #mv ToThrow_${lane}/SubBands_${lane}/ ./
  #prev_lane=`echo $lanes | awk '{print $1}'`
  #mv ToThrow_${lane}/ToThrow_${prev_lane}/ ./
  #mkdir Logs_${lane}
  #mv ToThrow_${lane}/*.log Logs_${lane}/
  #cd SubBands_${lane}

  #mv *.ar.ar ${PSR}.${datum}.lofar${lane}.ar

  #mv *.lofar${lane}.ar ../
  #cd ..
done 

echo "Finished analysis."

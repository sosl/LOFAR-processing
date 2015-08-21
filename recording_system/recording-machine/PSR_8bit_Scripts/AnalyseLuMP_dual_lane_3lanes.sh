#!/bin/bash

#
# Simple script to process LuMP single-station pulsar data. 
#
# Joris P.W. Verbiest, MPIfR, December 2012.
# Heavily modified by Stefan Oslowski between June 2013 and May 2015
#

if [ $# -eq 0 ] || [ "$1" == "-h" ] || [ $# -gt 4 ]
then
    echo "Need pulsar name and optionally number of threads as an argument:"
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
  psrcat -all -e $PSR > eph.par
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

if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
then 
  lanes="2 3"
else
  lanes="1"
fi

epoch=$(basename $(pwd))
for lane in $lanes
do
  LuMP_Pulsar_Cleanup.py --source_name=${PSR} --source_RA=${RA} --source_Dec=${DEC} --telescope=${station} --filename_base=${PSR}_${lane}.00 

  mkdir -p SubBands_${lane}
  mkdir -p ToThrow_${lane}
  for file in ` ls -1 ${PSR}_${lane}*.0*raw`
  do
      #determine if extra element in file name necessary when handling LuMP0 format:
      raw_file_fields=$(echo $file | awk -F_ '{print NF}')
      if [[ $raw_file_fields -eq 2 ]]
      then
	      extra=""
      elif [[ $raw_file_fields -eq 3 ]]
      then
	      extra="."$(echo $file | awk -F_ '{print substr($2,6,4)}')
      else
	      echo Unknown file naming scheme. Ensure compatibility with Analyse'*' script
	      extra=".unknown."
      fi

      small_DM=`echo $DM | awk '{if ($1 < 65 ) print "1"; else print "0"}'`
      #determine if we can use FFT-benchmarks
      power_of_two=`echo $threads | awk '{print int(log($1)/log(2))==log($1)/log(2)}'`
      if [[ $power_of_two -eq 1 ]] && [[ $channels -ne 39 ]] #why doesn't this work for -F nchan:D with nchan > NCHAN in baseband?
      then
	      fft_bench="-fft-bench"
      else
	      fft_bench=""
      fi

      if  [ $small_DM -eq 1 ]
      then
          #echo dspsr -F ${channels}:D -A -E eph.par -L 10 -t $threads -minram 1 -O ${PSR}.${epoch}.lofar${lane}${extra} $file $fft_bench
          time dspsr -F ${channels}:D -A -E eph.par -L 10 -t $threads -minram 1 -O ${PSR}.${epoch}.lofar${lane}${extra} $file $fft_bench
      else
          echo "High DM. Slowing down..."
          #echo dspsr -F ${channels}:D -A -E eph.par -L 10 -U minX2 -t $high_dm_threads -minram 1 -O ${PSR}.${epoch}.lofar${lane}${extra} $file $fft_bench
          time dspsr -F ${channels}:D -A -E eph.par -L 10 -U minX2 -t $high_dm_threads -minram 1 -O ${PSR}.${epoch}.lofar${lane}${extra} $file $fft_bench
      fi
      # if high-resolution data were recorded, form "normal" data and move high-res to a special directory:
      #mv ${file}.ar.ar SubBands_${lane}/
      mv $file ToThrow_${lane}/
      prefix=`basename $file .raw`
      mv ${prefix}* *_${lane}*lis *_${lane}*valid *_${lane}*info ToThrow_${lane}/
      mkdir -p Logs_${lane}
      mv *log Logs_${lane}
      #mv SubBands_${lane}/*ar ${PSR}.${epoch}.lofar${lane}.ar
      rmdir SubBands_${lane}
  done

  if [[ $channels -eq 39 ]]
  then
	  psradd -jF -R ${PSR}.${epoch}.lofar${lane}\.0*ar -o ${PSR}.${epoch}.lofar${lane}.ar 
	  mkdir -p /media/scratch/observer/LuMP_${station}_reduced_high_res/${PSR}/${epoch}/
	  mv ${PSR}.${epoch}.lofar${lane}\.0*ar /media/scratch/observer/LuMP_${station}_reduced_high_res/${PSR}/${epoch}/
  fi

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

#!/bin/bash

set -o nounset

if [ "$1" == "-h" ] || [ $# -gt 3 ] || [ $# -lt 2 ]  [ $# -eq 0 ]
then
  echo usage: $0 'STATION {HIGH_DM,LOW_DM} [THREADS]'
  echo 'will analyse all pulsars with either high (more than 60) or low (less than 60) DM recorded from station STATION'
  echo The split into DM allows for simultaneous processing of two pulsars which can be beneficial, depending on your recording and processing machines.
  echo 
  echo Example: $0 DE601 LOW_DM 16
  exit
fi

threads=""
threads_while_observing=8

dm_limit=""
if [[ $# -ge 2 ]]
then
  station=$1
  if [[ "$2" == "LOW_DM" ]]
  then
    dm_limit="-lt 60"
  elif [[ "$2" == "HIGH_DM" ]]
  then
    dm_limit"-ge 60"
  else
    echo Must provide either HIGH_DM or LOW_DM as second argument.
    exit
  fi
  threads=16
fi
if [[ $# -eq 3 ]]
then
  threads=$3
fi

data_dir=/media/scratch/observer/LuMP_${station}
failed_dir=/media/scratch/observer/LuMP_${station}_failed
cd $data_dir

datum=`date | awk '{print $6"-"$2"-"$3}'`

function reduce_single_obs
{
  export PYTHONPATH
  #export USE_LUMP_PULSAR_STUFF=1
  . /opt/lump/lump_2.0/SETUP.sh


  # Determine the host 
  Node=`hostname | awk '{print substr($1,length($1))}'`

  if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
  then 
    lanes="[2,3]"
    desired_channels=244
  else
    lanes="[1]"
    desired_channels=122
  fi

  pulsar_obs=$1
  pulsar=`echo $1 | awk -F/ '{print $1}'`
  observation=`echo $1 | awk -F/ '{print $2}'`
  threads=$2
  data_dir=$3
  station=$4
  failed_dir=$5
  echo "Now going to work on high DM pulsar $pulsar " `date`
  mkdir -p ${data_dir}_reduced/${pulsar}
  chmod g+w ${data_dir}_reduced/${pulsar}

  cd $pulsar
  cd $observation

  ~/PSR_8bit_Scripts/AnalyseLuMP_dual_lane_3lanes.sh $station $pulsar $threads >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
  nsub=`psredit -c nchan -qQ [JB]*.ar | awk '{SUM+=$1}END{print SUM}'`
  if [ "${nsub:-0}" -eq $desired_channels ]
  then
    rm -rf ToThrow_$lanes
    rm -f eph.par
    cd ..
    mv $observation ${data_dir}_reduced/$pulsar/
    chmod g+w ${data_dir}_reduced/$pulsar/${observation}
  else
    cd ..
    echo "Problem with pulsar " $pulsar " observation " $observation
    mkdir -p ${failed_dir}/${pulsar}
    mv $observation ${failed_dir}/${pulsar}
  fi

  cd $data_dir
  rmdir --ignore-fail-on-non-empty $pulsar
}

export PYTHONPATH
export USE_LUMP_PULSAR_STUFF=1
#. /opt/lump/lump_2.0/SETUP.sh
. ~/PSR_8bit_Scripts/setup.sh


#Reducing all pulsars while observing in  `pwd` in an ascending order of DM
declare -A DMS
declare -A PULSARS_BY_DM
if [ `ls -rtd1 [B,J]* | head -n -1 | wc -l` -gt 0 ]
then
  for pulsar in `ls -rtd1 [B,J]* | head -n -1`
  do
    dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print $1}'`
    DMS[$pulsar]=$dm
    PULSARS_BY_DM[$dm]=$pulsar
  done
  readarray -t DM_sorted < <(printf '%s\0' "${DMS[@]}" | sort -z -g | xargs -0n1)
  for DM in "${DM_sorted[@]}"
  do
    dm_int=`echo $DM | awk '{print int($1)}'`
    if [ $dm_int -lt 60 ]
    then
      reduce_single_obs ${PULSARS_BY_DM[$DM]} $threads_while_observing $data_dir $station $failed_dir
    fi
  done
fi

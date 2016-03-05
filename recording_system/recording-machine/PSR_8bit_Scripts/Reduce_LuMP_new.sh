#!/bin/bash

if [ "$1" == "-h" ] || [ $# -gt 2 ] || [ $# -eq 0 ]
then
  echo
  echo $(basename $0)
  echo
  echo " Usage: $(basename $0) STATION [THREADS]"  
  echo " This script will process all data from STATION using THREADS cores."
  echo
  exit
fi

threads=4

if [ $# -eq 1 ]
then
  station=$1
elif [ $# -eq 2 ]
then
  station=$1
  threads=$2
fi

data_dir=/media/scratch/observer/LuMP_${station}
failed_dir=/media/scratch/observer/LuMP_${station}_failed
cd $data_dir

datum=`date | awk '{print $6"-"$2"-"$3}'`

function reduce_single
{
  if [[ $# -lt 5 ]] || [[ $# -gt 6 ]]
  then
    echo 'No pulsars found (most likely)'
    echo received $# args
    echo $@
    return 1
  fi
  export PYTHONPATH
  export USE_LUMP_PULSAR_STUFF=1
  #. /opt/lump/lump_2.0/SETUP.sh
  . ~/PSR_8bit_Scripts/setup.sh


  # Determine the host 
  Node=`hostname | awk '{print substr($1,length($1))}'`
  # for dual lane mode:
  #  if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
  #  then 
  #    lanes="[3,4]"
  #  else
  #    lanes="[1,2]"
  #  fi
  # for single lane mode
  lanes=$Node

  pulsar=$1 
  threads=$2
  data_dir=$3
  station=$4
  failed_dir=$5
  if [[ $# -eq 6 ]]
  then
    channels=$6
  else
    channels=122
  fi
  echo "Now going to work on pulsar $pulsar  " `date`
  mkdir -p ${data_dir}_reduced/${pulsar}
  chmod g+w ${data_dir}_reduced/${pulsar}
  cd $pulsar
  for observation in `ls -1d 20[0-9]*`
  do 
    cd $observation
    ~/PSR_8bit_Scripts/AnalyseLuMP_new.sh $station $pulsar $threads $channels >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
    nsub=`psredit -c nchan -qQ [JB]*.ar | awk '{SUM+=$1}END{print SUM}'`
    if [ "${nsub:-0}" -eq 122 ]
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
      echo Moved the observation to ${failed_dir}/${pulsar}
    fi
  done
  cd $data_dir
  rmdir --ignore-fail-on-non-empty $pulsar
}

export PYTHONPATH
export USE_LUMP_PULSAR_STUFF=1
#. /opt/lump/lump_2.0/SETUP.sh
shopt -s expand_aliases
. ~/PSR_8bit_Scripts/setup.sh

#echo Reducing all pulsars while observing in  `pwd` in an ascending order of DM
declare -A DMS
declare -A PULSARS_BY_DM
current=`current_obs`
if [[ "$current" == "" ]]
then
  #current=`ls -rtd1 [B,J]* | tail -n 1`
  current=""
else
  current="| grep -v $current"
fi

if [ `eval "ls -rtd1 [B,J]* $current 2>&1 | grep -v 'cannot access [B,J]*' | wc -l"` -gt 0 ]
then
  for pulsar in `eval "ls -rtd1 [B,J]* $current 2>&1 | grep -v 'cannot access [B,J]*'"`
  do
    dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print $1}'`
    DMS[$pulsar]=$dm
    PULSARS_BY_DM[$dm]=$pulsar
  done
  readarray -t DM_sorted < <(printf '%s\0' "${DMS[@]}" | sort -z -g | xargs -0n1)
  for DM in "${DM_sorted[@]}"
  do
    dm_int=`echo $DM | awk '{print int($1)}'`
    if [ $dm_int -lt 55 ]
    then
      #for scintillation:
      if [[ "${PULSARS_BY_DM[$DM]}" = "J1136+1551" ]] 
      then
	channels=39
      else
	channels=""
      fi
      reduce_single ${PULSARS_BY_DM[$DM]} $threads $data_dir $station $failed_dir $channels 
    fi
  done
fi

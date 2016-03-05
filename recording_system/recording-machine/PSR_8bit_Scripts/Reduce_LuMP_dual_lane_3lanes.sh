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

export PYTHONPATH
export USE_LUMP_PULSAR_STUFF=1
#. /opt/lump/lump_2.0/SETUP.sh
. ~/PSR_8bit_Scripts/setup.sh

threads=8

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
  export PYTHONPATH
  export USE_LUMP_PULSAR_STUFF=1
  #. /opt/lump/lump_2.0/SETUP.sh
  . ~/PSR_8bit_Scripts/setup.sh


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

  pulsar=$1 
  if [[ "$pulsar" = "J0837+0610" ]]
  then
    desired_channels=$(echo $desired_channels"*39" | bc)
  fi
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
  current_obs_utc=`current_obs_with_utc | awk -F/ '{print $2}'`
  if [[ "$current_obs_utc" == "" ]]
  then
    current_obs_utc=""
  else
    current_obs_utc="| grep -v $current_obs_utc"
  fi

  if [ $(eval "ls -rtd1 20[0-9]* $current_obs_utc 2>&1 | grep -v 'cannot access 20' | wc -l") -gt 0 ]
  then 
    echo will process $(eval "ls -rtd1 20[0-9]* $current_obs_utc 2>&1 | grep -v 'cannot access 20'")
    for observation in $(eval "ls -1d 20[0-9]* $current_obs_utc 2>&1 | grep -v 'cannot access 20'")
    do 
      cd $observation
      ~/PSR_8bit_Scripts/AnalyseLuMP_dual_lane_3lanes.sh $station $pulsar $threads $channels >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
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
	echo Moved the observation to ${failed_dir}/${pulsar}
      fi
    done
  else
    echo "Only ongoing observation present, will not process"
  fi
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
#if [ `ls -rtd1 [B,J]* | head -n -1 | wc -l` -gt 0 ]
if [ `eval "ls -rtd1 [B,J]* 2>&1 | grep -v 'cannot access' | wc -l"` -gt 0 ]
then
  for pulsar in `eval "ls -rtd1 [B,J]* 2>&1 | grep -v 'cannot access'"`
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
      #for scintillation:
      if [[ "${PULSARS_BY_DM[$DM]}" = "J0837+0610" ]] || [[ "${PULSARS_BY_DM[$DM]}" = "J0332+5434" ]]
      then
	channels=39
      else
	channels=""
      fi
      reduce_single ${PULSARS_BY_DM[$DM]} $threads $data_dir $station $failed_dir $channels 
    fi
  done
fi

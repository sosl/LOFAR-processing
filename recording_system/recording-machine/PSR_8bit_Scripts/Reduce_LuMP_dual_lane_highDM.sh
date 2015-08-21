#!/bin/bash

if [ "$1" == "-h" ] || [ $# -gt 3 ] || [ $# -eq 0 ]
then
        echo "Help information:"
        echo "Reduce_LuMP.csh"
        echo "Optional arguments: "
        echo "  Reduce_LuMP.csh   : reduce all pulsars."
        echo "  Reduce_LuMP.csh 0 [threads] : reduce all pulsars."
        echo "  Reduce_LuMP.csh 1 [threads] : reduce the first half of all pulsars"
        echo "  Reduce_LuMP.csh 2 [threads] : reduce the second half of all pulsars"
        echo "  Reduce_LuMP.csh 3 [threads] : reduce all pulsars sorted by their DM value."
        echo "  Reduce_LuMP.csh 4  : reduce some pulsars while observing."
        exit
fi

threads=""
threads_while_observing=8

if [ $# -eq 2 ]
then
    Half=$1
    station=$2
    threads=20
elif [ $# -eq 1 ]
then
    Half=0
    station=$1
    threads=20
elif [ $# -eq 3 ]
then
    Half=$1
    station=$2
    threads=$3
fi

#data_dir=/media/scratch/observer/LuMP
data_dir=/media/scratch/observer/LuMP_${station}
failed_dir=/media/scratch/observer/LuMP_failed
cd $data_dir

datum=`date | awk '{print $6"-"$2"-"$3}'`

function reduce_single
{
  export PYTHONPATH
  #export USE_LUMP_PULSAR_STUFF=1
  #. /opt/lump/lump_2.0/SETUP.sh
  . ~/PSR_8bit_Scripts/setup.sh


  # Determine the host 
  Node=`hostname | awk '{print substr($1,length($1))}'`

  if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
  then 
    lanes="[3,4]"
  else
    lanes="[1,2]"
  fi

  pulsar=$1 
  threads=$2
  data_dir=$3
  station=$4
  failed_dir=$5
  echo "Now going to work on pulsar $pulsar  " `date`
  #mkdir -p /media/scratch/observer/LuMP_reduced/${pulsar}
  mkdir -p ${data_dir}_reduced/${pulsar}
  #chmod g+w /media/scratch/observer/LuMP_reduced/${pulsar}
  chmod g+w ${data_dir}_reduced/${pulsar}
  cd $pulsar
  for observation in `ls -1d 20[0-9]*`
  do 
    cd $observation
     ~/PSR_8bit_Scripts/AnalyseLuMP_dual_lane.sh $station $pulsar $threads >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
    nsub=`psredit -c nchan -qQ [JB]*.ar | awk '{SUM+=$1}END{print SUM}'`
    if [ "${nsub:-0}" -eq 244 ]
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
  done
  cd $data_dir
  rmdir $pulsar
}

function reduce_single_obs
{
  export PYTHONPATH
  #export USE_LUMP_PULSAR_STUFF=1
  . /opt/lump/lump_2.0/SETUP.sh


  # Determine the host 
  Node=`hostname | awk '{print substr($1,length($1))}'`

  if [[ $Node -eq 2 ]] || [[ $Node -eq 4 ]]
  then 
    lanes="[3,4]"
  else
    lanes="[1,2]"
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

  ~/PSR_8bit_Scripts/AnalyseLuMP_dual_lane.sh $station $pulsar $threads >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
  nsub=`psredit -c nchan -qQ [JB]*.ar | awk '{SUM+=$1}END{print SUM}'`
  if [ "${nsub:-0}" -eq 244 ]
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


if [ $Half -eq 0 ]
then 
    echo "Reducing all pulsars in " `pwd`
    for pulsar in `ls -1`
    do
      reduce_single $pulsar $threads $data_dir $station $failed_dir
    done
elif [ $Half -eq 1 ]
then
    echo "Reducing first half of pulsars in " `pwd`
    NPSR=`ls -1 | wc -w | awk '{print int($1/2)+int($1/2)%2}'`
    for pulsar in `ls -1 | head -${NPSR}`
    do
      reduce_single $pulsar $threads $data_dir $station $failed_dir
    done
elif [ $Half -eq 2 ]
then
    echo "Reducing second half of pulsars in " `pwd`
    NPSR=`ls -1 | wc -w | awk '{print int($1/2)}'`
    for pulsar in `ls -1 | tail -${NPSR}`
    do
      reduce_single $pulsar $threads $data_dir $station $failed_dir
    done
elif [ $Half -eq 3 ]
then
    echo Reducing all pulsars in  `pwd` in an ascending order of DM
    declare -A DMS
    declare -A PULSARS_BY_DM
    for pulsar in `ls -1`
    do
      dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print $1}'`
      DMS[$pulsar]=$dm
      PULSARS_BY_DM[$dm]=$pulsar
    done
    readarray -t DM_sorted < <(printf '%s\0' "${DMS[@]}" | sort -z -g | xargs -0n1)
    for DM in "${DM_sorted[@]}"
    do
      reduce_single ${PULSARS_BY_DM[$DM]} $threads $data_dir $station $failed_dir
    done
elif [ $Half -eq 4 ]
then
    echo "Reducing all pulsars while observing, skipping the latest observation."
    for pulsar in `ls -rt1 | head -n -1`
    do
      dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print int($1)}'`
      if [ $dm -ge 60 ]
      then
        reduce_single $pulsar $threads_while_observing $data_dir $station $failed_dir
      fi
    done
elif [ $Half -eq 5 ]
then
    #echo Reducing all pulsars while observing in  `pwd` in an ascending order of DM
    declare -A DMS
    declare -A PULSAR_OBS_BY_DM
    #for pulsar in `ls -rtd1 J* | head -n -1`
    #for pulsar in `ls -rt1 | head -n -1`
    if [ `ls -rtd1 [B,J]* | head -n -1 | wc -l` -gt 0 ]
    then
	    for pulsar_obs in `ls -rtd1 [B,J]*/20* | head -n -1`
	    do
		    pulsar=`echo $pulsar_obs | awk -F/ '{print $1}'`
		    dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print $1}'`
		    DMS[$pulsar_obs]=$dm
		    PULSAR_OBS_BY_DM[$dm]=$pulsar_obs
	    done
	    readarray -t DM_sorted < <(printf '%s\0' "${DMS[@]}" | sort -z -g | xargs -0n1)
	    for DM in "${DM_sorted[@]}"
	    do
		    dm_int=`echo $DM | awk '{print int($1)}'`
		    if [ $dm_int -ge 60 ]
		    then
			    reduce_single_obs ${PULSAR_OBS_BY_DM[$DM]} $threads_while_observing $data_dir $station $failed_dir
		    fi
	    done
    fi
fi

#echo Finished. `date`

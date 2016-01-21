#!/bin/bash

if [ "$1" == "-h" ] || [ $# -gt 2 ] || [ $# -eq 0 ]
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
        echo "  Reduce_LuMP.csh 5  : reduce some pulsars sorted by their DM value while observing."
        exit
fi

threads=""
threads_while_observing=4

if [ $# -eq 2 ]
then
    Half=$1
    station=$2
    threads=16
elif [ $# -eq 1 ]
then
    Half=$1
    station=DE601
    threads=16
elif [ $# -eq 3 ]
then
    Half=$1
    station=$2
    threads=$3
fi

#data_dir=/media/scratch/observer/LuMP
data_dir=/media/scratch/observer/LuMP_${station}
failed_dir=/media/scratch/observer/LuMP_${station}_failed
cd $data_dir

datum=`date | awk '{print $6"-"$2"-"$3}'`

function reduce_single
{
	if [[ $# -lt 4 ]] || [[ $# -gt 5 ]]
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
	if [[ $# -eq 5 ]]
	then
		channels=$5
	else
		channels=122
	fi
	echo "Now going to work on pulsar $pulsar  " `date`
	#mkdir -p /media/scratch/observer/LuMP_reduced/${pulsar}
	mkdir -p ${data_dir}_reduced/${pulsar}
	#chmod g+w /media/scratch/observer/LuMP_reduced/${pulsar}
	chmod g+w ${data_dir}_reduced/${pulsar}
	cd $pulsar
	for observation in `ls -1d 20[0-9]*`
	do 
		cd $observation
		echo ~/PSR_8bit_Scripts/AnalyseLuMP_new.sh $station $pulsar $threads $channels 
		~/PSR_8bit_Scripts/AnalyseLuMP_new.sh $station $pulsar $threads $channels >> ~/PSR_Logs/${datum}.${pulsar}.${observation}.log 2>&1
		nsub=`psredit -c nchan -qQ [JB]*.ar | awk '{SUM+=$1}END{print SUM}'`
		if [ "${nsub:-0}" -eq 122 ]
		then
			rm -rf ToThrow_$lanes
			rm -f eph.par
			cd ..
			#mv $observation ${data_dir}_reduced/$pulsar/
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

                  export PYTHONPATH
                  export USE_LUMP_PULSAR_STUFF=1
                  #. /opt/lump/lump_2.0/SETUP.sh
                  shopt -s expand_aliases
                  . ~/PSR_8bit_Scripts/setup.sh


                  if [ $Half -eq 0 ]
                  then 
                    echo "Reducing all pulsars in " `pwd`
                    for pulsar in `ls -1`
                    do
                      reduce_single $pulsar $threads $data_dir $station
                    done
                  elif [ $Half -eq 1 ]
                  then
                    echo "Reducing first half of pulsars in " `pwd`
                    NPSR=`ls -1 | wc -w | awk '{print int($1/2)+int($1/2)%2}'`
                    for pulsar in `ls -1 | head -${NPSR}`
                    do
                      reduce_single $pulsar $threads $data_dir $station
                    done
                  elif [ $Half -eq 2 ]
                  then
                    echo "Reducing second half of pulsars in " `pwd`
                    NPSR=`ls -1 | wc -w | awk '{print int($1/2)}'`
                    for pulsar in `ls -1 | tail -${NPSR}`
                    do
                      reduce_single $pulsar $threads $data_dir $station
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
                      reduce_single ${PULSARS_BY_DM[$DM]} $threads $data_dir $station
                    done
                  elif [ $Half -eq 4 ]
                  then
                    echo "Reducing all pulsars while observing, skipping the latest observation."
                    for pulsar in `ls -rt1 | head -n -1`
                    do
                      dm=`psrcat -c DM $pulsar -nohead -nonumber -o short | awk '{print int($1)}'`
                      if [ $dm -lt 60 ]
                      then
                        reduce_single $pulsar $threads_while_observing $data_dir $station
                      fi
                    done
                  elif [ $Half -eq 5 ]
                  then
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
    #if [ `ls -rtd1 [B,J]* | grep -v J1136+1551 | head -n -1 | wc -l` -gt 0 ]
    #if [ `eval "ls -rtd1 [B,J]* $current | grep -v J1136+1551 2>&1 | grep -v 'cannot access [B,J]*' | wc -l"` -gt 0 ]
    if [ `eval "ls -rtd1 [B,J]* $current 2>&1 | grep -v 'cannot access [B,J]*' | wc -l"` -gt 0 ]
    then
	    #for pulsar in `ls -rtd1 J* | head -n -1`
	    #for pulsar in `ls -rtd1 [B,J]* | grep -v J1136+1551 | head -n -1`
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
			    #if [[ "${PULSARS_BY_DM[$DM]}" = "J1136+1551" ]] || [[ "${PULSARS_BY_DM[$DM]}" = "J0700+6418" ]] || [[ "${PULSARS_BY_DM[$DM]}" = "J2219+4754" ]]
			    if [[ "${PULSARS_BY_DM[$DM]}" = "J1136+1551" ]] 
			    then
				    channels=39
			    else
				    channels=""
			    fi
			    #echo reduce_single ${PULSARS_BY_DM[$DM]} $threads_while_observing $data_dir $station $channels
			    reduce_single ${PULSARS_BY_DM[$DM]} $threads_while_observing $data_dir $station $channels $failed_dir
		    fi
	    done
    fi
fi

#echo Finished. `date`

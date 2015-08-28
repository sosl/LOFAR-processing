#!/bin/bash

# Set up a beam onto a known pulsar
# Default to standard choice of beamlets and subbands for three and four lane observing modes.
# Also allows to observe with an arbitrary selection of beamlets and subbands

set -o nounset
set -o errexit

export LC_NUMERIC=en_US.UTF-8
export PSRCAT_RUNDIR=/data/home/user9/LCU-scripts/psrcat_dbs
export PSRCAT_FILE ${PSRCAT_RUNDIR}/psrcat.db

if [[ $# -ne 2 ]] || [[ $# -ne 3 ]]
then
  echo This observing script has two modes:
  echo 
  echo Mode 1 : Observe a known pulsar and use default setup for 3 or 4 lane recording:
  echo usage: $0 PSR LANES
  echo E.g:   $0 B0329+54 3
  echo 
  echo If three lanes are chosen then the script will use:
  echo          beamlets=0:365
  echo          subbands=93:458
  echo
  echo If four lanes are chose then the script will use:
  echo          beamlets=0:487
  echo          subbands=12:499
  echo
  echo Mode 2 : Observe a known pulsar and use provided range of beamlets and subbands:
  echo usage: $0 PSR BEAMLET_RANGE SUBBAND_RANGE
  echo E.g.:  $0 B0329+54 0:365 93:458A
  echo 
  echo Make sure that the RSPDriver configuration reflects your choice of lanes.
  exit
fi

psr=$1
if [[ $# -eq 2 ]]
then
  lanes=$2
  if  [[ $lanes -eq 3 ]]
  then
    beamlet_range=0:365
    subband_range=93:458
  elif [[ $lanes -eq 4 ]]
  then
    beamlet_range=0:487
    subband_range=12:499
  else
    echo Only 3 or 4 lanes accepted while $lanes was provided
    exit 1
  fi
elif [[ $# -eq 3 ]]
then
  beamlet_range=$2
  subband_range=$3
fi

psr_info=$(psrcat -all -o short -nohead -nonumber -c "raj decj" $psr)
pos_rad=$(echo $psr_info[1] $psr_info[2] | sed s/\\:/" "/g | awk -v pi=3.1415926535 '{printf "%.6f %.6f\n",(($1+(($2+($3/60.0))/60.0))/24.0)*2*pi,(($4+(($5+($6/60.0))/60.0))/360.0)*2*pi}')
ra=${pos_rad[0]}
dec=${pos_rad[1]}

RCU_USE=$(grep "RCUMODE 5" /data/home/user9/LCU-scripts/GOOD_RCUS.txt | cut -d= -f2)
echo "beamctl --antennaset=HBA_JOINED --rcus=$RCU_USE --rcumode=5 --beamlets=${beamlet_range} --subbands=${subband_range} --anadir=$ra,$dec,J2000 --digdir=$ra,$dec,J2000&" > latest_beamctl_cmds

. latest_beamctl_cmds

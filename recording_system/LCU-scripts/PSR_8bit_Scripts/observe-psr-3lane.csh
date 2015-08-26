#!/bin/csh

# This script sets up a beam onto a known pulsar
# using only the first three lanes (366 subbands) in rcumode 5

setenv LC_NUMERIC en_US.UTF-8 #who the fuck added localization to awk???
setenv PSRCAT_RUNDIR /data/home/user9/LCU-scripts/psrcat_dbs
setenv PSRCAT_FILE $PSRCAT_RUNDIR/psrcat.db

set source = $1
set source_info = `psrcat -all -o short -nohead -nonumber -c "raj decj" $source`
echo $source_info
set pos_rad = `echo $source_info[1] $source_info[2] | sed s/\\:/" "/g | awk -v pi=3.1415926535 '{printf "%.6f %.6f\n",(($1+(($2+($3/60.0))/60.0))/24.0)*2*pi,(($4+(($5+($6/60.0))/60.0))/360.0)*2*pi}'`
set ra = $pos_rad[1]
set dec = $pos_rad[2]

set RCU_USE=`grep "RCUMODE 5" /data/home/user9/LCU-scripts/GOOD_RCUS.txt | cut -d= -f2`

echo "beamctl --antennaset=HBA_JOINED --rcus=$RCU_USE --rcumode=5 --beamlets=0:365 --subbands=93:458 --anadir=$ra,$dec,J2000 --digdir=$ra,$dec,J2000&" > latest_beamctl_cmds
source latest_beamctl_cmds

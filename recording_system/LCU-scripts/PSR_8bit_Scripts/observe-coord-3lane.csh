#!/bin/csh

# This script sets up a beam onto a given position
# give RA as first parameter (in radians!) and dec as second parameter (in radians!)
# using only the first three lanes (366 subbands) in rcumode 5

set ra = $1
set dec = $2

set RCU_USE=`grep "RCUMODE 5" /data/home/user9/LCU-scripts/GOOD_RCUS.txt | cut -d= -f2`

echo "beamctl --antennaset=HBA_JOINED --rcus=$RCU_USE --rcumode=5 --beamlets=0:365 --subbands=93:458 --anadir=$ra,$dec,J2000 --digdir=$ra,$dec,J2000&" > latest_beamctl_cmds
source latest_beamctl_cmds

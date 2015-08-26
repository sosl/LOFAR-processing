#!/bin/csh

# 
# This script should be all you need to call to 
# point the telescope, and send data to the 
# data-taking machines. 
# NB. only the psr mode works so far ...
#

# Added by Stefan Oslowski: this ensures that correct number formating is used
setenv LANG en_GB.UTF-8
setenv LC_ALL en_GB.UTF-8

# If not enough cmd line args then print usage #
if ( $# < 2 ) then 
    echo "Usage: observe [mode] [psr_name]/[coords]"
    echo "    mode = psr, rajdecj, azzen"
    echo "    psr_name = psr_name_for_psrcat"
    echo "    coords = RAJ DECJ, AZ ZEN"
    echo "e.g. observe psr B0329+54, observe rajdecj 01:23:00 +45:67:00"
    goto death
endif
set mode = $1
if ( $mode == "psr" ) then
    set source = $2
    goto psr_mode
else if ( $mode == "rajdecj" ) then
    set raj = $2
    set decj = $3
    goto rajdecj_mode
else if ( $mode == "azzen" ) then
    set az = $2
    set zen = $3
    goto azzen_mode
else 
    echo "Observing mode not understand. Dying."
    goto death
endif

# FUNCTIONS (really goto statements!) #
#
psr_mode:
~/LCU-scripts/PSR_8bit_Scripts/make_beamctl_knownpsr $source
source latest_beamctl_cmds
goto death
#
rajdecj_mode:
~/LCU-scripts/PSR_8bit_Scripts/make_beamctl_knownpsr $source
source latest_beamctl_cmds
goto death
#
azzen_mode:
~/LCU-scripts/PSR_8bit_Scripts/make_beamctl_knownpsr $source
source latest_beamctl_cmds
goto death
#


death:
exit


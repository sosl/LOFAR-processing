#!/bin/awk -f

# Copyright (C) 2015 by Stefan Oslowski
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work

# This script is necessary for parseBBSJonesPSRCHIVE.sh to work
# and you should have received the two files together. The
# script needs to be placed in the directory specified by
# the MSCORPOL_PYPATH variable.


BEGIN {}
{print $1,freq,$2,$3,$4,$5,$6,$7,$8,$9}
END {}

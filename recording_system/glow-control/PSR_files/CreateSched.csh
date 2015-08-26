#!/bin/tcsh

# set verbose

#set echo

#
# Makes a script to do DE601 observations, based on an input file
# (single argument) that provides the pulsars in the first column and
# the number of minutes they should be observed for, in the second
# column. Comment lines can be included by adding a # in the comment
# line, or by adding the comments (without #'s!) behind the
# integration time (separated by a space).
#
# Joris P.W. Verbiest, MPIfR, 5 May 2013.
# Stefan Oslowski, replaced double calls to echo by tee and added chmod
# Joris P.W. Verbiest, UBI, 24 Dec 2013: Extended with command-line-
#                  arguments for station and recording nodes

if( $#argv != 4 && $#argv != 3 )then
    echo "CreateSched.csh"
    echo " --- A simple script to convert source lists into observing scripts."
    echo " USAGE:"
    echo "         ./CreateSched.csh file.list [DE601|DE603|DE605] [A|B|C] {12|34}"
    echo " e.g.:"
    echo "         ./CreateSched.csh 2013-12-24.DE601.list DE601 C 34 "
    echo " Input arguments:"
    echo " file.list: a list of source names and integration lenghts. "
    echo "            Lines including hash marks are ignored."
    echo " "
    echo " DE60X: Defines the LOFAR station to be used."
    echo " "
    echo " A|B|C: Defines the set of recording computers to be used."
    echo " "
    echo " 12|34: In case of dual-lane recording, defines which set of computers"
    echo "        the data are recorded to (lofar?[12] or lofar?[34]). If this "
    echo "        argument is omitted, four single streams to four single "
    echo "        machines, will be recorded. (OPTIONAL)"
    exit
endif

set INFile = $1
set STATION = $2
set COMPUTERS = $3

if( $#argv == 4 ) then
    set NODES = $4
else if( $#argv == 3 ) then
    set NODES = 0
else
    echo argv $#argv
    echo "This should not be possible. Dying..."
    exit
endif

set OUTFile = {$INFile}.sched

echo "Making schedule based on " $INFile

set Length = `cat $INFile | grep -v -e "#" | wc -l | awk '{print $1}'`

echo '#\!/bin/tcsh ' > $OUTFile

@ ii = 1


if ( $NODES == B ) then
  set LANES = ""
else
  set LANES = "_3lanes"
endif
if( $NODES != 0 )then 
  echo "~/PSR_8bit_Scripts/ObserveNew_${STATION}_${COMPUTERS}${NODES}${LANES}.py -T 4 -P TEST -v >> $INFile.log " >> $OUTFile
else if ( $NODES == 0)then
  echo "~/PSR_8bit_Scripts/ObserveNew_${STATION}_${COMPUTERS}.py -T 4 -P TEST -v >> $INFile.log " >> $OUTFile
else
  echo NODES $NODES
  echo "This should not be possible. Dying..."
endif

while ( $ii <= $Length ) 
    set line = `cat $INFile | grep -v -e "#" | head -{$ii} | tail -1`
    set linelength = `echo $line | awk '{print NF}'`
    set source = `echo $line | awk '{print $1}'`
    set isPSR = `echo $source | awk '{if ($1 == "Process") print 0; else print 1}'`
    if( $isPSR ) then
	set Tint = `echo $line | awk '{print $2}'`
	echo "date | tee -a $INFile.log " >> $OUTFile
	if( $linelength == 4 ) then 
	    # Included start time
	    set StartTime = `echo $line | awk '{print $3,$4}'`
	    echo "echo 'Starting observation " $ii " on " $source " (expected at UTC " $StartTime ")' | tee -a {$INFile}.log" >> $OUTFile
	else
	    echo "echo 'Starting observation " $ii " on " $source  "' | tee -a $INFile.log" >> $OUTFile
	endif
	#echo "~/PSR_8bit_Scripts/psr-observe-LuMPkill-B.py -T $Tint -P $source -v >> $INFile.log " >> $OUTFile
	if ( $NODES == B ) then
	    set LANES = ""
        else
            set LANES = "_3lanes"
        endif
	if( $NODES != 0 )then 
	    echo "~/PSR_8bit_Scripts/ObserveNew_${STATION}_${COMPUTERS}${NODES}${LANES}.py -T $Tint -P $source -v >> $INFile.log " >> $OUTFile
	else if( $NODES == 0 )then
	    #echo "NOTE THIS MODE IS NOT SUPPORTED RIGHT NOW. YOU MAY HAVE TO MANUALLY CHANGE THE SCRIPT TO USE A psr-observe-LuMPkill-[ABC]*.py SCRIPT!!!!"
	    echo "~/PSR_8bit_Scripts/ObserveNew_${STATION}_${COMPUTERS}.py -T $Tint -P $source -v >> $INFile.log " >> $OUTFile
	else 
            echo NODES $NODES
	    echo "This should not be possible. Dying..."
	    exit
	endif
    else
	# Processing line. Get pulsar name
	set PSR1 = `echo $line | awk '{print $2}'`
	set PSR2 = `echo $line | awk '{print $3}'`
	set proclength = `echo $line | awk '{print $4*60}'`
	echo "date " >> $OUTFile 
	echo "date >> {$INFile}.log " >> $OUTFile
	echo "echo 'Starting processing of " $PSR1 " and " $PSR2 "' | tee -a {$INFile}.log" >> $OUTFile
	echo "psr-process-lofarBN.py -A --psr=$PSR1 --kill=$proclength >> {$INFile}.log &" >> $OUTFile
	echo "psr-process-lofarBN.py -A --psr=$PSR2 --kill=$proclength >> {$INFile}.log &" >> $OUTFile
	echo "sleep $proclength " >> $OUTFile
    endif 
    @ ii = $ii + 1
end

echo "date | tee -a {$INFile}.log " >> $OUTFile
echo "echo 'Finished observing' | tee -a {$INFile}.log " >> $OUTFile

if( $STATION == DE605 )then 
    echo "ssh glow605 ssh de605c 'swlevel 0' | tee -a {$INFile}.log " >> $OUTFile
else if( $STATION == DE601 )then
    echo "ssh glow601 ssh de601c 'swlevel 0' | tee -a {$INFile}.log " >> $OUTFile
else if( $STATION == DE602 )then
    echo "ssh glow602 ssh de602c 'swlevel 0' | tee -a {$INFile}.log " >> $OUTFile
else if( $STATION == DE603 )then
    echo "ssh glow603 ssh de603c 'swlevel 0' | tee -a {$INFile}.log " >> $OUTFile
else if( $STATION == DE609 )then
    echo "ssh glow609 ssh de609c 'swlevel 0' | tee -a {$INFile}.log " >> $OUTFile
else
    echo STATION $STATION
    echo "This should not be possible. Dying..."
    exit
endif
chmod 755 $OUTFile

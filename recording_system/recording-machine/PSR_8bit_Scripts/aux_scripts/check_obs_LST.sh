#!/bin/bash

if [ $# -ne 1 ]
then
	echo usage: $0 top_directory
	exit
fi

topdir=$1

cd $topdir

echo -e "\tPSR\t|\t\tEPOCH\t\t\t|\tOBS LST\t|\tOPT LST\t|   LST DIFF1   |   LST DIFF2   |   LST  DIFF   |"

for epoch in `find . -mindepth 2 -maxdepth 2 -type d -name '201*[0-9]'| sort -k 3,3 -t /`
do
	psr=`echo $epoch | awk -F/ '{print $2}'`
	cd $epoch
	epoch_stripped=`echo $epoch | awk -F/ '{print $3}'`
	formatted_epoch=`echo $epoch_stripped | awk -F- 'BEGIN{OFS="."}{print $3,$2,$1" "$4":00"}'`
	obs_LST=`~/PSR_8bit_Scripts/aux_scripts/sid.pl -t "$formatted_epoch" | awk '{ if (NR==2) print substr($2,1,5)}'`
	optimal_LST=`echo $psr | awk '{print substr($1,2,2)":"substr($1,4,2)}'`
	diff_LST1=`echo $obs_LST $optimal_LST | awk 'BEGIN{OFS=":"}{H_DIFF=int(substr($1,1,2))-int(substr($2,1,2)); M_DIFF=int(substr($1,4,2))-int(substr($2,4,2)); if (H_DIFF>=0 && M_DIFF >= 0) print H_DIFF,M_DIFF; else if (H_DIFF>=0 && M_DIFF<0) print H_DIFF-1,M_DIFF+60; else if (H_DIFF<0 && M_DIFF <= 0) print "-"-H_DIFF,-M_DIFF; else if (H_DIFF<0 && M_DIFF>0) print "-"-(H_DIFF+1),60-M_DIFF}'`
	diff_LST2=`echo $obs_LST $optimal_LST | awk 'BEGIN{OFS=":"}{H_DIFF=int(substr($1,1,2))-(24+int(substr($2,1,2))); M_DIFF=int(substr($1,4,2))-int(substr($2,4,2)); if (H_DIFF>=0 && M_DIFF >= 0) print H_DIFF,M_DIFF; else if (H_DIFF>=0 && M_DIFF<0) print H_DIFF-1,M_DIFF+60; else if (H_DIFF<0 && M_DIFF <= 0) print "-"-H_DIFF,-M_DIFF; else if (H_DIFF<0 && M_DIFF>0) print "-"-(H_DIFF+1),60-M_DIFF}'`
	diff_LST1_H=`echo $diff_LST1 | awk -F: '{print $1}'`
	diff_LST1_M=`echo $diff_LST1 | awk -F: '{print $2}'`
	diff_LST2_H=`echo $diff_LST2 | awk -F: '{print $1}'`
	diff_LST2_M=`echo $diff_LST2 | awk -F: '{print $2}'`
	if [ $diff_LST1_H -lt $diff_LST2_H ]
	then
		if [[ $diff_LST1_H -lt 1 || $diff_LST1_H -eq 1 && $diff_LST1_M -le 30 ]]; then
			bg_color='\e[42m'
		elif [[ $diff_LST1_H -lt 3 || $diff_LST1_H -eq 3 && $diff_LST1_M -eq 0 ]]; then
			bg_color='\e[43m'
		elif [[ $diff_LST1_H -lt 4 || $diff_LST1_H -eq 4 && $diff_LST1_M -le 30 ]]; then
			bg_color='\e[41m'
		else
			bg_color='\e[4m\e[101m'; fi
		echo -e $psr"\t|\t"$epoch"\t|\t"$obs_LST"\t|\t"$optimal_LST"\t|\t"$diff_LST1"\t|\t"$diff_LST2"\t|\t$bg_color$diff_LST1\e[0m\t|"
	else

		if [[ $diff_LST2_H -lt 1 || $diff_LST2_H -eq 1 && $diff_LST2_M -le 30 ]]; then
			bg_color='\e[42m'
		elif [[ $diff_LST2_H -lt 3 || $diff_LST2_H -eq 3 && $diff_LST2_M -eq 0 ]]; then
			bg_color='\e[43m'
		elif [[ $diff_LST2_H -lt 4 || $diff_LST2_H -eq 4 && $diff_LST2_M -le 30 ]]; then
			bg_color='\e[41m'
		else
			bg_color='\e[4m\e[101m'; fi
		echo -e $psr"\t|\t"$epoch"\t|\t"$obs_LST"\t|\t"$optimal_LST"\t|\t"$diff_LST1"\t|\t"$diff_LST2"\t|\t$bg_color$diff_LST2\e[0m\t|"
	fi
	cd $topdir
done

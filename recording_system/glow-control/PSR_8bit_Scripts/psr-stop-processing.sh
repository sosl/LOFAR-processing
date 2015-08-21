#!/bin/bash

for node_gen in b c
do
	for node in 1 2 3 4
	do
		ssh lofar${node_gen}${node} 'killall run_process_highdm_pulsars.sh; killall run_process_normal_pulsars.sh; killall main_daemon.sh; killall dspsr;'
	done
done

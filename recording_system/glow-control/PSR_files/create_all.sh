#!/bin/bash

if [[ $# -ne 1 ]] || [[ "$1" == "-h" ]]
then
	echo usage: $0 date
	echo format: 2014-06-13
	exit
fi

date=$1

echo 'assuming DE601 -> B'
echo 'assuming DE602 -> C12'
echo 'assuming DE603 -> C34'
echo 'assuming DE605 -> D12'
#echo 'assuming DE609 -> D34'

echo ./CreateSched.csh ${date}_DE601.list DE601 B
./CreateSched.csh ${date}_DE601.list DE601 B
echo ./CreateSched.csh ${date}_DE602.list DE602 C 12
./CreateSched.csh ${date}_DE602.list DE602 C 12
echo ./CreateSched.csh ${date}_DE603.list DE603 C 34
./CreateSched.csh ${date}_DE603.list DE603 C 34
echo ./CreateSched.csh ${date}_DE605.list DE605 D 12
./CreateSched.csh ${date}_DE605.list DE605 D 12
#echo ./CreateSched.csh ${date}_DE609.list DE609 D 34
#./CreateSched.csh ${date}_DE609.list DE609 D 34

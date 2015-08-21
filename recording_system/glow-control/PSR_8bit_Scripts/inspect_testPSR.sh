#!/bin/bash

for files in $(find /home/observer/PSR_files/test_obs/ -type f -name '*png' | sort)
do
  node=$(echo $files | awk -F/ '{print $6}')
  psr=$(echo $files | awk -F/ '{print $7}')
  echo handling psr $psr from node $node
  sleep 5
  file=$(basename $files)
  file_z=$(basename $files .png)
  echo showing $file from $node $psr
  display $files
  echo "delete?"
  read del
  if [[ "${del}" = y || "${del}" = Y ]]
  then
    ssh $node 'rm /media/scratch/observer/LuMP_DE60*/'${psr}'/201*/'$file_z'*'
    rm $files
    rmdir -p --ignore-fail-on-non-empty /home/observer/PSR_files/test_obs/$node/$psr
  else
    echo "will need to handle $file_z from $node ${psr}, copying..."
    mkdir -p ~/PSR_files/test_obs/inspect/
    scp ${node}:'/media/scratch/observer/LuMP_DE60*/'${psr}'/201*/'$file_z ~/PSR_files/test_obs/inspect/
  fi
done

#!/bin/tcsh

set node = $1

@ ii = 1

ssh observer@lofar${node}${ii} 'df -h /media/scratch/observer/' | tail -n 1

@ ii = $ii + 1

while ( $ii < 5 ) 
    ssh observer@lofar${node}${ii} 'df -h /media/scratch/observer/' |& grep -v Size | tail -n 1 #|& grep -v mapper
    @ ii = $ii + 1
end

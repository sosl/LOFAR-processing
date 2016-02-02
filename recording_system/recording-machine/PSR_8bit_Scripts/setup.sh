export PYTHONPATH
export PGPLOT_DEV=/xs
#export USE_LUMP_PULSAR_STUFF=1
. /opt/lump/lump_2.0/SETUP.sh
. /opt/pulsar-stuff/pulsar-init.sh
alias current_obs='ps -ef | grep RunLuMP | grep bash | grep -v grep | head -n1 | awk '"'"'{print $11}'"'"
alias current_obs_with_utc='ps -ef | grep RunLuMP | grep bash | grep -v grep | head -n1 | awk '"'"'{print $11"/"$13}'"'"
function move_current_obs (){
rm -rf ToThrow_? eph.par B*z
psr=$(pwd | awk -F / '{print $(NF-1)}')
station=$(pwd | awk -F / '{print $(NF-2)}')
epoch=$(pwd | awk -F / '{print $(NF)}')
cd ../../
mkdir -p ../${station}_reduced/${psr}
mv ${psr}/${epoch} ../${station}_reduced/${psr}/
rmdir ${psr}
}
alias check_test_obs='cd $(ls -1rtd /media/scratch/observer/LuMP_DE60?_reduced/B*/2*/ | tail -n1); . ~/PSR_8bit_Scripts/setup.sh ; ~/PSR_8bit_Scripts/zap_with_DAB_5C_6B_6D.psh -ez B*ar; for x in B*z; do pazi $x; done; rm B*z'
alias check_test_obs_ps='cd $(ls -1rtd /media/scratch/observer/LuMP_DE60?_reduced/B*/2*/ | tail -n1); . ~/PSR_8bit_Scripts/setup.sh ; ~/PSR_8bit_Scripts/zap_with_DAB_5C_6B_6D.psh -ez B*ar; psrplot -jDTp -pF -D test_obs.ps/CPS B*z'

alias list_P0DM='psrcat -all -x -c "JNAME DM P0" `ls -1d [B,J]*`'
alias bielefeld_data_tunnel='mkdir -p ~/.ssh/control/; ssh -M -4 -S ~/.ssh/control/bielefeld_data_socket -NfL 1234:lofarfs:22 soslowski@entry2.physik.uni-bielefeld.de'
alias bielefeld_data_tunnel_close='ssh -S ~/.ssh/control/bielefeld_data_socket -O exit soslowski@entry2.physik.uni-bielefeld.de'
alias wsd4so_data_tunnel='mkdir -p ~/.ssh/control/; ssh -M -4 -S ~/.ssh/control/wsd4so_data_socket -NfL 1233:wsd4so:22 soslowski@entry2.physik.uni-bielefeld.de'
alias wsd4so_data_tunnel_close='ssh -S ~/.ssh/control/wsd4so_data_socket -O exit soslowski@entry2.physik.uni-bielefeld.de'
alias rsync_DE601_bielefeld='rsync --chmod=ug+w -O -av -e "ssh -p 1234" --progress /media/scratch/observer/LuMP_DE601_reduced/ soslowski@127.0.0.1:/lofardata/DE601_new'
alias rsync_DE602_bielefeld='rsync --chmod=ug+w -O -av -e "ssh -p 1234" --progress /media/scratch/observer/LuMP_DE602_reduced/ soslowski@127.0.0.1:/lofardata/DE602_new'
alias rsync_DE603_bielefeld='rsync --chmod=ug+w -O -av -e "ssh -p 1234" --progress /media/scratch/observer/LuMP_DE603_reduced/ soslowski@127.0.0.1:/lofardata/DE603_new'
alias rsync_DE605_bielefeld='rsync --chmod=ug+w -O -av -e "ssh -p 1234" --progress /media/scratch/observer/LuMP_DE605_reduced/ soslowski@127.0.0.1:/lofardata/DE605_new'

alias rsync_DE601_lofarsrv='cd /media/scratch/observer/LuMP_DE601_reduced; rmdir */*/*/SubBands_?; rsync --chmod=ug+w -O -av --remove-source-files -e "ssh" --progress /media/scratch/observer/LuMP_DE601_reduced/ lofarsrv:/media/part1/observer/LuMP/DE601; cd /media/scratch/observer/LuMP_DE601_reduced/; rmdir -p --ignore-fail-on-non-empty */*/*; ls'
alias rsync_DE602_lofarsrv='cd /media/scratch/observer/LuMP_DE602_reduced; rmdir */*/*/SubBands_?; rsync --chmod=ug+w -O -av --remove-source-files -e "ssh" --progress /media/scratch/observer/LuMP_DE602_reduced/ lofarsrv:/media/part1/observer/LuMP/DE602; cd /media/scratch/observer/LuMP_DE602_reduced/; rmdir -p --ignore-fail-on-non-empty */*/*; ls'
alias rsync_DE603_lofarsrv='cd /media/scratch/observer/LuMP_DE603_reduced; rmdir */*/*/SubBands_?; rsync --chmod=ug+w -O -av --remove-source-files -e "ssh" --progress /media/scratch/observer/LuMP_DE603_reduced/ lofarsrv:/media/part1/observer/LuMP/DE603; cd /media/scratch/observer/LuMP_DE603_reduced/; rmdir -p --ignore-fail-on-non-empty */*/*; ls'
alias rsync_DE605_lofarsrv='cd /media/scratch/observer/LuMP_DE605_reduced; rmdir */*/*/SubBands_?; rsync --chmod=ug+w -O -av --remove-source-files -e "ssh" --progress /media/scratch/observer/LuMP_DE605_reduced/ lofarsrv:/media/part1/observer/LuMP/DE605; cd /media/scratch/observer/LuMP_DE605_reduced/; rmdir -p --ignore-fail-on-non-empty */*/*; ls'
alias rsync_DE609_lofarsrv='cd /media/scratch/observer/LuMP_DE609_reduced; rmdir */*/*/SubBands_?; rsync --chmod=ug+w -O -av --remove-source-files -e "ssh" --progress /media/scratch/observer/LuMP_DE609_reduced/ lofarsrv:/media/part1/observer/LuMP/DE609; cd /media/scratch/observer/LuMP_DE609_reduced/; rmdir -p --ignore-fail-on-non-empty */*/*; ls'

distribute_among_lofarXN() {
	if [ $# -ne 1 ]
	then
		echo function ${FUNCNAME} needs one argument
		exit
	fi

	for type in b c d
	do
		for node in 1 2 3 4
		do
			if [ "lofar${type}${node}" != "$(hostname)" ]
			then
				scp "$1" lofar${type}${node}:"$1"
			else
				echo skipping lofar${type}${node}
			fi
		done
	done
}

#defines naming scheme of processing file
_HOST=$(hostname)
_HOSTTYPE=${_HOST:5:1}
if [ "${_HOSTTYPE}" = "b" ]
then
	NODE_DUALITY="new"
else
	NODE_DUALITY="dual_lane_3lanes"
fi

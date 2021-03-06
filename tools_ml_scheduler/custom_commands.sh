#!/usr/bin/env bash
RED='\033[0;31m'
NC='\033[0m' # No Color

function c_killProc(){

#              dont know if ` is the right character for shell
#	for KILLPID in `ps aux | grep '$1' | awk ' { print $2;}'`;
#	do
#		print $KILLPID;
#		echo $KILLPID
#	done

	ps -ef | grep $1 | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_killServiceHandler(){
	ps -ef | grep service_handler | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_killScheduler(){
	ps -ef | grep cinder-scheduler | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_killApi(){
	ps -ef | grep cinder-api | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_killVolume(){
	ps -ef | grep cinder-volume | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_killExperiment(){
	ps -ef | grep experiment | grep -v grep | awk '{print $2}' | xargs kill -9
}

function c_getVolCount(){
	cinder list | grep false |wc
}

function cp_run(){
	cp_print "$2 running" "$1";

	if [ $# -eq 1 ]
	#if [ $2 = "nohup" ]
	then
	    #cp_print "$2 ELSE" "$1";
		eval "$1"
	else
	    #cp_print "$2 THEN" "$1";
		# run in background by default
		nohup $1  </dev/null &>/dev/null &

	fi
}

function c_launchInstance(){
    #!/bin/bash
#    | ID | Name      |   RAM | Disk | Ephemeral | VCPUs | Is Public |
#    | 3  | m1.medium |  4096 |   40 |         0 |     2 | True      |
#    | 4  | m1.large  |  8192 |   80 |         0 |     4 | True      |

    for i in `seq 1 $3`; do
        openstack server create --flavor "$2" --image 599a6e20-6071-4af6-a902-7f1383aa2347 --security-group default --key-name VM-test "$1-$i"

        sleep 4.5
    done
}

function c_novaDown(){
      nova service-list | grep down
}

function c_controllerRestartServices(){
    sudo python /root/cinder/cinder/MLScheduler/experiment.py execute-controller --command "service keystone restart; service nova-api restart; service nova-cert restart; service nova-consoleauth restart; service nova-scheduler restart; service nova-conductor restart; service nova-novncproxy restart; service neutron-server restart; service memcached restart"
}

function c_hostsBadTenants(){
    sudo python /root/cinder/cinder/MLScheduler/experiment.py execute --command "sudo fdisk -l | grep error" --print_output True --print_output_if_have_error True | less
}

function c_hostsReboot(){
     python ~/cinder/cinder/MLScheduler/experiment.py execute --command 'sudo reboot'
}

function c_hostsRunningWorkloadGen(){
     echo "<<<nodes with bigger than number 2 are running workload generator.>>>"
     echo "#####################################################################"

     python ~/cinder/cinder/MLScheduler/experiment.py execute --command 'sudo ps -ef | grep workload_generator | wc -l' --print_output True --print_output_if_have_error True | less
}

function c_hostsExecuteCmd(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute --command "$1" --print_output true  --print_output_if_have_error true | less
}

function c_delErrVolumes(){
    python ~/cinder/cinder/MLScheduler/experiment.py del-err
}

function c_delAvailErrVolumes(){
    python ~/cinder/cinder/MLScheduler/experiment.py del-avail-err
}

function c_shutdownExperiment(){
    python ~/cinder/cinder/MLScheduler/experiment.py shutdown
}

function c_detachDel(){
    python ~/cinder/cinder/MLScheduler/experiment.py det-del
}

function c_getProc(){
	ps aux | grep $1
}

function c_getCinderProc(){
	ps aux | grep cinder
}

function c_getExperiment(){
	ps aux | grep experiment
}

function c_source(){
	source /root/cinder/tools_ml_scheduler/custom_commands.sh
}

function c_activateVenv(){
	source /root/cinder/.venv/bin/activate
}

function c_initTenants(){
    python ~/cinder/cinder/MLScheduler/experiment.py init
}

function c_computesRestartServices(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-compute --command "service nova-compute restart; service neutron-linuxbridge-cleanup restart; service neutron-linuxbridge-agent restart"
}

function c_computesRebootNodes(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-compute --command "reboot"
}

function c_computesExecuteCmd(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-compute --command "$1" | less
}

function c_blocksExecuteCmd(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-blocks --command "$1" | less
}

function c_blocksCheckServices(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-blocks --command 'service --status-all 2>/dev/null | grep -e "cinder\|tgt" | grep -e "- ]"' | less
}

function c_blocksLvdisplay(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-blocks --command 'lvdisplay 2>/dev/null | grep cinder | wc -l' | less
}

function c_blocksLvremove(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-blocks --command "service tgt stop; lvdisplay 2>/dev/null | grep /dev/cinder-volumes | awk '{print $3}' | xargs lvremove -f; service tgt start" | less
}

function c_blocksRestartServices(){
    python /root/cinder/cinder/MLScheduler/experiment.py execute-blocks --command "service tgt restart; service cinder-volume restart" | less
}

function c_runScheduler(){
#/usr/bin/python
export cv_cmd="/root/cinder/tools/with_venv.sh /root/cinder/.venv/bin/cinder-scheduler --config-file=/root/cinder/.venv/etc/cinder/cinder.conf  --log-file=/root/cinder/.venv/var/log/cinder/cinder-scheduler.log"

export cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-scheduler.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf  --log-file=/root/cinder/.venv/var/log/cinder/cinder-scheduler.log"

	cp_run "$cv_cmd" $1
}

function c_runApi(){
#/usr/bin/python
    #cv_cmd="/root/cinder/tools/with_venv.sh /root/cinder/.venv/bin/cinder-api --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

    cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-api.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

    #source /root/cinder/.venv/bin/activate

    #until /root/cinder/tools/with_venv.sh python /root/cinder/cinder-api.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log; do
    #    echo "workload_generator crashed with exit code $?.  Respawning.." >&2
        sleep 1
    #done

	cp_run "$cv_cmd" $1
}

function c_runVolume(){
#/usr/bin/python

    cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-volume.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

	cp_run "$cv_cmd" $1
}

function c_runServiceHandler(){
#/usr/bin/python

#    cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-volume.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

    cv_cmd="python /root/cinder/cinder/MLScheduler/service_handler.py"

	cp_run "$cv_cmd" $1
}

function cp_print(){
    printf "	$1 ${RED} $2 ${NC}\n"
}

function c_cdr_SL(){
	printf "	running ${RED}service-list${NC}\n"

	cinder service-list
}

function c_debugClient(){

    # this is not working it can not find pudb.run maybe because its not registered with venv ?
    # cv_cmd="/root/cinder/tools/with_venv.sh python -m pudb.run /root/python-cinderclient/cinder.py iops-available"

    # python /root/python-cinderclient/cinder.py iops-available

    cv_cmd="python -m pudb.run /root/python-cinderclient/cinder.py iops-available"

    vars=""

    for var in "$@"
    do
        vars="$vars$var "
    done

    printf "$cv_cmd $vars\n"

    eval "$cv_cmd $vars"

	#cp_run "$cv_cmd" $1

}
#cd /root/cinder/
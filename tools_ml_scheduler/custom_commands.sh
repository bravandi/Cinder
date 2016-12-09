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

function c_killPyCharmProc(){
	ps -ef | grep pycharm | grep -v grep | awk '{print $2}' | xargs kill -9
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

function cp_run(){
	cp_print "$2 running" "$1";

	if [ $# -eq 1 ]
	#if [ $2 = "nohup" ]
	then
	    #cp_print "$2 THEN" "$1";
		# run in background by default
		nohup $1  </dev/null &>/dev/null &
	else
	    #cp_print "$2 ELSE" "$1";
		eval "$1"
	fi
}

function c_rebootHosts(){
     python ~/cinder/cinder/MLScheduler/experiment.py execute --command 'sudo reboot'
}

function c_delErrVolumes(){
    python ~/cinder/cinder/MLScheduler/experiment.py del-avail-err
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

function c_getPyCharmProc(){
	ps aux | grep pycharm
}

function c_source(){
	source /root/commands.sh
}

function c_enterVenv(){
	source /root/cinder/.venv/bin/activate
}

function c_runScheduler(){
#/usr/bin/python
export cv_cmd="/root/cinder/tools/with_venv.sh /root/cinder/.venv/bin/cinder-scheduler --config-file=/root/cinder/.venv/etc/cinder/cinder.conf  --log-file=/root/cinder/.venv/var/log/cinder/cinder-scheduler.log"

export cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-scheduler.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf  --log-file=/root/cinder/.venv/var/log/cinder/cinder-scheduler.log"

	cp_run "$cv_cmd" $1
}

function c_runApi(){
#/usr/bin/python
    cv_cmd="/root/cinder/tools/with_venv.sh /root/cinder/.venv/bin/cinder-api --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

    cv_cmd="/root/cinder/tools/with_venv.sh python /root/cinder/cinder-api.py --config-file=/root/cinder/.venv/etc/cinder/cinder.conf --log-file=/root/cinder/.venv/var/log/cinder/cinder-api.log"

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
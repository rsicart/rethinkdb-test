#!/bin/bash 

vboxmanage=/usr/bin/vboxmanage
uuidFile=./vbox_uids_rethink

usage() { echo "Usage: ./vmlaunch.sh -s|-x [all|1..20]"; exit 1; }

mastervm() {
	vm_uuid="$2"
	  
	case "$1" in
		start) 
		"$vboxmanage" startvm $vm_uuid --type headless 
		;; 
		stop) 
		"$vboxmanage" controlvm $vm_uuid poweroff
		;; 
		status) 
		"$vboxmanage" showvminfo $vm_uuid | grep State: 
		;; 
		*) 
		echo "Usage: $0 (start|stop|status)"
		;; 
	esac
}

# Valid options
# s -> start
# x -> stop
options="s:x:"

while getopts $options opt; do
	case $opt in
		s)
			if [[ "${OPTARG}" == "all" ]]; then
				for vm in $(cat $uuidFile); do
					mastervm start $vm && sleep 3;
				done;
			elif [[ ${OPTARG} -gt 0 && ${OPTARG} -lt 21 ]]; then
				echo ${OPTARG}
				mastervm start `cat $uuidFile | sed -e "${OPTARG}p"`
			else
				usage
			fi;
			exit 0;
			;;
		x)
			if [[ "${OPTARG}" == "all" ]]; then
				for vm in $(cat $uuidFile); do
					mastervm stop $vm && sleep 3;
				done;
			elif [[ ${OPTARG} -gt 0 && ${OPTARG} -lt 21 ]]; then
				echo ${OPTARG}
				mastervm stop `cat $uuidFile | sed -e "${OPTARG}p"`
			else
				usage
			fi;
			exit 0;
			;;
		\?)
			usage
			;;
	esac
done

#!/bin/bash

usage() { echo "Usage: ./rethink_launch_cluster.sh  -t master|node [-a IP_ADDR]"; exit 1; }

# Valid options
options="t:a:"
type=""
address=""

while getopts $options opt; do
	case $opt in
		t)
			if [[ "${OPTARG}" == "master" || "${OPTARG}" == "node" ]]; then
				type=${OPTARG}
			else
				usage
			fi
			;;
		a)
			if [[ ${OPTARG} =~ ^[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}$ ]]; then
				address=${OPTARG}
			else
				usage
			fi
			;;
		\?)
			usage
			;;
	esac
done

# Launch commands
if [ "$type" == "master"  ]; then
	exists=$(ps aux | grep rethink | grep -v grep)
	if [ "$?" == "0" ];  then
		nohup rethinkdb --bind all --daemon &
	fi
elif [[ "$type" == "node" && "$address" != "" ]]; then
	exists=$(ps aux | grep rethink | grep -v grep)
	if [ "$?" == "0" ];  then
		nohup rethinkdb --join $address:29015 --bind all --daemon &
	fi
else
	usage
fi

exit 0

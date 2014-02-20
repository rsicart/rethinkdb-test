#!/bin/bash

usage() { echo "Usage: ./rethink_launch_cluster.sh  -t master|node [-a IP_ADDR] [-k stop]"; exit 1; }

# Valid options
options="t:a:k:"
type=""
address=""
name=$(hostname | tr '-' '_')

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
		k)
			if [[ "${OPTARG}" == "stop" ]]; then
				stop=${OPTARG}
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
		nohup rethinkdb -n $name --bind all \
						--daemon --pid-file /var/run/rethinkdb/pid_file &
	fi
elif [[ "$type" == "node" && "$address" != "" ]]; then
	exists=$(ps aux | grep rethink | grep -v grep)
	if [ "$?" == "0" ];  then
		nohup rethinkdb -n $name --join $address:29015 --bind all \
						--daemon --pid-file /var/run/rethinkdb/pid_file &
	fi
elif [[ "$stop" == "stop" ]]; then
	nohup kill -SIGKILL `cat /var/run/rethinkdb/pid_file`
	rm /var/run/rethinkdb/pid_file
else
	usage
fi

exit 0

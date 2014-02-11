#!/bin/bash

# Check perms
user=$(whoami)
if [ "$user" != "root" ]; then
	echo "Error: you need to launch the script with sudo."
	exit 1
fi

# Add PPA
wget http://blog.anantshri.info/content/uploads/2010/09/add-apt-repository.sh.txt
mv add-apt-repository.sh.txt /usr/sbin/add-apt-repository
chmod o+x /usr/sbin/add-apt-repository
chown root:root /usr/sbin/add-apt-repository
add-apt-repository ppa:rethinkdb/ppa

# Install package
apt-get update
apt-get install rethinkdb

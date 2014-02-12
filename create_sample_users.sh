#!/bin/bash

maxUsers=500
tplFile="users.json.tpl"
destFile="data.users.json"

# Reset data file
echo "[" > $destFile

for i in $(seq 1 $maxUsers); do
	address="$RANDOM.$RANDOM.$RANDOM.$RANDOM"
	cat $tplFile | sed -e "s/%USERID%/$i/g" | sed -e "s/%USERIP%/$address/g" >> $destFile
done

lastLine=$(cat $destFile | wc -l)
sed -i -e "$lastLine s/\},/\}/g" $destFile

echo "]" >> $destFile

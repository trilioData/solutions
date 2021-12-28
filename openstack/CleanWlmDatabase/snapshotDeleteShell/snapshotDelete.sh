#!/bin/bash

init()
{
	ssFile="ssList.txt"
	delTrackLog="deleteTrack.log"
	
	echo "" >> ${delTrackLog}
	echo "Starting Deletion of Snapshots at `date`" >> ${delTrackLog}
}

delRecords()
{
	while read line
	do
		ss_id=`echo $line | cut -d"," -f1`
		ss_name=`echo $line | cut -d"," -f2`
		echo -e "\tDeleting ${ss_name} : ${ss_id}" >> ${delTrackLog}
		mysql -e "delete from snapshots where id = '${ss_id}'" workloadmgr
	done < ${ssFile}
	echo "Deletion over at `date`" >> ${delTrackLog}
	echo "" >> ${delTrackLog}
}

init
delRecords

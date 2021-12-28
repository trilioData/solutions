#!/bin/bash

init()
{
	ssFile="ssList.txt"
	delTrackLog="deleteTrack.log"

	echo "Fetch Snapshots to be deleted at `date`" >> ${delTrackLog}
}

setSnapshotCriteria()
{
	#Update below query to get required snapshot list
	mysql -e "select id, display_name, status from snapshots where status = 'deleted' order by created_at asc limit 3" \
	workloadmgr -Ns | sed 's/\t/,/g' > ${ssFile}
}

postLogging()
{
	echo "${ssFile} created with `wc -l ${ssFile}` snapshots to be deleted"
	cat ${ssFile} >> ${delTrackLog}
	echo "Fetched `wc -l ${ssFile}` records at `date`" >> ${delTrackLog}
	echo "" >> ${delTrackLog}
}

init
setSnapshotCriteria
postLogging

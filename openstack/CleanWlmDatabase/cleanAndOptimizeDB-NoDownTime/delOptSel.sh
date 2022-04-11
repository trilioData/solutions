#!/bin/bash
#set -x

if [ -z "$1" ]
then
	echo "File name not passed as argument; exiting"
	exit 1
fi

fileName=$1

iterations=80 #Currently not being used; if required, uncomment the lines having this variable and proceed
batchSize=10000
waitInSec=10
optimize="true"
database="workloadmgr"
mkdir -p LOGS

function logMsg() {
	#echo -e "`date +"%m/%d/%y %H:%M:%S"` : $1" 2<&1 | tee -a LOGS/${tableName}.log
	echo -e "`date +"%m/%d/%y %H:%M:%S"` : $1" 1>>LOGS/${tableName}.log 2>&1
}

grep -v -e '^#' -e '^$' ${fileName} | while read line
do
	echo $var | awk -F"FROM" '{print $2}' | cut -d" " -f2
	tableName=$(echo $line | awk -F"FROM" '{print $2}' | cut -d" " -f2)
	logMsg "Running Query $(echo $line | sed -e "s/#LIMIT#/${batchSize}/g")"
	totalDelRecs=0
	#for i in `seq 1 ${iterations}`
	for (( ; ; )) #Infinite loop to break only when ${batchSize} < actual number of records deleted
	do
		logMsg "\tDelete ${batchSize} records from ${tableName}"
		#mOut=$(mysql -e "$line limit ${batchSize}" ${database} -vv)
		mOut=$(mysql -e "$(echo $line | sed "s/#LIMIT#/${batchSize}/")" ${database} -vv)
		if [ $? != 0 ]
		then
			logMsg "\tCommand [ ${line} ] failing; Exiting !!"
			exit 1
		fi
		recCount=$(echo ${mOut} | awk '{print $(NF-3)}')
		logMsg "\tCurrently, ${recCount} Records deleted from ${tableName}"
		totalDelRecs=$( expr ${totalDelRecs} + ${recCount} )
		#if [ ${recCount} -le ${batchSize} ]
		if [ ${recCount} -eq 0 ]
		then
			logMsg "DELETE DONE FOR ${tableName}; EXITING DELETE LOOP !!"
			logMsg "Total ${totalDelRecs} records deleted from ${tableName}"
			break
		fi
		logMsg "\tWaiting for ${waitInSec} sec"
		sleep ${waitInSec}
	done
	
	if $optimize
	then
		for j in `seq 1 60`
		do
			syncStatus=$(mysql -e "SHOW STATUS LIKE 'wsrep%'" | grep wsrep_local_state_comment | awk '{print $2}')
			clusterSize=$(mysql -e "SHOW STATUS LIKE 'wsrep%'" | grep wsrep_cluster_size | awk '{print $2}')
			if [[ ${syncStatus} == "Synced" ]] || [ ${clusterSize} -eq 0 ]
			then
				logMsg "Cluster Synced"
				logMsg "Table Size Before: $(du -sh /var/lib/mysql/${database}/${tableName}.ibd)"
				logMsg "Start optimizing ${tableName}"
				mysql -e "optimize table ${tableName}" ${database}
				logMsg "Optimize done"
				logMsg "Table Size After: $(du -sh /var/lib/mysql/${database}/${tableName}.ibd)"
				logMsg "Waiting for ${waitInSec} sec"
				sleep ${waitInSec}
				break
			else
				logMsg "Cluster Not yet Synced"
			fi
			logMsg "Waiting 60 seconds for cluster sync, iteration $j"
			sleep 60
		done
	else
		logMsg "Skipping optimize for ${tableName}"
	fi
	logMsg "All Done for ${tableName}"
done
set +x

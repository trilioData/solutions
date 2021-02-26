#!/bin/bash

# This script is designed to provide CSV report for last/latest/running snapshot of all workloads in TVO and TVR environment.
# It will provide following fields in report
#'PROJECT_ID','WORKLOAD_ID','WORKLOAD_NAME','SNAPSHOT_ID','SNAPSHOT_NAME','VM_ID','VM_NAME','SNAPSHOT_TYPE','CREATED_AT','FINISHED_AT','STATUS','TIME_TAKEN','TVM_HOST','ERROR','UPLOADED_SIZE','BACKUP_SIZE','RESTORE_SIZE'
# Written By : Jayesh Chaudhari
# Date : 02/02/2021
# Last Updated : 26/02/2021

# Get date for filename to save
today=$(date '+%Y-%m-%d-%H:%M:%S')

# Fetch data directly from DB
mysql workloadmgr -e "
SELECT 'PROJECT_ID','WORKLOAD_ID','WORKLOAD_NAME','SNAPSHOT_ID','SNAPSHOT_NAME','VM_ID','VM_NAME','SNAPSHOT_TYPE','CREATED_AT','FINISHED_AT','STATUS','TIME_TAKEN','TVM_HOST','ERROR','UPLOADED_SIZE','BACKUP_SIZE','RESTORE_SIZE'
UNION ALL
SELECT
s1.project_id AS PROJECT_ID,
s1.workload_id AS WORKLOAD,
s4.display_name AS WORKLOAD_NAME,
s1.id AS SNAPSHOT_ID,
s1.display_name AS SNAPSHOT_NAME,
IFNULL(REPLACE(REPLACE(s3.vm_id,'\n',' '),'|',','),'N/A') as VM_ID,
IFNULL(REPLACE(REPLACE(s3.vm_name,'\n',' '),'|',','),'N/A') as VM_NAME,
s1.snapshot_type AS SNAPSHOT_TYPE,
s1.created_at AS CREATED_AT,
IFNULL(s1.finished_at,'N/A') AS FINISHED_AT,
s1.status AS STATUS,
IFNULL(s1.time_taken,'N/A') AS TIME_TAKEN,
s1.host as HOST,
IFNULL(REPLACE(REPLACE(s1.error_msg,'\n',''),'|',''),'N/A') AS ERROR,
s1.uploaded_size AS UPLOADED_SIZE,
s1.size AS BACKUP_SIZE,
s1.restore_size AS RESTORE_SIZE
FROM snapshots s1
INNER JOIN
(select
id,
workload_id,
max(created_at) as created_at
from snapshots
where status !='deleted'
group by workload_id) s2
ON s1.workload_id = s2.workload_id AND s1.created_at = s2.created_at 
INNER JOIN (select vm_id,vm_name,snapshot_id from snapshot_vms) s3 ON s2.id = s3.snapshot_id 
INNER JOIN (select id,display_name from workloads) s4 ON s1.workload_id = s4.id
INTO OUTFILE '/tmp/Trilio-Snapshot-Report-$today.csv'
FIELDS TERMINATED BY '|'
LINES TERMINATED BY '\n'
"

if [ $? -eq 0 ]; then
   echo "Completed"
   echo "Report : /tmp/Trilio-Snapshot-Report-$today.csv"
else
   echo "Failed"
fi

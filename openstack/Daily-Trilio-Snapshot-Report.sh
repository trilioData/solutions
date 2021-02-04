#!/bin/bash

# This script is designed to provide CSV report for last/latest/running snapshot of all workloads in environment.
# It will provide following fields in report
# 'PROJECT_ID','WORKLOAD_ID','SNAPSHOT_ID','SNAPSHOT_TYPE','CREATED_AT','FINISHED_AT','STATUS','TIME_TAKEN','ERROR','BACKUP_SIZE','RESTORE_SIZE'
# Written By : Jayesh Chaudhari
# Date : 02/02/2021

# Get date for filename to save
today=$(date '+%Y-%m-%d-%H:%M:%S')

# Fetch data directly from DB
mysql workloadmgr -e "
SELECT 'PROJECT_ID','WORKLOAD_ID','SNAPSHOT_ID','SNAPSHOT_TYPE','CREATED_AT','FINISHED_AT','STATUS','TIME_TAKEN','ERROR','UPLOADED_SIZE','BACKUP_SIZE','RESTORE_SIZE'
UNION ALL
SELECT
s1.project_id AS PROJECT_ID,
s1.workload_id AS WORKLOAD,
s1.id AS SNAPSHOT,
s1.snapshot_type AS SNAPSHOT_TYPE,
s1.created_at AS CREATED_AT,
IFNULL(s1.finished_at,'N/A') AS FINISHED_AT,
s1.status AS STATUS,
IFNULL(s1.time_taken,'N/A') AS TIME_TAKEN,
IFNULL(REPLACE(REPLACE(s1.error_msg,'\n',''),'|',''),'N/A') AS ERROR,
s1.uploaded_size AS UPLOADED_SIZE,
s1.size AS BACKUP_SIZE,
s1.restore_size AS RESTORE_SIZE
FROM snapshots s1
INNER JOIN
(select
workload_id,
max(created_at) as created_at
from snapshots
where status !='deleted'
group by workload_id) s2
ON s1.workload_id = s2.workload_id AND s1.created_at = s2.created_at
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

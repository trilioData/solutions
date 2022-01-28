workloadmgr Cleanup and table optimization
==========================================
Summary
-------
Current set of utilities/scripts should be used in case when physical deletion of logically deleted records from workloadmgr database required. Post physical deletion, to release the disk space from TVault appliance consumed by mysql ibd files, table optmization is required which is a time and resource consuming process.
Also this activity will require a downtime.
_**Note** : This utility can be run against any of the TVO releases_

Artifacts
---------
1. ReadMe.md : Steps to be followed for DB cleanup and disk optimization.
2. delStepByStep.sql : SQL script to add stored procedure cleanWLMDB to workloadmgr database. This procedure has the actual sql commands to do physical delete of records from tables.
3. getRecCounts.sh : This will create a file recCounts.txt having counts of records in tables as mentioned in tableList.txt without overwriting previous entries.
4. getFileSizes.sh : This will create a file filesizes-<NODE-NAME>.txt having sizes of datafiles against tables as mentioned in tableList.txt without overwriting previous entries.
5. tableList.txt : List of tables against which shell scripts will fetch stats regarding records count & table size on disk.

Pre-requisites:
--------------
1. Stop all snapshots/GJS.
2. Stop wlm-api, wlm-workloads on all nodes. Disable wlm-cron on primary.
3. Take WLM DB backup/dbdump OR TVM (all nodes) snapshot whichever feasible.
4. Please note that before doing this process, disk space on TVM (or the VM where DB resides) should have free space equivalent to 1.5 times of current workloadmgr DB size (Location : /var/lib/mysql/workloadmg). In case disk needs to be extended, VM reboot would be required; reference for the same below.
	Ref for reboot : https://docs.trilio.io/openstack/administration-guide/shutdown-restart-the-triliovault-cluster#restarting-the-complete-cluster-node-by-node 
5. Before starting cleanup, mariadb cluster should be in running state on all nodes and wlm services running without errors.
	mysql -e "SHOW STATUS LIKE 'wsrep%'" | grep -e wsrep_cluster_size -e wsrep_local_state_comment -e wsrep_incoming_addresses -e wsrep_local_state_uuid
6. If time & storage permit, take snapshot with increased disk sizes.
7. To check the system stability, start all wlm services and check logs. At this stage, all services & mysqldb should be working as usual.
8. Before moving ahead for cleaup & optimize, please stop all wlm services and disable GJS.
9. root user to be used for further DB operations from TrilioVault appliance.

Steps to cleanup and optimize storage on TVM:
---------------------------------------------
Assumption : wlm services & GJS are stopped, no snapshot/restore running.
1. Stop mysqld on node 2 & 3 one by one
	systemctl stop mysqld
	systemctl status mysqld
	Check on node 1 : mysql -e "SHOW STATUS LIKE 'wsrep%'" | grep -e wsrep_cluster_size -e wsrep_local_state_comment -e wsrep_incoming_addresses -e wsrep_local_state_uuid
2. Monitor mysql & wlm size on Node 1
	while [ 1 ];do date;expr 100 - `top -b -n 1 | grep  Cpu | awk '{print $8}' | cut -f 1 -d "."`;du -s /var/lib/mysql/workloadmgr/; echo "";mysql -e "SHOW STATUS LIKE 'wsrep%'" | grep -e wsrep_cluster_size -e wsrep_local_state_comment -e wsrep_incoming_addresses -e wsrep_local_state_uuid;sleep 5; done
3. Add clean up procedure to wlm DB.
	mysql workloadmgr < delStepByStep.sql
		This will add procedure cleanWLMDB to wlm DB.
4. Fetch & store Table Record & File size counts
	./getRecCounts.sh
	./getFileSizes.sh
5. Trigger clean up cmds/procedure from mysql prompt.
	call cleanWLMDB;
	Note : If timeout happens, please rerun the above command.
6. Start optimize set 1
	select now(); optimize table flowdetails, logbooks, snapshot_metadata, snapshots, snapshot_vm_metadata, snapshot_vms, tasks, task_status_messages, workload_metadata, workloads, workload_vm_metadata, workload_vms;select now();
7. Observe size change in monitoring command output; wait until the size reduction stops.
8. Start optimize set 2
	select now();optimize table vm_network_resource_snaps, snap_network_resources, vm_network_resource_snap_metadata, atomdetails, snap_network_resource_metadata, snapshot_vm_resources;select now();
9. Observe size change in monitoring command output; wait until the size reduction stops.
10. Start optimize set 3
	select now();optimize table snapshot_vm_resource_metadata, vm_security_group_rule_snap_metadata, vm_security_group_rule_snaps;select now();
11. Observe size change in monitoring command output; wait until the size reduction stops.
12. Fetch & store Table Record & File size counts
	./getRecCounts.sh
	./getFileSizes.sh
13. If time & storage permit, it's highly recommended to take node 1 snapshot/backup at this stage. In case further steps of mysql cluster sync fail, this snapshot can be used for recovery.
14. Start monitor command on node 2 & 3 as well.
15. Start mysql on node 2 only first and let the sync happen. Observe CPU utilization and wlm dir size reduction. Wait until it's nearly same as that of node 1.
16. Start mysql on node 3 and let the sync happen. Observe CPU utilization and wlm dir size reduction. Wait until it's nearly same as that of node 1 OR 2.
17. Fetch & store Table Record & File size counts on node 2 & 3 as well; for double check compare across all 3 nodes.
	./getRecCounts.sh
	./getFileSizes.sh
18. Start wlm services on all nodes, enable wlm-cron on primary
19. Create few snapshots for trials.

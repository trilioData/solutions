DELIMITER $$
CREATE OR REPLACE PROCEDURE cleanWLMDB()
BEGIN
DELETE 
FROM
	taskdetails 
WHERE
	state = "SUCCESS" 
	OR state = "REVERTED" 
	OR state = "FAILURE";

DELETE main 
FROM
	task_status_messages AS main,
	tasks AS sub 
WHERE
	main.task_id = sub.id 
	AND sub.STATUS = 'Done';

DELETE 
FROM
	tasks 
WHERE
	STATUS = "Done";

DELETE main 
FROM
	snap_network_resource_metadata AS main,
	snap_network_resources AS sub1,
	snapshots AS sub2 
WHERE
	main.snap_network_resource_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	snap_network_resources AS main,
	snapshots AS sub 
WHERE
	main.snapshot_id = sub.id 
	AND sub.deleted = 1;

DELETE main 
FROM
	vm_security_group_rule_snap_metadata AS main
	INNER JOIN vm_security_group_rule_snaps AS sub1
	INNER JOIN snapshot_vm_resources AS sub2
	INNER JOIN snapshots AS sub3 
WHERE
	main.vm_security_group_rule_snap_id = sub1.id 
	AND sub1.vm_security_group_snap_id = sub2.id 
	AND sub2.snapshot_id = sub3.id 
	AND sub3.deleted = 1;

DELETE main 
FROM
	vm_security_group_rule_snaps AS main
	INNER JOIN snapshot_vm_resources AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.vm_security_group_snap_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	vm_network_resource_snap_metadata AS main
	INNER JOIN vm_network_resource_snaps AS sub1
	INNER JOIN snapshot_vm_resources AS sub2
	INNER JOIN snapshots AS sub3 
WHERE
	main.vm_network_resource_snap_id = sub1.vm_network_resource_snap_id 
	AND sub1.vm_network_resource_snap_id = sub2.id 
	AND sub2.snapshot_id = sub3.id 
	AND sub3.deleted = 1;

DELETE main 
FROM
	vm_network_resource_snaps AS main
	INNER JOIN snapshot_vm_resources AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.vm_network_resource_snap_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	snapshot_vm_resource_metadata AS main
	INNER JOIN snapshot_vm_resources AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.snapshot_vm_resource_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	snapshot_vm_metadata AS main
	INNER JOIN snapshot_vms AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.snapshot_vm_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	snapshot_vms AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.snapshot_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	snapshot_metadata AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.snapshot_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	vm_disk_resource_snap_metadata AS main
	INNER JOIN vm_disk_resource_snaps AS sub1
	INNER JOIN snapshot_vm_resources AS sub2
	INNER JOIN snapshots AS sub3 
WHERE
	main.vm_disk_resource_snap_id = sub1.id 
	AND sub1.snapshot_vm_resource_id = sub2.id 
	AND sub2.snapshot_id = sub3.id 
	AND sub3.deleted = 1;

DELETE main 
FROM
	vm_disk_resource_snaps AS main
	INNER JOIN snapshot_vm_resources AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.snapshot_vm_resource_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	snapshot_vm_resources AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.snapshot_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	vm_recent_snapshot AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.snapshot_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	restore_metadata AS main
	INNER JOIN restores AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.restore_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	restored_vm_metadata AS main
	INNER JOIN restored_vms AS sub1
	INNER JOIN restores AS sub2
	INNER JOIN snapshots AS sub3 
WHERE
	main.restored_vm_id = sub1.id 
	AND sub1.restore_id = sub2.id 
	AND sub2.snapshot_id = sub3.id 
	AND sub3.deleted = 1;

DELETE main 
FROM
	restored_vms AS main
	INNER JOIN restores AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.restore_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	restored_vm_resource_metadata AS main
	INNER JOIN restored_vm_resources AS sub1
	INNER JOIN restores AS sub2
	INNER JOIN snapshots AS sub3 
WHERE
	main.restored_vm_resource_id = sub1.id 
	AND sub1.restore_id = sub2.id 
	AND sub2.snapshot_id = sub3.id 
	AND sub3.deleted = 1;

DELETE main 
FROM
	restored_vm_resources AS main
	INNER JOIN restores AS sub1
	INNER JOIN snapshots AS sub2 
WHERE
	main.restore_id = sub1.id 
	AND sub1.snapshot_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	restores AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.snapshot_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	workload_metadata AS main
	INNER JOIN workloads AS sub1 
WHERE
	main.workload_id = sub1.id 
	AND sub1.deleted = 1;

DELETE main 
FROM
	workload_vm_metadata AS main
	INNER JOIN workload_vms AS sub1
	INNER JOIN workloads AS sub2 
WHERE
	main.workload_vm_id = sub1.id 
	AND sub1.workload_id = sub2.id 
	AND sub2.deleted = 1;

DELETE main 
FROM
	workload_vms AS main
	INNER JOIN workloads AS sub1 
WHERE
	main.workload_id = sub1.id 
	AND sub1.deleted = 1;

DELETE 
FROM
	snapshots 
WHERE
	snapshots.deleted = 1;

DELETE main 
FROM
	workloads AS main
	INNER JOIN snapshots AS sub1 
WHERE
	main.id = sub1.workload_id 
	AND main.deleted = 1;

DELETE FROM RKDummy;

END $$
DELIMITER ;

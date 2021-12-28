## Summary

Current utility is created for enabling the physical deletion of selective snapshots (*and corresponding data along with respective metadata*) from the TrilioVault database.
    
## Artifacts

Utility consists of following artifacts:
1. fetchSS.sh : Shell script to fetch and store the list of snapshots which are to be physically deleted from TrilioVault Database.
2. snapshotDelete.sh : Shell script to physically delete the snapshots fetched and stored by fetchSS.sh


## Important points & pre-requisites

1. Since this utility does alteration of DB Schema definition and then a physical delete of the data, hence reverting of the change done is not possible. Hence, it's highly recommended, that if possible, a back up of *workloadmgr* database should be taken before proceeding ahead.

2. The shell scripts to be executed from TVault machine only; currently remote execution not feasible.

## Steps to create snapshot list

1. Edit DB select query present inside setSnapshotCriteria function in shell script fetchSS.sh as per the desired critieria.

2. Execute fetchSS.sh; post execution, respective snapshot IDs, names & statuses would be stored as csv format in ssList.txt in the same directory from where the script is executed.
    
    >   *./fetchSS.sh*

3. Corresponding log file will also be created in the same location.

    >   *Note: The utility assumes the mysql user/password are the default ones as set at Trilio appliance level; in case the same is modified by the customer, then respective select query in fetchSS.sh and delete query in snapshotDelete.sh should be modified accordingly to consider updated user id/password.*

## Validation
1. Manually check if ssList.txt has required data in format <SnapshotID>,<SnapshotName>,<SnapshotStatus>
    Eg. 233f86c3-fe0c-4496-ba4c-04a80d65fe94,5VMs-1GB-ParallelIncr,deleted

## Steps to delete snapshots from database

1. Execute snapshotDelete.sh shell script.

    >   *./snapshotDelete.sh*

3. All the required snapshots will be physically deleted from the database along with relevant data and related metadata, VMs mapping, security groups mapping, etc.

4. Corresponding log file will be created in the same location.

## Summary

Current utility is created for enabling the physical deletion of selective workloads (*and corresponding snapshots along with respective metadata*) from the TrilioVault database.
    
## Artifacts

Utility consists of following artifacts:
1. enablephysicaldelete.py : Python script to modify the definition of selective foreign keys so that physical deletion of interdependent data is feasible without major manual intervention. This script needs to be executed only once on any Tvault Machine.
2. workloads_delete.py : Python script to selectively delete workloads as provided by the user. This script is to be executed after execution of enablephysicaldelete.py is done. User can execute this multiple times, if need be.
3. config : This directory consistes of files connection.json and workloads_ids.txt. These are required to be populated by the user.


## Important points & pre-requisites

1. Since this utility does alteration of DB Schema definition and then a physical delete of the data, hence reverting of the change done is not possible. Hence, it's highly recommended, that if possible, a back up of *workloadmgr* database should be taken before proceeding ahead.

2. It is recommended to run the python scripts from TVault machine, however can be executed from  a remote CentOS VM as well provided the workloadmgr database on TVault machine is accessible remotely.

3. Execute following command to install required mysql-connector package

    > python install -r lib/requirement.txt
4. Provide valid details in config/connection.json.

**Note** : These details can be fetched from $HOME/.my.cnf file on TVault machine.

  > *user : User which has write access to database; preferably root.*
    
  > *password : DB password as present in $HOME/.my.cnf file*
    
  > *host : Can be localhost if executing script from TVault machine; else IP address of TVault machine if executing remotely.*
    
  > *database : Should be set as workloadmgr*

## Steps to enable physical delete

1. Execute enablephysicaldelete.py

    > *python enablephysicaldelete.py*
2. Post execution, respective keys' definition in tables will be modified.

3. Corresponding log files will be created in logs directory.

## Validation
1. Execute below mentioned command on TVault VM to ensure that physical deletion enabled.

    > mysql -e "SELECT  CONSTRAINT_NAME,  DELETE_RULE,  TABLE_NAME  FROM information_schema.REFERENTIAL_CONSTRAINTS where REFERENCED_TABLE_NAME = 'workloads' and TABLE_NAME = 'snapshots' " -Ns

    > **Expected output below**
    
    > snapshots_ibfk_1        CASCADE snapshots


## Steps to delete workloads from database

1. Provide ids of workloads which are to be deleted (*physically*) from the database in config/workload_ids.txt file.  

2. Execute workloads_delete.py script.

    >   *python workloads_delete.py*
3. All the required workloads will be physically deleted from the database along with respective snapshots and related metadata, VMs mapping, etc.

4. Corresponding log files will be created in logs directory.

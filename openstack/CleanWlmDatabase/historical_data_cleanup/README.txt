Workflow :
1. will loop through database from bottom to top sequence in terms of dependency
2. fetch records in batch size which needs to be deleted
3. write those records primary key in files
4. run delete on records written in file

FILEs:
1. DeleteHistoricalRecords.py : Main script to delete records from database
2. tableList.txt : List of tables in bottom to top sequence in terms of dependency
3. select_queries directory : Directory have files with all table names having select queries
4. delete_queries directory : Directory have files with all table names having delete queries
5. recordsToBeDeleted directory : Records which will be needed to delete will be written in files under this directory
6. getRecCounts.sh : script to get records from all table
7. getFileSizes.sh : script to get database size
8. fileList.txt : this file contain list of tables used by above 2 scripts
9. deleterecords.service : DeleteHistoricalRecords.py can be run as python script using this file(currently not working)

Usage :

[root@tvm1 historical_data_cleanup]# source /home/stack/myansible/bin/activate
(myansible) [root@tvm1 historical_data_cleanup]# python DeleteHistoricalRecords.py
...
(myansible) [root@tvm1 historical_data_cleanup]#


LOGS:
1. Logs directory will be created under current directory
2. It will Log all the events and queries


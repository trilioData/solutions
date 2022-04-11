Artifacts
=========
1. 28 Text files having table wise DELETE queries. Files numbered from 01 to 28; to be taken up for execution in same order manually.
2. delOptSel.sh : Shell script to be executed against each table file.
3. getRecCounts.sh : This will create a file recCounts.txt having counts of records in tables as mentioned in tableList.txt without overwriting previous entries.
4. getFileSizes.sh : This will create a file filesizes-<NODE-NAME>.txt having sizes of datafiles against tables as mentioned in tableList.txt without overwriting previous entries.
5. tableList.txt : tableList.txt : List of tables against which shell scripts will fetch stats regarding records count & table size on disk.

Details
=======
1. Parameters
	a. batchSize : Maximum records which can be deleted from any table in single loop. Default value is 10000.
	b. database : DB from which cleanup required. Default value is workloadmgr
	c. waitInSec : After every delete operation, allowing sometime for mysql to sync. Default value is 10 sec.
	d. optimize : To be true of false. Table optimization happens if it is set to true. Default value is true.	
2. Above parameters to be set inside shell script delOptSel.sh.
3. Workflow:
	a. Script delOptSel.sh proceeds for reading the input file (passed as argument) and replaces #LIMIT# by the pre defined limit. 
	b. Then the DELETE command as specified in the input file is executed on DB with limit.
	c. A loop runs which executes DELETE command until there are 0 eligible records left to be deleted.
	d. Next if optimize is set to true, the script checks galera sync status.
	e. If the nodes are not in sync, it waits and keeps checking every 1 min for maximum 60 min.
	f. If until 1 hour also, the galera sync isn't successful, the script timesout without doing optimize. In such case, optimize to be handled manually post DB sync is successful.
	g. If within 1 hour the galera sync is successful, the optimize starts and script exits once the operation is over.
4. Logging : The script writes all LOG statements to a log file in LOGS directory created in the same folder as that of the script; 1 log file per table.
5. Execution command : nohup ./delOptSel.sh <fileName> &
	a. Sample : nohup ./delOptSel.sh 01-taskdetails &
6. Same command as above to be repeated for each of 28 files in order.
7. If required to forcefully stop, we would need to kill the PID against delOptSel process when log shows message of "waiting for 20 sec".
8. Please ensure to run script against every table file in order of prefixed number. Also proceed for next file only after previous one is complete. On complete Execution of any file, respective log file will show message as "All Done for <table Name>"
9. Note : It's recommended to take the VM snapshot before proceeding before start of current clean up activity. Also, please fetch the table record counts and table file sizes (execute getRecCounts.sh & getFileSizes.sh) before starting of current execution.
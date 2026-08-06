import os
import time
import configparser
import re
import mysql.connector

# Get records to be deleted using select query
# Write those records into file
# Run delete on those records

batchSize=1000

# check if log directory is present, if not create one
LOG_DIR="./LOGS"
if not os.path.exists(LOG_DIR):
   os.mkdir(LOG_DIR)

# Create Logfile
timestr = time.strftime("%Y%m%d-%H%M%S")
LOG_FILE_NAME="deletehistoricalrecord-" + timestr + ".log"
LOG_FILE_PATH=LOG_DIR + "/" + LOG_FILE_NAME
logfile = open(LOG_FILE_PATH,"w")

# DB connection 
## Grab fields from the conf file
config = configparser.ConfigParser()
config.read('/etc/workloadmgr/workloadmgr.conf')
mysql_conn = config['DEFAULT']['sql_connection']
db_string = re.split('mysql://|=|@|/|:|\?', mysql_conn)

## Edit these 4 variable manually if you want to change any of them
db_user = db_string[1]
db_pass = db_string[2]
db_host = db_string[3]
db_db = db_string[4]

my_connect = mysql.connector.connect(user=db_user, password=db_pass, host=db_host, database=db_db, connection_timeout=600 )
# Set mysql connection timeout to 10 min
cursor = my_connect.cursor(dictionary=True)


def getRecords(batchSize):
    try:
       filepath="./select_queries/{}".format(table)
       tablename = open(filepath,"r")
       #print(tablename)
       query=tablename.readline()
       tablename.close()
       record_count=1
       while record_count > 0:
          print('\n\nGetting records from {}'.format(table))
          logfile.write("Getting records from " + table)
          query=query.replace("#LIMIT#",str(batchSize))
          print("Running query : {}".format(query))
          logfile.write("\nRunning Query : \n" + query)
          try:
             cursor.execute(query)
             result=cursor.fetchall()
             record_count=len(result)
             writeRecords(result)
          except:
             print("Exception occured while running SELECT query : \n {}".format(query))
             logfile.write("\nException occured while running SELECT query : \n" + query)
             record_count=1
    except IOError:
       print('File for table {} not present'.format(table))
       logfile.write("\nIOError while getting records")

def writeRecords(data):
    print('\nWritting records to be deleted from table {}'.format(table))
    logfile.write("\nWritting records to be deleted from table "+ table)
    try:
       filepath="./recordsToBeDeleted/{}".format(table)
       f = open(filepath,"w")
       for x in data:
         for i in x.values(): 
            f.writelines(i+"\n")
            #print(i)
       f.close()
       deleteRecords()
    except IOError:
       print('File for table {} not present'.format(table))
       logfile.write("\nIOError while writting records to file")

def deleteRecords():
    print('\nDeleting records from table {}'.format(table))
    logfile.write("\nDeleting records from table "+ table)
    try:
       filepath="./recordsToBeDeleted/{}".format(table)
       f = open(filepath,"r+")
       records=f.read().splitlines()
       filepath2="./delete_queries/{}".format(table)
       f2 = open(filepath2,"r")
       delete_query=f2.readline()
       delete_query=delete_query.replace("#IDs",'\',\''.join(records))
       print(delete_query)
       logfile.write("\nExecuting :\n" + delete_query)
       try:
          cursor.execute(delete_query)
          my_connect.commit()
       except:
          print("Exception occured while deleteing records. \n Query : {}".format(delete_query))
       #for i in records:   #if records needs to delete one by one use this
       #    print(delete_query.replace("#IDs",i))
       f.close()
       f2.close()
    except IOError:
       print('File for table {} not present'.format(table))
       logfile.write("\nIOError while deleting records")


file = open("tableList.txt")
data=file.read().splitlines()

for table in data:
    #print(table)
    logfile.write("\n-----------------------------------------------------\nTable : " + table + "\n")
    getRecords(batchSize)

file.close()
cursor.close()
my_connect.close()
logfile.close()

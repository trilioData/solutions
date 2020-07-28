import argparse
import mysql.connector
import configparser
import datetime
import os
import pickle

config = configparser.ConfigParser()
config.read('/etc/workloadmgr/workloadmgr.conf')


db_url = config['DEFAULT']['sql_connection']
user = db_url.split("//")[1].split(":")[0]
password = db_url.split("@")[0].split(":")[-1]
host = db_url.split("@")[1].split("/")[0]
database = db_url.split("/")[-1].split("?")[0]

mydb = mysql.connector.connect(
  host=host,
  user=user,
  passwd=password,
  database=database
)

def check_dir(directory):
    if not os.path.isdir(directory):
        return False
    return True

def print_delimeter(file):
    file.write("\n")
    file.write("#"*70+"\n")

def get_workloads():
    mycursor = mydb.cursor()
    mycursor.execute("select id, display_name, jobschedule from workloads where deleted=0;")
    myresult = mycursor.fetchall()
    workloads = []
    for row in myresult:
        workload_details = {}
        workload_details["id"]=row[0]
        workload_details["name"]=row[1]
        workload_details["jobschedule"]=pickle.loads(bytes(row[2].encode()))
        workloads.append(workload_details)
    return workloads

def get_current_date():
    now = datetime.datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H:%M:%S")
    return dt_string

def get_schedule(report, jobschedule):
    report.write("Schedule: \n")
    for k,v in jobschedule.items():
        report.write(" "*10+"%s:%s\n"%(k,v))

def get_protected_vms(workload_report, workload_id):
    mycursor = mydb.cursor()
    mycursor.execute("select vm_name from workload_vms where deleted=0 and workload_id='%s';"%(workload_id))
    myresult = mycursor.fetchall()
    workload_report.write("Protected VMs:\n")
    for row in myresult:
        workload_report.write(" "*10+"%s\n"%(row[0]))

def snapshot_details(workload_report, workload_id):
    workload_report.write("Snapshot details:\n")
    workload_report.write("Snapshot_id, Start time, End time, Status, Error message\n")

    mycursor = mydb.cursor()
    mycursor.execute("SELECT id,created_at,finished_at, status, error_msg from snapshots where deleted=0 and workload_id ='%s' and created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR);"%(workload_id))
    myresult = mycursor.fetchall()
    for row in myresult:
        workload_report.write("%s,%s,%s,%s,%s"%(row[0],row[1],row[2],row[3],row[4]))




if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", help="Specify output directory where reports should go",default="/home/stack")
    args = parser.parse_args()
    directory_path = args.output_dir
    status = check_dir(directory_path)
    if not status:
        print("Provided directory path is invalid or not present.")
    else:
        workloads = get_workloads()
        for workload in workloads:
            report_file_name = "Workload_Report-%s-%s-%s.txt" %(workload['id'],workload['name'],get_current_date())
            report_file_name = os.path.join(directory_path, report_file_name)

            workload_report = open(report_file_name, "w")
            print_delimeter(workload_report)
            workload_report.write(" " * 4 + "Report generated on %s for workload %s" % (get_current_date(),workload['id']))
            print_delimeter(workload_report)
            get_schedule(workload_report,workload['jobschedule'])
            print_delimeter(workload_report)
            get_protected_vms(workload_report, workload['id'])
            print_delimeter(workload_report)
            snapshot_details(workload_report, workload['id'])
            print_delimeter(workload_report)
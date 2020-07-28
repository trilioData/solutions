import argparse
import base64
import os
import logging
import datetime
import ovirtsdk4 as sdk
import configparser
import mysql.connector

logging.basicConfig(level=logging.DEBUG, filename='example.log')
config = configparser.ConfigParser(interpolation=None)
config.read('/etc/workloadmgr/workloadmgr.conf')

rhv_connection = sdk.Connection(
    url=str(config['ovirt_authtoken']['rhv_auth_url']+"/api"),
    username=str(config['ovirt_authtoken']['rhv_username']),
    password=base64.b85decode(config['ovirt_authtoken']['rhv_password']).decode("utf-8"),
    insecure=True,
    ca_file="",
)

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

def get_rhv_vms():
    vms_service = rhv_connection.system_service().vms_service()
    vms = vms_service.list()
    return vms

def get_protected_vms():
    mycursor = mydb.cursor()
    mycursor.execute("select vm_id from workload_vms where deleted=0;")
    myresult = mycursor.fetchall()
    vm_ids = []
    for row in myresult:
      vm_ids.append(row[0])

    return vm_ids
def get_current_date():
    now = datetime.datetime.now()
    dt_string = now.strftime("%d-%m-%Y-%H:%M:%S")
    return dt_string

def print_delimeter(file):
    file.write("\n")
    file.write("#"*70+"\n")

def get_workloads():
    mycursor = mydb.cursor()
    mycursor.execute("select id, display_name from workloads;")
    myresult = mycursor.fetchall()
    workload_details = {}
    for row in myresult:
        workload_details[row[0]]=row[1]
    return workload_details


def get_snapshots(TVM_report):
    successful_snapshots_count = 0
    failed_workloads = []
    mycursor = mydb.cursor()
    mycursor.execute("SELECT id, workload_id, status from snapshots where deleted=0  and created_at > DATE_SUB(NOW(), INTERVAL 24 HOUR)")
    myresult = mycursor.fetchall()
    total_snapshots = len(myresult)

    TVM_report.write("Number of Snapshots last 24h  : %s" % (total_snapshots))
    print_delimeter(TVM_report)

    for row in myresult:
        if row[2]!="available":
            failed_workloads.append(row[1])

    TVM_report.write("Number of successful Snapshots last 24h  : %s" % (total_snapshots-len(failed_workloads)))
    print_delimeter(TVM_report)
    TVM_report.write("Number of failed Snapshots last 24h  : %s" % (len(failed_workloads)))
    print_delimeter(TVM_report)

    workload_details = get_workloads()
    TVM_report.write("Failed workloads in last 24h..\n")
    if not failed_workloads:
        TVM_report.write("None")
    for failed_workload in failed_workloads:
        TVM_report.write("%s:%s\n"%(failed_workload,workload_details[failed_workload]))
    print_delimeter(TVM_report)



if __name__== "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output_dir", help="Specify output directory where reports should go",default="/home/stack")
    args = parser.parse_args()
    directory_path = args.output_dir
    status = check_dir(directory_path)
    if not status:
        print("Provided directory path is invalid or not present.")
    else:

        report_file_name = "TVM_Overall_Backup_Report-%s.txt" %(get_current_date())
        report_file_name=os.path.join(directory_path,report_file_name)
        TVM_report = open(report_file_name, "w")
        print_delimeter(TVM_report)
        TVM_report.write(" "*4 +"Report generated on %s" % (get_current_date()))
        print_delimeter(TVM_report)
        TVM_report.write("VMs existing: %s" % (len(get_rhv_vms())))
        TVM_report.write("\nVMs protected: %s" % (len(get_protected_vms())))
        print_delimeter(TVM_report)
        get_snapshots(TVM_report)

#!/bin/bash
set +x
export OS_DOMAIN_ID=default
export OS_TENANT_ID=723aa12337a44f818b6d1e1a59f16e49

days=1
lines=5

if [ $1 ]
then
   days=$1
else
   echo "Usage $0 <number of days>"
   echo
   echo "Defaulting to last one day"
fi

if [ $2 ]
then
   lines=$2
else
   echo "Usage $0 <number of days> <number of lines>"
   echo
   echo "Defaulting to 5 lines"
fi

echo "Snapshots that failed in the last $days days:"
echo "============================================="
for i in `workloadmgr snapshot-list --all True | egrep "error" | grep -v ID | grep -v Created | grep -v '\-\-\-' | awk -F'| *' '{printf "%s;%s;%s\n",$2,$6,$8}' | tail -n $lines`
do
   created_at=`python -c "print('$i'.split(';')[0])"`

   msg=`python -c "
from datetime import datetime
from datetime import timedelta

datetime_object = datetime.strptime('$created_at', '%Y-%m-%dT%H:%M:%S.000000');
delta = datetime.utcnow() - datetime_object;
if delta.days <= $days:
    print('Snapshot')
"`

   ctime=`python -c "
from datetime import datetime

datetime_object = datetime.strptime('$created_at', '%Y-%m-%dT%H:%M:%S.000000');
print(datetime_object)
"`

if [ $msg ]
then
   snap_id=`python -c "print('$i'.split(';')[1])"`
   workload_id=`python -c "print('$i'.split(';')[2])"`
   snap_err_msg=`workloadmgr snapshot-show $snap_id| grep error_msg | awk -F'|' '{print $3}'`
   workload_project_id=`workloadmgr workload-show $workload_id| grep project_id | awk -F'|' '{print $3}' | awk '{print $1}'`
   workload_domain_id=`openstack project show $workload_project_id | grep domain_id | awk '{print $4}'`
   workload_project_name=`openstack project show $workload_project_id | grep name | awk '{print $4}'`
   workload_domain_name=`openstack domain show $workload_domain_id | grep name | awk '{print $4}'`
   hypervisors=""
   for i in `workloadmgr snapshot-show $snap_id | grep ID | awk -F'|' '{print $3}' | xargs`
   do
      h=`openstack server show $i | grep hypervisor | awk -F'|' '{print $3}' | xargs`
      hypervisors=$h,$hypervisors
   done 
   echo "Snapshot $snap_id created at $ctime of workoad $workload_id in project $workload_project_id($workload_project_name:$workload_domain_id) erred with '$snap_err_msg.'. Instances are running on hypervisors: $hypervisors"
fi

done
echo "============================================="


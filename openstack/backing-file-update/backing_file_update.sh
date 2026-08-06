#!/bin/bash

# How to use: Checkout README file

declare -a qcow2list
LOG_FILE=/tmp/backing_file_update.log

if [ $# -lt "1" ]; then
  echo "Usage: $0 /var/lib/nova/triliovault-mounts/<base64>/workload_<workload_id>"
  exit 1;
fi

new_mount_path=$1
echo 'Entered location: ' $new_mount_path
# Trim the path
new_mount_path=`echo $new_mount_path | xargs`
# Remove path separator from end
new_mount_path=`echo $new_mount_path | sed 's/\/$//'`

if [ ! -d  $new_mount_path ]; then
  echo the directory $new_mount_path does not exist!
  exit 1
fi

workload_db_path="$new_mount_path/workload_db"
if [ ! -f "$workload_db_path" ]; then
  echo workload_db file $workload_db_path does not exist!
  exit 1
fi

# check if workload is encrypted and fetch the secret_uuid for same. ask user for payload
is_encrypted=`cat $workload_db_path | python3 -c "import json,sys;obj=json.load(sys.stdin);print(obj.get('encryption'));"`
if [ "$is_encrypted" == "True" ]; then
  secret_uuid=`cat $workload_db_path | python3 -c "import json,sys;obj=json.load(sys.stdin);print(obj.get('secret_uuid'));"`
  echo Please provide the --payload for the secret_uuid used in the workload:
  read payload
  echo "is_encrypted: $is_encrypted secret_uuid: $secret_uuid payload: $payload"
fi

# Get the list of qcow2 images
for i in `find $new_mount_path -type f`
do
    qemu-img info $i | grep format | grep qcow2 &> /dev/null
if [ $? = 0 ]; then
  qcow2list+=($i)
fi
done

# Update backing file path for all Qcow2 images
for qcow_file_path in ${qcow2list[@]}
do
  echo -e "\n-----------------------------------------------------------"
  echo "Processing: " $qcow_file_path

  if [ "$is_encrypted" == "True" ]; then
    # fetching backing file for encrypted workloads
    backing_cipher_json=`qemu-img info $qcow_file_path | grep "backing\ file:" | sed 's/.*json://'`
    current_backing_file=''
    if [ ! -z "$backing_cipher_json" ]
    then
	    current_backing_file=`echo $backing_cipher_json | python3 -c "import json,sys;obj=json.load(sys.stdin);print(obj['file']['filename']);"`
    fi
  else
    current_backing_file=`qemu-img info $qcow_file_path | grep "backing\ file:" | cut -f3 -d' '`
  fi

  if [ ! -z $current_backing_file ]
  then
    qcow2_file_to_rebase=$qcow_file_path

    new_backing_file="${new_mount_path%/*}/workload_"`echo ${current_backing_file} | sed 's/.*workload_//g'`
    echo -e "\n\n$(date)  \nRebasing Qcow2 image: $qcow_file_path\n\nold_backing_file_path: $current_backing_file\n\nnew_backing_file: $new_backing_file" >>$LOG_FILE

    if [ "$is_encrypted" == "True" ]; then
      backing_json="json:{\"encrypt.key-secret\":\"sec0\",\"driver\":\"qcow2\",\"file\":{\"driver\":\"file\",\"filename\":\"`echo ${new_backing_file}`\"}}"
      qemu-img rebase --object secret,id=sec0,data=$payload --image-opts driver=qcow2,encrypt.key-secret=sec0,encrypt.format=luks,file.filename=$qcow_file_path -b $backing_json
    else
      qemu-img rebase -u -F qcow2 -b $new_backing_file $qcow2_file_to_rebase
    fi

    echo -e "\nNew backing file: " $new_backing_file
  else
    echo -e "\nNo backing file found for image: $qcow_file_path, skipping rebasing" >>$LOG_FILE
  fi
done


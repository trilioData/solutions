
w to use: Checkout README file

declare -a qcow2list
LOG_FILE=/tmp/backing_file_update.log

if [ $# -lt "1" ]; then
  echo "Usage: $0 /var/triliovault-mounts/<base64>/workload_<workload_id>"
  exit 1;
fi

new_mount_path=$1
echo 'Entered location: ' $new_mount_path
# Trim the path
new_mount_path=`echo $new_mount_path | xargs`
# Remove path separator from end
new_mount_path=`echo $new_mount_path | sed 's/\/$//'`

if [ ! -d  $new_mount_path ]; then
  echo the directory does not exist!
  exit 1
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
  current_backing_file=`qemu-img info $qcow_file_path | grep "backing\ file:" | cut -f3 -d' '`
  if [ ! -z $current_backing_file ]
  then
    qcow2_file_to_rebase=$qcow_file_path
    new_backing_file="${new_mount_path%/*}/workload_"`echo ${current_backing_file} | sed 's/.*workload_//g'`
    echo -e "\n\n$(date)  \nRebasing Qcow2 image: $qcow_file_path\n\nold_backing_file_path: $current_backing_file\n\nnew_backing_file: $new_backing_file" >>$LOG_FILE
    qemu-img rebase -u -b $new_backing_file $qcow2_file_to_rebase
    echo -e "\nNew backing file: " $new_backing_file
  else
    echo -e "\nNo backing file found for image: $qcow_file_path, skipping rebasing" >>$LOG_FILE
  fi
done


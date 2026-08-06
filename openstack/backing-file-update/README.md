# Tvault Appliance NFS share migration

## Steps: (backing_file_update)

1. reinitialize the TVM and reconfigure with new NFS share device
2. after successful configuration verify that new NFS is mounted on TVM
3. **On compute:**
    1. configure data mover to add new NFS share
    2. update config _'vault_storage_nfs_export'_ value in _/etc/tvault-contego/tvault-contego.conf_ on compute (the device_name)
    3. restart tvault-contego service
    4. make sure all compute nodes sees both NFS shares
4. **On TVM:** with nova user (_`su nova`_)
    1. copy all the workloads directories to new NFS
        (/var/triliovault-mounts/<current-base64>/workload_* --> /var/lib/nova/triliovault-mounts/<new-base64>/workload_*)
    2. run the backing_file_update.sh script for all the workloads with new location (with nova user)
5. run workload import through CLI: (_`workloadmgr importworkloads`_)

## Usage:
_`./backing_file_update.sh /var/triliovault-mounts/<base64>/workload_<workload_id>`_
- `/var/lib/nova/triliovault-mounts/<base64>` is mounted NFS after reconfigure
- `<workload_id>` is the workload id to process (copied one)
- **Note:** In case of encrypted workloads, the user must have the payload of the secret used in the workload. The script will ask for payload for rabasing backup chain.

## Logs:
- Logs can be found at location `/tmp/backing_file_update.log`
- Please note that logs are in append mode for each time the script is run

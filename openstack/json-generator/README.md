# Restore JSON Generator Tool

## Table of Contents
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Arguments](#arguments)
- [Example](#example)

## Prerequisites
This tool requires communication with OpenStack and Workloadmgr services to fetch information about the Snapshot and related information.
So the user needs to export the OpenStack RC file before running this script, which should include below environment variables:

- `OS_AUTH_URL`
- `OS_USERNAME`
- `OS_PASSWORD`
- `OS_PROJECT_NAME`
- `OS_USER_DOMAIN_NAME`
- `OS_PROJECT_ID`
- `OS_PROJECT_DOMAIN_ID`

Additionally, make sure to execute this script where **workloadmgr-client** is installed to avoid dependency installation.

## Description
This tool is designed to generate a JSON file based on the restore operation types (selective/in-place), which can then be utilized with the CLI commands for selective and in-place restores.
The generated JSON may also need the user's intervention to verify the mappings of the source and target resources.
Hence, it is advised to check the mapping as per the requirement and then use it for the restore operation.

Checkout the CLI commands for restore operation at https://docs.trilio.io/openstack/user-guide/restores#selective-restore

## Usage
```bash
python3 restore_json_generator.py -h
```

```bash
python3 restore_json_generator.py -h
usage: JsonGenerator [-h] [--restore_type {selective, inplace}] <snapshot_id>

Generates the restore.json file, required for executing a Selective / Inplace
restore operation.

positional arguments:
  <snapshot_id>         Id of workload snapshot.

optional arguments:
  -h, --help            show this help message and exit
  --restore_type {selective, inplace}
                        Specify whether to generate JSON for selective restore
                        or inplace restore. The default behavior is to
                        generate JSON for selective restore. Set this field to
                        'inplace' if you want to generate JSON for inplace
                        restore.

```

## Command
```bash
python3 restore_json_generator.py [--restore_type {selective, inplace}] <snapshot_id>
```

## Arguments

### Positional Arguments

**<snapshot_id>**: Id of the workload snapshot.

### Optional Arguments

**-h, --help**: Show the help message and exit.

**--restore_type {selective, inplace}**: Specify whether to generate JSON for selective restore or in-place restore. The default behavior is to generate JSON for selective restore. Set this field to 'inplace' if you want to generate JSON for in-place restore.

## Output/Result
After successful execution, the tool will create a new JSON file in the current working directory with a file name format `<snapshot-id>-<restore-type>.json` 

## Example
```bash
python3 restore_json_generator.py --restore_type selective 7dee5340-2479-4a37-8fdc-60318c9c223f
```
This will generate the **7dee5340-2479-4a37-8fdc-60318c9c223f-selective-restore.json** file for a selective restore operation for the workload snapshot with ID 7dee5340-2479-4a37-8fdc-60318c9c223f.

```bash
python3 restore_json_generator.py --restore_type inplace 7dee5340-2479-4a37-8fdc-60318c9c223f
```
This will generate the **7dee5340-2479-4a37-8fdc-60318c9c223f-inplace-restore.json** file for an in-place restore operation for the workload snapshot with ID 7dee5340-2479-4a37-8fdc-60318c9c223f.

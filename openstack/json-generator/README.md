# Restore Json Generator Tool

## Table of Contents
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Arguments](#arguments)
- [Example](#example)

## Prerequisites
Before running this tool, ensure that the OpenStack RC file includes the necessary environment variables listed below:

- `OS_AUTH_URL`
- `OS_USERNAME`
- `OS_PASSWORD`
- `OS_PROJECT_NAME`
- `OS_USER_DOMAIN_NAME`
- `OS_PROJECT_ID`
- `OS_PROJECT_DOMAIN_ID`

Additionally, make sure to execute this script where **workloadmgr-client** is installed.

## Description
This tool is designed to generate a `restore.json` file required for executing a Selective/Inplace restore operation.

## Usage
```bash
python3 restore_json_generator.py -h
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

**--restore_type {selective, inplace}**: Specify whether to generate JSON for selective restore or inplace restore. The default behavior is to generate JSON for selective restore. Set this field to 'inplace' if you want to generate JSON for inplace restore.


## Example
```bash
python3 restore_json_generator.py --restore_type selective 7dee5340-2479-4a37-8fdc-60318c9c223f
```
This will generate the **7dee5340-2479-4a37-8fdc-60318c9c223f-selective-restore.json** file for a selective restore operation for the workload snapshot with ID 7dee5340-2479-4a37-8fdc-60318c9c223f.

```bash
python3 restore_json_generator.py --restore_type inplace 7dee5340-2479-4a37-8fdc-60318c9c223f
```
This will generate the **7dee5340-2479-4a37-8fdc-60318c9c223f-inplace-restore.json** file for an inplace restore operation for the workload snapshot with ID 7dee5340-2479-4a37-8fdc-60318c9c223f.

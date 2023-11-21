# Restore JSON Generator Tool

## Table of Contents
- [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Arguments](#arguments)
- [Output](#output)
- [Examples](#examples)

## Prerequisites
- This tool supports T4O with versions 4.2.x onwards
- This tool requires communication with OpenStack and Workloadmgr services to fetch information about the Snapshot and related information.
So the user needs to export the OpenStack RC file before running this script, which should include below environment variables:
  - `OS_AUTH_URL`
  - `OS_USERNAME`
  - `OS_PASSWORD`
  - `OS_PROJECT_NAME`
  - `OS_USER_DOMAIN_NAME`
  - `OS_PROJECT_ID`
  - `OS_PROJECT_DOMAIN_ID`

- Additionally, make sure to execute this script where **workloadmgr-client** is installed to avoid dependency installation.

## Description
This tool is designed to generate a JSON file based on the restore operation types (selective/in-place), which can then be utilized with the CLI commands for selective and in-place restores.
The generated JSON may also need the user's intervention to verify the mappings of the source and target resources.
Hence, it is advised to check the mapping as per the requirement and then use it for the restore operation.

Check out the CLI commands for restore operation at https://docs.trilio.io/openstack/user-guide/restores

## Usage
```bash
python3 restore_json_generator.py -h
```

```bash
usage: JsonGenerator [-h] [--restore-type {selective, inplace}] [--show-json-mapping <restore_json_file>] <snapshot_id>

Generates the restore.json file, required for executing a Selective / Inplace restore operation.

positional arguments:
  <snapshot_id>         Id of workload snapshot.

optional arguments:
  -h, --help            show this help message and exit
  --restore-type {selective, inplace}
                        Specify whether to generate JSON for selective restore or in-place restore. The default behavior is to generate JSON for selective restore. Set this field to 'inplace' if you want to generate JSON for inplace restore.
  --show-json-mapping <restore_json_file>
                        Display the JSON mapping if you've already created a JSON file. It requires a JSON file pre-created for the restore operation.

```

## Command
```bash
python3 restore_json_generator.py [--restore-type {selective, inplace}] [--show-json-mapping <restore_json_file>] <snapshot_id>
```

## Arguments

### Positional Arguments

**<snapshot_id>**: Id of the workload snapshot.

### Optional Arguments

**-h, --help**: Show the help message and exit.

**--restore-type {selective, inplace}**: Specify whether to generate JSON for selective restore or inplace restore. The default behavior is to generate JSON for selective restore. Set this field to 'inplace' if you want to generate JSON for inplace restore.

**--show-json-mapping <restore_json_file>**: Display the JSON mapping if you've already created a JSON file. It requires a JSON file pre-created for the restore operation.

## Output
- To generate a new JSON file for a particular restore type, the user needs to run the command without `--show-json-mapping`.
After successful execution, the tool will create a new JSON file in the current working directory with a file name format `<snapshot-id>-<restore-type>.json` 

- To display the mapping information from an existing JSON file, the user needs to run the command with `--show-json-mapping` and the JSON file path.
After successful execution, the tool will show the mapping information in a tabular format.

## Examples
```bash
python3 restore_json_generator.py --restore-type selective 7dee5340-2479-4a37-8fdc-60318c9c223f
#or
#python3 restore_json_generator.py 7dee5340-2479-4a37-8fdc-60318c9c223f

```
This will generate the `7dee5340-2479-4a37-8fdc-60318c9c223f-selective-restore.json` file for a selective restore operation for the workload snapshot with ID `7dee5340-2479-4a37-8fdc-60318c9c223f`.

```bash
python3 restore_json_generator.py --restore-type inplace 7dee5340-2479-4a37-8fdc-60318c9c223f

```
This will generate the `7dee5340-2479-4a37-8fdc-60318c9c223f-inplace-restore.json` file for an in-place restore operation for the workload snapshot with ID `7dee5340-2479-4a37-8fdc-60318c9c223f`. 

```bash
python3 restore_json_generator.py --show-json-mapping ./7dee5340-2479-4a37-8fdc-60318c9c223f-selective-restore.json 7dee5340-2479-4a37-8fdc-60318c9c223f

```
This will display the mapping information for restoring the snapshot with ID `7dee5340-2479-4a37-8fdc-60318c9c223f` by reading the existing JSON `7dee5340-2479-4a37-8fdc-60318c9c223f-selective-restore.json` file.

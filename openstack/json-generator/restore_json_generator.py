import argparse
import os
import json
import ipaddress
from openstack import connection
import workloadmgrclient
import workloadmgrclient.v1.client as wlmclient
from pkg_resources import packaging
import multiprocessing
from prettytable import PrettyTable, ALL

def openstack_client():
    try:
        osclient = connection.Connection(
            auth_url=os.environ.get('OS_AUTH_URL'),
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            project_name=os.environ.get('OS_PROJECT_NAME'),
            domain_id=os.environ.get('OS_PROJECT_DOMAIN_ID'),
            region_name=os.environ.get('OS_REGION_NAME'),
            insecure=True)
        return osclient
    except Exception as ex:
        raise ex

def get_wlm_client():
    try:
        wlm_ver = workloadmgrclient.__version__
        if packaging.version.parse(wlm_ver) < packaging.version.parse("5.0.0"):
            project_id = os.environ.get('OS_PROJECT_NAME')
        else:
            project_id = os.environ.get('OS_PROJECT_ID')

        wlm = wlmclient.Client(
            auth_url=os.environ.get('OS_AUTH_URL'),
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            project_id=project_id,
            domain_name=os.environ.get('OS_PROJECT_DOMAIN_ID'),
            insecure=True)
        return wlm
    except Exception as ex:
        raise ex


def get_snapshot_info(snapshot_id):
    client = get_wlm_client()
    snapshot_obj = client.snapshots.get(snapshot_id)
    return snapshot_obj._info


def read_json_file(file_path):
    restore_data = ''
    with open(file_path, 'r') as restore_file:
        restore_data = json.load(restore_file)
    return restore_data


def fetch_snapshot_network_data(snap_network, snapshot_id):
    client = get_wlm_client()
    snapshot_obj = client.snapshots.get(snapshot_id)
    snapshot_info = snapshot_obj._info
    instances = snapshot_info.pop('instances')
    network_data = None
    for instance in instances:
        networks = [nic for nic in instance['nics'] if nic['network']['id'] == snap_network.get('id')]
        network_list = [network for network in networks if network['network']['subnet']['id'] == snap_network['subnet']['id']]
        if not network_list:
            continue
        network_details = network_list[0]
        network_data = {
            'id': snap_network.get('id'),
            'name': network_details['network']['name'],
            'cidr': network_details['network']['subnet']['cidr'],
            'subnet_id': network_details['network']['subnet']['id']
        }
    return network_data


def fetch_target_network_data(network):
    if not network.get('id'):
        raise Exception("No target network selected.")
    osclient = openstack_client()
    subnets = list(osclient.network.subnets(
        project_id=os.environ.get('OS_PROJECT_ID'),
        network_id=network.get('id')))
    target_network_list = [{
        'id': subnet['network_id'],
        'name': network.get('name'),
        'cidr': subnet['cidr'],
        'subnet_id': subnet['id']
        }for subnet in  subnets if subnet['id'] == network['subnet']['id']]
    if target_network_list:
        target_network = target_network_list[0]
    return target_network


def fetch_volume_type_mapping_data(vdisk_data, snapshot_id):
    target_volume_type = {
        'new_volume_type': vdisk_data['new_volume_type'],
        'availability_zone': vdisk_data['availability_zone']
    }
    client = get_wlm_client()
    snapshot_obj = client.snapshots.get(snapshot_id)
    snapshot_info = snapshot_obj._info
    instances = snapshot_info.pop('instances')
    snapshot_disk = None
    for instance in instances:
        for vdisk in instance['vdisks']:
            if vdisk.get('volume_id', None) == vdisk_data['id']:
                snapshot_disk = vdisk
    if snapshot_disk:
        snapshot_volume_type = {
            'old_volume_type': snapshot_disk['volume_type'],
            'availability_zone': snapshot_disk['availability_zone']
        }
    return [snapshot_volume_type, target_volume_type]


def fetch_target_instance_data(instance):
    target_instance_data = {
        'id': instance['id'],
        'name': instance['name'],
        'flavor': instance.get('flavor'),
        'availability_zone': instance['availability_zone'],
        'ips': [nic['ip_address'] if nic['ip_address'] else None for nic in instance['nics']],
        'vdisks': []
    }
    for vdisk in instance['vdisks']:
        vdisk_dict = {
            'id': vdisk['id'],
            'availability_zone': vdisk['availability_zone']
        }
        target_instance_data['vdisks'].append(vdisk_dict)
    return target_instance_data

def fetch_snapshot_instance_data(instance, snapshot_id):
    client = get_wlm_client()
    snapshot_obj = client.snapshots.get(snapshot_id)
    snapshot_info = snapshot_obj._info
    snapshot_instances = snapshot_info.pop('instances')
    current_instance = None
    for snapshot_instance in snapshot_instances:
        if snapshot_instance['id'] == instance['id']:
            current_instance = snapshot_instance
    if not current_instance:
        raise Exception("Invalid instance.")

    snapshot_instance_data = {
        'id': current_instance['id'],
        'name': current_instance['name'],
        'flavor': current_instance['flavor'],
        'availability_zone': current_instance['metadata'].get('availability_zone'),
        'ips': [nic['ip_address']for nic in current_instance['nics']],
        'vdisks': []
    }
    for vdisk in current_instance['vdisks']:
        if vdisk.get('volume_id', None) is None:
                continue
        vdisk_dict = {
            'id': vdisk['volume_id'],
            'availability_zone': vdisk['availability_zone']
        }
        snapshot_instance_data['vdisks'].append(vdisk_dict)
    return snapshot_instance_data


def display_network_mapping(network_lists):

    header = ["Resource", "Source Network", "Target Network"]
    table = PrettyTable()
    table.field_names = header
    table.hrules = ALL
    table.title = "Network Mapping"

    for idx, network_list in enumerate(network_lists, start=1):
        net_list = [f"Network {idx}"]
        for each_net in network_list:
            subtable = PrettyTable()
            subtable.border = False
            subtable.header = False
            subtable.align = 'l'
            for k, v in each_net.items():
                subtable.add_row([f"{k} : {v}"])
            net_list.append(subtable)
        table.add_row(net_list)
    print("\nNetwrok Mapping Details:-")
    print(table)


def display_volume_mapping(volume_type_lists):

    header = ["Resource", "Source Volume Type", "Target Volume Type"]
    table = PrettyTable()
    table.field_names = header
    table.hrules = ALL
    table.title = "Volume Type Mapping"


    for idx, volume_type_list in enumerate(volume_type_lists, start=1):
        vol_type_list = [f"Volume Type {idx}"]
        for each_vol_type in volume_type_list:
            subtable = PrettyTable()
            subtable.border = False
            subtable.header = False
            subtable.align = 'l'
            for k, v in each_vol_type.items():
                subtable.add_row([f"{k} : {v}"])
            vol_type_list.append(subtable)
        table.add_row(vol_type_list)
    print("\nVolume type Mapping Details:-")
    print(table)


def display_instance_mapping(instance_mapping_list):

    header = ["Resource", "Source Instance", "Target Instance"]
    table = PrettyTable()
    table.field_names = header
    table.hrules = ALL
    table.title = "Instance Mapping"

    for idx, instance_list in enumerate(instance_mapping_list, start=1):
        instance_display_list = [f"Instance {idx}"]
        for each_instance in instance_list:
            subtable = PrettyTable()
            subtable.border = False
            subtable.header = False
            subtable.align = 'l'
            for k, v in each_instance.items():
                if k == 'vdisks':
                    for disk in v:
                        subtable.add_row([f"availability zone of volume {disk['id']} : {disk['availability_zone']}"])
                elif k == 'ips':
                    for ip in v:
                        if ip is not None:
                            subtable.add_row([f"Ip Address : {ip}"])
                        else:
                            subtable.add_row(["Ip Address : Choose next available IP address."])
                else:
                    subtable.add_row([f"{k} : {v}"])
            instance_display_list.append(subtable)
        table.add_row(instance_display_list)
    print("\nInstance Mapping Details:-")
    print(table)


def display_mapping(file_path, snapshot_id):
    restore_data = read_json_file(file_path)
    if not restore_data.get('restore_type'):
        print("\nCould not determine the restore type")
        return 1
    if restore_data.get('restore_type').lower() == 'inplace':
        # TODO
        print("\nInfo: Could not show mapping details")
        return 1

    def get_network_mapping_data(restore_data, snapshot_id):
        network_mapping = restore_data['openstack']['networks_mapping']['networks']
        if not network_mapping:
            return
        network_mapping_list = []
        for network in network_mapping:
            snapshot_data = fetch_snapshot_network_data(network.get('snapshot_network'), snapshot_id)
            target_data = fetch_target_network_data(network.get('target_network'))
            network_mapping_list.append([snapshot_data, target_data])
        return network_mapping_list

    def get_volume_type_mapping_data(restore_data, snapshot_id):
        instances = restore_data['openstack']['instances']
        vdisk_mapping_list = []
        for instance in instances:
            if not instance['include']:
                continue
            for vdisk in instance['vdisks']:
                volume_mapping_data = fetch_volume_type_mapping_data(vdisk, snapshot_id)
                if volume_mapping_data not in vdisk_mapping_list:
                    vdisk_mapping_list.append(volume_mapping_data)
        return vdisk_mapping_list

    def get_instance_mapping_data(restore_data, snapshot_id):
        instances = restore_data['openstack']['instances']
        instance_mapping_list = []
        for instance in instances:
            target_instance_data = fetch_target_instance_data(instance)
            snapshot_instance_data = fetch_snapshot_instance_data(instance, snapshot_id)
            instance_mapping_list.append([snapshot_instance_data, target_instance_data])
        return instance_mapping_list

    def show_mapping_data(fetch_function, display_function):
        data = fetch_function(restore_data, snapshot_id)
        if data:
            display_function(data)

    processes = []
    for fetch_function, display_function in zip(
            [get_instance_mapping_data, get_network_mapping_data, get_volume_type_mapping_data],
            [display_instance_mapping, display_network_mapping, display_volume_mapping]):
        process = multiprocessing.Process(target=show_mapping_data, args=(fetch_function, display_function))
        processes.append(process)
        process.start()

    # Wait for all processes to finish
    for process in processes:
        process.join()

def get_flavor(snapshot_flavor=None):
    """Get flavor.

    Args:
        snapshot_flavor (optional): flavor present in snapshot. Defaults to None.

    Returns:
        dict: Returns preffered flavor.
    """
    osclient = openstack_client()
    flavors_obj = list(osclient.compute.flavors())
    flavors = [{
        'id':flavor.id,
        'ram':flavor.ram,
        'disk':flavor.disk,
        'vcpus':flavor.vcpus,
        'ephemeral':flavor.ephemeral,
        'swap':flavor.swap} for flavor in flavors_obj]

    flavors.sort(key = lambda x: x['disk'])
    preferred_flavour = next((flavor for flavor in flavors \
            if flavor['disk'] >= int(snapshot_flavor['disk']) and \
            flavor['ram'] >= int(snapshot_flavor['ram']) and \
                flavor['vcpus'] >= int(snapshot_flavor['vcpus'])), None)
    if preferred_flavour:
        return preferred_flavour
    elif flavors:
        # TODO: Show warning, If we didn't find match for flavor.
        return flavors[-1]


def get_volume_type(existing_vol_type):
    """Get new volume type.

    Args:
        existing_vol_type (string): Volume type used in snapshot.

    Returns:
        string: Returns matching or first available volume type.
    """
    osclient = openstack_client()
    volume_types = list(osclient.block_storage.types())
    # TODO: first search by id then with name.
    volume_type_names = [volume_type.name for volume_type in volume_types]
    if volume_type_names:
        if existing_vol_type in volume_type_names:
            return existing_vol_type
        # TODO: Show warning, If we didn't find matching volue-type.
        return volume_type_names[0]


def get_available_network(existing_network_id, existing_network_cidr=None):
    """Get network for mapping.

    Args:
        existing_network_id (string): Network used in snapshot.

    Returns:
        dict: Returns matching or first available network.
    """
    osclient = openstack_client()
    networks = list(osclient.network.networks(project_id=os.environ.get('OS_PROJECT_ID')))
    network_list = [{
        'id': network.id,
        'name': network.name,
        'project_id': network.project_id,
        'subnet_ids': network.subnet_ids
        } for network in networks if network.status == 'ACTIVE']

    if network_list:
        for network in network_list:
            if network['id'] == existing_network_id:
                return network

        subnets = list(osclient.network.subnets(project_id=os.environ.get('OS_PROJECT_ID')))
        subnet_list = [{
            'allocation_pools': subnet.allocation_pools,
            'id': subnet.id,
            'cidr': subnet.cidr,
            'name': subnet.name,
            'network_id': subnet.network_id} for subnet in subnets]

        nearest_net_subnet = choose_existing_network(existing_network_cidr, subnet_list)
        nearest_network = [network for network in network_list if nearest_net_subnet['network_id'] in network['id']]

        return nearest_network


def choose_existing_network(snapshots_cidr, available_networks):
    # The code first attempts to find a matching CIDR (i.e., network address and netmask).
    # If an exact CIDR match is not found but the same network address is found, it proceeds to search for a higher IP range based on the netmask.
    # If both of the above conditions fail, the code selects a subnet based on the availability of address space, ensuring sufficient IP addresses.

    snapshots_cidr_obj = ipaddress.IPv4Network(snapshots_cidr)

    higher_ip_range = []
    for network in available_networks:
        subnet_cidr_obj = ipaddress.IPv4Network(network['cidr'])
        if snapshots_cidr_obj.network_address == subnet_cidr_obj.network_address:
            if snapshots_cidr_obj.netmask == subnet_cidr_obj.netmask:
                return network
            elif snapshots_cidr_obj.netmask > subnet_cidr_obj.netmask:
                higher_ip_range.append(network)

    if higher_ip_range:
        return higher_ip_range[0]

    # Address Space Availability
    nearest_network = None
    min_difference = float('inf')  # Initialize with positive infinity

    for network in available_networks:
        subnet_cidr_obj = ipaddress.IPv4Network(network['cidr'])
        difference = int(subnet_cidr_obj.network_address) - int(snapshots_cidr_obj.network_address)

        # Check if the current network is closer than the previous closest
        if 0 < difference < min_difference:
            min_difference = difference
            nearest_network = network

    return nearest_network


def generate_restore_json(snapshot_id, restore_type):
    client = get_wlm_client()
    snapshot_obj = client.snapshots.get(snapshot_id)
    snapshot_info = snapshot_obj._info
    instances = snapshot_info.pop('instances')


    restore_options = {
            'name': f"{restore_type} Restore.",
            'description': 'Restore_description',
            'oneclickrestore': False,
            'restore_type': restore_type,
            'type': 'openstack',
            'openstack': {
                'restore_topology': False,
                'instances': [],
                'networks_mapping': {
                        'networks': [],
                },
            },
        }

    snpashot_networks = []
    for instance in instances:
        vmoptions = {'id': instance['id'],
                    'include': True,
                    'name': instance['name'],
                    'flavor': get_flavor(instance['flavor']),
                    'availability_zone': instance['metadata'].get('availability_zone', 'nova')
                    }

        vmoptions['vdisks'] = []
        for vdisk in instance['vdisks']:

            if vdisk.get('volume_id', None) is None:
                continue
            new_volume_type = get_volume_type(vdisk['volume_type'])
            newdisk = {
                        'id': vdisk['volume_id'],
                        'new_volume_type': new_volume_type,
                        'availability_zone': instance['metadata'].get('availability_zone', 'nova'),
                        }
            vmoptions['vdisks'].append(newdisk)

        restore_options['openstack']['instances'].append(vmoptions)

        if restore_type == 'selective':
            vmoptions['nics'] = []
            for nic in instance['nics']:
                randomly_picked_network = get_available_network(nic['network']['id'], nic['network']['subnet']['cidr'])
                newnic = {
                    'id': nic['network']['id'],
                    'mac_address': '',
                    'ip_address': '',           # Check for next available IP addresses
                    'network': {'id': randomly_picked_network['id'],
                                'subnet': { 'id':
                                    randomly_picked_network['subnet_ids'][0]
                                    if randomly_picked_network['subnet_ids'] else ''},
                            },
                    }
                vmoptions['nics'].append(newnic)

                already_exists = any(
                    snap_nic['snapshot_network']['id'] == nic['network']['id']
                    for snap_nic in snpashot_networks)
                if already_exists:
                        continue

                snapshot_network = {
                        'id': nic['network']['id'],
                        'subnet': {
                            'id': nic['network']['subnet']['id']
                        }
                }
                selected_target_network = get_available_network(nic['network']['id'])
                target_network = {
                        'id': selected_target_network['id'],
                        'name': selected_target_network['name'],
                        'subnet': {
                            'id': selected_target_network['subnet_ids'][0] 
                            if selected_target_network['subnet_ids'] else ''
                        }
                }
                network = {
                        'snapshot_network': snapshot_network,
                        'target_network': target_network
                }
                snpashot_networks.append(network)
        else:
            # Flavors are not required for inplace restore.
            vmoptions.pop('flavor')
            # Set True value for restore_cinder_volume
            for vdisk in vmoptions['vdisks']:
                vdisk['restore_cinder_volume'] = True
                vdisk.pop('availability_zone')

    if restore_type == 'selective':
        restore_options['openstack']['networks_mapping']['networks'] = snpashot_networks

    return restore_options


def save_to_file(snapshot_id, restore_options, restore_type):
    file_name = f"{snapshot_id}-{restore_type}-restore.json"
    with open(file_name, "w") as restore_json:
        json.dump(restore_options, restore_json, indent=4)
    return file_name


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='JsonGenerator',
                description='Generates the restore.json file, '
                            'required for executing a Selective / Inplace restore operation.')
    parser.add_argument("--restore-type",
                        metavar="{selective, inplace}",
                        default='selective',
                        help="Specify whether to generate JSON for selective "
                        "restore or inplace restore. The default behavior is "
                        "to generate JSON for selective restore. Set this "
                        "field to 'inplace' if you want to generate JSON for "
                        "inplace restore."
                        )
    parser.add_argument('snapshot_id',
                        metavar="<snapshot_id>",
                        help='Id of workload snapshot.')
    parser.add_argument("--show-json-mapping",
                        metavar="<restore_json_file>",
                        help="Display the JSON mapping if you've already "
                        "created a JSON file.  It requires a JSON file "
                        "pre-created for the restore operation."
                        )

    args = parser.parse_args()
    if not args.show_json_mapping:
        restore_options = generate_restore_json(args.snapshot_id, args.restore_type)
        file_generated = save_to_file(args.snapshot_id, restore_options, args.restore_type)

        # Display mapping to user
        display_mapping(file_generated, args.snapshot_id)

        print(f"\nSuccessfully generated the JSON at {os.path.abspath(file_generated)} \n"
              "Please make sure to verify the mapping details before "
              "proceeding with the Restore operation.\n")

    else:
        display_mapping(args.show_json_mapping, args.snapshot_id)

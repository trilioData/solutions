import argparse
import os
import json
import ipaddress
import openstack
import workloadmgrclient.v1.client as wlmclient


def openstack_client():
    try:
        osclient = openstack.connect(
            auth_url=os.environ.get('OS_AUTH_URL'),
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            project_name=os.environ.get('OS_PROJECT_NAME'),
            user_domain_name = os.environ.get('OS_USER_DOMAIN_NAME'),
            project_domain_name=os.environ.get('OS_PROJECT_NAME'))
        return osclient
    except Exception as ex:
        raise ex


def get_wlm_client():
    try:
        wlm = wlmclient.Client(
            auth_url=os.environ.get('OS_AUTH_URL'),
            username=os.environ.get('OS_USERNAME'),
            password=os.environ.get('OS_PASSWORD'),
            project_id=os.environ.get('OS_PROJECT_ID'),
            project_name=os.environ.get('OS_PROJECT_NAME'),
            domain_name=os.environ.get('OS_PROJECT_DOMAIN_ID'))
        return wlm
    except Exception as ex:
        raise ex


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

    def save_to_file(snapshot_id, restore_options, restore_type):
        file_name = f"{snapshot_id}-{restore_type}-restore.json"
        with open(file_name, "w") as restore_json:
            json.dump(restore_options, restore_json, indent=4)

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

    save_to_file(snapshot_id, restore_options, restore_type)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='JsonGenerator',
                description='Generates the restore.json file, '
                            'required for executing a Selective / Inplace restore operation.')
    parser.add_argument("--restore_type",
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

    args = parser.parse_args()

    generate_restore_json(args.snapshot_id, args.restore_type)

    print(f"The '{args.snapshot_id}-{args.restore_type}-restore.json' file has been generated "
            "successfully. It's located in the current directory. "
            "The JSON file contains details like available flavors, "
            "network mapping, and volume types. "
            "Please double-check before proceeding further.")


# TODO: Display all the mappings done by us to the user in a tabular format.

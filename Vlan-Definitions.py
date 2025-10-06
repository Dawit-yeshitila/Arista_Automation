from netmiko import ConnectHandler

def create_vlans(device_params, vlan_ids, vlan_names=None):
    """
    Creates VLANs on a network device
    
    Args:
        device_params (dict): Device connection parameters
        vlan_ids (list): List of VLAN IDs to create (e.g., [10, 20, 30])
        vlan_names (list): Optional list of VLAN names (must match vlan_ids length)
    """
    if vlan_names and len(vlan_ids) != len(vlan_names):
        raise ValueError("vlan_ids and vlan_names must be the same length")

    commands = []
    for i, vlan_id in enumerate(vlan_ids):
        if not 1 <= vlan_id <= 4094:
            raise ValueError(f"Invalid VLAN ID {vlan_id}: Must be 1-4094")
        
        cmd = f"vlan {vlan_id}"
        if vlan_names:
            cmd += f"\nname {vlan_names[i]}"
        commands.append(cmd)

    with ConnectHandler(**device_params) as conn:
        output = conn.send_config_set(commands)
        conn.save_config()
    return output

# Example Usage
if __name__ == "__main__":
    switch = {
        'device_type': 'arista_eos',  # or 'cisco_ios'
        'host': '192.168.1.1',
        'username': 'admin',
        'password': 'password',
        'secret': 'enablepass'  # Only needed for Cisco
    }

    # Create VLANs (with optional names)
    vlans_to_create = [10, 20, 30, 40]
    vlan_names = ["MGMT", "VOICE", "DATA", "GUEST"]

    result = create_vlans(
        device_params=switch,
        vlan_ids=vlans_to_create,
        vlan_names=vlan_names
    )
    
    print("VLAN creation result:")
    print(result)
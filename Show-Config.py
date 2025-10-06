from netmiko import ConnectHandler

# Define device parameters
arista_switch = {
    'device_type': 'arista_eos',
    'ip': '192.0.2.10',          # Replace with the actual IP of your Arista switch
    'username': 'admin',         # Replace with your username
    'password': 'arista123',     # Replace with your password
    'secret': 'arista123',       # Replace with your enable password
}

try:
    # Connect to device
    print("Connecting to device...")
    net_connect = ConnectHandler(**arista_switch)
    
    # Enter enable mode if needed (Netmiko usually handles this automatically)
    net_connect.enable()
    
    # Get running configuration
    print("Retrieving running configuration...")
    output = net_connect.send_command('show running-config')
    print(output)
    
except Exception as e:
    print(f"An error occurred: {str(e)}")
finally:
    # Disconnect
    if 'net_connect' in locals():
        net_connect.disconnect()
        print("Disconnected from device.")
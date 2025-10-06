#!/usr/bin/env python3
"""
Arista EOS Console Configuration Script (Serial)
- Configures base system, MLAG, and Port-Channels via serial console
- Robust error handling for serial connections
- Idempotent operations for safe re-runs
"""
import logging
import serial
from netmiko import ConnectHandler
from time import sleep

# ===== Serial Connection Settings =====
SERIAL_PORT = 'COM4'  # Windows: 'COMX', Linux: '/dev/ttyUSB0'
BAUDRATE = 9600
TIMEOUT = 8

# ===== Configuration Variables =====
HOSTNAME = "DBDR-HCI-TOR-SW-02"
MGMT_IP = "172.16.105.11/24"
MLAG_PEER_IP = "10.0.0.1"
MLAG_VLAN_IP = "10.0.0.2/30"
# ===== Logging Setup =====
logging.basicConfig(
    filename='arista_console_deploy.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger()

# ===== Serial Connection Handler =====
def establish_serial_connection():
    """Establish serial connection with error handling"""
    try:
        ser = serial.Serial(
            port=SERIAL_PORT,
            baudrate=BAUDRATE,
            timeout=TIMEOUT,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS
        )
        logger.info(f"Serial connection established on {SERIAL_PORT}")
        return ser
    except serial.SerialException as e:
        logger.error(f"Serial connection failed: {e}")
        raise

# ===== Configuration Templates =====
def get_base_config():
    """Return base configuration commands"""
    return [
        "enable",
        "configure terminal",
        f"hostname {HOSTNAME}",
        "no aaa root",  # Disable default root access
        "username admin privilege 15 secret %TGBnhy6",  
        "enable secret %TGBnhy6",
        
        # Console hardening
        "line console 0",
        "login local",
        "exec-timeout 10 0",  # 10 minutes timeout
        "no history",
        "length 0",
        "transport input none",  # Disable reverse telnet
        "exit",

        # Management interface
        "interface Management1",
        f"ip address {MGMT_IP}",
        "no shutdown",
        "exit"
         # SSH server configuration
        "ip domain-name Dashen.local",
        "username admin privilege 15 secret %TGBnhy6",
        "ip ssh version 2",
        "crypto key generate rsa modulus 2048",
    ]

def get_mlag_config():
    """Return MLAG-specific configuration"""
    return [
        # MLAG VLAN
        "vlan 4094",
        "name MLAG-Peer",
        "trunk group MLAG-Peer",
        "exit",
        "interface Vlan4094",
        f"ip address {MLAG_VLAN_IP}",
        "no shutdown",
        "exit",

        # Peer Link
        "interface Ethernet49-50",  # Range syntax for EOS
        "description MLAG_PEER_LINK_MEMBER",
        "channel-group 100 mode active",
        "no shutdown",
        "exit",

        "interface Port-Channel100",
        "description MLAG_PEER_LINK",
        "switchport mode trunk",
        "mlag peer-link",
        "no shutdown",
        "exit",

        # MLAG Global Config
        "mlag configuration",
        "domain-id DR-TOR-MLAG",
        "local-interface Vlan4094",
        f"peer-address {MLAG_PEER_IP}",
        "peer-link Port-Channel100",
        "exit"
    ]

def generate_port_channels():
    """Generates Port-Channel configs (Port-Channel10 to 45) with 1:1 member mapping"""
    config = []
    for po in range(10, 46):  # 10-45 inclusive
        eth_port = po - 9  # Ethernet1 for PC10, Ethernet2 for PC11, etc.
        
        config.extend([
            # Member Interface
            f"interface Ethernet{eth_port}",
            f"description PC_{po}_MEMBER",
            f"channel-group {po} mode active",
            "no shutdown",
            "exit",

            # Port-Channel Interface
            f"interface Port-Channel{po}",
            f"description UPLINK_PO_{po}",
            "switchport mode trunk",
            f"mlag {po}",
            "no shutdown",
            "exit"
        ])
    return config

# ===== Main Deployment Logic =====
def deploy_config():
    """Main configuration deployment function"""
    try:
        # Initialize serial connection
        ser = establish_serial_connection()
        sleep(2)  # Allow for serial stabilization

        # Netmiko serial connection
        netmiko_device = {
            'device_type': 'terminal_server',  # Special type for serial
            'session_log': 'serial_session.log',
            'serial_settings': {
                'port': SERIAL_PORT,
                'baudrate': BAUDRATE,
                'timeout': TIMEOUT
            }
        }

        with ConnectHandler(**netmiko_device) as conn:
            logger.info("Netmiko session established")
            
            # Send base config
            conn.send_config_set(get_base_config())
            logger.info("Base configuration applied")

            # Send MLAG config
            conn.send_config_set(get_mlag_config())
            logger.info("MLAG configuration applied")

            # Send Port-Channels
            conn.send_config_set(generate_port_channels())
            logger.info("Port-Channels 10-45 configured")

            # Commit and save
            conn.send_command("write memory", expect_string=r"#")
            logger.info("Configuration saved")

            print("\n[SUCCESS] Deployment completed via console!")
            
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        print(f"[ERROR] {str(e)}")
        return False
    finally:
        if 'ser' in locals():
            ser.close()
    return True

if __name__ == "__main__":
    print(f"Starting console deployment to {HOSTNAME}...")
    if deploy_config():
        print("Done! Check arista_console_deploy.log for details")
    else:
        print("Deployment failed. Check logs for troubleshooting")
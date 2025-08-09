import socket
import subprocess
import sys
import os
import json
import requests
import time
from concurrent.futures import ThreadPoolExecutor

def get_config():
    """Get monitor configuration"""
    config_file = 'monitor_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    return None

def get_local_ips():
    """Get all local IP addresses"""
    addresses = []
    try:
        # Get all network interfaces
        interfaces = socket.getaddrinfo(host=socket.gethostname(), port=None, family=socket.AF_INET)
        for addr in interfaces:
            ip = addr[4][0]
            if not ip.startswith('127.'):
                addresses.append(ip)
        
        # If no other addresses found, try alternative method
        if not addresses:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            try:
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
                addresses.append(ip)
            except:
                addresses.append('127.0.0.1')
            finally:
                s.close()
    except:
        addresses.append('127.0.0.1')
    
    return addresses

def check_port(ip, port):
    """Check if port is open"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)
    try:
        result = sock.connect_ex((ip, port))
        return result == 0
    finally:
        sock.close()

def test_dashboard_access(ip, port):
    """Test if dashboard is accessible"""
    try:
        response = requests.get(f'http://{ip}:{port}', timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    # Get configuration
    config = get_config()
    if not config:
        print("❌ Error: Configuration file not found. Please start the monitor first.")
        return

    port = config['port']
    print("\n🔍 Network Connectivity Check")
    print("============================")

    # Get local IPs
    local_ips = get_local_ips()
    print("\n1️⃣ Local IP Addresses:")
    for ip in local_ips:
        print(f"   • {ip}")

    # Check port status
    print("\n2️⃣ Port Status:")
    for ip in local_ips:
        is_open = check_port(ip, port)
        print(f"   • {ip}:{port} - {'✅ Open' if is_open else '❌ Closed'}")

    # Test dashboard access
    print("\n3️⃣ Dashboard Access Test:")
    for ip in local_ips:
        is_accessible = test_dashboard_access(ip, port)
        print(f"   • http://{ip}:{port} - {'✅ Accessible' if is_accessible else '❌ Not accessible'}")

    # Check firewall status
    print("\n4️⃣ Firewall Status:")
    if sys.platform == 'win32':
        try:
            # Check Windows Firewall status
            output = subprocess.check_output('netsh advfirewall show allprofiles state', shell=True).decode()
            if 'ON' in output:
                print("   ⚠️ Windows Firewall is ON - May need to add an exception")
                print("   To add exception, run as administrator:")
                print(f'   netsh advfirewall firewall add rule name="Monitor Dashboard" dir=in action=allow protocol=TCP localport={port}')
            else:
                print("   ✅ Windows Firewall is OFF")
        except:
            print("   ❓ Could not determine firewall status")
    else:
        print("   ℹ️ Please check your system's firewall settings")

    print("\n5️⃣ Troubleshooting Steps:")
    print("   1. If port is closed:")
    print(f"      - Ensure no other application is using port {port}")
    print("      - Try changing the port in monitor_config.json")
    print("      - Check firewall settings")
    
    print("\n   2. If port is open but dashboard is not accessible:")
    print("      - Ensure the monitor is running")
    print("      - Check if antivirus is blocking the connection")
    print("      - Try accessing using different IP addresses")
    
    print("\n   3. For mobile devices:")
    print("      - Ensure device is on the same Wi-Fi network")
    print("      - Try both IP addresses if available")
    print("      - Clear browser cache or try different browser")

    print("\n   4. General tips:")
    print("      - Restart the monitor application")
    print("      - Temporarily disable firewall for testing")
    print("      - Check if Wi-Fi router has AP isolation enabled")
    print("      - Ensure both devices are on same network segment")

if __name__ == "__main__":
    main() 
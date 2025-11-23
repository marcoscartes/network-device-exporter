import socket
import requests
import logging
import time

from database import get_cached_vendor, save_cached_vendor

logger = logging.getLogger(__name__)

def get_vendor(mac_address):
    """
    Attempts to get the vendor name from the MAC address.
    Uses a simple online API or returns Unknown.
    """
    if not mac_address or mac_address.lower() == "unknown" or mac_address.startswith("unknown_"):
        return "Unknown"
        
    # Check Cache First
    cached_vendor = get_cached_vendor(mac_address)
    if cached_vendor:
        logger.debug(f"Vendor cache hit for {mac_address}: {cached_vendor}")
        return cached_vendor
        
    # Simple retry mechanism for rate limits
    for attempt in range(3):
        try:
            # Using api.macvendors.com (Simple text response)
            # Note: They have rate limits, so we should be careful.
            url = f"https://api.macvendors.com/{mac_address}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                vendor = response.text.strip()
                # Save to Cache
                save_cached_vendor(mac_address, vendor)
                return vendor
            elif response.status_code == 429:
                # Rate limited
                time.sleep(1.5 * (attempt + 1)) # Exponential backoff
                continue
            else:
                logger.debug(f"Vendor API returned {response.status_code} for {mac_address}")
                break
        except Exception as e:
            logger.debug(f"Vendor API failed: {e}")
            pass
            
    return "Unknown"

# Common ports to scan (most frequently used services)
COMMON_PORTS = [
    21,    # FTP
    22,    # SSH
    23,    # Telnet
    25,    # SMTP
    53,    # DNS
    80,    # HTTP
    110,   # POP3
    143,   # IMAP
    443,   # HTTPS
    445,   # SMB
    3306,  # MySQL
    3389,  # RDP
    5432,  # PostgreSQL
    5900,  # VNC
    8080,  # HTTP Alt
    8443,  # HTTPS Alt
    9100,  # Prometheus Node Exporter
    # IoT and Smart Home
    1883,  # MQTT
    8883,  # MQTT over SSL
    # Common web services
    3000,  # Node.js/React dev
    5000,  # Flask default
    5001,  # Synology DSM
    8000,  # Python HTTP
    8008,  # Google Home
    8081,  # Common alt HTTP
    8888,  # Jupyter
    9000,  # Portainer
    9090,  # Prometheus
]

def scan_ports(ip, ports=None, timeout=0.3):
    """
    Scans ports on the target IP.
    If ports is None, scans common ports.
    """
    if ports is None:
        ports = COMMON_PORTS
        
    open_ports = []
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            result = sock.connect_ex((ip, port))
            if result == 0:
                open_ports.append(port)
            sock.close()
        except Exception as e:
            logger.debug(f"Error scanning {ip}:{port} - {e}")
            pass
    return sorted(open_ports)

def identify_device(ip, mac):
    """
    Identifies device details based on IP and MAC.
    """
    vendor = get_vendor(mac)
    
    # Scan common ports to discover services
    logger.debug(f"Scanning ports for {ip}...")
    open_ports = scan_ports(ip)
    
    device_info = {
        "ip": ip,
        "mac": mac,
        "vendor": vendor,
        "open_ports": open_ports,
        "type": "Unknown"
    }
    
    # Simple heuristics based on discovered ports
    if 9100 in open_ports:
        device_info["type"] = "Node Exporter"
    elif 3389 in open_ports:
        device_info["type"] = "Windows PC"
    elif 22 in open_ports and 80 not in open_ports:
        device_info["type"] = "Linux Server"
    elif 445 in open_ports:
        device_info["type"] = "Windows/Samba"
    elif 80 in open_ports or 443 in open_ports:
        device_info["type"] = "Web Server"
    elif 1883 in open_ports or 8883 in open_ports:
        device_info["type"] = "MQTT Broker"
        
    return device_info

import scapy.all as scapy
import socket
import logging

logger = logging.getLogger(__name__)

def scan_network(ip_range):
    """
    Scans the network for active devices using ARP requests.
    
    Args:
        ip_range (str): The IP range to scan (e.g., "192.168.1.0/24").
        
    Returns:
        list: A list of dictionaries containing 'ip' and 'mac' of discovered devices.
    """
    logger.debug(f"Scanning network: {ip_range}")
    arp_request = scapy.ARP(pdst=ip_range)
    broadcast = scapy.Ether(dst="ff:ff:ff:ff:ff:ff")
    arp_request_broadcast = broadcast/arp_request
    
    # srp returns two lists: answered and unanswered packets
    try:
        answered_list = scapy.srp(arp_request_broadcast, timeout=2, verbose=False)[0]
    except Exception as e:
        logger.warning(f"ARP scan failed: {e}. Falling back to Ping scan.")
        return scan_network_ping(ip_range)
    
    clients_list = []
    for element in answered_list:
        client_dict = {"ip": element[1].psrc, "mac": element[1].hwsrc}
        clients_list.append(client_dict)
    
    if not clients_list:
        logger.info("ARP scan found no devices. Trying Ping scan...")
        return scan_network_ping(ip_range)
        
    return clients_list

def scan_network_ping(ip_range):
    """
    Scans the network using system ping command (slow but reliable).
    Assumes /24 subnet.
    """
    import subprocess
    import platform
    
    network_prefix = ".".join(ip_range.split(".")[:3])
    clients_list = []
    
    # Scan 1-254
    # To speed up, we could use threads, but keeping it simple for now.
    # We'll just scan a few IPs around the local one or just the gateway for demo if needed.
    # But for a real tool, we should thread this.
    
    logger.info("Starting Ping scan (this may take a while)...")
    
    # Let's use a ThreadPoolExecutor for speed
    from concurrent.futures import ThreadPoolExecutor
    
    def ping_host(ip):
        param = '-n' if platform.system().lower()=='windows' else '-c'
        command = ['ping', param, '1', '-w', '500', ip] # 500ms timeout
        return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

    with ThreadPoolExecutor(max_workers=50) as executor:
        # Generate IPs
        ips = [f"{network_prefix}.{i}" for i in range(1, 255)]
        results = executor.map(ping_host, ips)
        
        for ip, is_up in zip(ips, results):
            if is_up:
                mac = get_mac_from_arp(ip)
                clients_list.append({"ip": ip, "mac": mac})
                
    return clients_list

def get_mac_from_arp(ip):
    """
    Retrieves MAC address from system ARP table.
    """
    import subprocess
    import re
    
    try:
        # Run arp -a <ip>
        # Note: On some Windows systems, arp -a <ip> might return exit code 1 if not found.
        output = subprocess.check_output(['arp', '-a', ip], timeout=2).decode('utf-8', errors='ignore')
        
        # Regex to find MAC address (Windows/Linux style)
        mac_regex = r"([0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2}[:-][0-9a-fA-F]{2})"
        match = re.search(mac_regex, output)
        
        if match:
            mac = match.group(0).replace('-', ':').lower()
            logger.debug(f"Resolved MAC for {ip}: {mac}")
            return mac
        else:
            logger.debug(f"No MAC found in ARP output for {ip}: {output.strip()}")
            
    except Exception as e:
        logger.debug(f"ARP lookup failed for {ip}: {e}")
        pass
        
    return "Unknown"

if __name__ == "__main__":
    # Test the scanner
    logging.basicConfig(level=logging.DEBUG)
    # You might need to adjust the range based on your local network
    result = scan_network("192.168.1.1/24")
    for client in result:
        print(client)

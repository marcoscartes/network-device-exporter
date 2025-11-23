"""
Network Scanner - Main Entry Point

This module serves as the main entry point for the network scanner application.
It orchestrates network scanning, device identification, metrics collection, and export.
"""

import time
import argparse
import socket
import logging
from concurrent.futures import ThreadPoolExecutor

from network_scanner.core.scanner import scan_network
from network_scanner.core.identifier import identify_device
from network_scanner.core.probe import check_metrics
from network_scanner.exporters.prometheus import start_exporter, update_metrics
from network_scanner.storage.database import init_db, upsert_device, get_all_devices
from network_scanner.web.server import start_web_server_thread

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

def get_local_network():
    """
    Detects the local network range (assuming /24).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Connect to an external server to determine the interface
        s.connect(('8.8.8.8', 80))
        local_ip = s.getsockname()[0]
        # Assume /24 for simplicity
        return ".".join(local_ip.split(".")[:3]) + ".0/24"
    except Exception:
        return "192.168.1.0/24" # Fallback
    finally:
        s.close()

def process_device(device):
    """
    Enriches a single device with identification and metrics probing.
    """
    ip = device['ip']
    mac = device['mac']
    
    # Fix for DB collision: If MAC is Unknown, use a unique placeholder based on IP
    if mac == "Unknown":
        mac = f"unknown_{ip}"
        device['mac'] = mac
    
    # Identify Device
    info = identify_device(ip, mac)
    
    # Probe for Metrics
    metrics_urls = check_metrics(ip)
    info['metrics_urls'] = metrics_urls
    
    return info

def main():
    parser = argparse.ArgumentParser(description="Network Device Metrics Exporter")
    parser.add_argument("--range", help="IP range to scan (e.g., 192.168.1.0/24)", required=False)
    parser.add_argument("--interval", help="Scan interval in seconds", type=int, default=60)
    parser.add_argument("--port", help="Prometheus exporter port", type=int, default=8000)
    parser.add_argument("--web-port", help="Web interface port", type=int, default=5050)
    parser.add_argument("--loglevel", help="Log level (DEBUG, INFO, WARNING, ERROR)", default="INFO")
    args = parser.parse_args()

    # Set log level
    numeric_level = getattr(logging, args.loglevel.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {args.loglevel}')
    logging.getLogger().setLevel(numeric_level)

    scan_range = args.range
    if not scan_range:
        scan_range = get_local_network()
        logger.info(f"No range specified. Auto-detected: {scan_range}")

    # Initialize Database
    init_db()
    
    # Load existing devices from DB
    logger.info("Loading known devices from database...")
    known_devices = get_all_devices()
    update_metrics(known_devices)
    logger.info(f"Loaded {len(known_devices)} devices.")

    # Start Prometheus Exporter
    start_exporter(args.port)
    
    # Start Web Server
    start_web_server_thread(args.web_port)

    while True:
        logger.info(f"Starting Scan for {scan_range}")
        try:
            # 1. Scan Network (Discovery)
            devices = scan_network(scan_range)
            logger.info(f"Found {len(devices)} active devices.")

            # 2. Enrich Devices in Parallel
            logger.debug("Enriching device data (Parallel)...")
            enriched_devices = []
            
            with ThreadPoolExecutor(max_workers=20) as executor:
                results = executor.map(process_device, devices)
                
                for info in results:
                    if info.get('metrics_urls'):
                        logger.info(f"Found metrics at: {info['metrics_urls']} on {info['ip']}")
                    
                    # 3. Persist to DB
                    upsert_device(info)
                    enriched_devices.append(info)

            # 4. Update Exporter
            update_metrics(enriched_devices)
            logger.info("Metrics updated and saved to DB.")

        except Exception as e:
            logger.error(f"Error during scan: {e}", exc_info=True)

        logger.debug(f"Sleeping for {args.interval} seconds...")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()

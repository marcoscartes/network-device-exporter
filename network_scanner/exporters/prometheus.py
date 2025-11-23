from prometheus_client import start_http_server, Gauge
import time
import logging

logger = logging.getLogger(__name__)

# Define metrics
DEVICE_UP = Gauge('network_device_up', 'Network device status', ['ip', 'mac', 'vendor'])
METRICS_AVAILABLE = Gauge('network_device_metrics_available', 'Device exposes Prometheus metrics', ['ip', 'url'])

def start_exporter(port=8000):
    """
    Starts the Prometheus HTTP server.
    """
    start_http_server(port)
    logger.info(f"Prometheus exporter started on port {port}")

def update_metrics(devices):
    """
    Updates the Prometheus metrics based on the scan results.
    """
    # Clear old metrics if needed, or just overwrite. 
    # For a simple scanner, we might want to clear missing ones, but for now let's just set.
    # A better approach for a persistent exporter is to track state, but we'll keep it simple.
    
    for device in devices:
        ip = device['ip']
        mac = device['mac']
        vendor = device.get('vendor', 'Unknown')
        
        # Set device as up
        DEVICE_UP.labels(ip=ip, mac=mac, vendor=vendor).set(1)
        
        # Check if metrics are available
        metrics_urls = device.get('metrics_urls', [])
        for url in metrics_urls:
            METRICS_AVAILABLE.labels(ip=ip, url=url).set(1)
            
    # Note: Devices that disappear won't be automatically removed in this simple version
    # unless we implement a cleanup mechanism.

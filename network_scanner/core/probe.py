import requests
import logging

logger = logging.getLogger(__name__)

def check_metrics(ip, ports=[9100, 8080, 80, 3000, 9090]):
    """
    Checks if any of the common ports expose a /metrics endpoint.
    
    Returns:
        list: List of URLs that returned 200 OK for /metrics.
    """
    available_metrics = []
    
    for port in ports:
        url = f"http://{ip}:{port}/metrics"
        try:
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                # Basic check to see if it looks like Prometheus metrics
                if "# HELP" in response.text or "# TYPE" in response.text:
                    available_metrics.append(url)
        except requests.RequestException:
            continue
            
    return available_metrics

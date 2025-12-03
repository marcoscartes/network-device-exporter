from flask import Flask, render_template, jsonify, request
import logging
from database import get_all_devices, upsert_device
import threading
import time

logger = logging.getLogger(__name__)

app = Flask(__name__)

import ipaddress
from network_scanner.core.identifier import scan_ports

# Global state for tracking port scans
scan_state = {}

@app.route('/')
def index():
    devices = get_all_devices()
    # Sort by IP address (default)
    try:
        devices.sort(key=lambda x: ipaddress.ip_address(x['ip']))
    except Exception as e:
        logger.error(f"Error sorting by IP: {e}")
        # Fallback to string sort or last seen
        devices.sort(key=lambda x: x.get('last_seen', 0), reverse=True)
        
    return render_template('index.html', devices=devices)

@app.route('/api/scan-all-ports/<ip>', methods=['POST'])
def scan_all_ports(ip):
    """
    Initiates a full port scan (1-65535) for the specified IP.
    Runs in background thread and stores progress in scan_state.
    """
    if ip in scan_state and scan_state[ip].get('status') == 'running':
        return jsonify({'error': 'Scan already running for this IP'}), 400
    
    # Initialize scan state
    scan_state[ip] = {
        'status': 'running',
        'progress': 0,
        'current_port': 0,
        'total_ports': 65535,
        'open_ports': [],
        'start_time': time.time()
    }
    
    def run_full_scan():
        try:
            logger.info(f"Starting full port scan for {ip}")
            all_ports = list(range(1, 65536))
            open_ports = []
            
            # Scan in chunks for progress updates
            chunk_size = 1000
            for i in range(0, len(all_ports), chunk_size):
                if scan_state[ip].get('status') == 'cancelled':
                    break
                    
                chunk = all_ports[i:i+chunk_size]
                chunk_open = scan_ports(ip, ports=chunk, timeout=0.1)
                open_ports.extend(chunk_open)
                
                # Update progress
                scan_state[ip]['progress'] = int((i + chunk_size) / len(all_ports) * 100)
                scan_state[ip]['current_port'] = chunk[-1]
                scan_state[ip]['open_ports'] = sorted(open_ports)
            
            # Mark as complete
            scan_state[ip]['status'] = 'complete'
            scan_state[ip]['progress'] = 100
            scan_state[ip]['end_time'] = time.time()
            
            # Update database with new ports
            from database import get_all_devices
            devices = get_all_devices()
            device = next((d for d in devices if d['ip'] == ip), None)
            if device:
                device['open_ports'] = sorted(open_ports)
                upsert_device(device)
            
            logger.info(f"Full port scan complete for {ip}. Found {len(open_ports)} open ports.")
            
        except Exception as e:
            logger.error(f"Error during full port scan for {ip}: {e}")
            scan_state[ip]['status'] = 'error'
            scan_state[ip]['error'] = str(e)
    
    # Start scan in background thread
    thread = threading.Thread(target=run_full_scan, daemon=True)
    thread.start()
    
    return jsonify({'status': 'started', 'ip': ip})

@app.route('/api/scan-progress/<ip>', methods=['GET'])
def scan_progress(ip):
    """
    Returns the current progress of a port scan for the specified IP.
    """
    if ip not in scan_state:
        return jsonify({'error': 'No scan found for this IP'}), 404
    
    state = scan_state[ip]
    return jsonify({
        'status': state['status'],
        'progress': state['progress'],
        'current_port': state.get('current_port', 0),
        'total_ports': state['total_ports'],
        'open_ports': state['open_ports'],
        'ports_found': len(state['open_ports']),
        'elapsed_time': time.time() - state['start_time'] if 'start_time' in state else 0
    })

def run_web_server(port=5000):
    """
    Starts the Flask web server.
    """
    logger.info(f"Starting Web Server on port {port}")
    # Disable Flask's default logging to avoid clutter
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

def start_web_server_thread(port=5000):
    """
    Starts the web server in a separate daemon thread.
    """
    t = threading.Thread(target=run_web_server, args=(port,), daemon=True)
    t.start()

from flask import Flask, render_template
import logging
from database import get_all_devices
import threading

logger = logging.getLogger(__name__)

app = Flask(__name__)

import ipaddress

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

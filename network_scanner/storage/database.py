import sqlite3
import json
import time
import logging

logger = logging.getLogger(__name__)

DB_FILE = "network_devices.db"

def init_db():
    """
    Initializes the SQLite database and creates the devices table if it doesn't exist.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create devices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            mac TEXT PRIMARY KEY,
            ip TEXT,
            vendor TEXT,
            type TEXT,
            open_ports TEXT,
            metrics_urls TEXT,
            last_seen REAL
        )
    ''')
    
    # Create vendors table for caching
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendors (
            oui TEXT PRIMARY KEY,
            vendor TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def upsert_device(device):
    """
    Inserts or updates a device in the database.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Convert lists to JSON strings for storage
    metrics_urls_json = json.dumps(device.get('metrics_urls', []))
    open_ports_json = json.dumps(device.get('open_ports', []))
    
    cursor.execute('''
        INSERT INTO devices (mac, ip, vendor, type, open_ports, metrics_urls, last_seen)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(mac) DO UPDATE SET
            ip=excluded.ip,
            vendor=excluded.vendor,
            type=excluded.type,
            open_ports=excluded.open_ports,
            metrics_urls=excluded.metrics_urls,
            last_seen=excluded.last_seen
    ''', (
        device['mac'],
        device['ip'],
        device.get('vendor', 'Unknown'),
        device.get('type', 'Unknown'),
        open_ports_json,
        metrics_urls_json,
        time.time()
    ))
    
    conn.commit()
    conn.close()

def get_all_devices():
    """
    Retrieves all devices from the database.
    """
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM devices')
    rows = cursor.fetchall()
    
    devices = []
    for row in rows:
        device = dict(row)
        # Parse JSON strings back to lists
        try:
            device['metrics_urls'] = json.loads(device['metrics_urls'])
        except:
            device['metrics_urls'] = []
        try:
            device['open_ports'] = json.loads(device.get('open_ports', '[]'))
        except:
            device['open_ports'] = []
        devices.append(device)
        
    conn.close()
    return devices

def get_cached_vendor(mac):
    """
    Retrieves vendor from cache using OUI.
    """
    if len(mac) < 8:
        return None
        
    oui = mac[:8].lower() # xx:xx:xx
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    cursor.execute('SELECT vendor FROM vendors WHERE oui = ?', (oui,))
    result = cursor.fetchone()
    
    conn.close()
    
    if result:
        return result[0]
    return None

def save_cached_vendor(mac, vendor):
    """
    Saves vendor to cache using OUI.
    """
    if len(mac) < 8 or vendor == "Unknown":
        return
        
    oui = mac[:8].lower()
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO vendors (oui, vendor)
            VALUES (?, ?)
        ''', (oui, vendor))
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to cache vendor: {e}")
    finally:
        conn.close()

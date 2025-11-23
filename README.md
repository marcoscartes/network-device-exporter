# Network Device Exporter

A Python application that automatically discovers network devices, identifies them, scans for open ports, and exports metrics in Prometheus format. Includes a web dashboard for visualization.

## Features

- **Network Discovery**: Automatically scans your local network using ARP (with ping fallback)
- **Device Identification**: Identifies devices by vendor (MAC lookup) and type (based on open ports)
- **Dynamic Port Scanning**: Discovers ~30 common service ports on each device
- **Vendor Caching**: Caches MAC vendor lookups to reduce API calls
- **Prometheus Exporter**: Exports device metrics for Prometheus scraping
- **Web Dashboard**: Beautiful dark-mode web interface to view discovered devices
- **Persistent Storage**: SQLite database to maintain device history
- **Parallel Processing**: Fast scanning using concurrent threads

## Installation

### Prerequisites

- Python 3.7+
- Administrator/root privileges (for network scanning)
- Windows: [Npcap](https://npcap.com/) recommended for optimal ARP scanning

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python -m network_scanner
```

This will:
- Auto-detect your local network range
- Start scanning every 60 seconds
- Start Prometheus exporter on port 8000
- Start web dashboard on port 5050

### Advanced Options

```bash
python -m network_scanner --range 192.168.1.0/24 --interval 120 --port 9000 --web-port 8080 --loglevel DEBUG
```

**Arguments:**
- `--range`: IP range to scan (e.g., 192.168.1.0/24)
- `--interval`: Scan interval in seconds (default: 60)
- `--port`: Prometheus exporter port (default: 8000)
- `--web-port`: Web interface port (default: 5050)
- `--loglevel`: Log level - DEBUG, INFO, WARNING, ERROR (default: INFO)

## Accessing the Interfaces

### Web Dashboard
Open your browser to: `http://localhost:5050`

Features:
- View all discovered devices
- See open ports, vendor information, and device types
- Sort by any column (IP, vendor, type, etc.)
- Auto-refreshes every 10 seconds

### Prometheus Metrics
Scrape metrics from: `http://localhost:8000/metrics`

Available metrics:
- `network_device_up`: Device availability (1 = up, 0 = down)
- `network_device_metrics_available`: Whether device exposes Prometheus metrics

## Project Structure

```
network-device-exporter/
├── network_scanner/
│   ├── __init__.py
│   ├── __main__.py          # Main entry point
│   ├── core/                # Core scanning logic
│   │   ├── scanner.py       # Network discovery
│   │   ├── identifier.py    # Device identification & port scanning
│   │   └── probe.py         # Metrics endpoint probing
│   ├── storage/             # Data persistence
│   │   └── database.py      # SQLite operations
│   ├── exporters/           # Metric exporters
│   │   └── prometheus.py    # Prometheus exporter
│   └── web/                 # Web interface
│       ├── server.py        # Flask web server
│       └── templates/
│           └── index.html   # Dashboard UI
├── requirements.txt
├── .gitignore
└── README.md
```

## How It Works

1. **Network Scanning**: Uses ARP requests to discover active devices on the network
2. **Device Identification**: 
   - Looks up vendor from MAC address (with caching)
   - Scans ~30 common ports to identify services
   - Determines device type based on open ports
3. **Metrics Probing**: Checks for Prometheus `/metrics` endpoints
4. **Data Storage**: Saves all information to SQLite database
5. **Export**: 
   - Exposes Prometheus metrics for scraping
   - Provides web dashboard for visualization

## Port Scanning

The scanner checks the following common ports:
- **Basic Services**: SSH (22), HTTP (80/443), FTP (21), SMB (445)
- **Databases**: MySQL (3306), PostgreSQL (5432)
- **Web Services**: 3000, 5000, 8000, 8080, 8443, 9090
- **IoT/Smart Home**: MQTT (1883/8883)
- **Remote Access**: RDP (3389), VNC (5900)
- **Monitoring**: Prometheus Node Exporter (9100)

## Device Type Detection

The application automatically identifies device types:
- **Node Exporter**: Port 9100 open
- **Windows PC**: Port 3389 (RDP) open
- **Linux Server**: Port 22 (SSH) open, no HTTP
- **Windows/Samba**: Port 445 (SMB) open
- **Web Server**: Ports 80 or 443 open
- **MQTT Broker**: Ports 1883 or 8883 open

## Troubleshooting

### No devices found
- Ensure you're running with administrator/root privileges
- On Windows, install [Npcap](https://npcap.com/)
- Try specifying the network range manually with `--range`

### Vendor shows as "Unknown"
- The application uses a free MAC vendor API with rate limits
- Vendors are cached after first lookup
- Some MACs may not be in the vendor database

### Web dashboard not loading
- Check that port 5050 is not in use
- Try a different port with `--web-port`
- Check firewall settings

## License

MIT License - See LICENSE file for details

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Author

Created by marcoscartes

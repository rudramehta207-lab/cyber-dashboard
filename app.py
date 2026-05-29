import hashlib
import io
import os
import platform
import random
import sqlite3
import uuid
import psutil
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
incidents_log = [{"id": 1, "title": "Security Mesh Initialized", "desc": "Adaptive tactical firewalls online.", "type": "info"}]
incident_id_counter = 1

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

# --- CORE OPS ---
@app.route('/api/global-send', methods=['POST'])
def global_send():
    global incident_id_counter, incidents_log
    if 'username' not in session or session.get('verified') is not True: return jsonify({"error": "Unauthorized"}), 403
    
    file = request.files['file']
    secret_message = request.form['message']
    dest = request.form.get('country', 'Global Node')
    pwd = request.form.get('password', '')
    ttl = int(request.form.get('ttl', '30'))
    
    tracking_id = str(uuid.uuid4())[:8].upper()
    file_bytes = file.read()
    
    # CALCULATE INTEGRITY HASH (MNCs LOVE THIS)
    integrity_hash = hashlib.sha256(file_bytes).hexdigest()
    
    global_vault_tracker[tracking_id] = {
        "filename": secure_filename(file.filename),
        "file_bytes": file_bytes,
        "hash": integrity_hash,
        "destination": dest,
        "password": pwd,
        "sender_identity": session['username'],
        "status": "IN_TRANSIT",
        "expires_at": datetime.now() + timedelta(minutes=ttl),
        "failed_attempts": 0
    }
    
    incident_id_counter += 1
    incidents_log.append({"id": incident_id_counter, "title": "DEPLOYMENT ACTIVE", "desc": f"Package {tracking_id} routed to {dest}.", "type": "info"})
    
    return jsonify({"success": True, "tracking_id": tracking_id, "hash": integrity_hash[:16] + "..."})

@app.route('/api/global-receive', methods=['POST'])
def global_receive():
    global incident_id_counter, incidents_log
    tracking_id = request.form.get('tracking_id', '').upper()
    pwd = request.form.get('password', '')
    country = request.form.get('country', '').strip().lower()
    
    if tracking_id not in global_vault_tracker: return jsonify({"error": "Token not found."}), 404
    record = global_vault_tracker[tracking_id]
    
    if record["status"] != "IN_TRANSIT": return jsonify({"error": "Link Terminated."}), 403
    if datetime.now() > record["expires_at"]: return jsonify({"error": "Expired."}), 403
    
    if record["password"] != pwd or record["destination"].lower() != country:
        record["failed_attempts"] += 1
        incident_id_counter += 1
        if record["failed_attempts"] >= 3:
            record["status"] = "TERMINATED (BREACH)"
            incidents_log.append({"id": incident_id_counter, "title": "AUTO-SHRED TRIGGERED", "desc": f"Token {tracking_id} destroyed.", "type": "critical"})
        else:
            incidents_log.append({"id": incident_id_counter, "title": "INTERCEPTION ATTEMPT", "desc": f"Failed access on {tracking_id}.", "type": "critical"})
        return jsonify({"error": "Security Mismatch. Breach Logged."}), 403

    record["status"] = "DELIVERED"
    return send_file(io.BytesIO(record["file_bytes"]), as_attachment=True, download_name=record["filename"])

@app.route('/api/lock-token/<tracking_id>', methods=['POST'])
def lock_token(tracking_id):
    tid = tracking_id.upper()
    if tid in global_vault_tracker and global_vault_tracker[tid]["sender_identity"] == session['username']:
        global_vault_tracker[tid]["status"] = "REVOKED"
        return jsonify({"success": True})
    return jsonify({"success": False}), 400

@app.route('/api/stats')
def system_stats():
    # Dynamic Security Score Calculation
    breach_count = len([i for i in incidents_log if i['type'] == 'critical'])
    health_score = max(100 - (breach_count * 15), 10)
    
    clean_tracker = {}
    for tid, d in global_vault_tracker.items():
        clean_tracker[tid] = {
            "filename": d["filename"], "destination": d["destination"], 
            "status": d["status"], "hash": d["hash"][:12] + "...",
            "time_left": f"{int((d['expires_at'] - datetime.now()).total_seconds() // 60)}m" if d["status"] == "IN_TRANSIT" else "0m"
        }

    return jsonify({
        "cpu_usage": psutil.cpu_percent(),
        "health_score": health_score,
        "incidents": incidents_log[::-1][:10],
        "active_tracker": clean_tracker
    })

@app.route('/api/resolve-breach/<int:incident_id>', methods=['POST'])
def resolve_specific_breach(incident_id):
    global incidents_log
    for inc in incidents_log:
        if inc["id"] == incident_id:
            inc["type"] = "info"
            inc["title"] = f"[PATCHED] {inc['title']}"
            break
    return jsonify({"success": True})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

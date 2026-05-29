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
banned_ips = []
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

# --- CRYPTOGRAPHIC HELPERS ---
def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text) + '1111111111111110'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# --- AUTHENTICATION ROUTES ---
@app.route('/')
def home():
    if 'username' in session:
        # Check if they completed the secondary verification phase
        if session.get('verified') is True:
            return render_template('index.html', username=session['username'])
        return redirect(url_for('verify_gateway'))
    return render_template('login.html')

@app.route('/verify')
def verify_gateway():
    if 'username' not in session:
        return redirect(url_for('home'))
    if session.get('verified') is True:
        return redirect(url_for('home'))
return render_template('verify.html', username=session['username'].upper())
@app.route('/api/auth/signup', methods=['POST'])
def auth_signup():
    username = request.form.get('username', '').strip().lower()
    password = request.form.get('password', '')
    
    if not username or not password:
        return jsonify({"success": False, "error": "Missing registration fields."}), 400
        
    hashed = hash_password(password)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # SECURITY RULE: CRITICAL CROSS-PASSWORD DUPLICATION CHECK
    cursor.execute('SELECT id FROM users WHERE password = ?', (hashed,))
    duplicate_password = cursor.fetchone()
    if duplicate_password:
        conn.close()
        return jsonify({"success": False, "error": "CRITICAL RISK: This password has already been deployed by another network node user. You must supply a globally unique key string."}), 400

    try:
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Account registered securely! Proceeding to login."})
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({"success": False, "error": "Username already deployed to network registry."}), 400

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
        session['verified'] = False # Force them into the intermediate validation ring
        return jsonify({"success": True, "message": "Credentials validated. Initializing verification gateway sequence..."})
    return jsonify({"success": False, "error": "Access Denied: Invalid cryptographic identity keys."}), 401

@app.route('/api/auth/verify-submit', methods=['POST'])
def auth_verify_submit():
    if 'username' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 403
        
    method = request.form.get('method', '')
    token = request.form.get('token', '').strip()
    
    if not token:
        return jsonify({"success": False, "error": "Verification token string missing."}), 400
        
    # Standard simulation validation key (accepts mock passcode 7721)
    if token == "7721" or method in ['google', 'apple', 'mac']:
        session['verified'] = True
        
        global incident_id_counter, incidents_log
        incident_id_counter += 1
        incidents_log.append({
            "id": incident_id_counter,
            "title": "MFA PROTOCOL VERIFIED",
            "desc": f"Operator [{session['username']}] cleared secondary layer validation via system standard [{method.upper()}].",
            "type": "info"
        })
        return jsonify({"success": True, "message": "Verification confirmed. System access granted."})
        
    return jsonify({"success": False, "error": "Verification Failed: Invalid token response signature."}), 400

@app.route('/logout')
def logout():
    session.pop('username', None)
    session.pop('verified', None)
    return redirect(url_for('home'))

# --- CORE OPS TERMINALS ---
@app.route('/api/global-send', methods=['POST'])
def global_send():
    global incident_id_counter, incidents_log
    if 'username' not in session or session.get('verified') is not True:
        return jsonify({"error": "Unauthorized Access Attempt Blocked."}), 403
        
    if 'file' not in request.files or 'message' not in request.form:
        return jsonify({"error": "Missing payload packets."}), 400
        
    file = request.files['file']
    secret_message = request.form['message']
    destination_country = request.form.get('country', 'Global Node')
    access_password = request.form.get('password', '')
    ttl_minutes = int(request.form.get('ttl', '30'))
    
    if file.filename == '' or not secret_message:
        return jsonify({"error": "Payload invalid."}), 400

    tracking_id = str(uuid.uuid4())[:8].upper()
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    try:
        if file_ext in ['.png', '.jpg', '.jpeg']:
            img = Image.open(file.stream).convert('RGB')
            pixels = img.load()
            binary_msg = text_to_binary(secret_message)
            data_index, msg_length = 0, len(binary_msg)
            width, height = img.size
            
            for y in range(height):
                for x in range(width):
                    if data_index < msg_length:
                        r, g, b = pixels[x, y]
                        r = (r & ~1) | int(binary_msg[data_index]); data_index += 1
                        if data_index < msg_length: g = (g & ~1) | int(binary_msg[data_index]); data_index += 1
                        if data_index < msg_length: b = (b & ~1) | int(binary_msg[data_index]); data_index += 1
                        pixels[x, y] = (r, g, b)
                    else: break
                if data_index >= msg_length: break

            output_stream = io.BytesIO()
            img.save(output_stream, format="PNG")
            file_data_bytes = output_stream.getvalue()
            final_filename = f"secure_vault_{tracking_id}.png"
        else:
            file_data_bytes = file.read()
            final_filename = f"secure_vault_{tracking_id}{file_ext}"

        file_hash = hashlib.sha256(file_data_bytes).hexdigest()[:16]
        
        timestamp_now = datetime.now()
        expiration_time = timestamp_now + timedelta(minutes=ttl_minutes)

        global_vault_tracker[tracking_id] = {
            "filename": final_filename,
            "file_bytes": file_data_bytes,
            "hash": file_hash,
            "destination": destination_country,
            "password": access_password,
            "sender_identity": session['username'],
            "status": "IN_TRANSIT",
            "expires_at": expiration_time,
            "failed_attempts": 0
        }
        
        incident_id_counter += 1
        incidents_log.append({
            "id": incident_id_counter,
            "title": f"Secure Link Spawned: ID {tracking_id}",
            "desc": f"Sender [{session['username']}] deployed target assets with a {ttl_minutes}-minute countdown wall.",
            "type": "info"
        })
        
        return jsonify({
            "success": True,
            "tracking_id": tracking_id,
            "hash": file_hash,
            "destination": destination_country,
            "status_message": "🚀 SUCCESS: Cryptographic package deployed! TTL countdown sequence active."
        })
    except Exception as e:
        return jsonify({"error": f"Failed setting global pipeline node: {str(e)}"}), 500

@app.route('/api/global-receive', methods=['POST'])
def global_receive():
    global incident_id_counter, incidents_log
    if 'username' not in session or session.get('verified') is not True:
        return jsonify({"error": "Unauthorized Terminal Request Blocked."}), 403
        
    tracking_id = request.form.get('tracking_id', '').upper()
    provided_password = request.form.get('password', '')
    attempt_country = request.form.get('country', '').strip().lower()
    
    if tracking_id not in global_vault_tracker:
        return jsonify({"error": "Invalid Tracking ID reference tag."}), 404
        
    record = global_vault_tracker[tracking_id]
    
    if record["status"] == "REVOKED / LOCKED BY SENDER":
        return jsonify({"error": "🔒 ACCESS DENIED: This secure transmission package has been remotely terminated and locked by the sender."}), 403

    if record["status"] == "CONTAINMENT LOCKOUT / TERMINATED":
        return jsonify({"error": "🔒 CRITICAL EXPLOIT LOCKOUT: This node has permanently frozen due to excessive password failures."}), 403

    if datetime.now() > record["expires_at"]:
        record["status"] = "EXPIRED / TIME-ELAPSED SHREDDED"
        record["file_bytes"] = None  
        return jsonify({"error": "⌛ ROUTING ERROR: Transmission lifetime has elapsed. Asset file automatically shredded from cloud RAM."}), 403

    expected_country = record["destination"].strip().lower()
    
    if record["password"] != provided_password:
        record["failed_attempts"] += 1
        remaining_strikes = 3 - record["failed_attempts"]
        incident_id_counter += 1
        
        if record["failed_attempts"] >= 3:
            record["status"] = "CONTAINMENT LOCKOUT / TERMINATED"
            record["file_bytes"] = None
            incidents_log.append({
                "id": incident_id_counter,
                "title": "BRUTE FORCE AUTO-SHRED SWITCH TRIGGERED",
                "desc": f"Token {tracking_id} sustained 3 structural passkey failure strikes. File securely zeroed and dropped.",
                "type": "critical"
            })
            return jsonify({"error": "🔒 EXPLOIT TAMPERING DETECTED: 3 failed strikes reached. Data drop has completely self-destructed."}), 403
        
        incidents_log.append({
            "id": incident_id_counter,
            "title": "PASSKEY VALIDATION FAILURE STRIKE",
            "desc": f"User [{session['username']}] missed security key match on Token {tracking_id} [{remaining_strikes} attempts left].",
            "type": "critical"
        })
        return jsonify({"error": f"🔒 PASSKEY ERROR: Access blocked. {remaining_strikes} validation attempts remain before data self-destructs."}), 403

    if expected_country != attempt_country:
        incident_id_counter += 1
        incidents_log.append({
            "id": incident_id_counter,
            "title": "GEOLOCATION ROUTING COLD BREACH",
            "desc": f"Package {tracking_id} intercepted at un-routed node [{request.form.get('country', 'Unknown')}]. Target route was restricted to [{record['destination']}].",
            "type": "critical"
        })
        return jsonify({"error": "🔒 ROUTING ERROR: Secure deployment package is restricted. Access denied at this endpoint location."}), 403

    record["status"] = "DELIVERED"
    file_stream = io.BytesIO(record["file_bytes"])
    return send_file(file_stream, as_attachment=True, download_name=record["filename"])

@app.route('/api/stats')
def system_stats():
    cpu = psutil.cpu_percent(interval=None)
    clean_tracker_summary = {}
    for token, data in list(global_vault_tracker.items()):
        if data["status"] == "IN_TRANSIT" and datetime.now() > data["expires_at"]:
            data["status"] = "EXPIRED / TIME-ELAPSED SHREDDED"
            data["file_bytes"] = None
            
        time_left_str = "TERMINATED"
        if data["status"] == "IN_TRANSIT":
            diff = data["expires_at"] - datetime.now()
            if diff.total_seconds() > 0:
                mins, secs = divmod(int(diff.total_seconds()), 60)
                time_left_str = f"{mins}m {secs}s"
            else:
                time_left_str = "EXPIRED"

        clean_tracker_summary[token] = {
            "filename": data["filename"],
            "destination": data["destination"],
            "sender_identity": data["sender_identity"],
            "status": data["status"],
            "time_left": time_left_str
        }
        
    return jsonify({
        "cpu_usage": cpu,
        "os_platform": platform.system(),
        "incidents": incidents_log[::-1],
        "banned_count": len(banned_ips),
        "active_tracker": clean_tracker_summary
    })

@app.route('/api/resolve-breach/<int:incident_id>', methods=['POST'])
def resolve_specific_breach(incident_id):
    global incidents_log
    for inc in incidents_log:
        if inc["id"] == incident_id:
            inc["title"] = f"[RESOLVED] {inc['title']}"
            inc["type"] = "info"
            inc["desc"] = "Threat mitigated. Target link revoked and secure route re-established."
            break
    return jsonify({"success": True, "message": f"Incident #{incident_id} successfully isolated and patched."})

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

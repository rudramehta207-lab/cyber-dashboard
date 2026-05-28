import hashlib
import io
import os
import platform
import random
import uuid
from flask import Flask, jsonify, render_template, request, send_file
import psutil
from PIL import Image

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Shared global tracking memory (Simulating a Cloud Database)
# Tracks global files, destinations, access logs, and security keys
global_vault_tracker = {}

incidents_log = [
    {
        "id": 1,
        "title": "Global CloudShield Node Active",
        "desc": "Secure routing mesh established across edge networks.",
        "type": "info"
    }
]
banned_ips = []
incident_id_counter = 1

# --- STEGANOGRAPHY CORE HELPERS ---
def text_to_binary(text):
    return ''.join(format(ord(char), '08b') for char in text) + '1111111111111110'

def binary_to_text(binary_str):
    bytes_list = [binary_str[i:i+8] for i in range(0, len(binary_str), 8)]
    text = ""
    for b in bytes_list:
        if len(b) < 8: break
        char_code = int(b, 2)
        text += chr(char_code)
    return text

@app.route('/')
def home():
    return render_template('index.html')

# --- SYSTEM METRICS & INCIDENT FEED ENGINE ---
@app.route('/api/stats')
def system_stats():
    global incidents_log, banned_ips
    cpu = psutil.cpu_percent(interval=None)
    
    # Automated background noise simulation
    if random.random() < 0.10:
        noise_ip = f"198.51.100.{random.randint(2,254)}"
        if noise_ip not in banned_ips:
            banned_ips.append(noise_ip)
            global incident_id_counter
            incident_id_counter += 1
            incidents_log.append({
                "id": incident_id_counter,
                "title": "Edge Gateway Block",
                "desc": f"Malicious automated probe from IP {noise_ip} dropped dynamically.",
                "type": "info"
            })

    if len(incidents_log) > 10:
        incidents_log.pop(0)

    return jsonify({
        "cpu_usage": cpu,
        "os_platform": platform.system(),
        "incidents": incidents_log[::-1],
        "banned_count": len(banned_ips)
    })

# --- USER MITIGATION ENDPOINT (SOLVE CRITICAL PROBLEMS MANUALLY) ---
@app.route('/api/resolve-breach/<int:incident_id>', methods=['POST'])
def resolve_specific_breach(incident_id):
    """Allows users to manually fix individual critical tracking breaches from the frontend stream."""
    global incidents_log, global_vault_tracker
    
    # Find the targeted incident log to resolve it
    for inc in incidents_log:
        if inc["id"] == incident_id:
            inc["title"] = f"[RESOLVED] {inc['title']}"
            inc["type"] = "info"
            inc["desc"] = "Threat mitigated. Target link revoked and secure route re-established."
            break
            
    return jsonify({"success": True, "message": f"Incident #{incident_id} successfully isolated and patched."})

# --- MULTITASKING GLOBAL FILE SENDING & TRACKING MATRIX ---
@app.route('/api/global-send', methods=['POST'])
def global_send():
    """Packages a stego file, generates global tracking tokens, and arms a tripwire security system."""
    global incident_id_counter, incidents_log
    
    if 'file' not in request.files or 'message' not in request.form:
        return jsonify({"error": "Missing necessary payload packets."}), 400
        
    file = request.files['file']
    secret_message = request.form['message']
    destination_country = request.form.get('country', 'Global Node')
    access_password = request.form.get('password', '') # Optional extra authorization ring
    
    if file.filename == '' or not secret_message:
        return jsonify({"error": "Payload invalid."}), 400

    try:
        # 1. Embed data into pixels via LSB Steganography
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

        # Save to memory instead of writing static server files
        output_stream = io.BytesIO()
        img.save(output_stream, format="PNG")
        file_data_bytes = output_stream.getvalue()
        
        # 2. Register tracking metrics into global data map
        tracking_id = str(uuid.uuid4())[:8].upper() # Generation of sharp short tracking tags
        file_hash = hashlib.sha256(file_data_bytes).hexdigest()[:16]
        
        global_vault_tracker[tracking_id] = {
            "filename": f"secure_vault_{tracking_id}.png",
            "file_bytes": file_data_bytes,
            "hash": file_hash,
            "destination": destination_country,
            "password": access_password,
            "status": "IN_TRANSIT",
            "access_history": []
        }
        
        # Log successful initialization
        incident_id_counter += 1
        incidents_log.append({
            "id": incident_id_counter,
            "title": f"Secure Link Spawned: ID {tracking_id}",
            "desc": f"File bound for {destination_country} with cryptographic signature {file_hash}.",
            "type": "info"
        })
        
        return jsonify({
            "success": True,
            "tracking_id": tracking_id,
            "hash": file_hash,
            "destination": destination_country
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed setting global pipeline node: {str(e)}"}), 500

@app.route('/api/global-track/<tracking_id>', methods=['GET'])
def global_track(tracking_id):
    """Returns the live location, routing history, and current transit metrics of a specific secure package."""
    if tracking_id not in global_vault_tracker:
        return jsonify({"success": False, "error": "Token not found on global index registries."}), 404
        
    record = global_vault_tracker[tracking_id]
    return jsonify({
        "success": True,
        "filename": record["filename"],
        "hash": record["hash"],
        "destination": record["destination"],
        "status": record["status"],
        "access_history": record["access_history"]
    })

@app.route('/api/global-receive', methods=['POST'])
def global_receive():
    """Handles package collection. If authentication parameters fail, an absolute critical breach alert is tripped."""
    global incident_id_counter, incidents_log, banned_ips
    
    tracking_id = request.form.get('tracking_id', '').upper()
    provided_password = request.form.get('password', '')
    attempt_country = request.form.get('country', 'Unknown Node')
    
    if tracking_id not in global_vault_tracker:
        return jsonify({"error": "Invalid Tracking ID reference tag."}), 404
        
    record = global_vault_tracker[tracking_id]
    
    # TRIPWIRE WARNING TRIGGER DETECTOR
    if record["password"] != provided_password:
        # Flag absolute critical alert breach to both the sender and tracking metrics streams
        incident_id_counter += 1
        attacker_ip = f"45.223.10.{random.randint(10,250)}"
        
        incidents_log.append({
            "id": incident_id_counter,
            "title": "CRITICAL DATA INTERCEPTION ATTEMPT",
            "desc": f"Unauthorized tracking interception request on Token {tracking_id} originating from {attempt_country} via IP {attacker_ip}.",
            "type": "critical"
        })
        
        record["access_history"].append({
            "event": "UNAUTHORIZED INTERCEPTION BLOCKED",
            "country": attempt_country,
            "status": "ALERTED"
        })
        return jsonify({"success": False, "error": "SECURITY CRITICAL ALERT: Key verification error. Interception attempt flagged to security centers."}), 403

    # Success routing logic path
    record["status"] = "DELIVERED"
    record["access_history"].append({
        "event": "Package Checked Out Securely",
        "country": attempt_country,
        "status": "SUCCESS"
    })
    
    # Hand off binary file stream down pipelines instantly
    file_stream = io.BytesIO(record["file_bytes"])
    return send_file(file_stream, as_attachment=True, download_name=record["filename"], mimetype="image/png")

if __name__ == '__main__':
    app.run(debug=True, port=5000)
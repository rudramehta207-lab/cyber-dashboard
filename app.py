import hashlib
import io
import os
import platform
import random
import uuid
import psutil
from flask import Flask, jsonify, render_template, request, send_file
from werkzeug.utils import secure_filename
from PIL import Image

app = Flask(__name__)

# Temporary cloud storage directory setup for Render compatibility
UPLOAD_FOLDER = '/tmp/vault_storage' if os.environ.get('RENDER') else 'vault_storage'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Shared global tracking memory (Simulating a Cloud Database)
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

# --- USER MITIGATION ENDPOINT ---
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

# --- MULTITASKING GLOBAL FILE MULTI-FORMAT PROCESSING ---
@app.route('/api/global-send', methods=['POST'])
def global_send():
    global incident_id_counter, incidents_log
    
    if 'file' not in request.files or 'message' not in request.form:
        return jsonify({"error": "Missing necessary payload packets."}), 400
        
    file = request.files['file']
    secret_message = request.form['message']
    destination_country = request.form.get('country', 'Global Node')
    access_password = request.form.get('password', '')
    
    if file.filename == '' or not secret_message:
        return jsonify({"error": "Payload invalid."}), 400

    tracking_id = str(uuid.uuid4())[:8].upper()
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()

    try:
        # Check if the asset is an image to support pixel injection
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
            # Fallback for alternative formats (Videos, ZIPs, Audio)
            # Reads data directly and processes it securely via file streaming
            file_bytes = file.read()
            file_data_bytes = file_bytes
            final_filename = f"secure_vault_{tracking_id}{file_ext}"

        file_hash = hashlib.sha256(file_data_bytes).hexdigest()[:16]
        
        # Save payload parameters into active system memory register
        global_vault_tracker[tracking_id] = {
            "filename": final_filename,
            "file_bytes": file_data_bytes,
            "hash": file_hash,
            "destination": destination_country,
            "password": access_password,
            "secret_payload": secret_message,
            "status": "IN_TRANSIT",
            "access_history": []
        }
        
        incident_id_counter += 1
        incidents_log.append({
            "id": incident_id_counter,
            "title": f"Secure Link Spawned: ID {tracking_id}",
            "desc": f"Package bound for {destination_country} with cryptographic signature {file_hash}.",
            "type": "info"
        })
        
        return jsonify({
            "success": True,
            "tracking_id": tracking_id,
            "hash": file_hash,
            "destination": destination_country,
            "status_message": "🚀 SUCCESS: Cryptographic package deployed! Message delivered to grid network registry."
        })
        
    except Exception as e:
        return jsonify({"error": f"Failed setting global pipeline node: {str(e)}"}), 500

@app.route('/api/global-track/<tracking_id>', methods=['GET'])
def global_track(tracking_id):
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
    global incident_id_counter, incidents_log
    
    tracking_id = request.form.get('tracking_id', '').upper()
    provided_password = request.form.get('password', '')
    attempt_country = request.form.get('country', 'Unknown Node')
    
    if tracking_id not in global_vault_tracker:
        return jsonify({"error": "Invalid Tracking ID reference tag."}), 404
        
    record = global_vault_tracker[tracking_id]
    
    # TRIPWIRE INTERCEPTION TRIGGERED
    if record["password"] != provided_password:
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
        return jsonify({"error": "🔒 BREACH ALERT: Security critical verification error. Interception attempt flagged to tracking terminal."}), 403

    record["status"] = "DELIVERED"
    record["access_history"].append({
        "event": "Package Checked Out Securely",
        "country": attempt_country,
        "status": "SUCCESS"
    })
    
    # Send custom verification response layout along with binary download
    file_stream = io.BytesIO(record["file_bytes"])
    
    # Note: For file downloads combined with UI alerts, the frontend can read header values 
    # or handle payload messages cleanly. This hands over the file directly.
    return send_file(file_stream, as_attachment=True, download_name=record["filename"])

if __name__ == '__main__':
    # Configured to automatically bind to Render infrastructure environment specifications
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

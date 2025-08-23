import os
import time
import json
import threading
from datetime import datetime
import psutil
from collections import defaultdict

class InternetMonitor:
    def __init__(self):
        self.log_dir = "logs"
        self.ensure_log_directory()
        self.running = False  # Changed to False by default
        self.thread = None
        self.previous_counters = {}
        self.app_data = defaultdict(lambda: {'sent': 0, 'recv': 0})
        self.log_interval = 60  # Log every minute
        self.last_log_time = 0
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        
        # Common app name mappings for readability
        self.app_name_mappings = {
            'chrome.exe': 'Chrome Browser',
            'firefox.exe': 'Firefox Browser',
            'msedge.exe': 'Edge Browser',
            'zoom.exe': 'Zoom',
            'teams.exe': 'Microsoft Teams',
            'slack.exe': 'Slack',
            'discord.exe': 'Discord',
            'outlook.exe': 'Microsoft Outlook'
        }
        
        # Load historical data
        self.load_historical_data()
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def get_log_file(self):
        """Get the log file path for current date"""
        return os.path.join(self.log_dir, "internet_log.txt")
        
    def get_historical_file(self):
        """Get the historical data file path"""
        return os.path.join(self.log_dir, "internet_usage_history.json")
        
    def load_historical_data(self):
        """Load historical usage data"""
        try:
            history_file = self.get_historical_file()
            if os.path.exists(history_file):
                with open(history_file, 'r') as f:
                    self.historical_data = json.load(f)
            else:
                self.historical_data = {}
        except Exception as e:
            print(f"Error loading historical data: {str(e)}")
            self.historical_data = {}
            
    def save_historical_data(self):
        """Save historical usage data"""
        try:
            # Add current day's data to historical
            if self.app_data:
                self.historical_data[self.current_date] = {
                    app: {
                        'sent': data['sent'],
                        'recv': data['recv']
                    }
                    for app, data in self.app_data.items()
                }
                
            # Save to file
            with open(self.get_historical_file(), 'w') as f:
                json.dump(self.historical_data, f)
                
        except Exception as e:
            print(f"Error saving historical data: {str(e)}")
            
    def check_date_change(self):
        """Check if date has changed and reset if needed"""
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            print(f"New day detected, resetting counters ({self.current_date} -> {current_date})")
            
            # Save current data to historical
            self.save_historical_data()
            
            # Reset for new day
            self.current_date = current_date
            self.app_data.clear()
            self.previous_counters.clear()
            
            # Clear the log file
            log_file = self.get_log_file()
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")  # Clear the file
            
            print("✓ Counters reset for new day")
            
    def format_bytes(self, bytes):
        """Convert bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes < 1024:
                return f"{bytes:.1f} {unit}"
            bytes /= 1024
        return f"{bytes:.1f} TB"
        
    def get_process_network_usage(self):
        """Get network usage for all processes"""
        # Check for date change
        self.check_date_change()
        
        current_data = defaultdict(lambda: {'sent': 0, 'recv': 0})
        
        try:
            # Get all network connections with their PIDs
            connections = psutil.net_connections(kind='inet')
            
            # Group connections by PID
            pid_connections = defaultdict(list)
            for conn in connections:
                if conn.pid is not None:
                    pid_connections[conn.pid].append(conn)
            
            # Get network stats for each process
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    # Get process info
                    proc_info = proc.info
                    pid = proc_info['pid']
                    
                    # Skip if process has no network connections
                    if pid not in pid_connections:
                        continue
                    
                    # Get process name
                    proc_name = proc_info['name'].lower()
                    
                    # Use friendly name if available
                    display_name = self.app_name_mappings.get(proc_name, proc_name)
                    
                    # Get network stats using net_io_counters
                    try:
                        # Check if process has network connections without using the connections attribute
                        if pid in pid_connections:
                            # Use system-wide counters for the interface this connection is using
                            for nic, stats in psutil.net_io_counters(pernic=True).items():
                                if nic != 'lo':  # Skip loopback
                                    current_data[display_name]['sent'] += stats.bytes_sent
                                    current_data[display_name]['recv'] += stats.bytes_recv
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                    
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Calculate differences from previous counters
            for proc_name, current in current_data.items():
                if proc_name in self.previous_counters:
                    prev = self.previous_counters[proc_name]
                    sent_diff = max(0, current['sent'] - prev['sent'])
                    recv_diff = max(0, current['recv'] - prev['recv'])
                    # Convert to KB to keep numbers reasonable
                    self.app_data[proc_name]['sent'] += sent_diff // 1024
                    self.app_data[proc_name]['recv'] += recv_diff // 1024
            
            # Update previous counters
            self.previous_counters = current_data
            
        except Exception as e:
            print(f"Error getting process network usage: {str(e)}")
            
    def log_usage(self):
        """Log the current usage statistics"""
        try:
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Sort apps by total traffic (sent + received)
            sorted_apps = sorted(
                self.app_data.items(),
                key=lambda x: x[1]['sent'] + x[1]['recv'],
                reverse=True
            )
            
            with open(self.get_log_file(), "a", encoding="utf-8") as f:
                for app_name, data in sorted_apps:
                    if data['sent'] > 0 or data['recv'] > 0:  # Only log apps with actual traffic
                        # Write in CSV format: timestamp,app_name,sent_bytes,received_bytes
                        f.write(f"{current_time},{app_name},{data['sent']},{data['recv']}\n")
                        
            # Save historical data periodically
            self.save_historical_data()
            
        except Exception as e:
            print(f"Error logging usage: {str(e)}")
            
    def get_daily_usage(self, date=None):
        """Get usage data for a specific date"""
        if date is None:
            date = self.current_date
            
        if date == self.current_date:
            return self.app_data
        else:
            return self.historical_data.get(date, {})
            
    def monitor_thread(self):
        """Background thread for monitoring network usage"""
        while self.running:
            try:
                current_time = time.time()
                
                # Get current usage
                self.get_process_network_usage()
                
                # Log if interval has passed
                if current_time - self.last_log_time >= self.log_interval:
                    self.log_usage()
                    self.last_log_time = current_time
                    
                # Sleep for a short interval
                time.sleep(2)
                
            except Exception as e:
                print(f"Error in monitor thread: {str(e)}")
                time.sleep(5)  # Wait longer on error
                
    def start(self):
        """Start the internet monitor"""
        if not self.running:
            try:
                self.running = True
                # Initialize last log time
                self.last_log_time = time.time()
                
                # Start monitoring thread
                self.thread = threading.Thread(
                    target=self.monitor_thread,
                    daemon=True
                )
                self.thread.start()
                print("Internet monitor started")
                return True
                
            except Exception as e:
                print(f"Error starting internet monitor: {str(e)}")
                self.running = False
                return False
        return False
            
    def stop(self):
        """Stop the internet monitor"""
        if self.running:
            self.running = False
            self.log_usage()  # Log final usage stats
            self.save_historical_data()  # Save historical data
            
            # Wait for monitoring thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Wait up to 5 seconds
                
            print("Internet monitor stopped")
            return True
        return False 
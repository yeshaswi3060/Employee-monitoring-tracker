import os
import time
import json
import threading
from datetime import datetime
import win32gui
import win32process
import psutil
import re

class WebsiteTracker:
    def __init__(self):
        self.log_dir = "logs"
        self.ensure_log_directory()
        self.running = True
        
        # State tracking
        self.last_title = None
        self.last_browser = None
        self.last_start_time = None
        self.last_switch_time = None
        
        # Total duration tracking
        self.total_durations = {}  # {website: total_seconds}
        
        # Browser processes
        self.browsers = {
            'chrome.exe': 'Chrome',
            'firefox.exe': 'Firefox',
            'msedge.exe': 'Edge',
            'opera.exe': 'Opera',
            'brave.exe': 'Brave'
        }
        
        # Load existing data and durations
        self.website_visits = self.load_website_data()
        self.calculate_total_durations()
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def get_active_window_info(self):
        """Get information about the currently active window"""
        try:
            # Get the window handle
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None, None, None
                
            # Get window title and process info
            window_title = win32gui.GetWindowText(hwnd)
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
                browser_name = self.browsers.get(process_name)
                
                if browser_name:
                    # Extract website from title
                    website = self.extract_website_from_title(window_title)
                    return browser_name, website, window_title
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        except Exception as e:
            print(f"Error getting window info: {str(e)}")
            
        return None, None, None
        
    def extract_website_from_title(self, title):
        """Extract website name from browser window title"""
        # Common patterns in browser titles
        patterns = [
            r"(.+?)(?:\s*[-—]\s*.*)?$",  # Matches everything before a dash/hyphen
            r"(?:https?://)?(?:www\.)?([^/]+)"  # Matches domain names
        ]
        
        for pattern in patterns:
            match = re.search(pattern, title)
            if match:
                website = match.group(1).strip()
                if website and not website.isspace():
                    return website
                    
        return title.strip() if title else "Unknown"
        
    def format_duration(self, seconds):
        """Format duration in seconds to readable string"""
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if remaining_seconds == 0:
            return f"{minutes}m"
        return f"{minutes}m {remaining_seconds}s"
        
    def calculate_total_durations(self):
        """Calculate total duration for each website from visits"""
        self.total_durations = {}
        for visit in self.website_visits:
            website = visit['website']
            duration = visit.get('duration_seconds', 0)
            self.total_durations[website] = self.total_durations.get(website, 0) + duration
            
    def format_total_duration(self, seconds):
        """Format total duration in seconds to readable string"""
        if seconds < 60:
            return f"{seconds}s total"
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m total"
        return f"{minutes}m total"
        
    def load_website_data(self):
        """Load existing website visit data"""
        try:
            json_file = os.path.join(self.log_dir, "website_log.json")
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "visits" in data:
                        return data["visits"]
                    return data  # For backward compatibility
        except Exception as e:
            print(f"Error loading website data: {str(e)}")
        return []
        
    def save_website_data(self):
        """Save website visit data and total durations to JSON"""
        try:
            json_file = os.path.join(self.log_dir, "website_log.json")
            
            # Create summary data
            data = {
                "visits": self.website_visits,
                "total_durations": {
                    website: {
                        "seconds": duration,
                        "formatted": self.format_total_duration(duration)
                    }
                    for website, duration in self.total_durations.items()
                }
            }
            
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving website data: {str(e)}")
            
    def log_website_visit(self, browser, website, title, start_time, end_time=None):
        """Log website visit with duration"""
        try:
            # Calculate duration
            if end_time is None:
                end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
            start_dt = datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
            end_dt = datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
            duration_seconds = int((end_dt - start_dt).total_seconds())
            
            # Update total duration
            self.total_durations[website] = self.total_durations.get(website, 0) + duration_seconds
            
            # Create visit entry
            visit = {
                "browser": browser,
                "website": website,
                "title": title,
                "start_time": start_time,
                "end_time": end_time,
                "duration_seconds": duration_seconds,
                "duration_formatted": self.format_duration(duration_seconds),
                "total_duration_seconds": self.total_durations[website],
                "total_duration_formatted": self.format_total_duration(self.total_durations[website])
            }
            
            # Add to visits list
            self.website_visits.append(visit)
            
            # Also log to text file for backup
            self.log_to_text_file(visit)
            
            # Save JSON data periodically
            self.save_website_data()
            
        except Exception as e:
            print(f"Error logging website visit: {str(e)}")
            
    def log_to_text_file(self, visit):
        """Log visit to text file as backup"""
        try:
            log_file = os.path.join(self.log_dir, "website_log.txt")
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(f"[{visit['start_time']}] {visit['browser']} - {visit['website']}\n")
                f.write(f"Title: {visit['title']}\n")
                f.write(f"Visit Duration: {visit['duration_formatted']}\n")
                f.write(f"Total Time on Site: {visit['total_duration_formatted']}\n")
                f.write(f"End Time: {visit['end_time']}\n")
                f.write("-" * 80 + "\n")
        except Exception as e:
            print(f"Error writing to text log: {str(e)}")
            
    def monitor_websites(self):
        """Main monitoring loop"""
        while self.running:
            try:
                browser, website, title = self.get_active_window_info()
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                if browser and website:
                    # New website visit
                    if website != self.last_title:
                        # Log previous visit if exists
                        if self.last_title and self.last_start_time:
                            self.log_website_visit(
                                self.last_browser,
                                self.last_title,
                                title,
                                self.last_start_time,
                                current_time
                            )
                            
                        # Start tracking new website
                        self.last_browser = browser
                        self.last_title = website
                        self.last_start_time = current_time
                        
                elif self.last_title:
                    # Browser closed/switched to non-browser
                    self.log_website_visit(
                        self.last_browser,
                        self.last_title,
                        title,
                        self.last_start_time,
                        current_time
                    )
                    self.last_title = None
                    self.last_browser = None
                    self.last_start_time = None
                    
                time.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                print(f"Error in website monitor: {str(e)}")
                time.sleep(5)  # Wait longer on error
                
    def start(self):
        """Start website tracking"""
        monitor_thread = threading.Thread(target=self.monitor_websites, daemon=True)
        monitor_thread.start()
        return monitor_thread
        
    def stop(self):
        """Stop website tracking"""
        self.running = False
        # Log final visit if exists
        if self.last_title and self.last_start_time:
            self.log_website_visit(
                self.last_browser,
                self.last_title,
                None,
                self.last_start_time
            )
        self.save_website_data() 
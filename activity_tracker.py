import os
import time
import threading
from datetime import datetime
import win32gui

class ActivityTracker:
    def __init__(self):
        self.log_dir = "logs"
        self.ensure_log_directory()
        self.running = True
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def log_to_file(self, filename, message):
        """Helper method to log messages with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(self.log_dir, filename)
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to {filename}: {str(e)}")

    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            window = win32gui.GetForegroundWindow()
            title = win32gui.GetWindowText(window)
            return title
        except Exception as e:
            return f"Error getting window title: {str(e)}"

    def track_window_title(self):
        """Track active window title every 10 seconds (increased from 5)"""
        while self.running:
            try:
                title = self.get_active_window_title()
                if title:
                    self.log_to_file("window_log.txt", f"Active Window: {title}")
            except Exception as e:
                self.log_to_file("window_log.txt", f"Error tracking window: {str(e)}")
            time.sleep(10)  # Increased from 5 to 10 seconds

    def start(self):
        """Start all tracking threads"""
        self.running = True
        
        # Start window tracking in a separate thread
        window_thread = threading.Thread(target=self.track_window_title, daemon=True)
        window_thread.start()
        
        return True

    def stop(self):
        """Stop all tracking"""
        self.running = False 
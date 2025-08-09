import os
import time
import threading
from datetime import datetime
import win32gui
import win32process
import psutil
import mss
import mss.tools
from PIL import Image
import logging

class SmartScreenshotTaker:
    def __init__(self, debug=False):
        self.log_dir = "logs"
        self.screenshots_dir = os.path.join(self.log_dir, "screenshots")
        self.ensure_directories()
        
        # State tracking
        self.last_app = None
        self.last_title = None
        self.last_screenshot_time = 0
        self.min_interval = 3  # Minimum seconds between screenshots
        self.running = False  # Changed to False by default
        self.debug = debug
        self.enabled = True
        self.thread = None
        self.logger = logging.getLogger(__name__)
        
        # Windows to ignore
        self.ignored_processes = {
            "explorer.exe",
            "SearchApp.exe",
            "ShellExperienceHost.exe",
            "StartMenuExperienceHost.exe",
            "Taskmgr.exe",
            "SystemSettings.exe",
            "WindowsTerminal.exe",
            "cmd.exe",
            "powershell.exe",
            "conhost.exe",
            "SearchUI.exe",
            "LockApp.exe",
            "ApplicationFrameHost.exe",
            "TextInputHost.exe",
            "sihost.exe",
            "dwm.exe",
            "csrss.exe",
            "winlogon.exe",
            "wininit.exe",
            "services.exe",
            "lsass.exe",
            "svchost.exe"
        }
        
        # Window titles to ignore
        self.ignored_titles = {
            "",
            "Program Manager",
            "Windows Shell Experience Host",
            "Microsoft Text Input Application",
            "Settings",
            "Task Switching",
            "Search",
            "Cortana",
            "Task Manager",
            "Windows Security Alert",
            "Microsoft Store"
        }
        
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        os.makedirs(self.screenshots_dir, exist_ok=True)
        
    def get_active_window_info(self):
        """Get active window title and process name"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None, None
                
            # Get window title
            title = win32gui.GetWindowText(hwnd)
            
            # Get process info
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            try:
                process = psutil.Process(pid)
                process_name = process.name().lower()
                return process_name, title
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None, title
                
        except Exception as e:
            if self.debug:
                print(f"Error getting window info: {str(e)}")
            return None, None
            
    def should_take_screenshot(self, process_name, title):
        """Determine if screenshot should be taken"""
        # Skip if no process or title
        if not process_name or not title:
            return False
            
        # Skip ignored processes and titles
        if (process_name in self.ignored_processes or 
            title in self.ignored_titles or 
            len(title) < 5):
            return False
            
        current_time = time.time()
        
        # Check if enough time has passed
        if current_time - self.last_screenshot_time < self.min_interval:
            return False
            
        # Check if window changed
        if (process_name != self.last_app or title != self.last_title):
            # Special handling for browsers to avoid tab loading triggers
            if process_name in ["chrome.exe", "firefox.exe", "msedge.exe"]:
                # Skip if title contains loading indicators
                loading_indicators = ["Loading", "Connecting", "Waiting", "New Tab"]
                if any(indicator in title for indicator in loading_indicators):
                    return False
                    
                # Skip rapid tab switches
                if process_name == self.last_app and current_time - self.last_screenshot_time < 5:
                    return False
                    
            return True
            
        return False
        
    def take_screenshot(self, process_name, title):
        """Capture and save screenshot"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(self.screenshots_dir, filename)
            
            # Capture full screen
            with mss.mss() as sct:
                # Get the first monitor
                monitor = sct.monitors[1]
                screenshot = sct.grab(monitor)
                
                # Save with PIL for better compatibility
                img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
                img.save(filepath)
                
            # Update state
            self.last_screenshot_time = time.time()
            self.last_app = process_name
            self.last_title = title
            
            if self.debug:
                print(f"Screenshot taken: {process_name} - {title}")
                
            return True
            
        except Exception as e:
            if self.debug:
                print(f"Error taking screenshot: {str(e)}")
            return False
            
    def monitor_windows(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Get current window info
                process_name, title = self.get_active_window_info()
                
                # Check if we should take a screenshot
                if self.should_take_screenshot(process_name, title):
                    self.take_screenshot(process_name, title)
                    
                # Sleep to reduce CPU usage
                time.sleep(2)
                
            except Exception as e:
                if self.debug:
                    print(f"Error in monitor loop: {str(e)}")
                time.sleep(5)  # Wait longer on error
                
    def start(self):
        """Start the screenshot monitor"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
            self.logger.info("Screenshot monitor started")
            return True
        return False
        
    def stop(self):
        """Stop the screenshot monitor"""
        if self.running:
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Wait up to 5 seconds for thread to finish
            self.logger.info("Screenshot monitor stopped")
            return True
        return False

    def _run(self):
        """Main screenshot taking loop"""
        try:
            with mss.mss() as sct:
                while self.running:
                    try:
                        if self.enabled:
                            # Take screenshot
                            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                            filename = f"screenshot_{timestamp}.png"
                            filepath = os.path.join(self.screenshots_dir, filename)
                            
                            # Ensure directory exists
                            os.makedirs(os.path.dirname(filepath), exist_ok=True)
                            
                            # Capture screen
                            screen = sct.shot(output=filepath)
                            self.logger.info(f"Screenshot saved: {filename}")
                            
                        # Wait for 5 minutes
                        time.sleep(300)
                        
                    except Exception as e:
                        self.logger.error(f"Error taking screenshot: {str(e)}")
                        time.sleep(60)  # Wait a minute before retrying
                        
        except Exception as e:
            self.logger.error(f"Fatal error in screenshot taker: {str(e)}")
            self.running = False

def start_screenshot_capture(debug=False):
    """Initialize and start the screenshot taker"""
    screenshot_taker = SmartScreenshotTaker(debug=debug)
    return screenshot_taker.start() 
import os
import time
import threading
from datetime import datetime
import win32gui
import win32process
import win32con
import win32api
import psutil
import json
import logging
from collections import defaultdict

class AppUsageTracker:
    def __init__(self):
        self.log_dir = "logs"
        self.app_usage = defaultdict(float)  # Use defaultdict for automatic initialization
        self.current_app = None
        self.last_update_time = time.time()
        self.running = False  # Changed to False by default
        self.thread = None
        self.logger = logging.getLogger(__name__)
        self.ensure_log_directory()
        
        # Common app name mappings
        self.app_name_mappings = {
            # Browsers
            'chrome.exe': 'Google Chrome',
            'firefox.exe': 'Mozilla Firefox',
            'msedge.exe': 'Microsoft Edge',
            'opera.exe': 'Opera',
            'brave.exe': 'Brave Browser',
            'iexplore.exe': 'Internet Explorer',
            
            # Microsoft Office
            'excel.exe': 'Microsoft Excel',
            'word.exe': 'Microsoft Word',
            'powerpnt.exe': 'Microsoft PowerPoint',
            'outlook.exe': 'Microsoft Outlook',
            'onenote.exe': 'Microsoft OneNote',
            'winword.exe': 'Microsoft Word',
            
            # Development Tools
            'code.exe': 'Visual Studio Code',
            'devenv.exe': 'Visual Studio',
            'pycharm64.exe': 'PyCharm',
            'idea64.exe': 'IntelliJ IDEA',
            'webstorm64.exe': 'WebStorm',
            'sublime_text.exe': 'Sublime Text',
            'atom.exe': 'Atom',
            'eclipse.exe': 'Eclipse',
            'android studio.exe': 'Android Studio',
            'postman.exe': 'Postman',
            'git-bash.exe': 'Git Bash',
            'github desktop.exe': 'GitHub Desktop',
            'cursor.exe': 'Cursor',
            'webstorm.exe': 'WebStorm',
            'phpstorm.exe': 'PhpStorm',
            'clion.exe': 'CLion',
            'rider.exe': 'Rider',
            'datagrip.exe': 'DataGrip',
            'goland.exe': 'GoLand',
            'pycharm.exe': 'PyCharm',
            'idea.exe': 'IntelliJ IDEA',
            
            # Communication
            'teams.exe': 'Microsoft Teams',
            'slack.exe': 'Slack',
            'discord.exe': 'Discord',
            'zoom.exe': 'Zoom',
            'skype.exe': 'Skype',
            'telegram.exe': 'Telegram Desktop',
            'whatsapp.exe': 'WhatsApp',
            
            # Media
            'spotify.exe': 'Spotify',
            'vlc.exe': 'VLC Media Player',
            'wmplayer.exe': 'Windows Media Player',
            'obs64.exe': 'OBS Studio',
            'photoshop.exe': 'Adobe Photoshop',
            'illustrator.exe': 'Adobe Illustrator',
            'premiere.exe': 'Adobe Premiere Pro',
            'afterfx.exe': 'Adobe After Effects',
            
            # System
            'explorer.exe': 'File Explorer',
            'cmd.exe': 'Command Prompt',
            'powershell.exe': 'PowerShell',
            'taskmgr.exe': 'Task Manager',
            'control.exe': 'Control Panel',
            'mspaint.exe': 'Paint',
            'notepad.exe': 'Notepad',
            'notepad++.exe': 'Notepad++',
            'calculator.exe': 'Calculator',
            
            # Games and Entertainment
            'steam.exe': 'Steam',
            'epicgameslauncher.exe': 'Epic Games',
            'battle.net.exe': 'Battle.net',
            'leagueclient.exe': 'League of Legends',
            'minecraft.exe': 'Minecraft',
            
            # Other Common Apps
            'acrobat.exe': 'Adobe Acrobat',
            'adobereader.exe': 'Adobe Reader',
            '7zfm.exe': '7-Zip',
            'winrar.exe': 'WinRAR'
        }
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        try:
            if not os.path.exists(self.log_dir):
                os.makedirs(self.log_dir)
        except Exception as e:
            self.logger.error(f"Failed to create log directory: {e}")
            
    def get_window_info(self, hwnd):
        """Get detailed window information"""
        try:
            if not hwnd or not win32gui.IsWindow(hwnd):
                return None, None, None, None
                
            # Get window placement
            placement = win32gui.GetWindowPlacement(hwnd)
            if not placement:
                return None, None, None, None
                
            # Check if window is minimized or hidden
            if placement[1] == win32con.SW_SHOWMINIMIZED or not win32gui.IsWindowVisible(hwnd):
                return None, None, None, None
                
            # Get process ID and thread ID
            thread_id, pid = win32process.GetWindowThreadProcessId(hwnd)
            if not pid:
                return None, None, None, None
                
            try:
                # Get process information
                process = psutil.Process(pid)
                process_name = process.name().lower()
                exe_path = process.exe()
                window_title = win32gui.GetWindowText(hwnd)
                
                # Skip system processes that shouldn't be tracked
                if process_name in ['explorer.exe', 'dwm.exe', 'taskmgr.exe', 'control.exe']:
                    return None, None, None, None
                
                # Special handling for Discord and similar apps
                if process_name == "discord.exe" or "discord" in window_title.lower():
                    return "discord.exe", exe_path, "Discord", pid
                
                # For most applications, just return the process name directly
                # Only check parent process for specific cases where the actual app is a child
                if process_name in ['chrome.exe', 'firefox.exe', 'msedge.exe', 'code.exe', 'devenv.exe']:
                    return process_name, exe_path, window_title, pid
                
                # For other processes, check if they have a meaningful parent
                try:
                    parent = process.parent()
                    if parent and parent.name().lower() in self.app_name_mappings:
                        # If parent is a known app, use the parent
                        return parent.name().lower(), parent.exe(), window_title, parent.pid
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Default: return the current process
                return process_name, exe_path, window_title, pid
                
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return None, None, None, None
                
        except Exception as e:
            self.logger.error(f"Error getting window info: {e}")
            return None, None, None, None
            
    def get_active_window_name(self):
        """Get the name of the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            process_name, exe_path, window_title, pid = self.get_window_info(hwnd)
            
            if not process_name:
                return "No Active Window"
                
            # Special handling for Discord and similar apps
            if process_name == "discord.exe" or (window_title and "discord" in window_title.lower()):
                return "Discord"
                
            # Check mapped names first
            if process_name in self.app_name_mappings:
                mapped_name = self.app_name_mappings[process_name]
                
                # For browsers, try to get a meaningful name from the window title
                if process_name in ['chrome.exe', 'firefox.exe', 'msedge.exe'] and window_title:
                    # Remove common browser suffixes
                    for suffix in [
                        ' - Google Chrome',
                        ' - Mozilla Firefox', 
                        ' - Microsoft Edge',
                        ' - Brave',
                        ' - Opera'
                    ]:
                        if window_title.endswith(suffix):
                            clean_title = window_title[:-len(suffix)]
                            if clean_title and len(clean_title) > 3:  # Only use if meaningful
                                return f"{mapped_name} - {clean_title}"
                
                # For development tools, try to get project name
                if process_name in ['code.exe', 'devenv.exe', 'pycharm64.exe', 'idea64.exe'] and window_title:
                    # Remove common IDE suffixes
                    for suffix in [
                        ' - Visual Studio Code',
                        ' - Microsoft Visual Studio',
                        ' - PyCharm',
                        ' - IntelliJ IDEA'
                    ]:
                        if window_title.endswith(suffix):
                            clean_title = window_title[:-len(suffix)]
                            if clean_title and len(clean_title) > 3:
                                return f"{mapped_name} - {clean_title}"
                
                return mapped_name
                
            # Try to get a meaningful name from the window title
            if window_title:
                # Remove common suffixes
                for suffix in [
                    ' - Google Chrome',
                    ' - Mozilla Firefox',
                    ' - Microsoft Edge',
                    ' - Visual Studio Code',
                    ' - Discord',
                    ' - Slack',
                    ' - Microsoft Teams',
                    ' - Notepad++',
                    ' - Sublime Text'
                ]:
                    if window_title.endswith(suffix):
                        clean_title = window_title[:-len(suffix)]
                        if clean_title and len(clean_title) > 3:
                            return clean_title
                            
                # Check for specific apps in window title
                if 'discord' in window_title.lower():
                    return 'Discord'
                elif 'slack' in window_title.lower():
                    return 'Slack'
                elif 'teams' in window_title.lower():
                    return 'Microsoft Teams'
                    
                # Use window title if it's meaningful and not a system window
                if (len(window_title) > 3 and 
                    window_title not in ["Program Manager", "Windows Shell Experience Host", "Desktop Window Manager"]):
                    return window_title
                    
            # Use cleaned process name as fallback
            clean_name = process_name.replace('.exe', '').title()
            if clean_name not in ['Explorer', 'Dwm', 'Taskmgr', 'Control']:
                return clean_name
                
            return "Unknown Application"
            
        except Exception as e:
            self.logger.error(f"Error getting active window name: {e}")
            return "Unknown Application"
            
    def track_usage(self):
        """Main tracking loop"""
        last_save = time.time()
        last_app = None
        app_change_count = 0
        
        while self.running:
            try:
                current_time = time.time()
                current_app = self.get_active_window_name()
                
                # Only track if there's an active window and it changed
                if current_app not in ["No Active Window", "Unknown Application"]:
                    time_diff = current_time - self.last_update_time
                    
                    # Validate time difference (ignore system sleep/hibernate)
                    if 0 < time_diff < 60:  # Max 60 seconds between updates
                        # If app changed, log the change
                        if current_app != last_app:
                            app_change_count += 1
                            self.logger.info(f"App changed ({app_change_count}): {last_app} -> {current_app}")
                            
                        self.app_usage[current_app] += time_diff
                        
                        # Save data every 2 minutes or when app changes
                        if current_time - last_save >= 120 or current_app != last_app:
                            self.write_log()
                            self.save_usage_data()
                            last_save = current_time
                            
                last_app = current_app
                self.last_update_time = current_time
                
            except Exception as e:
                self.logger.error(f"Error in tracking loop: {e}")
                
            time.sleep(2)  # Increased sleep to reduce CPU usage
            
    def format_time(self, seconds):
        """Format time duration for display"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        
        if hours > 0:
            return f"{hours} hours {minutes} minutes"
        elif minutes > 0:
            return f"{minutes} minutes"
        return "Less than a minute"
            
    def write_log(self):
        """Write usage data to log file"""
        try:
            current_date = datetime.now().strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_dir, "app_usage_log.txt")
            
            # Sort apps by usage time
            sorted_apps = sorted(
                self.app_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            with open(log_file, "w", encoding="utf-8") as f:
                for app_name, seconds in sorted_apps:
                    # Format: AppName:Duration
                    duration = self.format_time(seconds)
                    f.write(f"{app_name}:{duration}\n")
                    
            # Prune zero-usage apps
            to_remove = [k for k, v in self.app_usage.items() if v < 1]
            for k in to_remove:
                del self.app_usage[k]
                    
        except Exception as e:
            self.logger.error(f"Error writing log: {e}")
            
    def save_usage_data(self):
        """Save usage data to JSON"""
        try:
            data_file = os.path.join(self.log_dir, "app_usage_data.json")
            with open(data_file, "w") as f:
                json.dump({
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "usage": dict(self.app_usage),  # Convert defaultdict to regular dict
                    "last_update": self.last_update_time
                }, f)
        except Exception as e:
            self.logger.error(f"Error saving usage data: {e}")
            
    def load_usage_data(self):
        """Load usage data for today"""
        try:
            data_file = os.path.join(self.log_dir, "app_usage_data.json")
            if os.path.exists(data_file):
                with open(data_file, "r") as f:
                    data = json.load(f)
                    if data["date"] == datetime.now().strftime("%Y-%m-%d"):
                        self.app_usage = defaultdict(float, data["usage"])
                        self.last_update_time = data.get("last_update", time.time())
        except Exception as e:
            self.logger.error(f"Error loading usage data: {e}")
            
    def start(self):
        """Start tracking"""
        if not self.running:
            try:
                self.running = True
                self.load_usage_data()
                
                self.thread = threading.Thread(target=self.track_usage, daemon=True)
                self.thread.start()
                
                self.logger.info("Application tracking started")
                return True
                
            except Exception as e:
                self.logger.error(f"Error starting tracker: {e}")
                self.running = False
                return False
        return False
            
    def stop(self):
        """Stop tracking"""
        if self.running:
            try:
                self.running = False
                self.write_log()
                self.save_usage_data()
                
                # Wait for tracking thread to finish
                if self.thread and self.thread.is_alive():
                    self.thread.join(timeout=5)  # Wait up to 5 seconds
                    
                self.logger.info("Application tracking stopped")
                return True
                
            except Exception as e:
                self.logger.error(f"Error stopping tracker: {e}")
                return False
        return False 
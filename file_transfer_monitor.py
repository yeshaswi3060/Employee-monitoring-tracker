import os
import json
import time
import psutil
import threading
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import win32file
import win32con
import win32api
import win32process
import win32gui
from urllib.parse import urlparse
import socket
import shutil

class FileTransferMonitor:
    def __init__(self):
        self.log_file = "logs/FileTransferLogs.json"
        self.running = True
        self.transfers = []
        self.known_transfers = set()  # To track unique transfers
        self.lock = threading.Lock()
        
        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)
        
        # Load existing transfers
        self.load_transfers()
        
        # Initialize paths to monitor
        self.download_paths = [
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents"),
            os.getenv("TEMP"),
            os.getenv("TMP")
        ]
        
        # Track browser processes
        self.browser_processes = {
            "chrome.exe": "Chrome",
            "firefox.exe": "Firefox",
            "msedge.exe": "Edge",
            "opera.exe": "Opera",
            "brave.exe": "Brave",
            "iexplore.exe": "Internet Explorer",
            "safari.exe": "Safari"
        }
        
        # File extensions to monitor
        self.monitored_extensions = {
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
            '.zip', '.rar', '.7z', '.tar', '.gz',
            '.txt', '.csv', '.json', '.xml',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp',
            '.mp3', '.mp4', '.avi', '.mkv', '.mov',
            '.exe', '.msi', '.iso'
        }
        
    def load_transfers(self):
        """Load existing transfers from JSON file"""
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.transfers = json.load(f)
                    # Update known transfers set
                    self.known_transfers = {
                        f"{t['filename']}_{t['time']}_{t['size']}"
                        for t in self.transfers
                    }
        except Exception as e:
            print(f"Error loading transfers: {e}")
            self.transfers = []
            
    def save_transfers(self):
        """Save transfers to JSON file"""
        try:
            with self.lock:
                with open(self.log_file, 'w') as f:
                    json.dump(self.transfers, f, indent=2)
        except Exception as e:
            print(f"Error saving transfers: {e}")
            
    def get_process_domain(self, pid):
        """Get domain from process connections"""
        try:
            process = psutil.Process(pid)
            connections = process.connections(kind='inet')
            
            for conn in connections:
                if conn.status == 'ESTABLISHED':
                    try:
                        domain = socket.gethostbyaddr(conn.raddr.ip)[0]
                        return urlparse(domain).netloc or domain
                    except:
                        return conn.raddr.ip
        except:
            pass
        return "Unknown Domain"
        
    def get_file_size(self, filepath):
        """Get human readable file size"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.2f} {unit}"
                size /= 1024
            return f"{size:.2f} TB"
        except:
            return "Unknown Size"
            
    def is_valid_transfer(self, filename):
        """Filter out invalid transfers"""
        try:
            # Check file extension
            ext = os.path.splitext(filename)[1].lower()
            if not ext:
                return False
                
            # Skip temporary and system files
            invalid_patterns = [
                '.tmp', '.crdownload', '.part', '.temp',
                'thumbs.db', '.ds_store', '~$', '.cache'
            ]
            
            return (
                ext in self.monitored_extensions and
                not any(pattern in filename.lower() for pattern in invalid_patterns) and
                not filename.startswith('.')
            )
        except:
            return False
            
    def add_transfer(self, filepath, direction, website=None):
        """Add new transfer to log"""
        try:
            print(f"Attempting to add transfer: {filepath}")  # Debug log
            filename = os.path.basename(filepath)
            if not self.is_valid_transfer(filename):
                print(f"Invalid transfer detected: {filename}")  # Debug log
                return
                
            # Wait briefly for file to be completely written
            time.sleep(0.5)
            
            size = self.get_file_size(filepath)
            time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create unique identifier
            transfer_id = f"{filename}_{time_str}_{size}"
            
            # Check if already logged
            if transfer_id in self.known_transfers:
                print(f"Transfer already logged: {transfer_id}")  # Debug log
                return
                
            transfer = {
                "time": time_str,
                "filename": filename,
                "size": size,
                "direction": direction,
                "website": website or "Unknown Domain"
            }
            
            print(f"Adding new transfer: {transfer}")  # Debug log
            
            with self.lock:
                self.transfers.append(transfer)
                self.known_transfers.add(transfer_id)
                self.save_transfers()
                print("Transfer saved successfully")  # Debug log
                
        except Exception as e:
            print(f"Error adding transfer: {e}")
            
    class FileHandler(FileSystemEventHandler):
        def __init__(self, monitor):
            self.monitor = monitor
            
        def on_created(self, event):
            if event.is_directory:
                return
                
            try:
                filepath = event.src_path
                print(f"New file detected: {filepath}")  # Debug log
                
                # Wait briefly for file to be completely written
                time.sleep(0.5)
                
                if not os.path.exists(filepath):
                    print(f"File no longer exists: {filepath}")  # Debug log
                    return
                    
                # Get process info
                handle = win32file.CreateFile(
                    filepath,
                    win32con.GENERIC_READ,
                    win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE,
                    None,
                    win32con.OPEN_EXISTING,
                    0,
                    None
                )
                
                info = win32file.GetFileInformationByHandle(handle)
                handle.Close()
                
                # Get process name
                pid = win32process.GetProcessIdOfThread(info.ProcessId)
                process = psutil.Process(pid)
                proc_name = process.name().lower()
                print(f"Process detected: {proc_name} (PID: {pid})")  # Debug log
                
                # Check if it's a browser or known application
                if proc_name in self.monitor.browser_processes:
                    website = self.monitor.get_process_domain(pid)
                    print(f"Browser download detected from: {website}")  # Debug log
                    self.monitor.add_transfer(filepath, "Download", website)
                elif self.monitor.is_valid_transfer(os.path.basename(filepath)):
                    # For non-browser downloads, try to get the application name
                    app_name = self.monitor.browser_processes.get(proc_name, proc_name)
                    print(f"Application download detected from: {app_name}")  # Debug log
                    self.monitor.add_transfer(filepath, "Download", app_name)
                    
            except Exception as e:
                print(f"Error handling file event: {e}")
                
    def monitor_uploads(self):
        """Monitor for file uploads"""
        while self.running:
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'].lower() in self.browser_processes:
                        # Check open files and connections
                        try:
                            process = psutil.Process(proc.info['pid'])
                            open_files = process.open_files()
                            connections = process.connections(kind='inet')
                            
                            if open_files and connections:
                                for file in open_files:
                                    if os.path.exists(file.path):
                                        filename = os.path.basename(file.path)
                                        if self.is_valid_transfer(filename):
                                            website = self.get_process_domain(proc.info['pid'])
                                            self.add_transfer(file.path, "Upload", website)
                                            
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                            
            except Exception as e:
                print(f"Error monitoring uploads: {e}")
                
            time.sleep(1)  # Check every second
            
    def start(self):
        """Start the file transfer monitoring"""
        try:
            print("Starting file transfer monitor...")  # Debug log
            # Start download monitoring
            self.observer = Observer()
            handler = self.FileHandler(self)
            
            # Monitor all download paths
            for path in self.download_paths:
                if path and os.path.exists(path):
                    print(f"Monitoring directory: {path}")  # Debug log
                    self.observer.schedule(handler, path, recursive=False)
            
            self.observer.start()
            print("File observer started successfully")  # Debug log
            
            # Start upload monitoring in separate thread
            self.upload_thread = threading.Thread(target=self.monitor_uploads)
            self.upload_thread.daemon = True
            self.upload_thread.start()
            print("Upload monitor thread started")  # Debug log
            
        except Exception as e:
            print(f"Error starting file transfer monitor: {e}")
            
    def stop(self):
        """Stop the file transfer monitoring"""
        self.running = False
        if hasattr(self, 'observer'):
            self.observer.stop()
            self.observer.join()
            
    def get_filtered_transfers(self, filter_period="all"):
        """Get transfers filtered by time period"""
        try:
            now = datetime.now()
            with self.lock:
                if filter_period == "today":
                    return [t for t in self.transfers 
                          if datetime.strptime(t['time'], "%Y-%m-%d %H:%M:%S").date() == now.date()]
                elif filter_period == "week":
                    week_ago = now.timestamp() - (7 * 24 * 60 * 60)
                    return [t for t in self.transfers 
                          if datetime.strptime(t['time'], "%Y-%m-%d %H:%M:%S").timestamp() > week_ago]
                else:
                    return self.transfers.copy()
        except Exception as e:
            print(f"Error filtering transfers: {e}")
            return [] 
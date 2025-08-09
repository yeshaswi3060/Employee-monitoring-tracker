import os
import time
import threading
from datetime import datetime
import psutil
import win32api
import win32file
import win32con
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import humanize

class USBFileSystemHandler(FileSystemEventHandler):
    def __init__(self, usb_label, mount_point, log_callback):
        self.usb_label = usb_label
        self.mount_point = mount_point
        self.log_callback = log_callback
        self.last_events = {}  # Store last events to prevent duplicates
        
    def get_file_size_mb(self, file_path):
        """Get file size in MB"""
        try:
            size_bytes = os.path.getsize(file_path)
            return humanize.naturalsize(size_bytes)
        except:
            return "Unknown size"
            
    def should_log_event(self, event_type, file_path, timestamp):
        """Check if event should be logged (prevent duplicates)"""
        event_key = f"{event_type}:{file_path}"
        last_time = self.last_events.get(event_key)
        
        # If no previous event or more than 1 second has passed
        if not last_time or (timestamp - last_time).total_seconds() > 1:
            self.last_events[event_key] = timestamp
            return True
        return False
        
    def on_created(self, event):
        if not event.is_directory:
            timestamp = datetime.now()
            if self.should_log_event('created', event.src_path, timestamp):
                size = self.get_file_size_mb(event.src_path)
                self.log_callback(
                    f"File Copied to USB '{self.usb_label}' - {os.path.basename(event.src_path)} "
                    f"({size}) at {event.src_path}"
                )
                
    def on_deleted(self, event):
        if not event.is_directory:
            timestamp = datetime.now()
            if self.should_log_event('deleted', event.src_path, timestamp):
                self.log_callback(
                    f"File Deleted from USB '{self.usb_label}' - {os.path.basename(event.src_path)} "
                    f"at {event.src_path}"
                )
                
    def on_modified(self, event):
        if not event.is_directory:
            timestamp = datetime.now()
            if self.should_log_event('modified', event.src_path, timestamp):
                size = self.get_file_size_mb(event.src_path)
                self.log_callback(
                    f"File Modified on USB '{self.usb_label}' - {os.path.basename(event.src_path)} "
                    f"({size}) at {event.src_path}"
                )

class PCFileSystemHandler(FileSystemEventHandler):
    def __init__(self, usb_monitor):
        self.usb_monitor = usb_monitor
        self.last_events = {}
        
    def on_created(self, event):
        if not event.is_directory:
            timestamp = datetime.now()
            event_key = f"created:{event.src_path}"
            
            # Check for duplicate events
            last_time = self.last_events.get(event_key)
            if not last_time or (timestamp - last_time).total_seconds() > 1:
                self.last_events[event_key] = timestamp
                
                # Check if file was copied from any connected USB
                file_name = os.path.basename(event.src_path)
                file_size = os.path.getsize(event.src_path) if os.path.exists(event.src_path) else 0
                
                for usb in self.usb_monitor.connected_usbs.values():
                    usb_path = os.path.join(usb['mount_point'], file_name)
                    if os.path.exists(usb_path) and os.path.getsize(usb_path) == file_size:
                        self.usb_monitor.log_event(
                            f"File Copied from USB '{usb['label']}' to PC - {file_name} "
                            f"({humanize.naturalsize(file_size)}) at {event.src_path}"
                        )
                        break

class USBMonitorAdvanced:
    def __init__(self):
        self.log_dir = "logs"
        self.ensure_log_directory()
        
        self.connected_usbs = {}  # Store connected USB info
        self.observers = {}       # Store file system observers
        self.running = False      # Changed to False by default
        self.thread = None
        
        # Monitored PC locations
        self.pc_monitored_paths = [
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Documents")
        ]
        
        # PC file system observers
        self.pc_observers = {}
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def log_event(self, message):
        """Log USB event with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(self.log_dir, "usb_activity_log.txt")
        
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to USB activity log: {str(e)}")
            
    def get_usb_info(self, drive_letter):
        """Get USB drive information"""
        try:
            volume_name = win32api.GetVolumeInformation(drive_letter)[0]
            return volume_name or "Unnamed USB Drive"
        except:
            return "Unknown USB Drive"
            
    def setup_pc_monitoring(self):
        """Setup file system monitoring for PC locations"""
        for path in self.pc_monitored_paths:
            if os.path.exists(path) and path not in self.pc_observers:
                try:
                    observer = Observer()
                    handler = PCFileSystemHandler(self)
                    observer.schedule(handler, path, recursive=False)
                    observer.start()
                    self.pc_observers[path] = observer
                except Exception as e:
                    print(f"Error setting up PC monitoring for {path}: {str(e)}")
                    
    def cleanup_pc_monitoring(self):
        """Clean up PC file system observers"""
        for observer in self.pc_observers.values():
            try:
                observer.stop()
                observer.join()
            except:
                pass
        self.pc_observers.clear()
        
    def setup_usb_monitoring(self, mount_point, usb_label):
        """Setup file system monitoring for USB drive"""
        try:
            observer = Observer()
            handler = USBFileSystemHandler(usb_label, mount_point, self.log_event)
            observer.schedule(handler, mount_point, recursive=True)
            observer.start()
            return observer
        except Exception as e:
            print(f"Error setting up USB monitoring for {mount_point}: {str(e)}")
            return None
            
    def check_usb_devices(self):
        """Check for USB device changes"""
        try:
            # Get current USB drives
            current_usbs = {}
            for partition in psutil.disk_partitions():
                try:
                    if win32file.GetDriveType(partition.mountpoint) == win32file.DRIVE_REMOVABLE:
                        usb_label = self.get_usb_info(partition.mountpoint)
                        current_usbs[partition.mountpoint] = {
                            'label': usb_label,
                            'mount_point': partition.mountpoint
                        }
                except:
                    continue
                    
            # Check for new USB devices
            for mount_point, usb_info in current_usbs.items():
                if mount_point not in self.connected_usbs:
                    # New USB connected
                    self.log_event(f"USB Connected - '{usb_info['label']}' mounted at {mount_point}")
                    
                    # Setup monitoring
                    observer = self.setup_usb_monitoring(mount_point, usb_info['label'])
                    if observer:
                        self.observers[mount_point] = observer
                        self.connected_usbs[mount_point] = usb_info
                        
            # Check for removed USB devices
            for mount_point in list(self.connected_usbs.keys()):
                if mount_point not in current_usbs:
                    # USB removed
                    usb_info = self.connected_usbs[mount_point]
                    self.log_event(f"USB Removed - '{usb_info['label']}' from {mount_point}")
                    
                    # Cleanup monitoring
                    if mount_point in self.observers:
                        try:
                            self.observers[mount_point].stop()
                            self.observers[mount_point].join()
                        except:
                            pass
                        del self.observers[mount_point]
                    del self.connected_usbs[mount_point]
                    
        except Exception as e:
            print(f"Error checking USB devices: {str(e)}")
            
    def monitor_usb_devices(self):
        """Main monitoring loop"""
        self.setup_pc_monitoring()
        
        while self.running:
            self.check_usb_devices()
            time.sleep(3)  # Check every 3 seconds
            
    def start(self):
        """Start USB monitoring"""
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.monitor_usb_devices, daemon=True)
            self.thread.start()
            print("USB monitoring started")
            return True
        return False
        
    def stop(self):
        """Stop USB monitoring"""
        if self.running:
            self.running = False
            
            # Cleanup USB observers
            for observer in self.observers.values():
                try:
                    observer.stop()
                    observer.join(timeout=5)  # Wait up to 5 seconds
                except:
                    pass
            self.observers.clear()
            
            # Cleanup PC observers
            self.cleanup_pc_monitoring()
            
            # Wait for monitoring thread to finish
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Wait up to 5 seconds
                
            print("USB monitoring stopped")
            return True
        return False 
import os
import time
import threading
from datetime import datetime
import psutil

class USBMonitor:
    def __init__(self):
        self.log_dir = "logs"
        self.previous_devices = set()
        self.ensure_log_directory()
        
    def ensure_log_directory(self):
        """Create logs directory if it doesn't exist"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
            
    def log_event(self, message):
        """Log USB event with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_path = os.path.join(self.log_dir, "usb_log.txt")
        try:
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            print(f"Error writing to USB log: {str(e)}")

    def get_removable_devices(self):
        """Get set of currently connected removable devices"""
        devices = set()
        try:
            for partition in psutil.disk_partitions():
                if 'removable' in partition.opts.lower() or 'cdrom' in partition.opts.lower():
                    devices.add(partition.device)
        except Exception as e:
            self.log_event(f"Error getting removable devices: {str(e)}")
        return devices

    def monitor_usb_devices(self):
        """Monitor USB device connections and disconnections"""
        # Initialize previous devices
        self.previous_devices = self.get_removable_devices()
        
        while True:
            try:
                # Get current devices
                current_devices = self.get_removable_devices()
                
                # Check for new devices
                new_devices = current_devices - self.previous_devices
                for device in new_devices:
                    self.log_event(f"USB Device Mounted at {device}")
                
                # Check for removed devices
                removed_devices = self.previous_devices - current_devices
                for device in removed_devices:
                    self.log_event(f"USB Device Removed from {device}")
                
                # Update previous devices
                self.previous_devices = current_devices
                
            except Exception as e:
                self.log_event(f"Error in USB monitoring: {str(e)}")
            
            time.sleep(5)

    def start(self):
        """Start USB monitoring in a daemon thread"""
        monitor_thread = threading.Thread(target=self.monitor_usb_devices, daemon=True)
        monitor_thread.start()
        return monitor_thread 
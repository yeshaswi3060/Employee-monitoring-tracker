# system_lock_overlay.py
# System Lock Overlay Application
# This creates a full-screen overlay when system is locked
# MADE BY YESHASWI SINGH

import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
import time
from datetime import datetime

class SystemLockOverlay:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("System Locked")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(bg='black')
        
        # Prevent closing with Alt+F4
        self.root.protocol("WM_DELETE_WINDOW", lambda: None)
        
        # Disable Alt+Tab and other system shortcuts
        self.root.bind('<Alt-Tab>', lambda e: "break")
        self.root.bind('<Control-Alt-Delete>', lambda e: "break")
        self.root.bind('<Alt-F4>', lambda e: "break")
        self.root.bind('<Escape>', lambda e: "break")
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg='black')
        self.main_frame.pack(expand=True, fill='both')
        
        # Create lock message
        self.lock_label = tk.Label(
            self.main_frame,
            text="🔒 SYSTEM LOCKED 🔒",
            font=('Arial', 48, 'bold'),
            fg='red',
            bg='black'
        )
        self.lock_label.pack(pady=100)
        
        # Create message
        self.message_label = tk.Label(
            self.main_frame,
            text="This system has been locked by the administrator.\nUnauthorized access is prohibited.",
            font=('Arial', 16),
            fg='white',
            bg='black',
            justify=tk.CENTER
        )
        self.message_label.pack(pady=20)
        
        # Create password entry
        self.password_frame = tk.Frame(self.main_frame, bg='black')
        self.password_frame.pack(pady=50)
        
        self.password_label = tk.Label(
            self.password_frame,
            text="Enter Password to Unlock:",
            font=('Arial', 16),
            fg='white',
            bg='black'
        )
        self.password_label.pack()
        
        self.password_entry = tk.Entry(
            self.password_frame,
            font=('Arial', 16),
            show='*',
            width=30,
            justify=tk.CENTER
        )
        self.password_entry.pack(pady=10)
        self.password_entry.focus()
        
        # Bind Enter key to unlock
        self.password_entry.bind('<Return>', self.check_password)
        
        # Create unlock button
        self.unlock_button = tk.Button(
            self.password_frame,
            text="🔓 Unlock System",
            font=('Arial', 14),
            command=self.check_password,
            bg='green',
            fg='white',
            width=20,
            height=2
        )
        self.unlock_button.pack(pady=10)
        
        # Create time display
        self.time_label = tk.Label(
            self.main_frame,
            font=('Arial', 14),
            fg='gray',
            bg='black'
        )
        self.time_label.pack(side=tk.BOTTOM, pady=20)
        
        # Update time
        self.update_time()
        
        # Start monitoring for unlock command
        self.monitor_thread = threading.Thread(target=self.monitor_unlock, daemon=True)
        self.monitor_thread.start()
        
        # Capture all mouse and keyboard events
        self.root.grab_set()
        
    def update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=f"Current Time: {current_time}")
        self.root.after(1000, self.update_time)
        
    def check_password(self, event=None):
        """Check if the entered password is correct"""
        password = self.password_entry.get()
        if password == 'yeshaswigod':
            self.unlock_system()
        else:
            # Clear the password field
            self.password_entry.delete(0, tk.END)
            self.password_entry.focus()
            
            # Show error message
            error_label = tk.Label(
                self.password_frame,
                text="❌ Invalid Password!",
                font=('Arial', 12),
                fg='red',
                bg='black'
            )
            error_label.pack()
            
            # Remove error message after 3 seconds
            self.root.after(3000, error_label.destroy)
    
    def unlock_system(self):
        """Unlock the system"""
        try:
            # Log unlock action
            log_dir = 'logs'
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
                
            with open(os.path.join(log_dir, 'remote_control_log.txt'), 'a') as f:
                f.write(f"[{datetime.now()}] System unlocked via password overlay\n")
            
            # Remove lock flag
            lock_flag_file = os.path.join(log_dir, 'lock_system.flag')
            if os.path.exists(lock_flag_file):
                os.remove(lock_flag_file)
                
        except Exception as e:
            print(f"Error during unlock: {e}")
        
        # Close the overlay
        self.root.destroy()
    
    def monitor_unlock(self):
        """Monitor for unlock command from web interface"""
        while True:
            try:
                unlock_file = os.path.join('logs', 'unlock_system.flag')
                if os.path.exists(unlock_file):
                    # Remove the flag file
                    os.remove(unlock_file)
                    # Unlock the system
                    self.root.after(0, self.unlock_system)
                    break
            except Exception as e:
                print(f"Error monitoring unlock: {e}")
            time.sleep(1)
    
    def run(self):
        """Run the lock overlay"""
        try:
            # Make sure the window stays on top and captures all input
            self.root.lift()
            self.root.attributes('-topmost', True)
            self.root.focus_force()
            
            # Start the main loop
            self.root.mainloop()
        except Exception as e:
            print(f"Error running lock overlay: {e}")

def main():
    """Main function to run the lock overlay"""
    try:
        # Check if lock flag exists
        lock_flag_file = os.path.join('logs', 'lock_system.flag')
        if not os.path.exists(lock_flag_file):
            print("Lock flag not found, system is not locked")
            return
            
        # Create and run the lock overlay
        lock_overlay = SystemLockOverlay()
        lock_overlay.run()
        
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()

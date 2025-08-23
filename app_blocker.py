# app_blocker.py
# Application Blocker
# This monitors and blocks specified applications
# MADE BY YESHASWI SINGH

import os
import json
import time
import threading
import psutil
import subprocess
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

class ApplicationBlocker:
    def __init__(self):
        self.blocked_apps_file = os.path.join('logs', 'blocked_apps.json')
        self.blocked_apps = self.load_blocked_apps()
        self.running = True
        self.monitor_thread = None
        self.log_file = os.path.join('logs', 'app_blocker_log.txt')
        
        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)
        
    def load_blocked_apps(self):
        """Load blocked applications from file"""
        try:
            if os.path.exists(self.blocked_apps_file):
                with open(self.blocked_apps_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading blocked apps: {e}")
        return []
    
    def save_blocked_apps(self):
        """Save blocked applications to file"""
        try:
            with open(self.blocked_apps_file, 'w') as f:
                json.dump(self.blocked_apps, f)
        except Exception as e:
            print(f"Error saving blocked apps: {e}")
    
    def is_app_blocked(self, process_name):
        """Check if an application is blocked"""
        return process_name.lower() in [app.lower() for app in self.blocked_apps]
    
    def block_application(self, app_name):
        """Add application to blocked list"""
        if app_name not in self.blocked_apps:
            self.blocked_apps.append(app_name)
            self.save_blocked_apps()
            self.log_action(f"Application blocked: {app_name}")
    
    def unblock_application(self, app_name):
        """Remove application from blocked list"""
        if app_name in self.blocked_apps:
            self.blocked_apps.remove(app_name)
            self.save_blocked_apps()
            self.log_action(f"Application unblocked: {app_name}")
    
    def log_action(self, message):
        """Log blocking actions"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Error logging action: {e}")
    
    def show_blocked_message(self, app_name):
        """Show blocked application message with password option"""
        try:
            # Create a simple Tkinter dialog
            root = tk.Tk()
            root.withdraw()  # Hide the main window
            
            # Create custom dialog
            dialog = tk.Toplevel(root)
            dialog.title("Application Blocked")
            dialog.geometry("400x300")
            dialog.resizable(False, False)
            dialog.configure(bg='red')
            
            # Make it stay on top
            dialog.attributes('-topmost', True)
            dialog.grab_set()
            
            # Blocked message
            blocked_label = tk.Label(
                dialog,
                text="🚫 APPLICATION BLOCKED 🚫",
                font=('Arial', 16, 'bold'),
                fg='white',
                bg='red'
            )
            blocked_label.pack(pady=20)
            
            app_label = tk.Label(
                dialog,
                text=f"Application: {app_name}",
                font=('Arial', 12),
                fg='white',
                bg='red'
            )
            app_label.pack(pady=10)
            
            message_label = tk.Label(
                dialog,
                text="This application has been blocked\nby the system administrator.",
                font=('Arial', 10),
                fg='white',
                bg='red',
                justify=tk.CENTER
            )
            message_label.pack(pady=10)
            
            # Password frame
            password_frame = tk.Frame(dialog, bg='red')
            password_frame.pack(pady=20)
            
            password_label = tk.Label(
                password_frame,
                text="Enter admin password to unblock:",
                font=('Arial', 10),
                fg='white',
                bg='red'
            )
            password_label.pack()
            
            password_entry = tk.Entry(
                password_frame,
                show='*',
                font=('Arial', 10),
                width=20
            )
            password_entry.pack(pady=5)
            password_entry.focus()
            
            # Buttons frame
            buttons_frame = tk.Frame(dialog, bg='red')
            buttons_frame.pack(pady=10)
            
            def check_password():
                password = password_entry.get()
                if password == 'yeshaswigod':
                    # Temporarily unblock the app for this session
                    self.log_action(f"Temporary unblock granted for {app_name} with admin password")
                    messagebox.showinfo("Access Granted", f"{app_name} has been temporarily unblocked for this session.")
                    dialog.destroy()
                    root.destroy()
                    return True
                else:
                    messagebox.showerror("Access Denied", "Invalid password!")
                    password_entry.delete(0, tk.END)
                    password_entry.focus()
                    return False
            
            def close_dialog():
                dialog.destroy()
                root.destroy()
            
            # Bind Enter key to password check
            password_entry.bind('<Return>', lambda e: check_password())
            
            unlock_button = tk.Button(
                buttons_frame,
                text="Unlock",
                command=check_password,
                bg='green',
                fg='white',
                width=10
            )
            unlock_button.pack(side=tk.LEFT, padx=5)
            
            close_button = tk.Button(
                buttons_frame,
                text="Close",
                command=close_dialog,
                bg='gray',
                fg='white',
                width=10
            )
            close_button.pack(side=tk.LEFT, padx=5)
            
            # Center the dialog
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Auto-close after 30 seconds
            dialog.after(30000, close_dialog)
            
            dialog.mainloop()
            
        except Exception as e:
            print(f"Error showing blocked message: {e}")
            # Fallback to simple message box
            try:
                subprocess.run([
                    'powershell', 
                    f'Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show("Application \'{app_name}\' is blocked by system administrator.\\n\\nPassword: yeshaswigod", "Application Blocked", [System.Windows.Forms.MessageBoxButtons]::OK, [System.Windows.Forms.MessageBoxIcon]::Warning)'
                ], shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            except:
                pass
    
    def monitor_processes(self):
        """Monitor running processes and block specified applications"""
        temporary_allowed = set()  # Store temporarily allowed apps
        
        while self.running:
            try:
                # Reload blocked apps in case they were updated
                self.blocked_apps = self.load_blocked_apps()
                
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_info = proc.info
                        process_name = proc_info['name']
                        pid = proc_info['pid']
                        
                        # Skip if temporarily allowed
                        if process_name in temporary_allowed:
                            continue
                        
                        if self.is_app_blocked(process_name):
                            # Kill the blocked process
                            try:
                                proc.terminate()
                                self.log_action(f"Blocked and terminated: {process_name} (PID: {pid})")
                                
                                # Show blocked message in a separate thread
                                threading.Thread(
                                    target=self.show_blocked_message, 
                                    args=(process_name,),
                                    daemon=True
                                ).start()
                                
                            except (psutil.NoSuchProcess, psutil.AccessDenied):
                                continue
                            
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                        
            except Exception as e:
                print(f"Error monitoring processes: {e}")
            
            time.sleep(2)  # Check every 2 seconds
    
    def start(self):
        """Start the application blocker"""
        if not self.running:
            self.running = True
            
        self.monitor_thread = threading.Thread(target=self.monitor_processes, daemon=True)
        self.monitor_thread.start()
        self.log_action("Application blocker started")
        print("Application blocker started")
    
    def stop(self):
        """Stop the application blocker"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        self.log_action("Application blocker stopped")
        print("Application blocker stopped")

def main():
    """Main function to run the application blocker"""
    try:
        blocker = ApplicationBlocker()
        blocker.start()
        
        print("Application Blocker is running...")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Stopping application blocker...")
            blocker.stop()
            
    except Exception as e:
        print(f"Error in main: {e}")

if __name__ == "__main__":
    main()

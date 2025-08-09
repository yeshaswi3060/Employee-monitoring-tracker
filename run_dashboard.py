import os
import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import DateEntry
from datetime import datetime, timedelta
import json
import re
from collections import defaultdict
from PIL import Image, ImageTk
import cv2
import threading

from file_transfer_monitor import FileTransferMonitor
from webcam_capture import WebcamCapture

class ScreenshotViewer:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Screenshots")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Configure grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Load screenshots
        self.load_screenshots()
        
    def load_screenshots(self):
        """Load and display screenshots"""
        # Check both possible screenshot directories
        screenshot_dirs = [
            os.path.join("logs", "screenshots"),  # Old location
            "screenshots",  # New location
        ]
        
        screenshots = []
        found_dir = None
        
        for directory in screenshot_dirs:
            print(f"Checking screenshot directory: {directory}")  # Debug log
            if os.path.exists(directory):
                found_dir = directory
                print(f"Found screenshot directory: {directory}")  # Debug log
                try:
                    for filename in os.listdir(directory):
                        if filename.endswith((".png", ".jpg", ".jpeg")):
                            filepath = os.path.join(directory, filename)
                            # Extract timestamp from filename
                            timestamp = self.extract_timestamp(filename)
                            screenshots.append((timestamp, filepath))
                            print(f"Found screenshot: {filepath}")  # Debug log
                except Exception as e:
                    print(f"Error reading directory {directory}: {e}")  # Debug log
        
        if not found_dir:
            print("Creating screenshots directory")  # Debug log
            # Create screenshots directory if it doesn't exist
            os.makedirs("screenshots", exist_ok=True)
            messagebox.showinfo("Info", "No screenshots available yet. Screenshots will be saved in the 'screenshots' folder.")
            return
            
        if not screenshots:
            print("No screenshots found in directories")  # Debug log
            messagebox.showinfo("Info", "No screenshots available yet.")
            return
            
        # Sort by timestamp (newest first)
        screenshots.sort(reverse=True)
        print(f"Total screenshots found: {len(screenshots)}")  # Debug log
        
        # Display screenshots
        for i, (timestamp, filepath) in enumerate(screenshots):
            try:
                # Create frame for this screenshot
                frame = ttk.Frame(self.scrollable_frame)
                frame.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
                frame.grid_columnconfigure(0, weight=1)
                
                # Load and resize image
                img = Image.open(filepath)
                img.thumbnail((320, 240))  # Resize to thumbnail
                photo = ImageTk.PhotoImage(img)
                
                # Create label for thumbnail
                img_label = ttk.Label(frame, image=photo)
                img_label.image = photo  # Keep reference
                img_label.grid(row=0, column=0, padx=5)
                
                # Add timestamp
                timestamp_label = ttk.Label(frame, text=timestamp)
                timestamp_label.grid(row=1, column=0, padx=5)
                
                # Bind click event to show full image
                img_label.bind("<Button-1>", lambda e, fp=filepath: self.show_full_image(fp))
                
            except Exception as e:
                print(f"Error loading screenshot {filepath}: {e}")  # Debug log
                
    def extract_timestamp(self, filename):
        """Extract timestamp from filename"""
        try:
            # Remove extension
            name = os.path.splitext(filename)[0]
            
            # Handle different filename formats
            if "screenshot_" in name:
                # Format: screenshot_YYYYMMDD_HHMMSS
                ts = name.split("screenshot_")[1]
                dt = datetime.strptime(ts, "%Y%m%d_%H%M%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                # Try to parse the filename as a timestamp
                return name.replace("_", " ")
        except:
            return filename  # Return filename if parsing fails
                
    def show_full_image(self, filepath):
        """Show full-size image in new window"""
        try:
            img = Image.open(filepath)
            
            # Create new window
            img_window = tk.Toplevel(self.window)
            img_window.title("Full Screenshot")
            
            # Calculate window size (max 80% of screen)
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            
            # Resize image if needed
            img_width, img_height = img.size
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width/img_width, max_height/img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Create and pack label
            label = ttk.Label(img_window, image=photo)
            label.image = photo  # Keep reference
            label.pack(padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening image: {str(e)}")

class WebcamViewer:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("Webcam Captures")
        self.window.geometry("800x600")
        self.window.minsize(600, 400)
        
        # Configure grid
        self.window.grid_rowconfigure(0, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create main frame
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Create canvas and scrollbar
        self.canvas = tk.Canvas(self.main_frame)
        self.scrollbar = ttk.Scrollbar(self.main_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Grid layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        # Add refresh button
        self.refresh_btn = ttk.Button(
            self.window,
            text="Refresh",
            command=self.refresh_images
        )
        self.refresh_btn.grid(row=1, column=0, pady=5)
        
        # Load images
        self.load_images()
        
        # Start auto-refresh
        self.schedule_refresh()
        
    def clear_images(self):
        """Clear all images from the scrollable frame"""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
    def refresh_images(self):
        """Refresh the images display"""
        self.clear_images()
        self.load_images()
        
    def schedule_refresh(self):
        """Schedule periodic refresh of images"""
        self.window.after(5000, self.refresh_callback)  # Refresh every 5 seconds
        
    def refresh_callback(self):
        """Callback for periodic refresh"""
        self.refresh_images()
        self.schedule_refresh()  # Schedule next refresh
        
    def load_images(self):
        """Load and display webcam captures"""
        webcam_dir = os.path.join("WebcamLogs")
        if not os.path.exists(webcam_dir):
            messagebox.showinfo("Info", "No webcam captures available.")
            return
            
        # Get list of images
        images = []
        for filename in os.listdir(webcam_dir):
            if filename.endswith((".jpg", ".png")):
                filepath = os.path.join(webcam_dir, filename)
                timestamp = filename.split(".")[0]  # Remove extension
                images.append((timestamp, filepath))
                
        # Sort by timestamp (newest first)
        images.sort(reverse=True)
        
        # Display images
        for i, (timestamp, filepath) in enumerate(images):
            try:
                # Create frame for this image
                frame = ttk.Frame(self.scrollable_frame)
                frame.grid(row=i, column=0, padx=10, pady=10, sticky="ew")
                frame.grid_columnconfigure(0, weight=1)
                
                # Load and resize image
                img = Image.open(filepath)
                img.thumbnail((320, 240))  # Resize to thumbnail
                photo = ImageTk.PhotoImage(img)
                
                # Create label for thumbnail
                img_label = ttk.Label(frame, image=photo)
                img_label.image = photo  # Keep reference
                img_label.grid(row=0, column=0, padx=5)
                
                # Add timestamp
                timestamp_label = ttk.Label(frame, text=timestamp)
                timestamp_label.grid(row=1, column=0, padx=5)
                
                # Bind click event to show full image
                img_label.bind("<Button-1>", lambda e, fp=filepath: self.show_full_image(fp))
                
            except Exception as e:
                print(f"Error loading image {filepath}: {str(e)}")
                
    def show_full_image(self, filepath):
        """Show full-size image in new window"""
        try:
            img = Image.open(filepath)
            
            # Create new window
            img_window = tk.Toplevel(self.window)
            img_window.title("Full Image")
            
            # Calculate window size (max 80% of screen)
            screen_width = self.window.winfo_screenwidth()
            screen_height = self.window.winfo_screenheight()
            max_width = int(screen_width * 0.8)
            max_height = int(screen_height * 0.8)
            
            # Resize image if needed
            img_width, img_height = img.size
            if img_width > max_width or img_height > max_height:
                ratio = min(max_width/img_width, max_height/img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(img)
            
            # Create and pack label
            label = ttk.Label(img_window, image=photo)
            label.image = photo  # Keep reference
            label.pack(padx=10, pady=10)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error opening image: {str(e)}")

class WebcamCapture:
    def __init__(self):
        self.running = False
        self.timer = None
        self.capture_thread = None
        
    def start(self):
        """Start webcam capture if not already running"""
        if not self.running:
            self.running = True
            self.ensure_directory()
            self.schedule_capture()
            
    def stop(self):
        """Stop webcam capture"""
        self.running = False
        if self.timer:
            self.timer.cancel()
            
    def ensure_directory(self):
        """Create WebcamLogs directory if it doesn't exist"""
        os.makedirs("WebcamLogs", exist_ok=True)
        
    def capture_image(self):
        """Capture image from webcam"""
        try:
            # Initialize webcam
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("Error: Could not open webcam")
                return
                
            # Capture frame
            ret, frame = cap.read()
            if ret:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join("WebcamLogs", f"{timestamp}.jpg")
                
                # Save image
                cv2.imwrite(filename, frame)
                
            # Release webcam
            cap.release()
            
        except Exception as e:
            print(f"Error capturing image: {str(e)}")
            
        finally:
            # Schedule next capture if still running
            if self.running:
                self.schedule_capture()
                
    def schedule_capture(self):
        """Schedule next capture after 1 hour"""
        if self.running:
            self.timer = threading.Timer(3600, self.capture_thread_wrapper)  # 3600 seconds = 1 hour
            self.timer.daemon = True
            self.timer.start()
            
    def capture_thread_wrapper(self):
        """Wrapper to run capture in separate thread"""
        self.capture_thread = threading.Thread(target=self.capture_image)
        self.capture_thread.daemon = True
        self.capture_thread.start()

class FileTransferMonitor:
    def __init__(self):
        self.running = False
        self.timer = None
        self.monitor_thread = None
        self.transfers = []
        self.lock = threading.Lock()
        
    def start(self):
        """Start file transfer monitoring if not already running"""
        if not self.running:
            self.running = True
            self.ensure_directory()
            self.schedule_monitor()
            
    def stop(self):
        """Stop file transfer monitoring"""
        self.running = False
        if self.timer:
            self.timer.cancel()
            
    def ensure_directory(self):
        """Create FileTransferLogs directory if it doesn't exist"""
        os.makedirs("FileTransferLogs", exist_ok=True)
        
    def monitor_files(self):
        """Monitor file transfer activity in the system"""
        try:
            # This is a placeholder for actual file monitoring logic
            # In a real application, you would use a library like pywin32 or psutil
            # to monitor file system events (create, write, delete, move)
            
            # Simulate file transfers
            self.add_transfer("2023-10-27 10:00:00", "report.pdf", "1.2MB", "Download", "www.example.com")
            self.add_transfer("2023-10-27 10:05:00", "image.jpg", "500KB", "Upload", "www.example.com")
            self.add_transfer("2023-10-27 10:10:00", "data.zip", "2.5MB", "Download", "www.example.com")
            self.add_transfer("2023-10-27 10:15:00", "video.mp4", "100MB", "Upload", "www.example.com")
            
            # In a real application, you would use a library to listen for system events
            # and parse them to identify file transfers.
            # For example, psutil.events.file_io() or pywin32.WinEventHook
            
        except Exception as e:
            print(f"Error during file monitoring: {str(e)}")
            
    def add_transfer(self, time_str, filename, size, direction, website):
        """Add a new file transfer to the list"""
        with self.lock:
            self.transfers.append({
                "time": time_str,
                "filename": filename,
                "size": size,
                "direction": direction,
                "website": website
            })
            
    def get_filtered_transfers(self, filter_type):
        """Get file transfers filtered by time range"""
        with self.lock:
            filtered_transfers = []
            for transfer in self.transfers:
                transfer_time = datetime.strptime(transfer["time"], "%Y-%m-%d %H:%M:%S")
                
                if filter_type == "all":
                    filtered_transfers.append(transfer)
                elif filter_type == "today":
                    if transfer_time.date() == datetime.now().date():
                        filtered_transfers.append(transfer)
                elif filter_type == "week":
                    if transfer_time.date() >= (datetime.now().date() - timedelta(days=7)):
                        filtered_transfers.append(transfer)
            return filtered_transfers
            
    def schedule_monitor(self):
        """Schedule next monitoring cycle"""
        if self.running:
            self.timer = threading.Timer(10, self.monitor_thread_wrapper) # Monitor every 10 seconds
            self.timer.daemon = True
            self.timer.start()
            
    def monitor_thread_wrapper(self):
        """Wrapper to run monitoring in a separate thread"""
        self.monitor_thread = threading.Thread(target=self.monitor_files)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

class FileTransferViewer:
    def __init__(self, parent, file_monitor):
        self.window = tk.Toplevel(parent)
        self.window.title("File Transfers")
        self.window.geometry("1000x600")
        self.window.minsize(800, 400)
        
        # Store file monitor reference
        self.file_monitor = file_monitor
        
        # Configure grid
        self.window.grid_rowconfigure(1, weight=1)
        self.window.grid_columnconfigure(0, weight=1)
        
        # Create control panel
        self.create_control_panel()
        
        # Create transfer table
        self.create_transfer_table()
        
        # Set default filter
        self.current_filter = "all"
        
        # Load initial data
        self.refresh_data()
        
    def create_control_panel(self):
        """Create the control panel with filter options and refresh button"""
        control_frame = ttk.Frame(self.window, padding="5")
        control_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        # Filter options
        ttk.Label(control_frame, text="Show:").pack(side="left", padx=5)
        
        self.filter_var = tk.StringVar(value="all")
        for text, value in [("All Time", "all"), ("Today", "today"), ("This Week", "week")]:
            rb = ttk.Radiobutton(
                control_frame,
                text=text,
                value=value,
                variable=self.filter_var,
                command=self.refresh_data
            )
            rb.pack(side="left", padx=5)
            
        # Refresh button
        refresh_btn = ttk.Button(
            control_frame,
            text="↻ Refresh",
            command=self.refresh_data
        )
        refresh_btn.pack(side="right", padx=5)
        
    def create_transfer_table(self):
        """Create the transfer table with scrollbar"""
        # Create frame for table and scrollbar
        table_frame = ttk.Frame(self.window)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)
        
        # Create treeview
        self.tree = ttk.Treeview(table_frame, show="headings")
        
        # Define columns
        self.tree["columns"] = ("time", "filename", "size", "direction", "website")
        
        # Configure columns
        self.tree.column("time", width=150)
        self.tree.column("filename", width=300)
        self.tree.column("size", width=100)
        self.tree.column("direction", width=100)
        self.tree.column("website", width=200)
        
        # Configure headings
        self.tree.heading("time", text="Time")
        self.tree.heading("filename", text="File Name")
        self.tree.heading("size", text="Size")
        self.tree.heading("direction", text="Direction")
        self.tree.heading("website", text="Website")
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
    def refresh_data(self):
        """Refresh the transfer data"""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # Get filtered transfers
        transfers = self.file_monitor.get_filtered_transfers(self.filter_var.get())
        
        # Add transfers to tree
        for transfer in transfers:
            self.tree.insert(
                "",
                "end",
                values=(
                    transfer["time"],
                    transfer["filename"],
                    transfer["size"],
                    transfer["direction"],
                    transfer["website"]
                )
            )

class LogViewerDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Employee Monitor Dashboard")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Configure root grid
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Available log files
        self.log_files = {
            "Keystrokes": "keyboard_log.txt",
            "Internet Usage": "internet_usage_log.txt",
            "Website Activity": "website_log.txt",
            "USB Events": "usb_activity_log.txt",
            "Window Activity": "window_log.txt"
        }
        
        self.current_log_type = None
        
        # Initialize monitors
        self.webcam = WebcamCapture()
        self.file_monitor = FileTransferMonitor()
        self.file_monitor.start()
        
        # Create frames
        self.create_button_panel()
        self.create_filter_frame()
        self.create_log_viewer_frame()

    def create_button_panel(self):
        """Create the button panel at the top"""
        button_frame = ttk.Frame(self.root, padding="5")
        button_frame.grid(row=0, column=0, sticky="ew")
        
        # Configure columns for even spacing
        num_columns = len(self.log_files) + 2  # +2 for Screenshots and Webcam
        for i in range(num_columns):
            button_frame.grid_columnconfigure(i, weight=1)
            
        # Create buttons for each log type
        for i, (log_type, _) in enumerate(self.log_files.items()):
            btn = ttk.Button(
                button_frame,
                text=log_type,
                command=lambda t=log_type: self.select_log_type(t),
                width=15
            )
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
        # Add Screenshots button
        screenshots_btn = ttk.Button(
            button_frame,
            text="Screenshots",
            command=self.show_screenshots,
            width=15
        )
        screenshots_btn.grid(row=0, column=len(self.log_files), padx=5, pady=5, sticky="ew")
        
        # Add Webcam button
        webcam_btn = ttk.Button(
            button_frame,
            text="Webcam",
            command=self.show_webcam,
            width=15
        )
        webcam_btn.grid(row=0, column=len(self.log_files) + 1, padx=5, pady=5, sticky="ew")
        
        # Start monitors
        self.webcam.start()

    def create_filter_frame(self):
        """Create the date & time filter section"""
        filter_frame = ttk.LabelFrame(self.root, text="Date & Time Filters", padding="10")
        filter_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
        
        # Configure grid columns for even spacing
        for i in range(8):
            filter_frame.grid_columnconfigure(i, weight=1)
            
        # Start Date
        ttk.Label(filter_frame, text="Start Date:").grid(row=0, column=0, padx=5, pady=5)
        self.start_date = DateEntry(filter_frame, width=12, background='darkblue',
                                  foreground='white', borderwidth=2)
        self.start_date.grid(row=0, column=1, padx=5, pady=5)
        
        # Start Time
        ttk.Label(filter_frame, text="Start Time:").grid(row=0, column=2, padx=5, pady=5)
        self.start_time = ttk.Entry(filter_frame, width=8)
        self.start_time.insert(0, "00:00")
        self.start_time.grid(row=0, column=3, padx=5, pady=5)
        
        # End Date
        ttk.Label(filter_frame, text="End Date:").grid(row=0, column=4, padx=5, pady=5)
        self.end_date = DateEntry(filter_frame, width=12, background='darkblue',
                                foreground='white', borderwidth=2)
        self.end_date.grid(row=0, column=5, padx=5, pady=5)
        
        # End Time
        ttk.Label(filter_frame, text="End Time:").grid(row=0, column=6, padx=5, pady=5)
        self.end_time = ttk.Entry(filter_frame, width=8)
        self.end_time.insert(0, "23:59")
        self.end_time.grid(row=0, column=7, padx=5, pady=5)
        
        # Filter button
        filter_btn = ttk.Button(filter_frame, text="Filter Logs", command=self.filter_logs)
        filter_btn.grid(row=0, column=8, padx=5, pady=5)

    def create_log_viewer_frame(self):
        """Create the log viewer section with TreeView"""
        viewer_frame = ttk.LabelFrame(self.root, text="Log Viewer", padding="10")
        viewer_frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Configure viewer frame grid
        viewer_frame.grid_rowconfigure(0, weight=1)
        viewer_frame.grid_columnconfigure(0, weight=1)
        
        # Create TreeView
        self.tree = ttk.Treeview(viewer_frame)
        
        # Add vertical scrollbar
        scrollbar = ttk.Scrollbar(viewer_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Grid layout
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")

    def filter_log_content(self, log_content):
        """Filter log content based on date/time range"""
        try:
            # Get filter dates and times
            start_date = self.start_date.get_date()
            end_date = self.end_date.get_date()
            
            try:
                start_time = datetime.strptime(self.start_time.get(), "%H:%M").time()
                end_time = datetime.strptime(self.end_time.get(), "%H:%M").time()
            except ValueError:
                messagebox.showwarning("Warning", "Invalid time format. Using full day range.")
                start_time = datetime.strptime("00:00", "%H:%M").time()
                end_time = datetime.strptime("23:59", "%H:%M").time()
            
            # Create datetime objects for comparison
            start_datetime = datetime.combine(start_date, start_time)
            end_datetime = datetime.combine(end_date, end_time)
            
            filtered_logs = []
            for line in log_content:
                if line.startswith("["):
                    try:
                        # Extract timestamp
                        timestamp_str = line[1:line.find("]")]
                        log_datetime = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                        
                        # Check if within range
                        if start_datetime <= log_datetime <= end_datetime:
                            filtered_logs.append(line)
                    except ValueError:
                        # If timestamp parsing fails, include the line
                        filtered_logs.append(line)
                else:
                    # Include non-timestamped lines that follow a matched timestamped line
                    if filtered_logs:
                        filtered_logs.append(line)
            
            return filtered_logs
            
        except Exception as e:
            print(f"Error filtering logs: {str(e)}")
            return log_content  # Return unfiltered content on error

    def display_logs(self, log_content):
        """Display log content in TreeView"""
        try:
            if self.current_log_type == "Internet Usage":
                # For Internet Usage, only clear the data if table not yet created
                if not hasattr(self, 'internet_table_created'):
                    self.setup_internet_table()
                    self.internet_table_created = True
                self.update_internet_data(log_content)
            elif self.current_log_type == "Website Activity":
                # Clear existing items
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # Configure columns for website activity
                self.tree["columns"] = ("duration", "title")
                self.tree.column("#0", width=300)  # For browser and website
                self.tree.column("duration", width=150)
                self.tree.column("title", width=450)
                
                self.tree.heading("#0", text="Browser/Website")
                self.tree.heading("duration", text="Duration")
                self.tree.heading("title", text="Page Title")

                # Track browsers and websites
                browsers = {}
                current_browser = None
                current_website = None
                
                for line in log_content:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("["):
                        # Extract timestamp and browser info
                        parts = line.split("]", 1)
                        if len(parts) == 2:
                            info = parts[1].strip()
                            if " - " in info:
                                browser, website = info.split(" - ", 1)
                                browser = browser.strip()
                                website = website.strip()
                                
                                # Create browser node if not exists
                                if browser not in browsers:
                                    browsers[browser] = self.tree.insert("", "end", text=browser, tags=("browser",))
                                current_browser = browser
                                
                                # Create website node
                                current_website = self.tree.insert(browsers[browser], "end", text=website, tags=("website",))
                                
                    elif line.startswith("Title:") and current_website:
                        # Add title to website
                        title = line[6:].strip()
                        self.tree.set(current_website, "title", title)
                    elif line.startswith("Duration:") and current_website:
                        # Add duration to website
                        duration = line[9:].strip()
                        self.tree.set(current_website, "duration", duration)
                
                # Configure tags
                self.tree.tag_configure("browser", foreground="blue")
                self.tree.tag_configure("website", foreground="dark green")
                
            elif self.current_log_type == "Window Activity":
                # Clear existing items
                for item in self.tree.get_children():
                    self.tree.delete(item)
                
                # Configure columns for window activity
                self.tree["columns"] = ("time", "duration")
                self.tree.column("#0", width=300)  # For application name and window title
                self.tree.column("time", width=150)
                self.tree.column("duration", width=150)
                
                self.tree.heading("#0", text="Application/Window")
                self.tree.heading("time", text="Time")
                self.tree.heading("duration", text="Duration")

                # Track applications
                applications = {}
                current_app = None
                
                for line in log_content:
                    line = line.strip()
                    if not line:
                        continue
                        
                    if line.startswith("["):
                        # Extract timestamp and app info
                        parts = line.split("]", 1)
                        if len(parts) == 2:
                            timestamp = parts[0][1:].strip()
                            info = parts[1].strip()
                            
                            # Extract app name and window title
                            if " - " in info:
                                app_name = info.split(" - ")[0].strip()
                                window_title = info.split(" - ", 1)[1].strip()
                                
                                # Create app node if not exists
                                if app_name not in applications:
                                    applications[app_name] = self.tree.insert("", "end", text=app_name, tags=("application",))
                                current_app = applications[app_name]
                                
                                # Add window entry
                                window_item = self.tree.insert(current_app, "end", text=window_title, 
                                                            values=(timestamp, ""), tags=("window",))
                                
                    elif line.startswith("Duration:") and current_app:
                        # Add duration to last window entry
                        duration = line[9:].strip()
                        last_window = self.tree.get_children(current_app)[-1]
                        self.tree.set(last_window, "duration", duration)
                
                # Configure tags
                self.tree.tag_configure("application", foreground="blue")
                self.tree.tag_configure("window", foreground="dark green")
                
            else:
                # For other log types, clear everything and show content
                for item in self.tree.get_children():
                    self.tree.delete(item)
                    
                self.tree["columns"] = ("timestamp", "details")
                self.tree.column("#0", width=0, stretch=False)
                self.tree.column("timestamp", width=150)
                self.tree.column("details", width=850)
                
                self.tree.heading("timestamp", text="Timestamp")
                self.tree.heading("details", text="Details")
                
                # Add log entries
                for line in log_content:
                    line = line.strip()
                    if line:
                        if line.startswith("["):
                            # Extract timestamp and details
                            parts = line.split("]", 1)
                            if len(parts) == 2:
                                timestamp = parts[0][1:]  # Remove [
                                details = parts[1].strip()
                                self.tree.insert("", "end", values=(timestamp, details))
                        else:
                            # Lines without timestamp
                            self.tree.insert("", "end", values=("", line))
                        
        except Exception as e:
            print(f"Error displaying logs: {str(e)}")
            messagebox.showerror("Error", f"Error displaying logs: {str(e)}")

    def setup_internet_table(self):
        """Set up the internet usage table structure"""
        # Configure columns for internet usage
        self.tree["columns"] = ("application", "sent", "received")
        self.tree.column("#0", width=0, stretch=False)
        self.tree.column("application", width=300)
        self.tree.column("sent", width=300)
        self.tree.column("received", width=300)
        
        self.tree.heading("application", text="Application")
        self.tree.heading("sent", text="Data Sent")
        self.tree.heading("received", text="Data Received")
        
        # Initialize storage for row IDs
        self.internet_rows = {}

    def update_internet_data(self, log_content):
        """Update the internet usage data in the existing table"""
        try:
            current_apps = set()  # Track current applications
            
            # Process log content
            for line in log_content:
                line = line.strip()
                if not line or line.startswith("[") or line.startswith("-"):
                    continue
                    
                # Parse application and usage data
                if " - " in line and "|" in line:
                    try:
                        # Split into app name and usage data
                        app_name, usage_data = line.split(" - ", 1)
                        app_name = app_name.strip()
                        
                        # Split usage data into sent and received
                        sent_data = usage_data.split("|")[0].replace("Sent:", "").strip()
                        received_data = usage_data.split("|")[1].replace("Received:", "").strip()
                        
                        # Update or create row for this app
                        if app_name in self.internet_rows:
                            # Update existing row
                            self.tree.item(self.internet_rows[app_name], 
                                         values=(app_name, sent_data, received_data))
                        else:
                            # Create new row
                            row_id = self.tree.insert("", "end", 
                                                    values=(app_name, sent_data, received_data))
                            self.internet_rows[app_name] = row_id
                            
                        current_apps.add(app_name)
                        
                    except Exception as e:
                        print(f"Error parsing internet usage line: {str(e)}")
                        continue
            
            # Remove rows for apps no longer present
            for app_name in list(self.internet_rows.keys()):
                if app_name not in current_apps:
                    self.tree.delete(self.internet_rows[app_name])
                    del self.internet_rows[app_name]
            
            # Sort rows by application name
            rows = [(self.tree.item(item)["values"][0], item) 
                   for item in self.tree.get_children()]
            rows.sort()
            for i, (_, item) in enumerate(rows):
                self.tree.move(item, "", i)
                
        except Exception as e:
            print(f"Error updating internet data: {str(e)}")
            messagebox.showerror("Error", f"Error updating internet data: {str(e)}")

    def select_log_type(self, log_type):
        """Handle log type selection"""
        try:
            # If switching away from Internet Usage, clear the table creation flag
            if self.current_log_type == "Internet Usage" and log_type != "Internet Usage":
                if hasattr(self, 'internet_table_created'):
                    delattr(self, 'internet_table_created')
                if hasattr(self, 'internet_rows'):
                    delattr(self, 'internet_rows')
            
            self.current_log_type = log_type
            log_file = self.log_files.get(log_type)
            
            if not log_file:
                return
                
            # Read log file content
            log_path = os.path.join("logs", log_file)
            if not os.path.exists(log_path):
                self.tree.delete(*self.tree.get_children())
                self.tree.insert("", "end", text="No log file found")
                return
                
            with open(log_path, "r", encoding="utf-8") as f:
                log_content = f.readlines()
                
            # Filter logs if date/time filters are set
            if hasattr(self, 'start_date') and hasattr(self, 'end_date'):
                filtered_logs = self.filter_log_content(log_content)
            else:
                filtered_logs = log_content
                
            # Display logs
            self.display_logs(filtered_logs)
            
            # If Internet Usage, set up auto-refresh
            if log_type == "Internet Usage":
                self.schedule_internet_refresh()
                
        except Exception as e:
            print(f"Error showing log: {str(e)}")
            messagebox.showerror("Error", f"Error showing log: {str(e)}")

    def filter_logs(self):
        """Apply date/time filters to current log view"""
        if self.current_log_type:
            self.select_log_type(self.current_log_type)
        else:
            messagebox.showinfo("Info", "Please select a log type first.")

    def show_screenshots(self):
        """Open screenshot viewer window"""
        ScreenshotViewer(self.root)

    def show_webcam(self):
        """Open webcam viewer window"""
        WebcamViewer(self.root)

    def schedule_internet_refresh(self):
        """Schedule periodic refresh of internet usage data"""
        if self.current_log_type == "Internet Usage":
            # Read and update data
            log_path = os.path.join("logs", self.log_files["Internet Usage"])
            if os.path.exists(log_path):
                with open(log_path, "r", encoding="utf-8") as f:
                    log_content = f.readlines()
                self.update_internet_data(log_content)
            
            # Schedule next update in 5 seconds
            self.root.after(5000, self.schedule_internet_refresh)

    def __del__(self):
        """Cleanup when dashboard is closed"""
        if hasattr(self, 'webcam'):
            self.webcam.stop()
        if hasattr(self, 'file_monitor'):
            self.file_monitor.stop()
            
def main():
    root = tk.Tk()
    app = LogViewerDashboard(root)
    root.mainloop()

if __name__ == "__main__":
    main() 
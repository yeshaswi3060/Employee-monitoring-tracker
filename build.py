import os
import sys
import shutil
import subprocess
from pathlib import Path
import time

def print_step(message, step_type="info"):
    """Print formatted step message"""
    symbols = {
        "info": "ℹ️",
        "progress": "⏳",
        "success": "✅",
        "error": "❌",
        "warning": "⚠️"
    }
    print(f"{symbols.get(step_type, 'ℹ️')} {message}")

def create_readme():
    """Create README.txt with usage instructions"""
    print_step("Creating README.txt...", "progress")
    readme_content = """Employee Monitoring System
=======================

This package contains two executables:
1. monitor.exe - Launches the full monitoring system
2. dashboard.exe - Runs the web-based dashboard only

Quick Start Guide:
----------------
1. Extract all files to a folder
2. Double-click monitor.exe
3. First Time Setup:
   - Enter Monitor Name (e.g., "Office PC 1")
   - Choose Port Number (default: 5050)
4. The system will start automatically and show the dashboard URL
5. Access the dashboard from any device on the same Wi-Fi:
   http://<computer-ip>:<port>
   Example: http://192.168.1.100:5050

Important Notes:
--------------
- Both computer and mobile device must be on the same Wi-Fi network
- Required folders will be created automatically:
  - logs/ (for all activity logs)
  - logs/screenshots/ (for screen captures)
  - WebcamLogs/ (for webcam images)

Troubleshooting:
--------------
1. If dashboard doesn't open:
   - Check if port (default 5050) is available
   - Try a different port number
   - Ensure firewall allows the connection

2. If can't access from mobile:
   - Verify both devices are on same Wi-Fi
   - Try accessing the IP address directly
   - Check Windows Firewall settings

3. If monitoring doesn't start:
   - Run as administrator
   - Check antivirus settings
   - Ensure webcam is available (if using webcam feature)

Security Note:
------------
- All data is stored locally on this computer
- No data is sent to external servers
- Access is limited to devices on the same network

For support or issues, contact your system administrator."""

    with open("dist/README.txt", "w", encoding="utf-8") as f:
        f.write(readme_content)
    print_step("README.txt created successfully", "success")

def run_command(command, description):
    """Run a command and show detailed output"""
    print_step(f"Starting: {description}", "progress")
    
    # Print the command being run
    print(f"Running command: {' '.join(command)}")
    
    try:
        # Run command and capture output in real-time
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Redirect stderr to stdout
            universal_newlines=True,
            bufsize=1,
            encoding='utf-8'
        )

        # Track progress
        start_time = time.time()
        last_output_time = start_time
        
        # Read output line by line
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            
            if line:
                # Strip ANSI color codes and other control characters
                line = line.strip()
                if line:  # Only print non-empty lines
                    print(f"  {line}")
                last_output_time = time.time()
            else:
                # Show progress indicator if no output for a while
                current_time = time.time()
                if current_time - last_output_time > 5:
                    elapsed = int(current_time - start_time)
                    print_step(f"Still working... ({elapsed}s elapsed)", "progress")
                    last_output_time = current_time
                time.sleep(0.1)

        # Get the return code
        return_code = process.wait()
        
        if return_code != 0:
            print_step(f"Command failed with return code {return_code}", "error")
            raise Exception(f"Command failed with return code {return_code}")
            
        print_step(f"Completed: {description} ({int(time.time() - start_time)}s)", "success")
        
    except Exception as e:
        print_step(f"Error running command: {str(e)}", "error")
        raise

def check_requirements():
    """Check and install required packages"""
    print_step("Checking requirements...", "progress")
    required_packages = [
        'pyinstaller',
        'pefile',
        'pywin32-ctypes',
        'altgraph'
    ]
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print_step(f"Installing {package}...", "progress")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    
    print_step("All requirements satisfied", "success")

def build_executables():
    """Build monitor.exe and dashboard.exe"""
    try:
        print_step("\nStarting build process...", "info")
        
        # Check Python version
        if sys.version_info < (3, 10):
            print_step("Error: Python 3.10 or higher is required", "error")
            sys.exit(1)
        
        # Check requirements
        check_requirements()
        
        # Clean dist directory
        if os.path.exists("dist"):
            print_step("Cleaning dist directory...", "progress")
            shutil.rmtree("dist")
        os.makedirs("dist")
        print_step("Dist directory prepared", "success")
        
        # Common PyInstaller options
        common_options = [
            '--noconfirm',
            '--clean',
            '--noconsole',
            '--onefile',
            '--uac-admin',
            '--hidden-import=PIL._tkinter_finder',
            '--log-level=INFO'  # Add this to get more detailed output
        ]
        
        # Data files to include
        print_step("Checking data files...", "progress")
        data_files = [
            ('templates', 'templates'),
            ('static', 'static'),
            ('requirements.txt', '.'),
            ('monitor_config.json', '.') if os.path.exists('monitor_config.json') else None,
            ('logo-1-1.webp', 'static') if os.path.exists('logo-1-1.webp') else None,
            ('static/favicon.ico', 'static') if os.path.exists('static/favicon.ico') else None
        ]
        data_files = [f for f in data_files if f]
        
        # Build monitor.exe
        print_step("Building monitor.exe...", "progress")
        monitor_command = [
            sys.executable,  # Use current Python interpreter
            '-m',
            'PyInstaller',
            'run_monitor.py',
            '--name=monitor',
            *common_options,
            *[f'--add-data={src};{dst}' for src, dst in data_files]
        ]
        run_command(monitor_command, "Building monitor.exe")
        
        # Build dashboard.exe
        print_step("Building dashboard.exe...", "progress")
        dashboard_command = [
            sys.executable,  # Use current Python interpreter
            '-m',
            'PyInstaller',
            'run_dashboard.py',
            '--name=dashboard',
            *common_options,
            *[f'--add-data={src};{dst}' for src, dst in data_files]
        ]
        run_command(dashboard_command, "Building dashboard.exe")
        
        # Create README
        create_readme()
        
        # Create ZIP file
        print_step("Creating ZIP package...", "progress")
        shutil.make_archive("dist/monitor_and_dashboard", "zip", "dist")
        print_step("ZIP package created", "success")
        
        print_step("\nBuild completed successfully!", "success")
        print("\nOutput files in dist/:")
        for file in ["monitor.exe", "dashboard.exe", "monitor_and_dashboard.zip", "README.txt"]:
            if os.path.exists(os.path.join("dist", file)):
                size_mb = os.path.getsize(os.path.join("dist", file)) / (1024 * 1024)
                print(f"- {file} ({size_mb:.1f} MB)")
        
    except Exception as e:
        print_step(f"Build failed: {str(e)}", "error")
        sys.exit(1)

if __name__ == "__main__":
    build_executables() 
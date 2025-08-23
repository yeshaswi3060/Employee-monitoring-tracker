#!/usr/bin/env python3
"""
Test Script for System Control Functions
This script tests the key system control features to ensure they work properly
"""

import os
import sys
import subprocess
import time
import threading
from datetime import datetime

def get_logs_dir():
    """Get the logs directory path, creating it if it doesn't exist"""
    logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir, exist_ok=True)
    return logs_dir

def log_test_action(action):
    """Log test actions"""
    try:
        logs_dir = get_logs_dir()
        with open(os.path.join(logs_dir, 'test_log.txt'), 'a') as f:
            f.write(f"[{datetime.now()}] {action}\n")
        print(f"✅ {action}")
    except Exception as e:
        print(f"❌ Error logging: {e}")

def test_system_lock():
    """Test system lock functionality"""
    print("\n🔒 Testing System Lock...")
    
    try:
        # Create lock flag
        logs_dir = get_logs_dir()
        lock_flag_file = os.path.join(logs_dir, 'lock_system.flag')
        
        with open(lock_flag_file, 'w') as f:
            f.write('locked')
        
        log_test_action("Lock flag created successfully")
        
        # Try to start lock overlay
        try:
            overlay_script = os.path.join(os.path.dirname(__file__), 'system_lock_overlay.py')
            if os.path.exists(overlay_script):
                # Start overlay in background
                process = subprocess.Popen([sys.executable, overlay_script], 
                                        creationflags=subprocess.CREATE_NO_WINDOW)
                log_test_action("Lock overlay started successfully")
                
                # Wait a bit then unlock
                time.sleep(3)
                
                # Create unlock flag
                unlock_flag_file = os.path.join(logs_dir, 'unlock_system.flag')
                with open(unlock_flag_file, 'w') as f:
                    f.write('unlocked')
                
                log_test_action("Unlock flag created")
                
                # Terminate overlay
                process.terminate()
                time.sleep(1)
                if process.poll() is None:
                    process.kill()
                
                log_test_action("Lock overlay terminated")
                
            else:
                log_test_action("Lock overlay script not found")
                
        except Exception as e:
            log_test_action(f"Error starting lock overlay: {e}")
            
    except Exception as e:
        log_test_action(f"Error in system lock test: {e}")

def test_system_commands():
    """Test system command execution"""
    print("\n⚡ Testing System Commands...")
    
    try:
        # Test shutdown command (with delay to prevent actual shutdown)
        result = subprocess.run(['shutdown', '/a'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            log_test_action("Shutdown command accessible")
        else:
            log_test_action("Shutdown command not accessible")
            
        # Test powercfg command
        result = subprocess.run(['powercfg', '/list'], capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            log_test_action("Power management commands accessible")
        else:
            log_test_action("Power management commands not accessible")
            
        # Test rundll32 command
        result = subprocess.run(['rundll32.exe', 'user32.dll,GetSystemMetrics', '0'], 
                              capture_output=True, text=True, shell=True)
        if result.returncode == 0:
            log_test_action("System API commands accessible")
        else:
            log_test_action("System API commands not accessible")
            
    except Exception as e:
        log_test_action(f"Error in system commands test: {e}")

def test_file_operations():
    """Test file operations"""
    print("\n📁 Testing File Operations...")
    
    try:
        logs_dir = get_logs_dir()
        
        # Test file creation
        test_file = os.path.join(logs_dir, 'test_file.txt')
        with open(test_file, 'w') as f:
            f.write('Test content')
        
        if os.path.exists(test_file):
            log_test_action("File creation successful")
            
            # Test file reading
            with open(test_file, 'r') as f:
                content = f.read()
            if content == 'Test content':
                log_test_action("File reading successful")
            
            # Test file deletion
            os.remove(test_file)
            if not os.path.exists(test_file):
                log_test_action("File deletion successful")
        else:
            log_test_action("File creation failed")
            
    except Exception as e:
        log_test_action(f"Error in file operations test: {e}")

def test_permissions():
    """Test system permissions"""
    print("\n🔐 Testing System Permissions...")
    
    try:
        # Test if we can create directories
        logs_dir = get_logs_dir()
        test_dir = os.path.join(logs_dir, 'test_dir')
        
        os.makedirs(test_dir, exist_ok=True)
        if os.path.exists(test_dir):
            log_test_action("Directory creation permission granted")
            os.rmdir(test_dir)
        else:
            log_test_action("Directory creation permission denied")
            
        # Test if we can access system information
        try:
            import psutil
            cpu_percent = psutil.cpu_percent(interval=1)
            log_test_action(f"System monitoring accessible (CPU: {cpu_percent}%)")
        except ImportError:
            log_test_action("psutil not available")
        except Exception as e:
            log_test_action(f"System monitoring error: {e}")
            
    except Exception as e:
        log_test_action(f"Error in permissions test: {e}")

def test_network_access():
    """Test network access"""
    print("\n🌐 Testing Network Access...")
    
    try:
        # Test localhost access
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5050))
        sock.close()
        
        if result == 0:
            log_test_action("Port 5050 is available")
        else:
            log_test_action("Port 5050 is not available")
            
        # Test network interface access
        try:
            import netifaces
            interfaces = netifaces.interfaces()
            log_test_action(f"Network interfaces accessible: {len(interfaces)} found")
        except ImportError:
            log_test_action("netifaces not available")
        except Exception as e:
            log_test_action(f"Network interface error: {e}")
            
    except Exception as e:
        log_test_action(f"Error in network test: {e}")

def main():
    """Run all tests"""
    print("🧪 System Control Function Test Suite")
    print("=" * 50)
    print(f"Testing at: {datetime.now()}")
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Script location: {os.path.dirname(os.path.abspath(__file__))}")
    
    # Run tests
    test_file_operations()
    test_permissions()
    test_network_access()
    test_system_commands()
    test_system_lock()
    
    print("\n" + "=" * 50)
    print("🎯 Test Suite Completed!")
    print("Check the logs/test_log.txt file for detailed results")
    
    # Wait for user input
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()


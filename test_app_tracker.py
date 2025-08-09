#!/usr/bin/env python3
"""
Test script for AppUsageTracker to verify it's working correctly
"""

import time
import sys
import os

# Add current directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app_usage_tracker import AppUsageTracker

def test_app_tracker():
    """Test the AppUsageTracker functionality"""
    print("🧪 Testing AppUsageTracker...")
    print("=" * 50)
    
    # Create tracker instance
    tracker = AppUsageTracker()
    
    print("1. Testing window detection...")
    for i in range(5):
        app_name = tracker.get_active_window_name()
        print(f"   Active app: {app_name}")
        time.sleep(2)
    
    print("\n2. Testing tracking functionality...")
    print("   Starting tracker for 10 seconds...")
    print("   Please switch between different applications during this time.")
    
    # Start tracking
    if tracker.start():
        print("   ✓ Tracker started successfully")
        
        # Let it run for 10 seconds
        time.sleep(10)
        
        # Stop tracking
        tracker.stop()
        print("   ✓ Tracker stopped")
        
        # Check results
        print("\n3. Checking results...")
        if tracker.app_usage:
            print("   ✓ Applications detected:")
            for app, seconds in tracker.app_usage.items():
                minutes = seconds / 60
                print(f"     - {app}: {minutes:.1f} minutes")
        else:
            print("   ⚠️ No applications detected")
            
        # Check log file
        log_file = os.path.join('logs', 'app_usage_log.txt')
        if os.path.exists(log_file):
            with open(log_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    print("   ✓ Log file updated:")
                    for line in content.split('\n'):
                        if line.strip():
                            print(f"     {line}")
                else:
                    print("   ⚠️ Log file is empty")
        else:
            print("   ❌ Log file not found")
            
    else:
        print("   ❌ Failed to start tracker")
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    test_app_tracker() 
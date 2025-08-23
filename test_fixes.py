#!/usr/bin/env python3
"""
Test script to verify the fixes for:
1. Ngrok health monitoring and automatic restart
2. Password protection for system control actions
3. Improved WiFi control functionality
"""

import requests
import json
import time
import subprocess
import sys

def test_password_protection():
    """Test password protection on system control endpoints"""
    print("🔐 Testing password protection...")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints that require password
    test_endpoints = [
        "/api/system/restart",
        "/api/system/poweroff", 
        "/api/system/sleep",
        "/api/system/logout",
        "/api/system/lock",
        "/api/system/unlock",
        "/api/system/killwifi",
        "/api/system/enablewifi",
        "/api/system/killprocess",
        "/api/system/blockapp",
        "/api/system/unblockapp",
        "/api/system/delete"
    ]
    
    for endpoint in test_endpoints:
        print(f"  Testing {endpoint}...")
        
        # Test without password (should fail)
        try:
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={}, 
                                   timeout=5)
            if response.status_code == 401:
                print(f"    ✓ {endpoint} correctly rejects requests without password")
            else:
                print(f"    ⚠️ {endpoint} returned {response.status_code} instead of 401")
        except Exception as e:
            print(f"    ⚠️ Error testing {endpoint}: {str(e)}")
        
        # Test with wrong password (should fail)
        try:
            response = requests.post(f"{base_url}{endpoint}", 
                                   json={"password": "wrongpassword"}, 
                                   timeout=5)
            if response.status_code == 401:
                print(f"    ✓ {endpoint} correctly rejects requests with wrong password")
            else:
                print(f"    ⚠️ {endpoint} returned {response.status_code} instead of 401")
        except Exception as e:
            print(f"    ⚠️ Error testing {endpoint}: {str(e)}")
    
    print("✅ Password protection test completed")

def test_ngrok_health():
    """Test ngrok health monitoring"""
    print("\n🌐 Testing ngrok health monitoring...")
    
    try:
        # Check if ngrok API is accessible
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            if tunnels and 'tunnels' in tunnels and tunnels['tunnels']:
                tunnel_url = tunnels['tunnels'][0]['public_url']
                print(f"  ✓ Ngrok tunnel is running: {tunnel_url}")
                
                # Test tunnel accessibility
                try:
                    test_response = requests.get(f"{tunnel_url}/", timeout=5)
                    print(f"  ✓ Tunnel is accessible (status: {test_response.status_code})")
                except Exception as e:
                    print(f"  ⚠️ Tunnel accessibility test failed: {str(e)}")
            else:
                print("  ⚠️ No active tunnels found")
        else:
            print(f"  ⚠️ Ngrok API returned status {response.status_code}")
    except Exception as e:
        print(f"  ⚠️ Ngrok health check failed: {str(e)}")
    
    print("✅ Ngrok health test completed")

def test_wifi_control():
    """Test WiFi control functionality"""
    print("\n📶 Testing WiFi control...")
    
    base_url = "http://localhost:5000"
    
    # Test WiFi disable
    try:
        response = requests.post(f"{base_url}/api/system/killwifi", 
                               json={"password": "mangotree"}, 
                               timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("  ✓ WiFi disable command executed successfully")
            else:
                print(f"  ⚠️ WiFi disable failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ⚠️ WiFi disable returned status {response.status_code}")
    except Exception as e:
        print(f"  ⚠️ WiFi disable test failed: {str(e)}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test WiFi enable
    try:
        response = requests.post(f"{base_url}/api/system/enablewifi", 
                               json={"password": "mangotree"}, 
                               timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("  ✓ WiFi enable command executed successfully")
            else:
                print(f"  ⚠️ WiFi enable failed: {result.get('error', 'Unknown error')}")
        else:
            print(f"  ⚠️ WiFi enable returned status {response.status_code}")
    except Exception as e:
        print(f"  ⚠️ WiFi enable test failed: {str(e)}")
    
    print("✅ WiFi control test completed")

def main():
    """Run all tests"""
    print("🧪 Starting system control and ngrok tests...")
    print("=" * 50)
    
    # Check if the monitor is running
    try:
        response = requests.get("http://localhost:5000/api/system/status", timeout=5)
        if response.status_code == 200:
            print("✓ Monitor application is running")
        else:
            print("⚠️ Monitor application returned unexpected status")
            return
    except Exception as e:
        print(f"✗ Monitor application is not running: {str(e)}")
        print("Please start the monitor application first")
        return
    
    # Run tests
    test_password_protection()
    test_ngrok_health()
    test_wifi_control()
    
    print("\n" + "=" * 50)
    print("🎉 All tests completed!")

if __name__ == "__main__":
    main()

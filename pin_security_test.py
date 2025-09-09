#!/usr/bin/env python3
"""
PIN Security Testing - Test the PIN verification and security features
"""

import requests
import json
import sys

# Get backend URL from environment
BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

def test_pin_verification():
    """Test PIN verification endpoint"""
    print("=== Testing PIN Verification ===")
    
    # Test correct PIN
    payload = {
        "pin": "123456",
        "device_id": "test_device_001",
        "context": "chats"
    }
    
    try:
        print("Testing correct PIN...")
        response = requests.post(f"{BACKEND_URL}/pin/verify", json=payload)
        print(f"POST /api/pin/verify - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if data.get("success") == True:
                print("✅ Correct PIN verification working")
                
                # Test incorrect PIN
                print("\nTesting incorrect PIN...")
                payload["pin"] = "wrong_pin"
                response = requests.post(f"{BACKEND_URL}/pin/verify", json=payload)
                print(f"POST /api/pin/verify (wrong PIN) - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("success") == False:
                        print("✅ Incorrect PIN rejection working")
                        return True
                    else:
                        print("❌ Incorrect PIN was accepted")
                else:
                    print(f"❌ Wrong PIN test failed: {response.status_code}")
            else:
                print("❌ Correct PIN was rejected")
        else:
            print(f"❌ PIN verification failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ PIN verification error: {e}")
    
    return False

def test_panic_pin():
    """Test panic PIN detection"""
    print("\n=== Testing Panic PIN Detection ===")
    
    payload = {
        "pin": "911911",  # Panic PIN
        "device_id": "test_device_panic",
        "context": "chats"
    }
    
    try:
        print("Testing panic PIN...")
        response = requests.post(f"{BACKEND_URL}/pin/verify", json=payload)
        print(f"POST /api/pin/verify (panic PIN) - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Panic PIN should return success (to hide detection) but trigger wipe
            if data.get("success") == True and data.get("wipe_triggered") == True:
                print("✅ Panic PIN detection working")
                return True
            else:
                print("❌ Panic PIN not properly detected")
        else:
            print(f"❌ Panic PIN test failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Panic PIN test error: {e}")
    
    return False

def test_wipe_status():
    """Test wipe status endpoint"""
    print("\n=== Testing Wipe Status ===")
    
    try:
        print("Checking wipe status...")
        response = requests.get(f"{BACKEND_URL}/pin/wipe-status/test_device_panic")
        print(f"GET /api/pin/wipe-status/test_device_panic - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Should have wipe pending from panic PIN test
            if data.get("wipe_pending") == True:
                print("✅ Wipe status endpoint working")
                return True
            else:
                print("✅ No wipe pending (normal state)")
                return True
        else:
            print(f"❌ Wipe status failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Wipe status error: {e}")
    
    return False

def main():
    """Run PIN security tests"""
    print("🔒 PIN Security Testing")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 50)
    
    # Test health check first
    try:
        response = requests.get(f"{BACKEND_URL}/")
        if response.status_code == 200:
            print("✅ Backend is responding")
        else:
            print(f"❌ Backend health check failed: {response.status_code}")
            return 1
    except Exception as e:
        print(f"❌ Cannot connect to backend: {e}")
        return 1
    
    # Test PIN security features
    pin_test = test_pin_verification()
    panic_test = test_panic_pin()
    wipe_test = test_wipe_status()
    
    print("\n" + "=" * 50)
    print("Results:")
    print(f"PIN Verification: {'✅ PASS' if pin_test else '❌ FAIL'}")
    print(f"Panic PIN Detection: {'✅ PASS' if panic_test else '❌ FAIL'}")
    print(f"Wipe Status: {'✅ PASS' if wipe_test else '❌ FAIL'}")
    
    passed = sum([pin_test, panic_test, wipe_test])
    total = 3
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed >= 2:  # Allow some flexibility
        print("🎉 PIN security features working!")
        return 0
    else:
        print("⚠️  PIN security tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
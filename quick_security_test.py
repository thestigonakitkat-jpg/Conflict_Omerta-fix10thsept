#!/usr/bin/env python3
"""
Quick Security Test for STEELOS-SHREDDER
"""

import requests
import json
import time

BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

def test_input_sanitization():
    """Test input sanitization"""
    print("=== Testing Input Sanitization ===")
    
    # Test dangerous payload
    payload = {
        "device_id": "<script>alert('xss')</script>",
        "trigger_type": "manual",
        "confirmation_token": "test"
    }
    
    response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
    print(f"Dangerous payload response: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"Response data: {data}")
        if data.get("shredder_activated") == False:
            print("✅ Input sanitization working - dangerous payload blocked")
            return True
        else:
            print("❌ Input sanitization failed - dangerous payload accepted")
            return False
    else:
        print(f"Unexpected status: {response.status_code}")
        return False

def test_rate_limiting():
    """Test rate limiting with unique device IDs"""
    print("\n=== Testing Rate Limiting ===")
    
    success_count = 0
    failed_count = 0
    
    for i in range(8):  # Test 8 requests (limit is 5)
        payload = {
            "device_id": f"rate_test_unique_{i}_{int(time.time())}",
            "trigger_type": "manual",
            "confirmation_token": f"test_{i}"
        }
        
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("shredder_activated") == True:
                success_count += 1
                print(f"Request {i+1}: SUCCESS")
            else:
                failed_count += 1
                print(f"Request {i+1}: BLOCKED (rate limited)")
        else:
            failed_count += 1
            print(f"Request {i+1}: BLOCKED (status {response.status_code})")
        
        time.sleep(0.2)  # Small delay
    
    print(f"Results: {success_count} successful, {failed_count} blocked")
    
    if failed_count > 0:
        print("✅ Rate limiting working - some requests blocked")
        return True
    else:
        print("❌ Rate limiting not working - all requests succeeded")
        return False

def test_basic_functionality():
    """Test basic functionality still works"""
    print("\n=== Testing Basic Functionality ===")
    
    payload = {
        "device_id": f"basic_test_{int(time.time())}",
        "trigger_type": "panic_pin",
        "confirmation_token": None
    }
    
    response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
    
    if response.status_code == 200:
        data = response.json()
        if data.get("shredder_activated") == True:
            print("✅ Basic functionality working")
            return True
        else:
            print(f"❌ Basic functionality failed: {data}")
            return False
    else:
        print(f"❌ Basic functionality failed: {response.status_code}")
        return False

if __name__ == "__main__":
    print("🔒 Quick Security Test for STEELOS-SHREDDER")
    print("=" * 50)
    
    results = []
    results.append(("Input Sanitization", test_input_sanitization()))
    results.append(("Rate Limiting", test_rate_limiting()))
    results.append(("Basic Functionality", test_basic_functionality()))
    
    print("\n" + "=" * 50)
    print("RESULTS:")
    
    passed = 0
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<20} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(results)} tests passed")
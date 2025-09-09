#!/usr/bin/env python3
"""
STEELOS-SHREDDER System Testing
Tests the new STEELOS-SHREDDER endpoints and enhanced panic PIN functionality
"""

import requests
import json
import time
import sys
import hmac
import hashlib
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

def test_steelos_shredder_deploy_panic_pin():
    """Test STEELOS-SHREDDER deployment with panic_pin trigger"""
    print("=== Testing POST /api/steelos-shredder/deploy (panic_pin trigger) ===")
    
    payload = {
        "device_id": "test_device_panic_001",
        "trigger_type": "panic_pin",
        "confirmation_token": None
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify response structure
            required_fields = ["shredder_activated", "kill_token_generated", "destruction_initiated", "message"]
            if all(field in data for field in required_fields):
                if (data["shredder_activated"] == True and 
                    data["kill_token_generated"] == True and 
                    data["destruction_initiated"] == True and
                    "CYANIDE TABLET DEPLOYED" in data["message"]):
                    print("✅ STEELOS-SHREDDER deployment successful with panic_pin trigger")
                    return True
                else:
                    print(f"❌ Incorrect response values: {data}")
            else:
                print(f"❌ Missing required fields in response")
        else:
            print(f"❌ STEELOS-SHREDDER deployment failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ STEELOS-SHREDDER deployment error: {e}")
    
    return False

def test_steelos_shredder_deploy_emergency_nuke():
    """Test STEELOS-SHREDDER deployment with emergency_nuke trigger"""
    print("\n=== Testing POST /api/steelos-shredder/deploy (emergency_nuke trigger) ===")
    
    payload = {
        "device_id": "test_device_nuke_002",
        "trigger_type": "emergency_nuke",
        "confirmation_token": "EMERGENCY_CONFIRMED"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if (data.get("shredder_activated") == True and 
                data.get("kill_token_generated") == True and 
                data.get("destruction_initiated") == True):
                print("✅ STEELOS-SHREDDER deployment successful with emergency_nuke trigger")
                return True
            else:
                print(f"❌ Incorrect response values: {data}")
        else:
            print(f"❌ STEELOS-SHREDDER deployment failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ STEELOS-SHREDDER deployment error: {e}")
    
    return False

def test_steelos_shredder_deploy_anti_forensics():
    """Test STEELOS-SHREDDER deployment with anti_forensics trigger"""
    print("\n=== Testing POST /api/steelos-shredder/deploy (anti_forensics trigger) ===")
    
    payload = {
        "device_id": "test_device_forensics_003",
        "trigger_type": "anti_forensics",
        "confirmation_token": None
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if (data.get("shredder_activated") == True and 
                data.get("kill_token_generated") == True and 
                data.get("destruction_initiated") == True):
                print("✅ STEELOS-SHREDDER deployment successful with anti_forensics trigger")
                return True
            else:
                print(f"❌ Incorrect response values: {data}")
        else:
            print(f"❌ STEELOS-SHREDDER deployment failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ STEELOS-SHREDDER deployment error: {e}")
    
    return False

def test_steelos_shredder_deploy_manual():
    """Test STEELOS-SHREDDER deployment with manual trigger"""
    print("\n=== Testing POST /api/steelos-shredder/deploy (manual trigger) ===")
    
    payload = {
        "device_id": "test_device_manual_004",
        "trigger_type": "manual",
        "confirmation_token": "USER_CONFIRMED_MANUAL_WIPE"
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if (data.get("shredder_activated") == True and 
                data.get("kill_token_generated") == True and 
                data.get("destruction_initiated") == True):
                print("✅ STEELOS-SHREDDER deployment successful with manual trigger")
                return True
            else:
                print(f"❌ Incorrect response values: {data}")
        else:
            print(f"❌ STEELOS-SHREDDER deployment failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ STEELOS-SHREDDER deployment error: {e}")
    
    return False

def test_steelos_shredder_status_retrieval():
    """Test STEELOS-SHREDDER kill token retrieval and one-time use"""
    print("\n=== Testing GET /api/steelos-shredder/status/{device_id} (Kill Token Retrieval) ===")
    
    # First deploy a shredder to create a kill token
    device_id = "test_device_status_005"
    deploy_payload = {
        "device_id": device_id,
        "trigger_type": "panic_pin",
        "confirmation_token": None
    }
    
    try:
        # Deploy shredder
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=deploy_payload)
        print(f"POST /api/steelos-shredder/deploy - Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to deploy shredder for status test: {response.status_code}")
            return False
        
        print("Shredder deployed successfully, now testing status retrieval...")
        
        # First status check - should return kill token
        print("\nFirst status check (should return kill token):")
        response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
        print(f"GET /api/steelos-shredder/status/{device_id} - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if (data.get("shredder_pending") == True and 
                data.get("cyanide_deployed") == True and
                data.get("kill_token") is not None):
                
                kill_token = data["kill_token"]
                
                # Verify kill token structure
                required_token_fields = ["command", "device_id", "wipe_type", "timestamp", "trigger_type", "signature", "token_data"]
                if all(field in kill_token for field in required_token_fields):
                    print("✅ First status check successful - kill token returned with correct structure")
                    
                    # Verify cryptographic signature
                    expected_data = kill_token["token_data"]
                    expected_signature = hmac.new(
                        b"STEELOS_SHREDDER_KILL_TOKEN_SECRET_2025_NSA_GRADE",
                        expected_data.encode(),
                        hashlib.sha256
                    ).hexdigest()
                    
                    if kill_token["signature"] == expected_signature:
                        print("✅ Cryptographic signature verification successful")
                    else:
                        print(f"❌ Cryptographic signature mismatch: expected {expected_signature}, got {kill_token['signature']}")
                        return False
                else:
                    print(f"❌ Kill token missing required fields: {kill_token}")
                    return False
            else:
                print(f"❌ First status check failed: {data}")
                return False
        else:
            print(f"❌ First status check failed: {response.status_code} - {response.text}")
            return False
        
        # Second status check - should return empty (one-time use)
        print("\nSecond status check (should be empty due to one-time use):")
        response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
        print(f"GET /api/steelos-shredder/status/{device_id} - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if (data.get("shredder_pending") == False and 
                data.get("cyanide_deployed") == False and
                data.get("kill_token") is None):
                print("✅ Second status check successful - kill token removed (one-time use working)")
                return True
            else:
                print(f"❌ Second status check failed - kill token not removed: {data}")
                return False
        else:
            print(f"❌ Second status check failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Status retrieval test error: {e}")
    
    return False

def test_multiple_devices_separate_tokens():
    """Test that multiple devices can have separate kill tokens"""
    print("\n=== Testing Multiple Devices with Separate Kill Tokens ===")
    
    device_ids = ["test_device_multi_001", "test_device_multi_002", "test_device_multi_003"]
    
    try:
        # Deploy shredders for multiple devices
        for i, device_id in enumerate(device_ids):
            payload = {
                "device_id": device_id,
                "trigger_type": "manual",
                "confirmation_token": f"MULTI_TEST_{i}"
            }
            
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
            print(f"Deploy shredder for {device_id} - Status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"❌ Failed to deploy shredder for {device_id}: {response.status_code}")
                return False
        
        print("All shredders deployed successfully")
        
        # Check that each device has its own kill token
        retrieved_tokens = {}
        for device_id in device_ids:
            response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
            print(f"Status check for {device_id} - Status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get("shredder_pending") == True and 
                    data.get("kill_token") is not None):
                    
                    kill_token = data["kill_token"]
                    retrieved_tokens[device_id] = kill_token
                    
                    # Verify device_id matches in token
                    if kill_token.get("device_id") != device_id:
                        print(f"❌ Device ID mismatch in kill token for {device_id}")
                        return False
                else:
                    print(f"❌ No kill token found for {device_id}: {data}")
                    return False
            else:
                print(f"❌ Status check failed for {device_id}: {response.status_code}")
                return False
        
        # Verify all tokens are unique
        signatures = [token["signature"] for token in retrieved_tokens.values()]
        if len(signatures) == len(set(signatures)):
            print("✅ All devices have unique kill tokens")
            
            # Verify tokens are properly removed after retrieval
            for device_id in device_ids:
                response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
                if response.status_code == 200:
                    data = response.json()
                    if data.get("shredder_pending") == False:
                        print(f"✅ Kill token properly removed for {device_id}")
                    else:
                        print(f"❌ Kill token not removed for {device_id}")
                        return False
            
            print("✅ Multiple devices test successful - separate tokens and proper cleanup")
            return True
        else:
            print(f"❌ Duplicate signatures found: {signatures}")
            return False
            
    except Exception as e:
        print(f"❌ Multiple devices test error: {e}")
    
    return False

def test_enhanced_panic_pin_000000():
    """Test the enhanced panic PIN 000000"""
    print("\n=== Testing Enhanced Panic PIN (000000) ===")
    
    payload = {
        "device_id": "test_device_panic_pin_006",
        "pin": "000000",
        "timestamp": int(time.time())
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/pin/verify", json=payload)
        print(f"POST /api/pin/verify (PIN: 000000) - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Should return success (fake) but include kill token
            if (data.get("success") == True and 
                data.get("kill_token") is not None):
                
                kill_token = data["kill_token"]
                
                # Verify kill token structure for panic PIN
                if (kill_token.get("command") == "SIGNED_KILL_TOKEN_PANIC" and
                    kill_token.get("device_id") == payload["device_id"] and
                    kill_token.get("wipe_type") == "panic_automatic_kill" and
                    kill_token.get("auto_execute") == True):
                    print("✅ Enhanced panic PIN (000000) working - generates signed kill token")
                    return True
                else:
                    print(f"❌ Kill token structure incorrect: {kill_token}")
            else:
                print(f"❌ Panic PIN response incorrect: {data}")
        else:
            print(f"❌ Panic PIN verification failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Panic PIN test error: {e}")
    
    return False

def test_normal_pin_still_works():
    """Test that normal PIN verification still works"""
    print("\n=== Testing Normal PIN Verification (123456) ===")
    
    payload = {
        "device_id": "test_device_normal_pin_007",
        "pin": "123456",  # Correct PIN from pin_security.py
        "timestamp": int(time.time())
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/pin/verify", json=payload)
        print(f"POST /api/pin/verify (PIN: 123456) - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Should return success without kill token
            if (data.get("success") == True and 
                data.get("message") == "PIN verified successfully" and
                data.get("kill_token") is None):
                print("✅ Normal PIN verification working correctly")
                return True
            else:
                print(f"❌ Normal PIN response incorrect: {data}")
        else:
            print(f"❌ Normal PIN verification failed: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Normal PIN test error: {e}")
    
    return False

def test_steelos_shredder_input_sanitization():
    """Test input sanitization on STEELOS-SHREDDER endpoints"""
    print("\n=== Testing STEELOS-SHREDDER Input Sanitization ===")
    
    dangerous_payloads = [
        "<script>alert('xss')</script>",
        "'; DROP TABLE devices; --",
        "javascript:alert(1)",
        "../../../etc/passwd",
        "eval('malicious code')"
    ]
    
    blocked_count = 0
    
    try:
        for i, dangerous_input in enumerate(dangerous_payloads):
            print(f"\nTesting dangerous payload {i+1}: {dangerous_input[:30]}...")
            
            payload = {
                "device_id": dangerous_input,
                "trigger_type": "manual",
                "confirmation_token": "test"
            }
            
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("shredder_activated") == False and "deployment failed" in data.get("message", ""):
                    blocked_count += 1
                    print(f"✅ Dangerous payload {i+1} BLOCKED (deployment failed)")
                else:
                    print(f"❌ Dangerous payload {i+1} ACCEPTED (200) - SECURITY VULNERABILITY!")
            else:
                print(f"⚠️  Dangerous payload {i+1} unexpected status: {response.status_code}")
        
        if blocked_count == len(dangerous_payloads):
            print("✅ Input sanitization working correctly - all dangerous payloads blocked")
            return True
        else:
            print(f"❌ Input sanitization FAILED - {len(dangerous_payloads) - blocked_count} dangerous payloads were accepted")
            return False
            
    except Exception as e:
        print(f"❌ Input sanitization test error: {e}")
        return False

def test_steelos_shredder_rate_limiting():
    """Test rate limiting on STEELOS-SHREDDER endpoints"""
    print("\n=== Testing STEELOS-SHREDDER Rate Limiting ===")
    
    payload = {
        "device_id": "rate_limit_test_device",
        "trigger_type": "manual",
        "confirmation_token": "rate_test"
    }
    
    success_count = 0
    rate_limited_count = 0
    
    try:
        print("Sending 15 requests rapidly to test rate limiting...")
        
        for i in range(15):
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("shredder_activated") == True:
                    success_count += 1
                else:
                    rate_limited_count += 1
                    print(f"Request {i+1}: Rate limited (deployment failed)")
            elif response.status_code == 429:
                rate_limited_count += 1
                print(f"Request {i+1}: Rate limited (429)")
            else:
                print(f"Request {i+1}: Unexpected status {response.status_code}")
            
            time.sleep(0.1)
        
        print(f"Results: {success_count} successful, {rate_limited_count} rate limited")
        
        # Should have some rate limiting in effect
        if rate_limited_count > 0:
            print("✅ Rate limiting working on STEELOS-SHREDDER endpoints")
            return True
        else:
            print("❌ No rate limiting detected on STEELOS-SHREDDER endpoints")
            return False
            
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

def test_integration_flow():
    """Test the complete integration flow: trigger → deploy → retrieve → one-time use"""
    print("\n=== Testing Complete Integration Flow ===")
    
    device_id = "integration_test_device_008"
    
    try:
        # Step 1: Deploy STEELOS-SHREDDER
        print("Step 1: Deploying STEELOS-SHREDDER...")
        deploy_payload = {
            "device_id": device_id,
            "trigger_type": "panic_pin",
            "confirmation_token": None
        }
        
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=deploy_payload)
        if response.status_code != 200:
            print(f"❌ Step 1 failed - Deploy: {response.status_code}")
            return False
        
        deploy_data = response.json()
        if not deploy_data.get("shredder_activated"):
            print(f"❌ Step 1 failed - Shredder not activated: {deploy_data}")
            return False
        
        print("✅ Step 1 successful - STEELOS-SHREDDER deployed")
        
        # Step 2: Retrieve kill token
        print("\nStep 2: Retrieving kill token...")
        response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
        if response.status_code != 200:
            print(f"❌ Step 2 failed - Status check: {response.status_code}")
            return False
        
        status_data = response.json()
        if not status_data.get("shredder_pending") or not status_data.get("kill_token"):
            print(f"❌ Step 2 failed - No kill token: {status_data}")
            return False
        
        kill_token = status_data["kill_token"]
        print("✅ Step 2 successful - Kill token retrieved")
        
        # Step 3: Verify one-time use (token should be gone)
        print("\nStep 3: Verifying one-time use...")
        response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{device_id}")
        if response.status_code != 200:
            print(f"❌ Step 3 failed - Second status check: {response.status_code}")
            return False
        
        second_status_data = response.json()
        if second_status_data.get("shredder_pending") or second_status_data.get("kill_token"):
            print(f"❌ Step 3 failed - Token not removed: {second_status_data}")
            return False
        
        print("✅ Step 3 successful - Kill token properly removed (one-time use)")
        
        # Step 4: Verify cryptographic signature
        print("\nStep 4: Verifying cryptographic signature...")
        expected_signature = hmac.new(
            b"STEELOS_SHREDDER_KILL_TOKEN_SECRET_2025_NSA_GRADE",
            kill_token["token_data"].encode(),
            hashlib.sha256
        ).hexdigest()
        
        if kill_token["signature"] == expected_signature:
            print("✅ Step 4 successful - Cryptographic signature verified")
        else:
            print(f"❌ Step 4 failed - Signature mismatch")
            return False
        
        print("✅ Complete integration flow successful!")
        return True
        
    except Exception as e:
        print(f"❌ Integration flow test error: {e}")
        return False

def test_error_handling():
    """Test error handling when shredder deployment fails"""
    print("\n=== Testing Error Handling ===")
    
    # Test with invalid trigger type
    payload = {
        "device_id": "error_test_device",
        "trigger_type": "invalid_trigger_type_xyz",
        "confirmation_token": None
    }
    
    try:
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy (invalid trigger) - Status: {response.status_code}")
        
        # Should still work due to input sanitization, but let's check response
        if response.status_code == 200:
            data = response.json()
            if data.get("shredder_activated"):
                print("✅ Error handling test - system handles invalid trigger gracefully")
                return True
        
        # Test with missing device_id
        payload = {
            "trigger_type": "manual",
            "confirmation_token": None
        }
        
        response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=payload)
        print(f"POST /api/steelos-shredder/deploy (missing device_id) - Status: {response.status_code}")
        
        if response.status_code == 422:  # Validation error
            print("✅ Error handling test - missing device_id properly rejected")
            return True
        else:
            print(f"❌ Error handling test failed - expected 422, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error handling test error: {e}")
        return False

def main():
    """Run all STEELOS-SHREDDER tests"""
    print("💊🧬 STEELOS-SHREDDER SYSTEM TESTING")
    print("Testing the new STEELOS-SHREDDER implementation and enhanced panic PIN")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    results = []
    
    # STEELOS-SHREDDER Endpoint Tests
    print("\n💊 STEELOS-SHREDDER ENDPOINT TESTS")
    print("=" * 50)
    
    results.append(("Deploy: panic_pin trigger", test_steelos_shredder_deploy_panic_pin()))
    results.append(("Deploy: emergency_nuke trigger", test_steelos_shredder_deploy_emergency_nuke()))
    results.append(("Deploy: anti_forensics trigger", test_steelos_shredder_deploy_anti_forensics()))
    results.append(("Deploy: manual trigger", test_steelos_shredder_deploy_manual()))
    results.append(("Status: Kill token retrieval & one-time use", test_steelos_shredder_status_retrieval()))
    results.append(("Multiple devices separate tokens", test_multiple_devices_separate_tokens()))
    
    # Enhanced Panic PIN Tests
    print("\n🔒 ENHANCED PANIC PIN TESTS")
    print("=" * 50)
    
    results.append(("Enhanced Panic PIN (000000)", test_enhanced_panic_pin_000000()))
    results.append(("Normal PIN still works (123456)", test_normal_pin_still_works()))
    
    # Security Tests
    print("\n🛡️  SECURITY VERIFICATION TESTS")
    print("=" * 50)
    
    results.append(("Input sanitization", test_steelos_shredder_input_sanitization()))
    results.append(("Rate limiting", test_steelos_shredder_rate_limiting()))
    
    # Integration Tests
    print("\n🔄 INTEGRATION TESTS")
    print("=" * 50)
    
    results.append(("Complete integration flow", test_integration_flow()))
    results.append(("Error handling", test_error_handling()))
    
    # Summary
    print("\n" + "=" * 80)
    print("💊🧬 STEELOS-SHREDDER TEST RESULTS:")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<40} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    success_rate = (passed / total) * 100 if total > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate == 100.0:
        print("🎉 ALL STEELOS-SHREDDER TESTS PASSED! System ready for deployment!")
        return 0
    elif success_rate >= 80.0:
        print("⚠️  Most tests passed - minor issues to address")
        return 1
    else:
        print("❌ CRITICAL ISSUES FOUND - Immediate attention required!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
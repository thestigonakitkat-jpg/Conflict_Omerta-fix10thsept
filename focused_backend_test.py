#!/usr/bin/env python3
"""
Focused Backend API Testing for OMERTA Security Features
Tests the specific endpoints requested in the review
"""

import requests
import json
import time
import sys
from datetime import datetime, timezone

# Get backend URL from environment
BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

def test_secure_notes_endpoints():
    """Test Secure Notes endpoints (POST /api/notes, GET /api/notes/{id})"""
    print("=== Testing Secure Notes Endpoints ===")
    
    # Test POST /api/notes
    payload = {
        "ciphertext": "encrypted_secure_note_content_abc123",
        "ttl_seconds": 300,  # 5 minutes
        "read_limit": 1,     # Backend enforces 1-time read only
        "meta": {"type": "secure_note", "created_by": "test_user"}
    }
    
    try:
        print("Testing POST /api/notes...")
        response = requests.post(f"{BACKEND_URL}/notes", json=payload)
        print(f"POST /api/notes - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            # Verify response structure
            required_fields = ["id", "expires_at", "views_left"]
            if all(field in data for field in required_fields):
                note_id = data["id"]
                print("✅ Secure note created successfully")
                
                # Test GET /api/notes/{id}
                print(f"\nTesting GET /api/notes/{note_id}...")
                response = requests.get(f"{BACKEND_URL}/notes/{note_id}")
                print(f"GET /api/notes/{note_id} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    if data.get("ciphertext") == payload["ciphertext"]:
                        print("✅ Secure note read successfully")
                        
                        # Test second read (should fail - one-time read only)
                        print(f"\nTesting second read (should fail)...")
                        response = requests.get(f"{BACKEND_URL}/notes/{note_id}")
                        print(f"GET /api/notes/{note_id} (second read) - Status: {response.status_code}")
                        
                        if response.status_code == 404:
                            print("✅ One-time read policy working - note purged after first read")
                            return True
                        else:
                            print(f"❌ One-time read policy failed - expected 404, got {response.status_code}")
                    else:
                        print("❌ Incorrect ciphertext returned")
                else:
                    print(f"❌ Failed to read note: {response.status_code} - {response.text}")
            else:
                print(f"❌ Missing required fields in create response")
        else:
            print(f"❌ Failed to create note: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Secure notes test error: {e}")
    
    return False

def test_messaging_envelopes_endpoints():
    """Test Messaging envelopes endpoints (POST /api/envelopes/send, GET /api/envelopes/poll)"""
    print("\n=== Testing Messaging Envelopes Endpoints ===")
    
    # Test POST /api/envelopes/send
    payload = {
        "to_oid": "alice_user_2025",
        "from_oid": "bob_user_2025",
        "ciphertext": "encrypted_message_hello_alice_from_bob"
    }
    
    try:
        print("Testing POST /api/envelopes/send...")
        response = requests.post(f"{BACKEND_URL}/envelopes/send", json=payload)
        print(f"POST /api/envelopes/send - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            
            if "id" in data:
                envelope_id = data["id"]
                print("✅ Envelope sent successfully")
                
                # Test GET /api/envelopes/poll
                print(f"\nTesting GET /api/envelopes/poll...")
                response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid={payload['to_oid']}")
                print(f"GET /api/envelopes/poll?oid={payload['to_oid']} - Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    messages = data.get("messages", [])
                    if len(messages) == 1:
                        msg = messages[0]
                        if (msg.get("id") == envelope_id and 
                            msg.get("from_oid") == payload["from_oid"] and
                            msg.get("ciphertext") == payload["ciphertext"] and
                            "ts" in msg):
                            print("✅ Envelope polled successfully with correct data")
                            
                            # Test delete-on-delivery (second poll should be empty)
                            print(f"\nTesting delete-on-delivery (second poll)...")
                            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid={payload['to_oid']}")
                            print(f"GET /api/envelopes/poll (second) - Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                data = response.json()
                                messages = data.get("messages", [])
                                if len(messages) == 0:
                                    print("✅ Delete-on-delivery working - second poll empty")
                                    return True
                                else:
                                    print(f"❌ Delete-on-delivery failed - expected 0 messages, got {len(messages)}")
                            else:
                                print(f"❌ Second poll failed: {response.status_code}")
                        else:
                            print("❌ Incorrect message data returned")
                    else:
                        print(f"❌ Expected 1 message, got {len(messages)}")
                else:
                    print(f"❌ Failed to poll envelopes: {response.status_code} - {response.text}")
            else:
                print("❌ Missing envelope ID in send response")
        else:
            print(f"❌ Failed to send envelope: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Messaging envelopes test error: {e}")
    
    return False

def test_health_check():
    """Test basic health check endpoint"""
    print("\n=== Testing Basic Health Check ===")
    
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"GET /api/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            if data.get("message") == "Hello World":
                print("✅ Health check endpoint working")
                return True
            else:
                print("❌ Unexpected health check response")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
    
    return False

def test_security_headers():
    """Test security headers implementation"""
    print("\n=== Testing Security Headers ===")
    
    expected_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security",
        "Content-Security-Policy",
        "Referrer-Policy",
        "Permissions-Policy",
        "X-Permitted-Cross-Domain-Policies",
        "Cross-Origin-Embedder-Policy",
        "Cross-Origin-Opener-Policy",
        "Cross-Origin-Resource-Policy"
    ]
    
    try:
        response = requests.get(f"{BACKEND_URL}/")
        print(f"GET /api/ - Status: {response.status_code}")
        
        if response.status_code == 200:
            headers = response.headers
            present_count = 0
            
            print("\nSecurity headers check:")
            for header in expected_headers:
                if header in headers:
                    present_count += 1
                    print(f"✅ {header}: {headers[header]}")
                else:
                    print(f"❌ {header}: MISSING")
            
            print(f"\nResults: {present_count}/{len(expected_headers)} headers present")
            
            if present_count == len(expected_headers):
                print("✅ All security headers present")
                return True
            else:
                print(f"❌ Missing {len(expected_headers) - present_count} security headers")
        else:
            print(f"❌ Failed to get response for header testing: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Security headers test error: {e}")
    
    return False

def test_rate_limiting_basic():
    """Test basic rate limiting functionality"""
    print("\n=== Testing Rate Limiting Functionality ===")
    
    # Test with a simple endpoint - just verify rate limiting is active
    payload = {
        "ciphertext": "rate_limit_test_content",
        "ttl_seconds": 60,
        "read_limit": 1
    }
    
    success_count = 0
    rate_limited_count = 0
    
    try:
        print("Testing rate limiting with 12 rapid requests...")
        
        for i in range(12):
            response = requests.post(f"{BACKEND_URL}/notes", json=payload)
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited_count += 1
                if i < 3:  # Only show first few rate limit messages
                    print(f"Request {i+1}: Rate limited (429)")
            else:
                print(f"Request {i+1}: Unexpected status {response.status_code}")
            
            time.sleep(0.1)
        
        print(f"Results: {success_count} successful, {rate_limited_count} rate limited")
        
        # Rate limiting is working if we got some rate limited responses
        if rate_limited_count > 0:
            print("✅ Rate limiting is active and working")
            return True
        else:
            print("❌ Rate limiting not working - no 429 responses")
            return False
            
    except Exception as e:
        print(f"❌ Rate limiting test error: {e}")
        return False

def main():
    """Run focused backend tests as requested in review"""
    print("🔒 OMERTA Backend API Testing - Focused Review")
    print("Testing specific endpoints as requested:")
    print("1. Secure Notes endpoints (POST /api/notes, GET /api/notes/{id})")
    print("2. Messaging envelopes endpoints (POST /api/envelopes/send, GET /api/envelopes/poll)")
    print("3. Basic health check and security headers")
    print("4. Rate limiting functionality")
    print(f"Backend URL: {BACKEND_URL}")
    print("=" * 80)
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Security headers
    results.append(("Security Headers", test_security_headers()))
    
    # Test 3: Secure Notes endpoints
    results.append(("Secure Notes Endpoints", test_secure_notes_endpoints()))
    
    # Test 4: Messaging envelopes endpoints
    results.append(("Messaging Envelopes Endpoints", test_messaging_envelopes_endpoints()))
    
    # Test 5: Rate limiting functionality
    results.append(("Rate Limiting Functionality", test_rate_limiting_basic()))
    
    # Summary
    print("\n" + "=" * 80)
    print("🔒 FOCUSED BACKEND TEST RESULTS:")
    print("=" * 80)
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<35} {status}")
        if success:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All focused backend tests passed! Backend is working correctly.")
        return 0
    else:
        print(f"⚠️  {total - passed} test(s) failed - see details above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
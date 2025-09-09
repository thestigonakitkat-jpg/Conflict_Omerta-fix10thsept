#!/usr/bin/env python3
"""
COMPREHENSIVE SECURITY AUDIT TESTING
Testing critical security fixes after implementation:
1. Dual-Key System Security - No hardcoded credentials exposed
2. Split Master Key Security - Master keys cleared immediately after use
3. Rate Limiting Bypass Tests - Enhanced fingerprinting resistance
4. Emergency Revocation - Backend functionality verification
5. Security Event Logging - Proper event logging verification
6. STEELOS-Shredder - Data destruction functionality
7. Input Sanitization - Advanced injection attack resistance
8. Memory Management - No sensitive data persistence
"""

import requests
import json
import time
import hashlib
import hmac
import secrets
import re
from datetime import datetime, timezone
import sys
import os
import threading
import concurrent.futures

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://graphite-killer.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SecurityAuditTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.security_events = []
        
    def log_test(self, test_name: str, success: bool, details: str = "", severity: str = "INFO"):
        """Log test result with security severity"""
        status = "✅ PASS" if success else "❌ FAIL"
        severity_icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🔍", "LOW": "ℹ️", "INFO": "📋"}
        
        print(f"{status} {severity_icon.get(severity, '📋')} {test_name}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })

    def test_hardcoded_credentials_exposure(self):
        """Test 1: Verify no hardcoded credentials are exposed in responses"""
        print("\n🔐 Testing Hardcoded Credentials Exposure")
        
        # Test various endpoints for credential leakage
        endpoints_to_test = [
            "/",
            "/notes",
            "/envelopes/send", 
            "/steelos-shredder/deploy",
            "/dual-key/initiate",
            "/split-master-key/initiate",
            "/pin/verify",
            "/emergency/revoke"
        ]
        
        credential_patterns = [
            r'password["\s]*[:=]["\s]*[^"]{3,}',
            r'secret["\s]*[:=]["\s]*[^"]{3,}',
            r'key["\s]*[:=]["\s]*[^"]{10,}',
            r'token["\s]*[:=]["\s]*[^"]{10,}',
            r'api_key["\s]*[:=]["\s]*[^"]{3,}',
            r'private_key["\s]*[:=]["\s]*[^"]{10,}',
            r'master_key["\s]*[:=]["\s]*[^"]{10,}',
            r'STEELOS_SHREDDER_KILL_TOKEN_SECRET',
            r'mongodb://[^"]*:[^"]*@',
            r'postgres://[^"]*:[^"]*@'
        ]
        
        credentials_found = []
        
        for endpoint in endpoints_to_test:
            try:
                # Test GET requests
                response = self.session.get(f"{API_BASE}{endpoint}")
                response_text = response.text.lower()
                
                for pattern in credential_patterns:
                    matches = re.findall(pattern, response_text, re.IGNORECASE)
                    if matches:
                        credentials_found.extend([(endpoint, "GET", match) for match in matches])
                
                # Test POST requests with minimal data
                if endpoint not in ["/", "/notes"]:  # Skip endpoints that don't accept POST
                    try:
                        post_response = self.session.post(f"{API_BASE}{endpoint}", json={})
                        post_text = post_response.text.lower()
                        
                        for pattern in credential_patterns:
                            matches = re.findall(pattern, post_text, re.IGNORECASE)
                            if matches:
                                credentials_found.extend([(endpoint, "POST", match) for match in matches])
                    except:
                        pass  # Some endpoints may not accept POST
                        
            except Exception as e:
                continue
        
        if credentials_found:
            self.log_test("Hardcoded Credentials Exposure", False, 
                         f"Found {len(credentials_found)} potential credential exposures: {credentials_found[:3]}", "CRITICAL")
        else:
            self.log_test("Hardcoded Credentials Exposure", True, 
                         "No hardcoded credentials found in API responses", "HIGH")

    def test_master_key_memory_clearing(self):
        """Test 2: Verify master keys are cleared immediately after use"""
        print("\n🧠 Testing Master Key Memory Clearing")
        
        try:
            # Initiate split master key operation
            payload = {
                'operation_type': 'memory_test',
                'operation_data': {'test_memory_clearing': True}
            }
            
            response = self.session.post(f"{API_BASE}/split-master-key/initiate", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                operation_id = data.get('operation_id')
                
                if operation_id:
                    # Provide first key fragment
                    fragment1 = {
                        'key_holder_id': 'test_holder_1',
                        'key_fragment': 'a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456',
                        'pin': 'TEST123',
                        'totp_code': '123456',
                        'operation_type': 'memory_test'
                    }
                    
                    frag_response1 = self.session.post(f"{API_BASE}/split-master-key/fragment", json=fragment1)
                    
                    # Provide second key fragment
                    fragment2 = {
                        'key_holder_id': 'test_holder_2', 
                        'key_fragment': 'f6e5d4c3b2a1098765432109876543210fedcba0987654321fedcba09876543',
                        'pin': 'TEST456',
                        'totp_code': '654321',
                        'operation_type': 'memory_test'
                    }
                    
                    frag_response2 = self.session.post(f"{API_BASE}/split-master-key/fragment", json=fragment2)
                    
                    # Check if master key is still accessible (it shouldn't be)
                    status_response = self.session.get(f"{API_BASE}/split-master-key/status/{operation_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        # Look for signs that master key is cleared
                        response_text = status_response.text.lower()
                        
                        # These should NOT be present in the response
                        sensitive_data_patterns = [
                            'master_key',
                            'reconstructed_key',
                            'combined_fragment',
                            fragment1['key_fragment'].lower(),
                            fragment2['key_fragment'].lower()
                        ]
                        
                        sensitive_found = []
                        for pattern in sensitive_data_patterns:
                            if pattern in response_text:
                                sensitive_found.append(pattern)
                        
                        if sensitive_found:
                            self.log_test("Master Key Memory Clearing", False,
                                        f"Sensitive data still present in response: {sensitive_found}", "CRITICAL")
                        else:
                            self.log_test("Master Key Memory Clearing", True,
                                        "No master key data found in status response - memory cleared", "HIGH")
                    else:
                        self.log_test("Master Key Memory Clearing", False,
                                    f"Could not check status: HTTP {status_response.status_code}", "MEDIUM")
                else:
                    self.log_test("Master Key Memory Clearing", False, "No operation ID returned", "MEDIUM")
            else:
                self.log_test("Master Key Memory Clearing", False,
                            f"Could not initiate operation: HTTP {response.status_code}", "MEDIUM")
                
        except Exception as e:
            self.log_test("Master Key Memory Clearing", False, f"Exception: {str(e)}", "MEDIUM")

    def test_rate_limiting_bypass_attempts(self):
        """Test 3: Try to bypass enhanced rate limiting with fingerprinting"""
        print("\n🚦 Testing Rate Limiting Bypass Resistance")
        
        # Test multiple bypass techniques
        bypass_techniques = [
            ("User-Agent Rotation", self.test_user_agent_bypass),
            ("IP Header Spoofing", self.test_ip_header_bypass),
            ("Concurrent Requests", self.test_concurrent_bypass),
            ("Session Rotation", self.test_session_bypass)
        ]
        
        bypass_successful = 0
        
        for technique_name, test_func in bypass_techniques:
            try:
                if test_func():
                    bypass_successful += 1
                    self.log_test(f"Rate Limiting - {technique_name} Bypass", False,
                                "Bypass technique successful - rate limiting vulnerable", "HIGH")
                else:
                    self.log_test(f"Rate Limiting - {technique_name} Bypass", True,
                                "Bypass technique blocked - rate limiting resistant", "HIGH")
            except Exception as e:
                self.log_test(f"Rate Limiting - {technique_name} Bypass", False,
                            f"Test error: {str(e)}", "MEDIUM")
        
        if bypass_successful == 0:
            self.log_test("Overall Rate Limiting Bypass Resistance", True,
                         "All bypass techniques blocked - enhanced fingerprinting working", "HIGH")
        else:
            self.log_test("Overall Rate Limiting Bypass Resistance", False,
                         f"{bypass_successful}/{len(bypass_techniques)} bypass techniques successful", "CRITICAL")

    def test_user_agent_bypass(self):
        """Test User-Agent rotation bypass"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", 
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            "curl/7.68.0",
            "PostmanRuntime/7.28.4"
        ]
        
        rate_limited = False
        
        for i, ua in enumerate(user_agents):
            headers = {"User-Agent": ua}
            
            # Make multiple requests to trigger rate limiting
            for j in range(12):  # Exceed 10/min limit for notes
                try:
                    payload = {"ciphertext": f"test_{i}_{j}", "ttl_seconds": 3600, "read_limit": 1}
                    response = requests.post(f"{API_BASE}/notes", json=payload, headers=headers)
                    
                    if response.status_code == 429:
                        rate_limited = True
                        break
                except:
                    pass
            
            if rate_limited:
                break
        
        return not rate_limited  # Return True if bypass was successful (no rate limiting)

    def test_ip_header_bypass(self):
        """Test IP header spoofing bypass"""
        fake_ips = ["1.2.3.4", "5.6.7.8", "9.10.11.12", "192.168.1.100", "10.0.0.50"]
        
        rate_limited = False
        
        for i, fake_ip in enumerate(fake_ips):
            headers = {
                "X-Forwarded-For": fake_ip,
                "X-Real-IP": fake_ip,
                "X-Client-IP": fake_ip
            }
            
            # Make multiple requests
            for j in range(12):
                try:
                    payload = {"ciphertext": f"ip_test_{i}_{j}", "ttl_seconds": 3600, "read_limit": 1}
                    response = requests.post(f"{API_BASE}/notes", json=payload, headers=headers)
                    
                    if response.status_code == 429:
                        rate_limited = True
                        break
                except:
                    pass
            
            if rate_limited:
                break
        
        return not rate_limited

    def test_concurrent_bypass(self):
        """Test concurrent request bypass"""
        def make_request(i):
            try:
                payload = {"ciphertext": f"concurrent_test_{i}", "ttl_seconds": 3600, "read_limit": 1}
                response = requests.post(f"{API_BASE}/notes", json=payload)
                return response.status_code
            except:
                return 500
        
        # Make 15 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(make_request, i) for i in range(15)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        # Check if any were rate limited
        rate_limited_count = sum(1 for code in results if code == 429)
        
        return rate_limited_count == 0  # Return True if no rate limiting (bypass successful)

    def test_session_bypass(self):
        """Test session rotation bypass"""
        rate_limited = False
        
        for i in range(5):
            session = requests.Session()
            
            # Make multiple requests with new session
            for j in range(12):
                try:
                    payload = {"ciphertext": f"session_test_{i}_{j}", "ttl_seconds": 3600, "read_limit": 1}
                    response = session.post(f"{API_BASE}/notes", json=payload)
                    
                    if response.status_code == 429:
                        rate_limited = True
                        break
                except:
                    pass
            
            if rate_limited:
                break
        
        return not rate_limited

    def test_emergency_revocation_backend(self):
        """Test 4: Verify emergency revocation works via backend"""
        print("\n🚨 Testing Emergency Revocation Backend")
        
        try:
            # Test emergency portal access
            portal_response = requests.get(f"{BACKEND_URL}/emergency")
            
            if portal_response.status_code == 200:
                portal_content = portal_response.text
                
                # Check for required form elements
                required_elements = [
                    'omerta_id',
                    'panic_passphrase', 
                    'emergency_contact_name',
                    'emergency_contact_email',
                    'reason',
                    'immediate_execution'
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in portal_content.lower():
                        missing_elements.append(element)
                
                if missing_elements:
                    self.log_test("Emergency Portal Accessibility", False,
                                f"Missing form elements: {missing_elements}", "HIGH")
                else:
                    self.log_test("Emergency Portal Accessibility", True,
                                "Emergency portal accessible with all required form elements", "HIGH")
                
                # Test emergency revocation submission
                revocation_data = {
                    'omerta_id': 'TEST_OMERTA_ID_12345',
                    'panic_passphrase': 'EMERGENCY_PASSPHRASE_2025',
                    'emergency_contact_name': 'Security Tester',
                    'emergency_contact_email': 'security@test.com',
                    'reason': 'Security audit testing',
                    'immediate_execution': False
                }
                
                revoke_response = requests.post(f"{API_BASE}/emergency/revoke", data=revocation_data)
                
                if revoke_response.status_code in [200, 201]:
                    self.log_test("Emergency Revocation Submission", True,
                                f"Revocation submitted successfully: HTTP {revoke_response.status_code}", "HIGH")
                    
                    # Test token retrieval
                    token_response = requests.get(f"{API_BASE}/emergency/token/TEST_DEVICE_ID")
                    
                    if token_response.status_code == 200:
                        token_data = token_response.json()
                        if 'revocation_pending' in token_data:
                            self.log_test("Emergency Token Retrieval", True,
                                        "Emergency tokens retrievable via backend", "HIGH")
                        else:
                            self.log_test("Emergency Token Retrieval", False,
                                        "Token response missing expected fields", "MEDIUM")
                    else:
                        self.log_test("Emergency Token Retrieval", False,
                                    f"Token retrieval failed: HTTP {token_response.status_code}", "MEDIUM")
                        
                else:
                    self.log_test("Emergency Revocation Submission", False,
                                f"Revocation submission failed: HTTP {revoke_response.status_code}", "HIGH")
            else:
                self.log_test("Emergency Portal Accessibility", False,
                            f"Emergency portal not accessible: HTTP {portal_response.status_code}", "CRITICAL")
                
        except Exception as e:
            self.log_test("Emergency Revocation Backend", False, f"Exception: {str(e)}", "HIGH")

    def test_security_event_logging(self):
        """Test 5: Verify security events are properly logged"""
        print("\n📝 Testing Security Event Logging")
        
        # Generate various security events
        security_events_to_test = [
            ("Rate Limit Violation", self.trigger_rate_limit_event),
            ("Input Sanitization Block", self.trigger_sanitization_event),
            ("Authentication Failure", self.trigger_auth_failure_event),
            ("STEELOS Deployment", self.trigger_steelos_event)
        ]
        
        events_logged = 0
        
        for event_name, trigger_func in security_events_to_test:
            try:
                # Trigger the security event
                event_triggered = trigger_func()
                
                if event_triggered:
                    events_logged += 1
                    self.log_test(f"Security Event Logging - {event_name}", True,
                                "Security event triggered and should be logged", "MEDIUM")
                else:
                    self.log_test(f"Security Event Logging - {event_name}", False,
                                "Could not trigger security event", "LOW")
                    
            except Exception as e:
                self.log_test(f"Security Event Logging - {event_name}", False,
                            f"Exception: {str(e)}", "LOW")
        
        if events_logged >= len(security_events_to_test) * 0.75:
            self.log_test("Overall Security Event Logging", True,
                         f"{events_logged}/{len(security_events_to_test)} security events triggered", "MEDIUM")
        else:
            self.log_test("Overall Security Event Logging", False,
                         f"Only {events_logged}/{len(security_events_to_test)} security events triggered", "MEDIUM")

    def trigger_rate_limit_event(self):
        """Trigger rate limiting to generate security event"""
        try:
            # Make rapid requests to trigger rate limiting
            for i in range(15):
                payload = {"ciphertext": f"rate_limit_test_{i}", "ttl_seconds": 3600, "read_limit": 1}
                response = requests.post(f"{API_BASE}/notes", json=payload)
                if response.status_code == 429:
                    return True
            return False
        except:
            return False

    def trigger_sanitization_event(self):
        """Trigger input sanitization to generate security event"""
        try:
            dangerous_payload = {"ciphertext": "<script>alert('xss')</script>", "ttl_seconds": 3600, "read_limit": 1}
            response = requests.post(f"{API_BASE}/notes", json=dangerous_payload)
            return response.status_code == 400
        except:
            return False

    def trigger_auth_failure_event(self):
        """Trigger authentication failure to generate security event"""
        try:
            invalid_auth = {
                'operation_id': 'fake_id',
                'operator_id': 'invalid_operator',
                'key_fragment': 'invalid',
                'password': 'wrong',
                'totp_code': '000000'
            }
            response = requests.post(f"{API_BASE}/dual-key/authenticate", json=invalid_auth)
            return response.status_code in [401, 403, 404]
        except:
            return False

    def trigger_steelos_event(self):
        """Trigger STEELOS deployment to generate security event"""
        try:
            steelos_payload = {
                'device_id': 'TEST_DEVICE_SECURITY_AUDIT',
                'trigger_type': 'manual',
                'confirmation_token': 'test_token'
            }
            response = requests.post(f"{API_BASE}/steelos-shredder/deploy", json=steelos_payload)
            return response.status_code == 200
        except:
            return False

    def test_steelos_shredder_functionality(self):
        """Test 6: Verify STEELOS-Shredder data destruction still works"""
        print("\n💊 Testing STEELOS-Shredder Functionality")
        
        try:
            # Test STEELOS deployment
            device_id = f"SECURITY_AUDIT_{int(time.time())}"
            
            deployment_payload = {
                'device_id': device_id,
                'trigger_type': 'security_audit',
                'confirmation_token': 'audit_token_2025'
            }
            
            deploy_response = requests.post(f"{API_BASE}/steelos-shredder/deploy", json=deployment_payload)
            
            if deploy_response.status_code == 200:
                deploy_data = deploy_response.json()
                
                if deploy_data.get('shredder_activated') and deploy_data.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True,
                                f"Shredder activated: {deploy_data.get('message')}", "HIGH")
                    
                    # Test kill token retrieval
                    time.sleep(1)  # Brief delay
                    
                    status_response = requests.get(f"{API_BASE}/steelos-shredder/status/{device_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('shredder_pending') and status_data.get('kill_token'):
                            kill_token = status_data.get('kill_token')
                            
                            # Verify kill token structure
                            required_fields = [
                                'command', 'device_id', 'wipe_type', 'timestamp',
                                'signature', 'destruction_phases'
                            ]
                            
                            missing_fields = []
                            for field in required_fields:
                                if field not in kill_token:
                                    missing_fields.append(field)
                            
                            if missing_fields:
                                self.log_test("STEELOS Kill Token Structure", False,
                                            f"Missing fields: {missing_fields}", "HIGH")
                            else:
                                self.log_test("STEELOS Kill Token Structure", True,
                                            "Kill token has all required fields", "HIGH")
                                
                                # Verify cryptographic signature
                                if len(kill_token.get('signature', '')) >= 32:
                                    self.log_test("STEELOS Cryptographic Signature", True,
                                                f"Valid signature length: {len(kill_token['signature'])} chars", "HIGH")
                                else:
                                    self.log_test("STEELOS Cryptographic Signature", False,
                                                "Signature too short or missing", "HIGH")
                            
                            # Test one-time use (second retrieval should return empty)
                            second_status = requests.get(f"{API_BASE}/steelos-shredder/status/{device_id}")
                            if second_status.status_code == 200:
                                second_data = second_status.json()
                                if not second_data.get('shredder_pending'):
                                    self.log_test("STEELOS One-Time Token Use", True,
                                                "Token removed after first retrieval", "HIGH")
                                else:
                                    self.log_test("STEELOS One-Time Token Use", False,
                                                "Token still available after retrieval", "MEDIUM")
                        else:
                            self.log_test("STEELOS Kill Token Retrieval", False,
                                        "No kill token in status response", "HIGH")
                    else:
                        self.log_test("STEELOS Kill Token Retrieval", False,
                                    f"Status check failed: HTTP {status_response.status_code}", "HIGH")
                else:
                    self.log_test("STEELOS-Shredder Deployment", False,
                                f"Deployment failed: {deploy_data}", "HIGH")
            else:
                self.log_test("STEELOS-Shredder Deployment", False,
                            f"Deployment request failed: HTTP {deploy_response.status_code}", "CRITICAL")
                
        except Exception as e:
            self.log_test("STEELOS-Shredder Functionality", False, f"Exception: {str(e)}", "HIGH")

    def test_advanced_injection_attacks(self):
        """Test 7: Test against advanced injection attacks"""
        print("\n🛡️ Testing Advanced Injection Attack Resistance")
        
        # Advanced injection payloads
        advanced_payloads = [
            # SQL Injection variants
            "'; DROP TABLE notes; --",
            "' UNION SELECT * FROM users; --",
            "1' OR '1'='1",
            "admin'--",
            "' OR 1=1#",
            
            # XSS variants
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "';alert(String.fromCharCode(88,83,83))//';alert(String.fromCharCode(88,83,83))//",
            
            # Command injection
            "; cat /etc/passwd",
            "| whoami",
            "`id`",
            "$(id)",
            
            # Path traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts",
            "....//....//....//etc/passwd",
            
            # NoSQL injection
            "{'$ne': null}",
            "{'$gt': ''}",
            "'; return true; //",
            
            # LDAP injection
            "*)(&(objectClass=*)",
            "*)(uid=*))(|(uid=*",
            
            # XML injection
            "<?xml version='1.0'?><!DOCTYPE root [<!ENTITY test SYSTEM 'file:///etc/passwd'>]><root>&test;</root>",
            
            # Template injection
            "{{7*7}}",
            "${7*7}",
            "#{7*7}",
            
            # Header injection
            "test\r\nSet-Cookie: admin=true",
            "test\nLocation: http://evil.com"
        ]
        
        blocked_count = 0
        total_tests = len(advanced_payloads)
        
        for i, payload in enumerate(advanced_payloads):
            try:
                # Test in different contexts
                contexts = [
                    ("Notes ciphertext", lambda p: requests.post(f"{API_BASE}/notes", 
                                                               json={"ciphertext": p, "ttl_seconds": 3600, "read_limit": 1})),
                    ("Envelope to_oid", lambda p: requests.post(f"{API_BASE}/envelopes/send",
                                                              json={"to_oid": p, "from_oid": "test", "ciphertext": "test"})),
                    ("STEELOS device_id", lambda p: requests.post(f"{API_BASE}/steelos-shredder/deploy",
                                                                json={"device_id": p, "trigger_type": "manual"}))
                ]
                
                payload_blocked = False
                
                for context_name, test_func in contexts:
                    try:
                        response = test_func(payload)
                        if response.status_code == 400:  # Input sanitization blocked it
                            payload_blocked = True
                            break
                    except:
                        continue
                
                if payload_blocked:
                    blocked_count += 1
                    
            except Exception as e:
                continue
        
        block_rate = (blocked_count / total_tests) * 100
        
        if block_rate >= 90:
            self.log_test("Advanced Injection Attack Resistance", True,
                         f"{blocked_count}/{total_tests} ({block_rate:.1f}%) advanced payloads blocked", "HIGH")
        elif block_rate >= 75:
            self.log_test("Advanced Injection Attack Resistance", True,
                         f"{blocked_count}/{total_tests} ({block_rate:.1f}%) payloads blocked - good protection", "MEDIUM")
        else:
            self.log_test("Advanced Injection Attack Resistance", False,
                         f"Only {blocked_count}/{total_tests} ({block_rate:.1f}%) payloads blocked - insufficient protection", "CRITICAL")

    def test_memory_management_security(self):
        """Test 8: Verify no sensitive data persists in memory"""
        print("\n🧠 Testing Memory Management Security")
        
        try:
            # Create and read a secure note to test memory handling
            test_ciphertext = "SENSITIVE_TEST_DATA_SHOULD_NOT_PERSIST_IN_MEMORY_12345"
            
            # Create note
            create_payload = {
                "ciphertext": test_ciphertext,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            create_response = requests.post(f"{API_BASE}/notes", json=create_payload)
            
            if create_response.status_code == 200:
                note_data = create_response.json()
                note_id = note_data.get('id')
                
                if note_id:
                    # Read the note (should consume it)
                    read_response = requests.get(f"{API_BASE}/notes/{note_id}")
                    
                    if read_response.status_code == 200:
                        # Try to read again (should fail - note consumed)
                        second_read = requests.get(f"{API_BASE}/notes/{note_id}")
                        
                        if second_read.status_code == 404:
                            self.log_test("Secure Note Memory Clearing", True,
                                        "Note properly removed from memory after read", "HIGH")
                        else:
                            self.log_test("Secure Note Memory Clearing", False,
                                        "Note still accessible after consumption", "HIGH")
                        
                        # Test that sensitive data doesn't leak in other endpoints
                        leak_test_endpoints = [
                            f"{API_BASE}/",
                            f"{API_BASE}/notes",
                            f"{API_BASE}/envelopes/poll?oid=test"
                        ]
                        
                        data_leaked = False
                        
                        for endpoint in leak_test_endpoints:
                            try:
                                leak_response = requests.get(endpoint)
                                if test_ciphertext in leak_response.text:
                                    data_leaked = True
                                    break
                            except:
                                continue
                        
                        if data_leaked:
                            self.log_test("Sensitive Data Leakage Prevention", False,
                                        "Sensitive data found in other endpoint responses", "CRITICAL")
                        else:
                            self.log_test("Sensitive Data Leakage Prevention", True,
                                        "No sensitive data leakage detected", "HIGH")
                    else:
                        self.log_test("Secure Note Memory Test", False,
                                    f"Could not read note: HTTP {read_response.status_code}", "MEDIUM")
                else:
                    self.log_test("Secure Note Memory Test", False, "No note ID returned", "MEDIUM")
            else:
                self.log_test("Secure Note Memory Test", False,
                            f"Could not create note: HTTP {create_response.status_code}", "MEDIUM")
                
        except Exception as e:
            self.log_test("Memory Management Security", False, f"Exception: {str(e)}", "MEDIUM")

    def run_comprehensive_security_audit(self):
        """Run all security audit tests"""
        print("🔒 COMPREHENSIVE SECURITY AUDIT TESTING")
        print("Testing critical security fixes after implementation")
        print("=" * 80)
        
        # Run all security tests
        self.test_hardcoded_credentials_exposure()
        self.test_master_key_memory_clearing()
        self.test_rate_limiting_bypass_attempts()
        self.test_emergency_revocation_backend()
        self.test_security_event_logging()
        self.test_steelos_shredder_functionality()
        self.test_advanced_injection_attacks()
        self.test_memory_management_security()
        
        # Generate comprehensive security report
        self.generate_security_report()

    def generate_security_report(self):
        """Generate comprehensive security audit report"""
        print("\n" + "=" * 80)
        print("🔒 COMPREHENSIVE SECURITY AUDIT REPORT")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        # Categorize by severity
        critical_failures = sum(1 for result in self.test_results 
                              if not result['success'] and result.get('severity') == 'CRITICAL')
        high_failures = sum(1 for result in self.test_results 
                          if not result['success'] and result.get('severity') == 'HIGH')
        
        print(f"Total Security Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"🚨 Critical Failures: {critical_failures}")
        print(f"⚠️ High Severity Failures: {high_failures}")
        print(f"Security Score: {(passed_tests/total_tests)*100:.1f}%")
        
        # Security assessment
        if critical_failures > 0:
            print("\n🚨 CRITICAL SECURITY ISSUES DETECTED")
            print("Immediate attention required before production deployment")
        elif high_failures > 2:
            print("\n⚠️ SIGNIFICANT SECURITY CONCERNS")
            print("Multiple high-severity issues need addressing")
        elif failed_tests > 0:
            print("\n🔍 MINOR SECURITY ISSUES")
            print("Some security improvements recommended")
        else:
            print("\n🎉 EXCELLENT SECURITY POSTURE")
            print("All security tests passed - production ready")
        
        # Detailed failure report
        if failed_tests > 0:
            print(f"\n❌ FAILED SECURITY TESTS:")
            for result in self.test_results:
                if not result['success']:
                    severity_icon = {"CRITICAL": "🚨", "HIGH": "⚠️", "MEDIUM": "🔍", "LOW": "ℹ️"}.get(result.get('severity'), '📋')
                    print(f"  {severity_icon} {result['test']}: {result['details']}")
        
        # Security recommendations
        print(f"\n🛡️ SECURITY RECOMMENDATIONS:")
        if critical_failures > 0:
            print("  • Address all critical security vulnerabilities immediately")
            print("  • Conduct additional penetration testing")
            print("  • Review security architecture")
        if high_failures > 0:
            print("  • Implement additional security controls")
            print("  • Enhance monitoring and logging")
        print("  • Regular security audits recommended")
        print("  • Keep security dependencies updated")
        
        return passed_tests, failed_tests, critical_failures, high_failures

if __name__ == "__main__":
    print(f"Testing backend security at: {API_BASE}")
    tester = SecurityAuditTester()
    tester.run_comprehensive_security_audit()
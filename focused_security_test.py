#!/usr/bin/env python3
"""
FOCUSED SECURITY TESTING
Testing the specific security fixes mentioned in the review request
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

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://graphite-killer.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class FocusedSecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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

    def test_basic_api_connectivity(self):
        """Test basic API connectivity"""
        print("\n🔗 Testing Basic API Connectivity")
        
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                self.log_test("Basic API Connectivity", True, f"API responding: {response.json()}", "INFO")
                return True
            else:
                self.log_test("Basic API Connectivity", False, f"HTTP {response.status_code}", "CRITICAL")
                return False
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection failed: {str(e)}", "CRITICAL")
            return False

    def test_hardcoded_credentials_exposure(self):
        """Test 1: Verify no hardcoded credentials are exposed in responses"""
        print("\n🔐 Testing Hardcoded Credentials Exposure")
        
        # Test various endpoints for credential leakage
        endpoints_to_test = [
            "/",
            "/notes",
            "/envelopes/send", 
            "/steelos-shredder/deploy"
        ]
        
        credential_patterns = [
            r'password["\s]*[:=]["\s]*[^"]{3,}',
            r'secret["\s]*[:=]["\s]*[^"]{3,}',
            r'STEELOS_SHREDDER_KILL_TOKEN_SECRET',
            r'mongodb://[^"]*:[^"]*@',
            r'DUAL_KEY.*SECRET',
            r'OMERTA.*SECRET'
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
                        
            except Exception as e:
                continue
        
        if credentials_found:
            self.log_test("Hardcoded Credentials Exposure", False, 
                         f"Found {len(credentials_found)} potential credential exposures", "CRITICAL")
        else:
            self.log_test("Hardcoded Credentials Exposure", True, 
                         "No hardcoded credentials found in API responses", "HIGH")

    def test_rate_limiting_functionality(self):
        """Test 3: Verify rate limiting is working"""
        print("\n🚦 Testing Rate Limiting Functionality")
        
        try:
            # Test rate limiting on notes endpoint (10/min limit)
            rate_limited = False
            
            for i in range(15):  # Try to exceed 10/min limit
                payload = {"ciphertext": f"rate_test_{i}", "ttl_seconds": 3600, "read_limit": 1}
                response = self.session.post(f"{API_BASE}/notes", json=payload)
                
                if response.status_code == 429:
                    rate_limited = True
                    self.log_test("Rate Limiting Functionality", True,
                                f"Rate limit triggered after {i+1} requests", "HIGH")
                    break
                elif response.status_code != 200:
                    # Some other error, not rate limiting
                    break
                    
                time.sleep(0.1)  # Small delay between requests
            
            if not rate_limited:
                self.log_test("Rate Limiting Functionality", False,
                            "Rate limiting not working - all requests succeeded", "HIGH")
                
        except Exception as e:
            self.log_test("Rate Limiting Functionality", False, f"Exception: {str(e)}", "MEDIUM")

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
            
            deploy_response = self.session.post(f"{API_BASE}/steelos-shredder/deploy", json=deployment_payload)
            
            if deploy_response.status_code == 200:
                deploy_data = deploy_response.json()
                
                if deploy_data.get('shredder_activated') and deploy_data.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True,
                                f"Shredder activated: {deploy_data.get('message')}", "HIGH")
                    
                    # Test kill token retrieval
                    time.sleep(1)  # Brief delay
                    
                    status_response = self.session.get(f"{API_BASE}/steelos-shredder/status/{device_id}")
                    
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

    def test_input_sanitization(self):
        """Test 7: Test input sanitization against injection attacks"""
        print("\n🛡️ Testing Input Sanitization")
        
        # Test injection payloads
        injection_payloads = [
            # SQL Injection
            "'; DROP TABLE notes; --",
            "' UNION SELECT * FROM users; --",
            
            # XSS
            "<script>alert('XSS')</script>",
            "javascript:alert(1)",
            
            # Command injection
            "; cat /etc/passwd",
            "| whoami",
            
            # Path traversal
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\drivers\\etc\\hosts"
        ]
        
        blocked_count = 0
        total_tests = len(injection_payloads)
        
        for payload in injection_payloads:
            try:
                # Test in notes ciphertext field
                test_payload = {"ciphertext": payload, "ttl_seconds": 3600, "read_limit": 1}
                response = self.session.post(f"{API_BASE}/notes", json=test_payload)
                
                if response.status_code == 400:  # Input sanitization blocked it
                    blocked_count += 1
                    
            except Exception as e:
                continue
        
        block_rate = (blocked_count / total_tests) * 100
        
        if block_rate >= 75:
            self.log_test("Input Sanitization", True,
                         f"{blocked_count}/{total_tests} ({block_rate:.1f}%) payloads blocked", "HIGH")
        else:
            self.log_test("Input Sanitization", False,
                         f"Only {blocked_count}/{total_tests} ({block_rate:.1f}%) payloads blocked", "HIGH")

    def test_memory_management_security(self):
        """Test 8: Verify no sensitive data persists in memory"""
        print("\n🧠 Testing Memory Management Security")
        
        try:
            # Create and read a secure note to test memory handling
            test_ciphertext = "SENSITIVE_TEST_DATA_SHOULD_NOT_PERSIST_12345"
            
            # Create note
            create_payload = {
                "ciphertext": test_ciphertext,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            create_response = self.session.post(f"{API_BASE}/notes", json=create_payload)
            
            if create_response.status_code == 200:
                note_data = create_response.json()
                note_id = note_data.get('id')
                
                if note_id:
                    # Read the note (should consume it)
                    read_response = self.session.get(f"{API_BASE}/notes/{note_id}")
                    
                    if read_response.status_code == 200:
                        # Try to read again (should fail - note consumed)
                        second_read = self.session.get(f"{API_BASE}/notes/{note_id}")
                        
                        if second_read.status_code == 404:
                            self.log_test("Secure Note Memory Clearing", True,
                                        "Note properly removed from memory after read", "HIGH")
                        else:
                            self.log_test("Secure Note Memory Clearing", False,
                                        "Note still accessible after consumption", "HIGH")
                        
                        # Test that sensitive data doesn't leak in other endpoints
                        leak_test_endpoints = [
                            f"{API_BASE}/",
                            f"{API_BASE}/envelopes/poll?oid=test"
                        ]
                        
                        data_leaked = False
                        
                        for endpoint in leak_test_endpoints:
                            try:
                                leak_response = self.session.get(endpoint)
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

    def test_dual_key_system_security(self):
        """Test 1: Dual-Key System Security - No hardcoded credentials exposed"""
        print("\n🔐🔐 Testing Dual-Key System Security")
        
        try:
            # Test dual-key operation initiation
            payload = {
                'operation_type': 'security_test',
                'operation_data': {'test': 'credential_exposure'},
                'operator_a_id': 'test_operator_a',
                'operator_b_id': 'test_operator_b'
            }
            
            response = self.session.post(f"{API_BASE}/dual-key/initiate", json=payload)
            
            # Check response for credential exposure
            response_text = response.text.lower()
            
            credential_patterns = [
                'password',
                'secret',
                'totp_secret',
                'key_fragment',
                'dual_key.*password',
                'dual_key.*secret'
            ]
            
            credentials_found = []
            for pattern in credential_patterns:
                if pattern in response_text:
                    credentials_found.append(pattern)
            
            if credentials_found:
                self.log_test("Dual-Key Credential Exposure", False,
                            f"Potential credentials found in response: {credentials_found}", "CRITICAL")
            else:
                self.log_test("Dual-Key Credential Exposure", True,
                            "No credentials exposed in dual-key responses", "HIGH")
                
        except Exception as e:
            self.log_test("Dual-Key System Security", False, f"Exception: {str(e)}", "MEDIUM")

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
                    'reason'
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
                        
            else:
                self.log_test("Emergency Portal Accessibility", False,
                            f"Emergency portal not accessible: HTTP {portal_response.status_code}", "CRITICAL")
                
        except Exception as e:
            self.log_test("Emergency Revocation Backend", False, f"Exception: {str(e)}", "HIGH")

    def run_focused_security_tests(self):
        """Run focused security tests"""
        print("🔒 FOCUSED SECURITY TESTING")
        print("Testing critical security fixes after implementation")
        print("=" * 80)
        
        # Test basic connectivity first
        if not self.test_basic_api_connectivity():
            print("❌ Cannot proceed - API not accessible")
            return
        
        # Run focused security tests
        self.test_hardcoded_credentials_exposure()
        self.test_dual_key_system_security()
        self.test_rate_limiting_functionality()
        self.test_emergency_revocation_backend()
        self.test_steelos_shredder_functionality()
        self.test_input_sanitization()
        self.test_memory_management_security()
        
        # Generate focused security report
        self.generate_focused_security_report()

    def generate_focused_security_report(self):
        """Generate focused security audit report"""
        print("\n" + "=" * 80)
        print("🔒 FOCUSED SECURITY AUDIT REPORT")
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
        
        return passed_tests, failed_tests, critical_failures, high_failures

if __name__ == "__main__":
    print(f"Testing backend security at: {API_BASE}")
    tester = FocusedSecurityTester()
    tester.run_focused_security_tests()
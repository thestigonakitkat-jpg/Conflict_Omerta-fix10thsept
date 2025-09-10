#!/usr/bin/env python3
"""
🔒 OMERTÁ TARGETED SECURITY TEST
Focus on specific security aspects without triggering rate limiting
"""

import requests
import time
import json
from datetime import datetime

BACKEND_URL = "http://localhost:8001/api"

class TargetedSecurityTester:
    def __init__(self):
        self.results = []
        
    def log_result(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} | {test_name}"
        if details:
            result += f" | {details}"
        print(result)
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details
        })

    def test_sql_injection_single_payload(self):
        """Test a single SQL injection payload to avoid rate limiting"""
        print("\n🛡️ TESTING SQL INJECTION (Single Payload)")
        
        payload = "'; DROP TABLE notes; --"
        try:
            note_data = {
                "ciphertext": payload,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 400:
                self.log_result("SQL Injection Blocking", True, "Dangerous SQL payload blocked")
                return True
            else:
                self.log_result("SQL Injection Blocking", False, f"SQL payload not blocked (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.log_result("SQL Injection Blocking", False, f"Error: {str(e)}")
            return False

    def test_xss_single_payload(self):
        """Test a single XSS payload to avoid rate limiting"""
        print("\n🛡️ TESTING XSS (Single Payload)")
        
        payload = "<script>alert('xss')</script>"
        try:
            note_data = {
                "ciphertext": payload,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 400:
                self.log_result("XSS Attack Blocking", True, "Dangerous XSS payload blocked")
                return True
            else:
                self.log_result("XSS Attack Blocking", False, f"XSS payload not blocked (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.log_result("XSS Attack Blocking", False, f"Error: {str(e)}")
            return False

    def test_command_injection_single_payload(self):
        """Test a single command injection payload to avoid rate limiting"""
        print("\n🛡️ TESTING COMMAND INJECTION (Single Payload)")
        
        payload = "; rm -rf /"
        try:
            note_data = {
                "ciphertext": payload,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 400:
                self.log_result("Command Injection Blocking", True, "Dangerous command payload blocked")
                return True
            else:
                self.log_result("Command Injection Blocking", False, f"Command payload not blocked (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.log_result("Command Injection Blocking", False, f"Error: {str(e)}")
            return False

    def test_legitimate_content(self):
        """Test that legitimate encrypted content is not blocked"""
        print("\n🛡️ TESTING LEGITIMATE CONTENT")
        
        # Base64 encoded content (simulating encrypted data)
        legitimate_payload = "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt"
        try:
            note_data = {
                "ciphertext": legitimate_payload,
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                self.log_result("Legitimate Content Allowed", True, "Encrypted content properly accepted")
                return True
            else:
                self.log_result("Legitimate Content Allowed", False, f"Legitimate content blocked (HTTP {response.status_code})")
                return False
        except Exception as e:
            self.log_result("Legitimate Content Allowed", False, f"Error: {str(e)}")
            return False

    def test_security_headers(self):
        """Test security headers"""
        print("\n🛡️ TESTING SECURITY HEADERS")
        
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            
            required_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security",
                "Content-Security-Policy"
            ]
            
            headers_present = 0
            for header in required_headers:
                if header in response.headers:
                    headers_present += 1
            
            success = headers_present >= 4  # At least 4 out of 5 critical headers
            self.log_result("Security Headers", success, f"{headers_present}/{len(required_headers)} critical headers present")
            return success
            
        except Exception as e:
            self.log_result("Security Headers", False, f"Error: {str(e)}")
            return False

    def test_csrf_token_generation(self):
        """Test CSRF token generation"""
        print("\n🛡️ TESTING CSRF TOKEN GENERATION")
        
        try:
            response = requests.get(f"{BACKEND_URL}/security/csrf-token", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('csrf_token') and data.get('expires_in'):
                    self.log_result("CSRF Token Generation", True, "CSRF token generated successfully")
                    return True
                else:
                    self.log_result("CSRF Token Generation", False, "Invalid CSRF token response")
                    return False
            else:
                self.log_result("CSRF Token Generation", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("CSRF Token Generation", False, f"Error: {str(e)}")
            return False

    def test_core_system_basic_api(self):
        """Test basic API functionality"""
        print("\n🛡️ TESTING BASIC API")
        
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            if response.status_code == 200 and response.json().get("message") == "Hello World":
                self.log_result("Basic API", True, "API responding correctly")
                return True
            else:
                self.log_result("Basic API", False, f"API not responding correctly")
                return False
        except Exception as e:
            self.log_result("Basic API", False, f"Error: {str(e)}")
            return False

    def test_steelos_shredder(self):
        """Test STEELOS-Shredder system"""
        print("\n🛡️ TESTING STEELOS-SHREDDER")
        
        try:
            shredder_data = {
                "device_id": "security_test_device",
                "trigger_type": "manual"
            }
            
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=shredder_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('shredder_activated') and result.get('kill_token_generated'):
                    self.log_result("STEELOS-Shredder", True, "STEELOS-Shredder deployment successful")
                    return True
                else:
                    self.log_result("STEELOS-Shredder", False, "STEELOS-Shredder deployment failed")
                    return False
            else:
                self.log_result("STEELOS-Shredder", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("STEELOS-Shredder", False, f"Error: {str(e)}")
            return False

    def test_pin_security(self):
        """Test PIN security system"""
        print("\n🛡️ TESTING PIN SECURITY")
        
        try:
            # Test normal PIN
            pin_data = {
                "device_id": "security_test_pin_device",
                "pin": "123456",
                "timestamp": int(time.time())
            }
            
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_result("PIN Security", True, "PIN verification working")
                    return True
                else:
                    self.log_result("PIN Security", False, "PIN verification failed")
                    return False
            else:
                self.log_result("PIN Security", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("PIN Security", False, f"Error: {str(e)}")
            return False

    def test_admin_authentication(self):
        """Test admin authentication"""
        print("\n🛡️ TESTING ADMIN AUTHENTICATION")
        
        try:
            auth_data = {
                "admin_passphrase": "Omertaisthecode#01",
                "device_id": "security_test_admin_device"
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/authenticate", json=auth_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('session_token'):
                    self.log_result("Admin Authentication", True, "Admin authentication working")
                    return True
                else:
                    self.log_result("Admin Authentication", False, "Admin authentication failed")
                    return False
            else:
                self.log_result("Admin Authentication", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_result("Admin Authentication", False, f"Error: {str(e)}")
            return False

    def run_targeted_test(self):
        """Run targeted security tests"""
        print("🔒 OMERTÁ TARGETED SECURITY TEST")
        print("=" * 60)
        
        # Wait a bit to avoid rate limiting from previous tests
        print("⏳ Waiting to avoid rate limiting...")
        time.sleep(5)
        
        tests = [
            self.test_core_system_basic_api,
            self.test_legitimate_content,
            self.test_sql_injection_single_payload,
            self.test_xss_single_payload,
            self.test_command_injection_single_payload,
            self.test_security_headers,
            self.test_csrf_token_generation,
            self.test_steelos_shredder,
            self.test_pin_security,
            self.test_admin_authentication
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
                # Small delay between tests to avoid rate limiting
                time.sleep(1)
            except Exception as e:
                print(f"Test error: {e}")
        
        print("\n" + "=" * 60)
        print("🎯 TARGETED SECURITY TEST RESULTS")
        print("=" * 60)
        
        success_rate = (passed / total) * 100
        print(f"📊 TESTS PASSED: {passed}/{total} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT SECURITY POSTURE")
        elif success_rate >= 80:
            print("✅ GOOD SECURITY POSTURE")
        elif success_rate >= 70:
            print("⚠️ ACCEPTABLE SECURITY POSTURE")
        else:
            print("🚨 SECURITY IMPROVEMENTS NEEDED")
        
        # Detailed results
        print(f"\n📋 DETAILED RESULTS:")
        for result in self.results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['details']}")
        
        return success_rate

if __name__ == "__main__":
    tester = TargetedSecurityTester()
    success_rate = tester.run_targeted_test()
    print(f"\n🔒 FINAL ASSESSMENT: {success_rate:.1f}% security compliance")
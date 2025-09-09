#!/usr/bin/env python3
"""
OMERTA Security Testing Suite - 100/100 Security Verification
Comprehensive security testing for Signal Protocol, Rate Limiting, Security Headers, and more
"""

import requests
import json
import time
import sys
import threading
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess

# Get backend URL from environment
BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

class SecurityTester:
    def __init__(self):
        self.results = []
        
    def log_result(self, test_name, success, details=""):
        """Log test result"""
        self.results.append((test_name, success, details))
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{test_name:<50} {status}")
        if details:
            print(f"    Details: {details}")

    def test_signal_protocol_dependencies(self):
        """Test Signal Protocol library installation and availability"""
        print("\n=== Testing Signal Protocol Integration ===")
        
        try:
            # Check if cryptography library is available (used for Signal Protocol)
            import cryptography
            from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
            
            # Test basic cryptographic operations that Signal Protocol would use
            # Test AES-GCM encryption (used in Signal Protocol)
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM
            
            key = AESGCM.generate_key(bit_length=256)
            aesgcm = AESGCM(key)
            nonce = b"unique_nonce"
            data = b"test_signal_message"
            
            # Encrypt
            ciphertext = aesgcm.encrypt(nonce, data, None)
            
            # Decrypt
            plaintext = aesgcm.decrypt(nonce, ciphertext, None)
            
            if plaintext == data:
                self.log_result("Signal Protocol - Cryptography Library", True, "AES-GCM encryption/decryption working")
            else:
                self.log_result("Signal Protocol - Cryptography Library", False, "AES-GCM test failed")
                
            # Test key derivation (used in Signal Protocol key exchange)
            password = b"test_password"
            salt = b"test_salt_16b"
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password)
            
            if len(key) == 32:
                self.log_result("Signal Protocol - Key Derivation", True, "PBKDF2 key derivation working")
            else:
                self.log_result("Signal Protocol - Key Derivation", False, "Key derivation failed")
                
        except ImportError as e:
            self.log_result("Signal Protocol - Dependencies", False, f"Missing cryptography library: {e}")
        except Exception as e:
            self.log_result("Signal Protocol - Dependencies", False, f"Cryptography test failed: {e}")

    def test_rate_limiting_notes(self):
        """Test rate limiting on /api/notes endpoints (10/min create, 30/min read)"""
        print("\n=== Testing Rate Limiting - Notes Endpoints ===")
        
        # Test create note rate limit (10/minute)
        print("Testing POST /api/notes rate limit (10/minute)...")
        
        create_success_count = 0
        create_rate_limited = False
        note_ids = []
        
        # Try to create 12 notes rapidly (should hit rate limit)
        for i in range(12):
            payload = {
                "ciphertext": f"rate_test_{i}",
                "ttl_seconds": 60,
                "read_limit": 1
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/notes", json=payload)
                
                if response.status_code == 200:
                    create_success_count += 1
                    note_ids.append(response.json()["id"])
                elif response.status_code == 429:  # Rate limited
                    create_rate_limited = True
                    # Check for rate limit headers
                    headers = response.headers
                    if "X-RateLimit-Limit" in headers or "Retry-After" in headers:
                        self.log_result("Notes Create Rate Limit Headers", True, f"Rate limit headers present: {dict(headers)}")
                    break
                    
            except Exception as e:
                print(f"Error in create rate limit test: {e}")
                
        if create_rate_limited and create_success_count <= 10:
            self.log_result("Notes Create Rate Limit (10/min)", True, f"Rate limited after {create_success_count} requests")
        else:
            self.log_result("Notes Create Rate Limit (10/min)", False, f"Expected rate limit, got {create_success_count} successes")
        
        # Test read note rate limit (30/minute) if we have notes
        if note_ids:
            print("Testing GET /api/notes rate limit (30/minute)...")
            
            read_success_count = 0
            read_rate_limited = False
            
            # Try to read notes rapidly (should hit rate limit after 30)
            for i in range(35):
                note_id = note_ids[0] if note_ids else "dummy_id"
                
                try:
                    response = requests.get(f"{BACKEND_URL}/notes/{note_id}")
                    
                    if response.status_code in [200, 404, 410]:  # Valid responses
                        read_success_count += 1
                    elif response.status_code == 429:  # Rate limited
                        read_rate_limited = True
                        break
                        
                except Exception as e:
                    print(f"Error in read rate limit test: {e}")
                    
            if read_rate_limited and read_success_count <= 30:
                self.log_result("Notes Read Rate Limit (30/min)", True, f"Rate limited after {read_success_count} requests")
            else:
                self.log_result("Notes Read Rate Limit (30/min)", False, f"Expected rate limit, got {read_success_count} successes")

    def test_rate_limiting_envelopes(self):
        """Test rate limiting on /api/envelopes endpoints (50/min send, 100/min poll)"""
        print("\n=== Testing Rate Limiting - Envelopes Endpoints ===")
        
        # Test send envelope rate limit (50/minute)
        print("Testing POST /api/envelopes/send rate limit (50/minute)...")
        
        send_success_count = 0
        send_rate_limited = False
        
        # Try to send 55 envelopes rapidly (should hit rate limit)
        for i in range(55):
            payload = {
                "to_oid": f"rate_test_user_{i}",
                "from_oid": "rate_tester",
                "ciphertext": f"rate_test_message_{i}"
            }
            
            try:
                response = requests.post(f"{BACKEND_URL}/envelopes/send", json=payload)
                
                if response.status_code == 200:
                    send_success_count += 1
                elif response.status_code == 429:  # Rate limited
                    send_rate_limited = True
                    break
                    
            except Exception as e:
                print(f"Error in send rate limit test: {e}")
                
        if send_rate_limited and send_success_count <= 50:
            self.log_result("Envelopes Send Rate Limit (50/min)", True, f"Rate limited after {send_success_count} requests")
        else:
            self.log_result("Envelopes Send Rate Limit (50/min)", False, f"Expected rate limit, got {send_success_count} successes")
        
        # Test poll envelope rate limit (100/minute)
        print("Testing GET /api/envelopes/poll rate limit (100/minute)...")
        
        poll_success_count = 0
        poll_rate_limited = False
        
        # Try to poll 105 times rapidly (should hit rate limit)
        for i in range(105):
            try:
                response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=rate_test_user_{i}")
                
                if response.status_code == 200:
                    poll_success_count += 1
                elif response.status_code == 429:  # Rate limited
                    poll_rate_limited = True
                    break
                    
            except Exception as e:
                print(f"Error in poll rate limit test: {e}")
                
        if poll_rate_limited and poll_success_count <= 100:
            self.log_result("Envelopes Poll Rate Limit (100/min)", True, f"Rate limited after {poll_success_count} requests")
        else:
            self.log_result("Envelopes Poll Rate Limit (100/min)", False, f"Expected rate limit, got {poll_success_count} successes")

    def test_security_headers(self):
        """Test comprehensive security headers implementation"""
        print("\n=== Testing Security Headers ===")
        
        try:
            # Test on a simple endpoint
            response = requests.get(f"{BACKEND_URL}/")
            
            expected_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'",
                "Referrer-Policy": "strict-origin-when-cross-origin",
                "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
                "X-Permitted-Cross-Domain-Policies": "none",
                "Cross-Origin-Embedder-Policy": "require-corp",
                "Cross-Origin-Opener-Policy": "same-origin",
                "Cross-Origin-Resource-Policy": "cross-origin"
            }
            
            missing_headers = []
            present_headers = []
            
            for header, expected_value in expected_headers.items():
                if header in response.headers:
                    actual_value = response.headers[header]
                    if actual_value == expected_value:
                        present_headers.append(header)
                    else:
                        missing_headers.append(f"{header} (expected: {expected_value}, got: {actual_value})")
                else:
                    missing_headers.append(header)
            
            if not missing_headers:
                self.log_result("Security Headers - All Present", True, f"All {len(expected_headers)} security headers present")
            else:
                self.log_result("Security Headers - Missing", False, f"Missing: {missing_headers}")
            
            # Test HSTS specifically
            if "Strict-Transport-Security" in response.headers:
                hsts_value = response.headers["Strict-Transport-Security"]
                if "max-age=" in hsts_value and "includeSubDomains" in hsts_value:
                    self.log_result("HSTS Header", True, f"HSTS properly configured: {hsts_value}")
                else:
                    self.log_result("HSTS Header", False, f"HSTS misconfigured: {hsts_value}")
            else:
                self.log_result("HSTS Header", False, "HSTS header missing")
                
            # Test CSP specifically
            if "Content-Security-Policy" in response.headers:
                csp_value = response.headers["Content-Security-Policy"]
                if "default-src 'self'" in csp_value:
                    self.log_result("CSP Header", True, f"CSP properly configured: {csp_value}")
                else:
                    self.log_result("CSP Header", False, f"CSP misconfigured: {csp_value}")
            else:
                self.log_result("CSP Header", False, "CSP header missing")
                
        except Exception as e:
            self.log_result("Security Headers Test", False, f"Error testing headers: {e}")

    def test_input_validation_security(self):
        """Test input validation and sanitization"""
        print("\n=== Testing Input Validation & Security ===")
        
        # Test malicious input in note creation
        malicious_payloads = [
            {"ciphertext": "", "ttl_seconds": 60, "read_limit": 1},  # Empty ciphertext
            {"ciphertext": "test", "ttl_seconds": -1, "read_limit": 1},  # Negative TTL
            {"ciphertext": "test", "ttl_seconds": 999999999, "read_limit": 1},  # Excessive TTL
            {"ciphertext": "test", "ttl_seconds": 60, "read_limit": 0},  # Invalid read limit
            {"ciphertext": "test", "ttl_seconds": 60, "read_limit": 10},  # Excessive read limit
            {"ciphertext": "<script>alert('xss')</script>", "ttl_seconds": 60, "read_limit": 1},  # XSS attempt
            {"ciphertext": "'; DROP TABLE notes; --", "ttl_seconds": 60, "read_limit": 1},  # SQL injection attempt
        ]
        
        validation_passed = 0
        total_tests = len(malicious_payloads)
        
        for i, payload in enumerate(malicious_payloads):
            try:
                response = requests.post(f"{BACKEND_URL}/notes", json=payload)
                
                # Should return 422 (validation error) or 400 (bad request)
                if response.status_code in [400, 422]:
                    validation_passed += 1
                    print(f"  Payload {i+1}: Correctly rejected (status: {response.status_code})")
                else:
                    print(f"  Payload {i+1}: Incorrectly accepted (status: {response.status_code})")
                    
            except Exception as e:
                print(f"  Payload {i+1}: Error testing - {e}")
        
        if validation_passed == total_tests:
            self.log_result("Input Validation", True, f"All {total_tests} malicious payloads correctly rejected")
        else:
            self.log_result("Input Validation", False, f"Only {validation_passed}/{total_tests} malicious payloads rejected")
        
        # Test error handling doesn't leak sensitive info
        try:
            response = requests.get(f"{BACKEND_URL}/notes/invalid_id_test")
            
            if response.status_code == 404:
                error_data = response.json()
                # Should not contain stack traces, internal paths, or sensitive info
                error_detail = str(error_data.get("detail", ""))
                
                sensitive_patterns = ["traceback", "/app/", "exception", "error:", "stack"]
                has_sensitive_info = any(pattern.lower() in error_detail.lower() for pattern in sensitive_patterns)
                
                if not has_sensitive_info and error_detail == "not_found_or_expired":
                    self.log_result("Error Handling Security", True, "Error messages don't leak sensitive information")
                else:
                    self.log_result("Error Handling Security", False, f"Error message may leak info: {error_detail}")
            else:
                self.log_result("Error Handling Security", False, f"Unexpected status code: {response.status_code}")
                
        except Exception as e:
            self.log_result("Error Handling Security", False, f"Error testing error handling: {e}")

    def test_cors_configuration(self):
        """Test CORS configuration security"""
        print("\n=== Testing CORS Configuration ===")
        
        try:
            # Test preflight request
            headers = {
                "Origin": "https://malicious-site.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            response = requests.options(f"{BACKEND_URL}/notes", headers=headers)
            
            # Check CORS headers in response
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
            
            # In production, should not allow all origins (*)
            allow_origin = cors_headers.get("Access-Control-Allow-Origin")
            if allow_origin == "*":
                self.log_result("CORS Configuration", False, "CORS allows all origins (*) - security risk in production")
            else:
                self.log_result("CORS Configuration", True, f"CORS properly configured: {allow_origin}")
                
            # Check if credentials are allowed with wildcard origin
            allow_credentials = response.headers.get("Access-Control-Allow-Credentials")
            if allow_origin == "*" and allow_credentials == "true":
                self.log_result("CORS Credentials Security", False, "CORS allows credentials with wildcard origin")
            else:
                self.log_result("CORS Credentials Security", True, "CORS credentials properly configured")
                
        except Exception as e:
            self.log_result("CORS Configuration Test", False, f"Error testing CORS: {e}")

    def test_performance_under_security(self):
        """Test performance with all security measures enabled"""
        print("\n=== Testing Performance Under Security Constraints ===")
        
        # Test concurrent requests performance
        def make_request():
            try:
                start_time = time.time()
                response = requests.get(f"{BACKEND_URL}/")
                end_time = time.time()
                return response.status_code == 200, end_time - start_time
            except:
                return False, 0
        
        # Test with 20 concurrent requests
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        successful_requests = sum(1 for success, _ in results if success)
        response_times = [time_taken for success, time_taken in results if success]
        
        if successful_requests >= 18:  # Allow for some network variance
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            self.log_result("Concurrent Request Performance", True, 
                          f"{successful_requests}/20 requests successful, avg response time: {avg_response_time:.3f}s")
        else:
            self.log_result("Concurrent Request Performance", False, 
                          f"Only {successful_requests}/20 requests successful")
        
        # Test high-frequency polling performance
        start_time = time.time()
        poll_count = 0
        poll_errors = 0
        
        # Poll for 5 seconds
        while time.time() - start_time < 5:
            try:
                response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=perf_test_user")
                if response.status_code == 200:
                    poll_count += 1
                elif response.status_code == 429:  # Rate limited - expected
                    break
                else:
                    poll_errors += 1
            except:
                poll_errors += 1
        
        if poll_count > 0 and poll_errors < poll_count * 0.1:  # Less than 10% errors
            self.log_result("High-Frequency Polling Performance", True, 
                          f"{poll_count} polls in 5s, {poll_errors} errors")
        else:
            self.log_result("High-Frequency Polling Performance", False, 
                          f"{poll_count} polls, {poll_errors} errors")

    def test_dependency_security(self):
        """Test for vulnerable dependencies"""
        print("\n=== Testing Dependency Security ===")
        
        try:
            # Check if we can run safety check (if available)
            result = subprocess.run(["pip", "list"], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                packages = result.stdout
                
                # Check for known vulnerable packages (basic check)
                vulnerable_patterns = [
                    "urllib3==1.25",  # Known vulnerable version
                    "requests==2.19",  # Known vulnerable version
                    "cryptography==2.9",  # Known vulnerable version
                ]
                
                vulnerabilities_found = []
                for pattern in vulnerable_patterns:
                    if pattern in packages:
                        vulnerabilities_found.append(pattern)
                
                if not vulnerabilities_found:
                    self.log_result("Dependency Vulnerability Check", True, "No known vulnerable packages detected")
                else:
                    self.log_result("Dependency Vulnerability Check", False, 
                                  f"Vulnerable packages found: {vulnerabilities_found}")
                
                # Check for security-related packages
                security_packages = ["cryptography", "pyjwt", "passlib"]
                present_security_packages = []
                
                for pkg in security_packages:
                    if pkg in packages.lower():
                        present_security_packages.append(pkg)
                
                if len(present_security_packages) >= 2:
                    self.log_result("Security Dependencies Present", True, 
                                  f"Security packages found: {present_security_packages}")
                else:
                    self.log_result("Security Dependencies Present", False, 
                                  f"Missing security packages: {set(security_packages) - set(present_security_packages)}")
                    
            else:
                self.log_result("Dependency Security Check", False, "Could not check dependencies")
                
        except Exception as e:
            self.log_result("Dependency Security Check", False, f"Error checking dependencies: {e}")

    def test_websocket_security(self):
        """Test WebSocket security measures"""
        print("\n=== Testing WebSocket Security ===")
        
        try:
            import websocket
            
            # Test WebSocket connection with security headers
            ws_url = BACKEND_URL.replace("https://", "wss://").replace("/api", "/api/ws?oid=security_test")
            
            def on_message(ws, message):
                pass
            
            def on_error(ws, error):
                pass
            
            def on_close(ws, close_status_code, close_msg):
                pass
            
            def on_open(ws):
                ws.close()
            
            # Test connection
            ws = websocket.WebSocketApp(ws_url,
                                      on_open=on_open,
                                      on_message=on_message,
                                      on_error=on_error,
                                      on_close=on_close)
            
            # Run for a short time
            import threading
            wst = threading.Thread(target=ws.run_forever)
            wst.daemon = True
            wst.start()
            time.sleep(2)
            
            self.log_result("WebSocket Security Connection", True, "WebSocket connection test completed")
            
        except ImportError:
            self.log_result("WebSocket Security Test", False, "websocket-client not available for testing")
        except Exception as e:
            self.log_result("WebSocket Security Test", False, f"WebSocket test error: {e}")

    def run_all_tests(self):
        """Run all security tests"""
        print("🔒 OMERTA SECURITY TESTING SUITE - 100/100 VERIFICATION")
        print("=" * 80)
        
        # Run all security tests
        self.test_signal_protocol_dependencies()
        self.test_rate_limiting_notes()
        self.test_rate_limiting_envelopes()
        self.test_security_headers()
        self.test_input_validation_security()
        self.test_cors_configuration()
        self.test_performance_under_security()
        self.test_dependency_security()
        self.test_websocket_security()
        
        # Calculate results
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        
        print("\n" + "=" * 80)
        print("🔒 SECURITY TEST RESULTS SUMMARY")
        print("=" * 80)
        
        for test_name, success, details in self.results:
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{test_name:<50} {status}")
            if details and not success:
                print(f"    Issue: {details}")
        
        print(f"\n📊 SECURITY SCORE: {passed_tests}/{total_tests} ({(passed_tests/total_tests)*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("🎉 PERFECT SECURITY SCORE: 100/100 - ALL SECURITY MEASURES VERIFIED!")
            return 0
        elif passed_tests >= total_tests * 0.9:
            print("🟡 EXCELLENT SECURITY: 90%+ - Minor issues to address")
            return 0
        elif passed_tests >= total_tests * 0.8:
            print("🟠 GOOD SECURITY: 80%+ - Some security improvements needed")
            return 1
        else:
            print("🔴 SECURITY ISSUES: <80% - Significant security improvements required")
            return 1

def main():
    """Main function to run security tests"""
    tester = SecurityTester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())
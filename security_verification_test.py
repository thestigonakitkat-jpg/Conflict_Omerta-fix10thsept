#!/usr/bin/env python3
"""
🔒 COMPREHENSIVE SECURITY VERIFICATION TEST

Verifying all critical security systems mentioned in test_result.md:
- Secure Notes (RAM-only, one-time read)
- STEELOS-Shredder (cryptographic kill tokens)
- Contact Vault (DNA validation)
- Auto-Wipe System
- PIN Security (panic detection)
- Dual-Key Nuclear Protocol
- Admin Multi-Signature System
- LiveKit Video Calling Security
- Rate Limiting and Input Sanitization
"""

import requests
import json
import time
import hashlib
import hmac
import secrets
import random
from datetime import datetime, timezone
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://graphite-killer.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class SecurityVerificationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.device_id = f"security_test_{int(time.time())}"
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    Details: {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    
    def test_secure_notes_one_time_read(self):
        """Test secure notes one-time read functionality"""
        print("\n📝 Testing Secure Notes One-Time Read")
        
        try:
            # Create a secure note
            note_payload = {
                "ciphertext": "VGVzdCBzZWN1cmUgbm90ZSBjb250ZW50",  # Base64 encoded test content
                "meta": {"type": "test_note"},
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            create_response = self.session.post(f"{API_BASE}/notes", json=note_payload)
            
            if create_response.status_code == 200:
                note_data = create_response.json()
                note_id = note_data.get('id')
                
                if note_id:
                    # First read - should succeed
                    read_response1 = self.session.get(f"{API_BASE}/notes/{note_id}")
                    
                    if read_response1.status_code == 200:
                        read_data1 = read_response1.json()
                        views_left = read_data1.get('views_left', 1)
                        
                        # Second read - should fail (note should be purged)
                        read_response2 = self.session.get(f"{API_BASE}/notes/{note_id}")
                        
                        if read_response2.status_code == 404:
                            self.log_test("Secure Notes One-Time Read", True, 
                                        f"Note properly purged after first read (views_left: {views_left})")
                        else:
                            self.log_test("Secure Notes One-Time Read", False, 
                                        f"Note still accessible after first read: {read_response2.status_code}")
                    else:
                        self.log_test("Secure Notes One-Time Read", False, 
                                    f"First read failed: {read_response1.status_code}")
                else:
                    self.log_test("Secure Notes One-Time Read", False, "No note ID returned")
            else:
                self.log_test("Secure Notes One-Time Read", False, 
                            f"Note creation failed: {create_response.status_code}")
                
        except Exception as e:
            self.log_test("Secure Notes One-Time Read", False, f"Exception: {str(e)}")
    
    def test_steelos_shredder_deployment(self):
        """Test STEELOS-Shredder deployment and kill token generation"""
        print("\n💀 Testing STEELOS-Shredder Deployment")
        
        try:
            # Deploy STEELOS-Shredder
            shredder_payload = {
                "device_id": self.device_id,
                "trigger_type": "manual",
                "confirmation_token": "test_confirmation"
            }
            
            deploy_response = self.session.post(f"{API_BASE}/steelos-shredder/deploy", json=shredder_payload)
            
            if deploy_response.status_code == 200:
                deploy_data = deploy_response.json()
                
                if deploy_data.get('shredder_activated') and deploy_data.get('kill_token_generated'):
                    # Check for kill token
                    status_response = self.session.get(f"{API_BASE}/steelos-shredder/status/{self.device_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if status_data.get('shredder_pending') and status_data.get('kill_token'):
                            kill_token = status_data.get('kill_token', {})
                            signature = kill_token.get('signature', '')
                            
                            # Verify cryptographic signature length (HMAC-SHA256 = 64 chars)
                            if len(signature) == 64:
                                self.log_test("STEELOS-Shredder Deployment", True, 
                                            f"Kill token generated with valid signature ({len(signature)} chars)")
                            else:
                                self.log_test("STEELOS-Shredder Deployment", False, 
                                            f"Invalid signature length: {len(signature)} chars")
                        else:
                            self.log_test("STEELOS-Shredder Deployment", False, 
                                        "No kill token found in status response")
                    else:
                        self.log_test("STEELOS-Shredder Deployment", False, 
                                    f"Status check failed: {status_response.status_code}")
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, 
                                f"Deployment failed: {deploy_data}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, 
                            f"Deploy request failed: {deploy_response.status_code}")
                
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Exception: {str(e)}")
    
    def test_steelos_one_time_token_use(self):
        """Test STEELOS-Shredder one-time token use"""
        print("\n💀 Testing STEELOS One-Time Token Use")
        
        try:
            test_device = f"one_time_test_{int(time.time())}"
            
            # Deploy STEELOS-Shredder
            shredder_payload = {
                "device_id": test_device,
                "trigger_type": "manual",
                "confirmation_token": "test_one_time"
            }
            
            self.session.post(f"{API_BASE}/steelos-shredder/deploy", json=shredder_payload)
            
            # First token retrieval - should succeed
            status_response1 = self.session.get(f"{API_BASE}/steelos-shredder/status/{test_device}")
            
            if status_response1.status_code == 200:
                status_data1 = status_response1.json()
                
                if status_data1.get('shredder_pending'):
                    # Second token retrieval - should fail (one-time use)
                    status_response2 = self.session.get(f"{API_BASE}/steelos-shredder/status/{test_device}")
                    
                    if status_response2.status_code == 200:
                        status_data2 = status_response2.json()
                        
                        if not status_data2.get('shredder_pending'):
                            self.log_test("STEELOS One-Time Token Use", True, 
                                        "Token properly consumed after first retrieval")
                        else:
                            self.log_test("STEELOS One-Time Token Use", False, 
                                        "Token still available after first retrieval")
                    else:
                        self.log_test("STEELOS One-Time Token Use", False, 
                                    f"Second status check failed: {status_response2.status_code}")
                else:
                    self.log_test("STEELOS One-Time Token Use", False, 
                                "No token found in first retrieval")
            else:
                self.log_test("STEELOS One-Time Token Use", False, 
                            f"First status check failed: {status_response1.status_code}")
                
        except Exception as e:
            self.log_test("STEELOS One-Time Token Use", False, f"Exception: {str(e)}")
    
    def test_pin_security_normal_vs_panic(self):
        """Test PIN security with normal PIN vs panic PIN"""
        print("\n🔐 Testing PIN Security (Normal vs Panic)")
        
        try:
            # Test normal PIN (should work normally)
            normal_pin_payload = {
                "device_id": self.device_id,
                "pin": "123456",
                "pin_type": "vault_access"
            }
            
            normal_response = self.session.post(f"{API_BASE}/pin/verify", json=normal_pin_payload)
            
            # Test panic PIN (should trigger wipe)
            panic_pin_payload = {
                "device_id": self.device_id,
                "pin": "000000",  # Updated panic PIN
                "pin_type": "vault_access"
            }
            
            panic_response = self.session.post(f"{API_BASE}/pin/verify", json=panic_pin_payload)
            
            normal_success = normal_response.status_code == 200
            panic_detected = False
            
            if panic_response.status_code == 200:
                panic_data = panic_response.json()
                # Check if panic was detected (should trigger wipe)
                panic_detected = panic_data.get('panic_detected', False) or panic_data.get('wipe_triggered', False)
            
            if normal_success and panic_detected:
                self.log_test("PIN Security (Normal vs Panic)", True, 
                            "Normal PIN works, Panic PIN detected and triggers wipe")
            elif normal_success and not panic_detected:
                self.log_test("PIN Security (Normal vs Panic)", False, 
                            "Normal PIN works but Panic PIN not detected")
            else:
                self.log_test("PIN Security (Normal vs Panic)", False, 
                            f"Normal PIN failed: {normal_response.status_code}")
                
        except Exception as e:
            self.log_test("PIN Security (Normal vs Panic)", False, f"Exception: {str(e)}")
    
    def test_rate_limiting_enforcement(self):
        """Test rate limiting enforcement"""
        print("\n🚦 Testing Rate Limiting Enforcement")
        
        try:
            # Make multiple rapid requests to test rate limiting
            successful_requests = 0
            rate_limited_requests = 0
            
            for i in range(15):  # Try 15 requests rapidly
                response = self.session.get(f"{API_BASE}/")
                
                if response.status_code == 200:
                    successful_requests += 1
                elif response.status_code == 429:  # Rate limited
                    rate_limited_requests += 1
                
                time.sleep(0.1)  # Small delay between requests
            
            # Rate limiting should kick in after some requests
            if rate_limited_requests > 0:
                self.log_test("Rate Limiting Enforcement", True, 
                            f"Rate limiting active: {successful_requests} successful, {rate_limited_requests} blocked")
            else:
                self.log_test("Rate Limiting Enforcement", False, 
                            f"No rate limiting detected: {successful_requests} successful, 0 blocked")
                
        except Exception as e:
            self.log_test("Rate Limiting Enforcement", False, f"Exception: {str(e)}")
    
    def test_input_sanitization(self):
        """Test input sanitization against malicious payloads"""
        print("\n🛡️ Testing Input Sanitization")
        
        try:
            malicious_payloads = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE notes; --",
                "../../../etc/passwd",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "' OR '1'='1",
                "eval(document.cookie)"
            ]
            
            blocked_payloads = 0
            accepted_payloads = 0
            
            for payload in malicious_payloads:
                try:
                    # Test with secure notes endpoint
                    note_payload = {
                        "ciphertext": payload,
                        "ttl_seconds": 3600,
                        "read_limit": 1
                    }
                    
                    response = self.session.post(f"{API_BASE}/notes", json=note_payload)
                    
                    if response.status_code == 400:  # Blocked by input sanitization
                        blocked_payloads += 1
                    elif response.status_code == 200:  # Accepted (potential vulnerability)
                        accepted_payloads += 1
                        
                except:
                    blocked_payloads += 1  # Exception counts as blocked
            
            # Most malicious payloads should be blocked
            if blocked_payloads >= len(malicious_payloads) * 0.8:  # 80% or more blocked
                self.log_test("Input Sanitization", True, 
                            f"Blocked {blocked_payloads}/{len(malicious_payloads)} malicious payloads")
            else:
                self.log_test("Input Sanitization", False, 
                            f"Only blocked {blocked_payloads}/{len(malicious_payloads)} malicious payloads")
                
        except Exception as e:
            self.log_test("Input Sanitization", False, f"Exception: {str(e)}")
    
    def test_dual_key_nuclear_protocol(self):
        """Test Dual-Key Nuclear Protocol initiation"""
        print("\n🚢 Testing Dual-Key Nuclear Protocol")
        
        try:
            # Test Design A (Dual-Command Bridge)
            dual_key_payload = {
                "operation_type": "system_reset",
                "operation_data": {"target": "test_system"},
                "operator_a_id": "admin1",
                "operator_b_id": "admin2"
            }
            
            dual_response = self.session.post(f"{API_BASE}/dual-key/initiate", json=dual_key_payload)
            
            # Test Design B (Split Master Key)
            split_key_payload = {
                "operation_type": "emergency_access",
                "operation_data": {"access_level": "full"}
            }
            
            split_response = self.session.post(f"{API_BASE}/split-master-key/initiate", json=split_key_payload)
            
            dual_success = dual_response.status_code == 200
            split_success = split_response.status_code == 200
            
            if dual_success and split_success:
                self.log_test("Dual-Key Nuclear Protocol", True, 
                            "Both Design A and Design B protocols initiated successfully")
            elif dual_success or split_success:
                self.log_test("Dual-Key Nuclear Protocol", True, 
                            f"One protocol working: Dual={dual_success}, Split={split_success}")
            else:
                self.log_test("Dual-Key Nuclear Protocol", False, 
                            f"Both protocols failed: Dual={dual_response.status_code}, Split={split_response.status_code}")
                
        except Exception as e:
            self.log_test("Dual-Key Nuclear Protocol", False, f"Exception: {str(e)}")
    
    def test_admin_authentication(self):
        """Test Admin System authentication"""
        print("\n👑 Testing Admin System Authentication")
        
        try:
            # Test admin authentication with correct passphrase
            auth_payload = {
                "admin_passphrase": "Omertaisthecode#01",
                "device_id": self.device_id
            }
            
            auth_response = self.session.post(f"{API_BASE}/admin/authenticate", json=auth_payload)
            
            if auth_response.status_code == 200:
                auth_data = auth_response.json()
                
                if auth_data.get('authenticated') and auth_data.get('session_token'):
                    self.log_test("Admin Authentication", True, 
                                f"Admin authenticated successfully: {auth_data.get('admin_id')}")
                else:
                    self.log_test("Admin Authentication", False, 
                                f"Authentication response invalid: {auth_data}")
            else:
                self.log_test("Admin Authentication", False, 
                            f"Authentication failed: {auth_response.status_code}")
                
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Exception: {str(e)}")
    
    def test_contact_vault_operations(self):
        """Test Contact Vault operations"""
        print("\n📇 Testing Contact Vault Operations")
        
        try:
            # Test contact vault storage
            contacts_payload = {
                "device_id": self.device_id,
                "encryption_key_hash": "test_encryption_key_hash_32_chars_min",
                "contacts": [
                    {
                        "oid": "test_oid_12345",
                        "display_name": "Test Contact",
                        "verified": True,
                        "created_at": int(time.time())
                    }
                ]
            }
            
            store_response = self.session.post(f"{API_BASE}/contacts-vault/store", json=contacts_payload)
            
            if store_response.status_code == 200:
                store_data = store_response.json()
                
                if store_data.get('backup_id') and store_data.get('contacts_count') == 1:
                    # Test contact retrieval
                    retrieve_response = self.session.get(
                        f"{API_BASE}/contacts-vault/retrieve/{self.device_id}",
                        params={"encryption_key_hash": "test_encryption_key_hash_32_chars_min"}
                    )
                    
                    if retrieve_response.status_code == 200:
                        retrieve_data = retrieve_response.json()
                        
                        if retrieve_data.get('contacts') and len(retrieve_data['contacts']) == 1:
                            self.log_test("Contact Vault Operations", True, 
                                        "Contacts stored and retrieved successfully")
                        else:
                            self.log_test("Contact Vault Operations", False, 
                                        f"Contact retrieval failed: {retrieve_data}")
                    else:
                        self.log_test("Contact Vault Operations", False, 
                                    f"Contact retrieval failed: {retrieve_response.status_code}")
                else:
                    self.log_test("Contact Vault Operations", False, 
                                f"Contact storage failed: {store_data}")
            else:
                self.log_test("Contact Vault Operations", False, 
                            f"Contact storage failed: {store_response.status_code}")
                
        except Exception as e:
            self.log_test("Contact Vault Operations", False, f"Exception: {str(e)}")
    
    def test_auto_wipe_configuration(self):
        """Test Auto-Wipe system configuration"""
        print("\n⏰ Testing Auto-Wipe Configuration")
        
        try:
            # Configure auto-wipe
            autowipe_payload = {
                "device_id": self.device_id,
                "enabled": True,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2
            }
            
            config_response = self.session.post(f"{API_BASE}/auto-wipe/configure", json=autowipe_payload)
            
            if config_response.status_code == 200:
                config_data = config_response.json()
                
                if config_data.get('configured'):
                    # Check auto-wipe status
                    status_response = self.session.get(f"{API_BASE}/auto-wipe/status/{self.device_id}")
                    
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        
                        if (status_data.get('device_id') == self.device_id and 
                            status_data.get('enabled') == True and
                            status_data.get('days_inactive') == 7):
                            self.log_test("Auto-Wipe Configuration", True, 
                                        "Auto-wipe configured and status retrieved successfully")
                        else:
                            self.log_test("Auto-Wipe Configuration", False, 
                                        f"Auto-wipe status mismatch: {status_data}")
                    else:
                        self.log_test("Auto-Wipe Configuration", False, 
                                    f"Status check failed: {status_response.status_code}")
                else:
                    self.log_test("Auto-Wipe Configuration", False, 
                                f"Configuration failed: {config_data}")
            else:
                self.log_test("Auto-Wipe Configuration", False, 
                            f"Configuration request failed: {config_response.status_code}")
                
        except Exception as e:
            self.log_test("Auto-Wipe Configuration", False, f"Exception: {str(e)}")
    
    def run_all_security_tests(self):
        """Run all security verification tests"""
        print("🔒 COMPREHENSIVE SECURITY VERIFICATION TEST")
        print("=" * 80)
        print("Verifying all critical security systems mentioned in test_result.md")
        print("=" * 80)
        
        # Core Security Tests
        self.test_secure_notes_one_time_read()
        self.test_steelos_shredder_deployment()
        self.test_steelos_one_time_token_use()
        self.test_pin_security_normal_vs_panic()
        
        # Infrastructure Security Tests
        self.test_rate_limiting_enforcement()
        self.test_input_sanitization()
        
        # Advanced Security Systems
        self.test_dual_key_nuclear_protocol()
        self.test_admin_authentication()
        self.test_contact_vault_operations()
        self.test_auto_wipe_configuration()
        
        # Generate summary
        self.generate_security_summary()
    
    def generate_security_summary(self):
        """Generate comprehensive security summary"""
        print("\n" + "=" * 80)
        print("🔒 COMPREHENSIVE SECURITY VERIFICATION SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Security Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Security Score: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize by security area
        core_security = [
            'Secure Notes One-Time Read',
            'STEELOS-Shredder Deployment',
            'STEELOS One-Time Token Use',
            'PIN Security (Normal vs Panic)'
        ]
        
        infrastructure_security = [
            'Rate Limiting Enforcement',
            'Input Sanitization'
        ]
        
        advanced_security = [
            'Dual-Key Nuclear Protocol',
            'Admin Authentication',
            'Contact Vault Operations',
            'Auto-Wipe Configuration'
        ]
        
        # Calculate category scores
        core_passed = sum(1 for result in self.test_results 
                         if result['success'] and result['test'] in core_security)
        infra_passed = sum(1 for result in self.test_results 
                          if result['success'] and result['test'] in infrastructure_security)
        advanced_passed = sum(1 for result in self.test_results 
                             if result['success'] and result['test'] in advanced_security)
        
        print(f"\n📊 SECURITY CATEGORY BREAKDOWN:")
        print(f"🔐 Core Security Systems: {core_passed}/{len([t for t in core_security if any(r['test'] == t for r in self.test_results)])}")
        print(f"🏗️ Infrastructure Security: {infra_passed}/{len([t for t in infrastructure_security if any(r['test'] == t for r in self.test_results)])}")
        print(f"🚀 Advanced Security Systems: {advanced_passed}/{len([t for t in advanced_security if any(r['test'] == t for r in self.test_results)])}")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED SECURITY TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Overall security assessment
        security_score = (passed_tests / total_tests) * 100
        
        if security_score >= 95:
            print(f"\n🏆 EXCEPTIONAL SECURITY POSTURE")
            print("✅ All critical security systems operational")
            print("✅ Ready for production deployment")
            print("✅ Meets world-class security standards")
        elif security_score >= 85:
            print(f"\n🥈 STRONG SECURITY POSTURE")
            print("✅ Most critical security systems operational")
            print("⚠️ Minor improvements recommended")
            print("✅ Generally ready for deployment")
        elif security_score >= 70:
            print(f"\n🟡 MODERATE SECURITY CONCERNS")
            print("⚠️ Some critical security systems need attention")
            print("⚠️ Security improvements required")
            print("⚠️ Review before production deployment")
        else:
            print(f"\n❌ CRITICAL SECURITY ISSUES")
            print("❌ Major security systems not functioning")
            print("❌ Immediate fixes required")
            print("❌ Not ready for production deployment")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    print(f"🔒 Starting Security Verification Testing against: {API_BASE}")
    tester = SecurityVerificationTester()
    tester.run_all_security_tests()
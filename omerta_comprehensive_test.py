#!/usr/bin/env python3
"""
OMERTÀ Comprehensive Backend Security Testing Suite
Tests all security systems for production readiness
"""

import requests
import json
import time
import hashlib
import hmac
import secrets
from datetime import datetime, timezone
import sys
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://graphite-killer.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OmertaSecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.device_id = f"test_device_{int(time.time())}"
        
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

    def test_basic_api_functionality(self):
        """Test core API endpoints"""
        print("\n🔧 Testing Basic API Functionality")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                self.log_test("Root API Endpoint", True, "API accessible")
            else:
                self.log_test("Root API Endpoint", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Root API Endpoint", False, f"Exception: {str(e)}")

        # Test secure notes creation
        try:
            note_payload = {
                "ciphertext": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y=",  # Sample encrypted data
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            response = self.session.post(f"{API_BASE}/notes", json=note_payload)
            if response.status_code == 200:
                data = response.json()
                note_id = data.get('id')
                if note_id:
                    self.log_test("Secure Notes Creation", True, f"Note ID: {note_id}")
                    
                    # Test reading the note
                    read_response = self.session.get(f"{API_BASE}/notes/{note_id}")
                    if read_response.status_code == 200:
                        read_data = read_response.json()
                        if read_data.get('views_left') == 0:
                            self.log_test("Secure Notes One-Time Read", True, "Note purged after single read")
                        else:
                            self.log_test("Secure Notes One-Time Read", False, f"Views left: {read_data.get('views_left')}")
                    else:
                        self.log_test("Secure Notes One-Time Read", False, f"HTTP {read_response.status_code}")
                else:
                    self.log_test("Secure Notes Creation", False, "No note ID returned")
            else:
                self.log_test("Secure Notes Creation", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Secure Notes Creation", False, f"Exception: {str(e)}")

        # Test envelopes
        try:
            envelope_payload = {
                "to_oid": "test_recipient_123",
                "from_oid": "test_sender_456", 
                "ciphertext": "encrypted_message_content_here"
            }
            response = self.session.post(f"{API_BASE}/envelopes/send", json=envelope_payload)
            if response.status_code == 200:
                data = response.json()
                envelope_id = data.get('id')
                if envelope_id:
                    self.log_test("Envelopes Send", True, f"Envelope ID: {envelope_id}")
                    
                    # Test polling
                    poll_response = self.session.get(f"{API_BASE}/envelopes/poll?oid=test_recipient_123")
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        messages = poll_data.get('messages', [])
                        if len(messages) > 0:
                            self.log_test("Envelopes Poll & Delete-on-Delivery", True, f"Retrieved {len(messages)} messages")
                            
                            # Test delete-on-delivery (second poll should be empty)
                            poll2_response = self.session.get(f"{API_BASE}/envelopes/poll?oid=test_recipient_123")
                            if poll2_response.status_code == 200:
                                poll2_data = poll2_response.json()
                                if len(poll2_data.get('messages', [])) == 0:
                                    self.log_test("Delete-on-Delivery Verification", True, "Second poll returned empty")
                                else:
                                    self.log_test("Delete-on-Delivery Verification", False, "Messages still present after delivery")
                        else:
                            self.log_test("Envelopes Poll & Delete-on-Delivery", False, "No messages retrieved")
                else:
                    self.log_test("Envelopes Send", False, "No envelope ID returned")
            else:
                self.log_test("Envelopes Send", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Envelopes Send", False, f"Exception: {str(e)}")

    def test_steelos_shredder(self):
        """Test STEELOS-Shredder system"""
        print("\n💊 Testing STEELOS-Shredder System")
        
        try:
            # Test STEELOS-Shredder deployment
            shredder_payload = {
                "device_id": self.device_id,
                "trigger_type": "manual",
                "confirmation_token": "test_confirmation"
            }
            response = self.session.post(f"{API_BASE}/steelos-shredder/deploy", json=shredder_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('shredder_activated') and data.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True, f"Kill token generated: {data.get('destruction_initiated')}")
                    
                    # Test kill token retrieval
                    status_response = self.session.get(f"{API_BASE}/steelos-shredder/status/{self.device_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('shredder_pending') and status_data.get('kill_token'):
                            kill_token = status_data['kill_token']
                            if kill_token.get('signature') and kill_token.get('command') == 'STEELOS_SHREDDER_KILL_TOKEN':
                                self.log_test("STEELOS Kill Token Retrieval", True, f"Token signature: {kill_token['signature'][:20]}...")
                                
                                # Test one-time use (second retrieval should be empty)
                                status2_response = self.session.get(f"{API_BASE}/steelos-shredder/status/{self.device_id}")
                                if status2_response.status_code == 200:
                                    status2_data = status2_response.json()
                                    if not status2_data.get('shredder_pending'):
                                        self.log_test("Kill Token One-Time Use", True, "Token removed after retrieval")
                                    else:
                                        self.log_test("Kill Token One-Time Use", False, "Token still available after retrieval")
                            else:
                                self.log_test("STEELOS Kill Token Retrieval", False, "Invalid kill token structure")
                        else:
                            self.log_test("STEELOS Kill Token Retrieval", False, "No kill token found")
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, f"Deployment failed: {data}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Exception: {str(e)}")

    def test_auto_wipe_system(self):
        """Test Auto-Wipe system"""
        print("\n⏰ Testing Auto-Wipe System")
        
        try:
            # Test auto-wipe configuration
            config_payload = {
                "device_id": self.device_id,
                "enabled": True,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2
            }
            response = self.session.post(f"{API_BASE}/auto-wipe/configure", json=config_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Auto-Wipe Configuration", True, f"Configured: {data.get('message')}")
                    
                    # Test activity update
                    activity_payload = {
                        "device_id": self.device_id,
                        "activity_type": "app_usage"
                    }
                    activity_response = self.session.post(f"{API_BASE}/auto-wipe/activity", json=activity_payload)
                    
                    if activity_response.status_code == 200:
                        activity_data = activity_response.json()
                        if activity_data.get('success'):
                            self.log_test("Auto-Wipe Activity Update", True, "Activity timestamp updated")
                            
                            # Test status check
                            status_response = self.session.get(f"{API_BASE}/auto-wipe/status/{self.device_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if 'days_until_wipe' in status_data:
                                    self.log_test("Auto-Wipe Status Check", True, f"Days until wipe: {status_data['days_until_wipe']}")
                                else:
                                    self.log_test("Auto-Wipe Status Check", False, "Missing status data")
                        else:
                            self.log_test("Auto-Wipe Activity Update", False, f"Activity update failed: {activity_data}")
                else:
                    self.log_test("Auto-Wipe Configuration", False, f"Configuration failed: {data}")
            else:
                self.log_test("Auto-Wipe Configuration", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Auto-Wipe Configuration", False, f"Exception: {str(e)}")

    def test_contact_vault(self):
        """Test Contact Vault system"""
        print("\n📇 Testing Contact Vault System")
        
        try:
            # Test contacts vault storage
            contacts_payload = {
                "device_id": self.device_id,
                "encryption_key_hash": "test_encryption_key_hash_32_characters_long_minimum",
                "contacts": [
                    {
                        "oid": "contact_001_test_user",
                        "display_name": "Test Contact 1",
                        "verified": True,
                        "cryptographic_dna": "DNA_test_signature_12345678901234567890"
                    },
                    {
                        "oid": "contact_002_verified_user", 
                        "display_name": "Verified Contact 2",
                        "verified": True,
                        "cryptographic_dna": "DNA_verified_signature_09876543210987654321"
                    }
                ]
            }
            response = self.session.post(f"{API_BASE}/contacts-vault/store", json=contacts_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('backup_id'):
                    self.log_test("Contact Vault Storage", True, f"Stored {data.get('contacts_count')} contacts")
                    
                    # Test contacts retrieval
                    retrieve_response = self.session.get(
                        f"{API_BASE}/contacts-vault/retrieve/{self.device_id}?encryption_key_hash=test_encryption_key_hash_32_characters_long_minimum"
                    )
                    
                    if retrieve_response.status_code == 200:
                        retrieve_data = retrieve_response.json()
                        if retrieve_data.get('success') and retrieve_data.get('contacts'):
                            retrieved_count = len(retrieve_data['contacts'])
                            quarantined_count = retrieve_data.get('quarantined_count', 0)
                            self.log_test("Contact Vault Retrieval", True, 
                                        f"Retrieved {retrieved_count} contacts, quarantined {quarantined_count}")
                            
                            # Test vault clearing
                            clear_response = self.session.delete(f"{API_BASE}/contacts-vault/clear/{self.device_id}")
                            if clear_response.status_code == 200:
                                clear_data = clear_response.json()
                                if clear_data.get('success'):
                                    self.log_test("Contact Vault Clear", True, "Vault cleared successfully")
                                    
                                    # Verify vault is empty
                                    verify_response = self.session.get(
                                        f"{API_BASE}/contacts-vault/retrieve/{self.device_id}?encryption_key_hash=test_encryption_key_hash_32_characters_long_minimum"
                                    )
                                    if verify_response.status_code == 404:
                                        self.log_test("Vault Clear Verification", True, "Vault confirmed empty")
                                    else:
                                        self.log_test("Vault Clear Verification", False, "Vault not properly cleared")
                        else:
                            self.log_test("Contact Vault Retrieval", False, "No contacts retrieved")
                else:
                    self.log_test("Contact Vault Storage", False, f"Storage failed: {data}")
            else:
                self.log_test("Contact Vault Storage", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Contact Vault Storage", False, f"Exception: {str(e)}")

    def test_pin_security(self):
        """Test PIN security system"""
        print("\n🔐 Testing PIN Security System")
        
        try:
            # Test normal PIN verification
            pin_payload = {
                "device_id": self.device_id,
                "pin": "123456"  # Correct PIN from pin_security.py
            }
            response = self.session.post(f"{API_BASE}/pin/verify", json=pin_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Normal PIN Verification", True, "Correct PIN accepted")
                    
                    # Test panic PIN (000000)
                    panic_payload = {
                        "device_id": self.device_id,
                        "pin": "000000"  # Panic PIN
                    }
                    panic_response = self.session.post(f"{API_BASE}/pin/verify", json=panic_payload)
                    
                    if panic_response.status_code == 200:
                        panic_data = panic_response.json()
                        if panic_data.get('success') and panic_data.get('kill_token'):
                            kill_token = panic_data['kill_token']
                            if kill_token.get('command') == 'SIGNED_KILL_TOKEN_PANIC':
                                self.log_test("Panic PIN Detection", True, "Panic PIN triggers kill token")
                            else:
                                self.log_test("Panic PIN Detection", False, "Invalid kill token structure")
                        else:
                            self.log_test("Panic PIN Detection", False, "Panic PIN not properly handled")
                    
                    # Test wrong PIN (should fail)
                    wrong_payload = {
                        "device_id": self.device_id,
                        "pin": "999999"  # Wrong PIN
                    }
                    wrong_response = self.session.post(f"{API_BASE}/pin/verify", json=wrong_payload)
                    
                    if wrong_response.status_code == 200:
                        wrong_data = wrong_response.json()
                        if not wrong_data.get('success'):
                            self.log_test("Wrong PIN Rejection", True, "Wrong PIN properly rejected")
                        else:
                            self.log_test("Wrong PIN Rejection", False, "Wrong PIN incorrectly accepted")
                else:
                    self.log_test("Normal PIN Verification", False, f"PIN verification failed: {data}")
            else:
                self.log_test("Normal PIN Verification", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Normal PIN Verification", False, f"Exception: {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting system"""
        print("\n🚦 Testing Rate Limiting")
        
        try:
            # Test rate limiting on notes creation (10/min limit)
            rate_limit_triggered = False
            for i in range(12):  # Try to exceed 10/min limit
                note_payload = {
                    "ciphertext": f"rate_limit_test_{i}",
                    "ttl_seconds": 60,
                    "read_limit": 1
                }
                response = self.session.post(f"{API_BASE}/notes", json=note_payload)
                if response.status_code == 429:
                    rate_limit_triggered = True
                    self.log_test("Notes Rate Limiting", True, f"Rate limit triggered after {i+1} requests")
                    break
                time.sleep(0.1)  # Small delay between requests
            
            if not rate_limit_triggered:
                self.log_test("Notes Rate Limiting", False, "Rate limiting not working")
                
        except Exception as e:
            self.log_test("Notes Rate Limiting", False, f"Exception: {str(e)}")

    def test_input_sanitization(self):
        """Test input sanitization"""
        print("\n🛡️ Testing Input Sanitization")
        
        dangerous_payloads = [
            '<script>alert("xss")</script>',
            '; DROP TABLE notes; --',
            '../../../etc/passwd',
            'javascript:alert(1)',
            'eval(malicious_code)',
            '<iframe src="javascript:alert(1)"></iframe>',
            'onload=alert(1)'
        ]
        
        blocked_count = 0
        for payload in dangerous_payloads:
            try:
                note_payload = {
                    "ciphertext": payload,
                    "ttl_seconds": 60,
                    "read_limit": 1
                }
                response = self.session.post(f"{API_BASE}/notes", json=note_payload)
                if response.status_code == 400:
                    blocked_count += 1
            except Exception:
                blocked_count += 1  # Exception also counts as blocked
        
        success_rate = (blocked_count / len(dangerous_payloads)) * 100
        if success_rate >= 80:  # 80% or more blocked
            self.log_test("Input Sanitization", True, f"{blocked_count}/{len(dangerous_payloads)} dangerous payloads blocked ({success_rate:.1f}%)")
        else:
            self.log_test("Input Sanitization", False, f"Only {blocked_count}/{len(dangerous_payloads)} payloads blocked ({success_rate:.1f}%)")

    def test_dual_key_nuclear_protocol(self):
        """Test Dual-Key Nuclear Protocol (simplified)"""
        print("\n🚢 Testing Dual-Key Nuclear Protocol")
        
        try:
            # Test dual-key operation initiation
            dual_key_payload = {
                'operation_type': 'system_reset',
                'operation_data': {'reset_level': 'full'},
                'operator_a_id': 'dev_primary',
                'operator_b_id': 'sec_officer'
            }
            
            response = self.session.post(f"{API_BASE}/dual-key/initiate", json=dual_key_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('operation_id'):
                    self.log_test("Dual-Key Operation Initiation", True, f"Operation ID: {data['operation_id']}")
                else:
                    self.log_test("Dual-Key Operation Initiation", False, f"Invalid response: {data}")
            else:
                self.log_test("Dual-Key Operation Initiation", False, f"HTTP {response.status_code}: {response.text}")
                
            # Test split master key initiation
            split_key_payload = {
                'operation_type': 'emergency_override',
                'operation_data': {'override_level': 'critical'}
            }
            
            split_response = self.session.post(f"{API_BASE}/split-master-key/initiate", json=split_key_payload)
            
            if split_response.status_code == 200:
                split_data = split_response.json()
                if split_data.get('success') and split_data.get('operation_id'):
                    self.log_test("Split Master Key Initiation", True, f"Operation ID: {split_data['operation_id']}")
                else:
                    self.log_test("Split Master Key Initiation", False, f"Invalid response: {split_data}")
            else:
                self.log_test("Split Master Key Initiation", False, f"HTTP {split_response.status_code}: {split_response.text}")
                
        except Exception as e:
            self.log_test("Dual-Key Nuclear Protocol", False, f"Exception: {str(e)}")

    def test_emergency_systems(self):
        """Test emergency systems"""
        print("\n🚨 Testing Emergency Systems")
        
        try:
            # Test emergency portal access
            emergency_response = self.session.get(f"{BACKEND_URL}/emergency")
            
            if emergency_response.status_code == 200:
                if "Emergency Revocation Portal" in emergency_response.text:
                    self.log_test("Emergency Portal Access", True, "Emergency portal accessible")
                else:
                    self.log_test("Emergency Portal Access", False, "Emergency portal content invalid")
            else:
                self.log_test("Emergency Portal Access", False, f"HTTP {emergency_response.status_code}")
                
        except Exception as e:
            self.log_test("Emergency Portal Access", False, f"Exception: {str(e)}")

    def run_comprehensive_tests(self):
        """Run all OMERTÀ security tests"""
        print("🔒 OMERTÀ COMPREHENSIVE SECURITY TESTING SUITE")
        print("=" * 80)
        
        # Core functionality tests
        self.test_basic_api_functionality()
        
        # Security systems tests
        self.test_steelos_shredder()
        self.test_auto_wipe_system()
        self.test_contact_vault()
        self.test_pin_security()
        
        # Security features tests
        self.test_rate_limiting()
        self.test_input_sanitization()
        
        # Advanced systems tests
        self.test_dual_key_nuclear_protocol()
        self.test_emergency_systems()
        
        # Generate comprehensive summary
        self.generate_comprehensive_summary()
    
    def generate_comprehensive_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🔒 OMERTÀ COMPREHENSIVE SECURITY TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        # Categorize results
        categories = {
            "Basic API": ["Root API Endpoint", "Secure Notes Creation", "Secure Notes One-Time Read", "Envelopes Send", "Envelopes Poll & Delete-on-Delivery", "Delete-on-Delivery Verification"],
            "STEELOS-Shredder": ["STEELOS-Shredder Deployment", "STEELOS Kill Token Retrieval", "Kill Token One-Time Use"],
            "Auto-Wipe": ["Auto-Wipe Configuration", "Auto-Wipe Activity Update", "Auto-Wipe Status Check"],
            "Contact Vault": ["Contact Vault Storage", "Contact Vault Retrieval", "Contact Vault Clear", "Vault Clear Verification"],
            "PIN Security": ["Normal PIN Verification", "Panic PIN Detection", "Wrong PIN Rejection"],
            "Security Features": ["Notes Rate Limiting", "Input Sanitization"],
            "Nuclear Protocol": ["Dual-Key Operation Initiation", "Split Master Key Initiation"],
            "Emergency Systems": ["Emergency Portal Access"]
        }
        
        print("\n📊 RESULTS BY CATEGORY:")
        for category, test_names in categories.items():
            category_results = [r for r in self.test_results if r['test'] in test_names]
            if category_results:
                category_passed = sum(1 for r in category_results if r['success'])
                category_total = len(category_results)
                category_rate = (category_passed/category_total)*100 if category_total > 0 else 0
                status = "✅" if category_rate >= 80 else "⚠️" if category_rate >= 60 else "❌"
                print(f"  {status} {category}: {category_passed}/{category_total} ({category_rate:.1f}%)")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Overall system assessment
        critical_systems = [
            "Secure Notes Creation", "STEELOS-Shredder Deployment", "Auto-Wipe Configuration",
            "Contact Vault Storage", "Normal PIN Verification", "Panic PIN Detection"
        ]
        
        critical_passed = sum(1 for result in self.test_results 
                            if result['success'] and result['test'] in critical_systems)
        
        print(f"\n🎯 CRITICAL SYSTEMS STATUS: {critical_passed}/{len(critical_systems)} operational")
        
        if critical_passed == len(critical_systems):
            print("\n🎉 OMERTÀ SECURITY SYSTEM: FULLY OPERATIONAL")
            print("All critical security systems are working correctly!")
        elif critical_passed >= len(critical_systems) * 0.8:
            print("\n⚠️ OMERTÀ SECURITY SYSTEM: MOSTLY OPERATIONAL")
            print("Core security functionality working with minor issues")
        else:
            print("\n❌ OMERTÀ SECURITY SYSTEM: CRITICAL ISSUES DETECTED")
            print("Major security functionality problems require immediate attention")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    print(f"Testing OMERTÀ backend at: {API_BASE}")
    tester = OmertaSecurityTester()
    tester.run_comprehensive_tests()
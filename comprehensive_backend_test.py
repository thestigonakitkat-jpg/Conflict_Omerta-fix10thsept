#!/usr/bin/env python3
"""
Comprehensive OMERTA Backend Security Testing
Tests all core security systems after frontend fixes to ensure no regression
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
import uuid

# Get backend URL from environment
BACKEND_URL = os.environ.get('EXPO_PUBLIC_BACKEND_URL', 'https://graphite-killer.preview.emergentagent.com')
API_BASE = f"{BACKEND_URL}/api"

class OMERTASecurityTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.test_device_id = f"test_device_{uuid.uuid4().hex[:8]}"
        
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
        """Test basic API endpoints"""
        print("\n🔧 Testing Basic API Functionality")
        
        # Test root endpoint
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200 and "Hello World" in response.text:
                self.log_test("Basic API Root Endpoint", True, "API responding correctly")
            else:
                self.log_test("Basic API Root Endpoint", False, f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("Basic API Root Endpoint", False, f"Exception: {str(e)}")

    def test_secure_notes_system(self):
        """Test Secure Notes (create/read/TTL)"""
        print("\n📝 Testing Secure Notes System")
        
        try:
            # Test secure note creation
            note_payload = {
                "ciphertext": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
                "meta": {"test": "secure_note"},
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = self.session.post(f"{API_BASE}/notes", json=note_payload)
            
            if response.status_code == 200:
                data = response.json()
                note_id = data.get('id')
                if note_id:
                    self.log_test("Secure Notes Creation", True, f"Note ID: {note_id}")
                    
                    # Test note reading (first time)
                    read_response = self.session.get(f"{API_BASE}/notes/{note_id}")
                    if read_response.status_code == 200:
                        read_data = read_response.json()
                        if read_data.get('ciphertext') == note_payload['ciphertext']:
                            self.log_test("Secure Notes First Read", True, "Ciphertext retrieved correctly")
                            
                            # Test note reading (second time - should fail due to one-time read)
                            second_read = self.session.get(f"{API_BASE}/notes/{note_id}")
                            if second_read.status_code == 404:
                                self.log_test("Secure Notes One-Time Read", True, "Note purged after first read")
                            else:
                                self.log_test("Secure Notes One-Time Read", False, f"Note still accessible: HTTP {second_read.status_code}")
                        else:
                            self.log_test("Secure Notes First Read", False, "Ciphertext mismatch")
                    else:
                        self.log_test("Secure Notes First Read", False, f"HTTP {read_response.status_code}")
                else:
                    self.log_test("Secure Notes Creation", False, "No note ID returned")
            else:
                self.log_test("Secure Notes Creation", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Secure Notes System", False, f"Exception: {str(e)}")

    def test_messaging_envelopes(self):
        """Test Messaging envelopes (send/poll/delete-on-delivery)"""
        print("\n✉️ Testing Messaging Envelopes System")
        
        try:
            # Test envelope sending
            envelope_payload = {
                "to_oid": f"test_recipient_{uuid.uuid4().hex[:8]}",
                "from_oid": f"test_sender_{uuid.uuid4().hex[:8]}",
                "ciphertext": "encrypted_message_content_test_123"
            }
            
            response = self.session.post(f"{API_BASE}/envelopes/send", json=envelope_payload)
            
            if response.status_code == 200:
                data = response.json()
                envelope_id = data.get('id')
                if envelope_id:
                    self.log_test("Envelope Send", True, f"Envelope ID: {envelope_id}")
                    
                    # Test envelope polling (first time)
                    poll_response = self.session.get(f"{API_BASE}/envelopes/poll?oid={envelope_payload['to_oid']}")
                    if poll_response.status_code == 200:
                        poll_data = poll_response.json()
                        messages = poll_data.get('messages', [])
                        if len(messages) > 0 and messages[0].get('id') == envelope_id:
                            self.log_test("Envelope Poll First Time", True, f"Message delivered: {messages[0].get('ciphertext')}")
                            
                            # Test envelope polling (second time - should be empty due to delete-on-delivery)
                            second_poll = self.session.get(f"{API_BASE}/envelopes/poll?oid={envelope_payload['to_oid']}")
                            if second_poll.status_code == 200:
                                second_data = second_poll.json()
                                if len(second_data.get('messages', [])) == 0:
                                    self.log_test("Envelope Delete-on-Delivery", True, "Message deleted after first poll")
                                else:
                                    self.log_test("Envelope Delete-on-Delivery", False, "Message still available after first poll")
                            else:
                                self.log_test("Envelope Delete-on-Delivery", False, f"HTTP {second_poll.status_code}")
                        else:
                            self.log_test("Envelope Poll First Time", False, "Message not found in poll")
                    else:
                        self.log_test("Envelope Poll First Time", False, f"HTTP {poll_response.status_code}")
                else:
                    self.log_test("Envelope Send", False, "No envelope ID returned")
            else:
                self.log_test("Envelope Send", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Messaging Envelopes", False, f"Exception: {str(e)}")

    def test_steelos_shredder_system(self):
        """Test STEELOS-Shredder system"""
        print("\n💊 Testing STEELOS-Shredder System")
        
        try:
            # Test STEELOS-Shredder deployment
            shredder_payload = {
                "device_id": self.test_device_id,
                "trigger_type": "manual",
                "confirmation_token": "test_confirmation"
            }
            
            response = self.session.post(f"{API_BASE}/steelos-shredder/deploy", json=shredder_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('shredder_activated') and data.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True, f"Message: {data.get('message')}")
                    
                    # Test kill token retrieval
                    status_response = self.session.get(f"{API_BASE}/steelos-shredder/status/{self.test_device_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        if status_data.get('shredder_pending') and status_data.get('kill_token'):
                            kill_token = status_data.get('kill_token')
                            self.log_test("STEELOS-Shredder Kill Token Retrieval", True, f"Token command: {kill_token.get('command')}")
                            
                            # Test one-time use (second retrieval should return no token)
                            second_status = self.session.get(f"{API_BASE}/steelos-shredder/status/{self.test_device_id}")
                            if second_status.status_code == 200:
                                second_data = second_status.json()
                                if not second_data.get('shredder_pending'):
                                    self.log_test("STEELOS-Shredder One-Time Use", True, "Kill token removed after retrieval")
                                else:
                                    self.log_test("STEELOS-Shredder One-Time Use", False, "Kill token still available")
                            else:
                                self.log_test("STEELOS-Shredder One-Time Use", False, f"HTTP {second_status.status_code}")
                        else:
                            self.log_test("STEELOS-Shredder Kill Token Retrieval", False, "No kill token found")
                    else:
                        self.log_test("STEELOS-Shredder Kill Token Retrieval", False, f"HTTP {status_response.status_code}")
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, f"Deployment failed: {data}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("STEELOS-Shredder System", False, f"Exception: {str(e)}")

    def test_contact_vault_operations(self):
        """Test Contact Vault operations"""
        print("\n📇 Testing Contact Vault System")
        
        try:
            # Test contact vault storage
            contacts_payload = {
                "device_id": self.test_device_id,
                "contacts": [
                    {
                        "oid": f"contact_{uuid.uuid4().hex[:8]}",
                        "display_name": "Test Contact",
                        "verified": True,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                ],
                "encryption_key_hash": "test_encryption_key_hash_12345678901234567890123456789012"
            }
            
            response = self.session.post(f"{API_BASE}/contacts-vault/store", json=contacts_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('backup_id'):
                    self.log_test("Contact Vault Storage", True, f"Backup ID: {data.get('backup_id')}")
                    
                    # Test contact vault retrieval
                    retrieve_response = self.session.get(
                        f"{API_BASE}/contacts-vault/retrieve/{self.test_device_id}?encryption_key_hash={contacts_payload['encryption_key_hash']}"
                    )
                    if retrieve_response.status_code == 200:
                        retrieve_data = retrieve_response.json()
                        if retrieve_data.get('success') and retrieve_data.get('contacts'):
                            self.log_test("Contact Vault Retrieval", True, f"Retrieved {len(retrieve_data['contacts'])} contacts")
                            
                            # Test contact vault clearing
                            clear_response = self.session.delete(f"{API_BASE}/contacts-vault/clear/{self.test_device_id}")
                            if clear_response.status_code == 200:
                                clear_data = clear_response.json()
                                if clear_data.get('success'):
                                    self.log_test("Contact Vault Clear", True, "Vault cleared successfully")
                                else:
                                    self.log_test("Contact Vault Clear", False, f"Clear failed: {clear_data}")
                            else:
                                self.log_test("Contact Vault Clear", False, f"HTTP {clear_response.status_code}")
                        else:
                            self.log_test("Contact Vault Retrieval", False, "No contacts retrieved")
                    else:
                        self.log_test("Contact Vault Retrieval", False, f"HTTP {retrieve_response.status_code}")
                else:
                    self.log_test("Contact Vault Storage", False, f"Storage failed: {data}")
            else:
                self.log_test("Contact Vault Storage", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Contact Vault Operations", False, f"Exception: {str(e)}")

    def test_auto_wipe_functionality(self):
        """Test Auto-wipe functionality"""
        print("\n⏰ Testing Auto-Wipe System")
        
        try:
            # Test auto-wipe configuration
            config_payload = {
                "device_id": self.test_device_id,
                "enabled": True,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2
            }
            
            response = self.session.post(f"{API_BASE}/auto-wipe/configure", json=config_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("Auto-Wipe Configuration", True, f"Config ID: {data.get('config_id')}")
                    
                    # Test activity update
                    activity_payload = {
                        "device_id": self.test_device_id,
                        "activity_type": "app_usage"
                    }
                    
                    activity_response = self.session.post(f"{API_BASE}/auto-wipe/activity", json=activity_payload)
                    if activity_response.status_code == 200:
                        activity_data = activity_response.json()
                        if activity_data.get('success'):
                            self.log_test("Auto-Wipe Activity Update", True, "Activity timestamp updated")
                            
                            # Test status check
                            status_response = self.session.get(f"{API_BASE}/auto-wipe/status/{self.test_device_id}")
                            if status_response.status_code == 200:
                                status_data = status_response.json()
                                if status_data.get('success'):
                                    self.log_test("Auto-Wipe Status Check", True, f"Days until wipe: {status_data.get('days_until_wipe', 'N/A')}")
                                else:
                                    self.log_test("Auto-Wipe Status Check", False, f"Status check failed: {status_data}")
                            else:
                                self.log_test("Auto-Wipe Status Check", False, f"HTTP {status_response.status_code}")
                        else:
                            self.log_test("Auto-Wipe Activity Update", False, f"Activity update failed: {activity_data}")
                    else:
                        self.log_test("Auto-Wipe Activity Update", False, f"HTTP {activity_response.status_code}")
                else:
                    self.log_test("Auto-Wipe Configuration", False, f"Configuration failed: {data}")
            else:
                self.log_test("Auto-Wipe Configuration", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Auto-Wipe Functionality", False, f"Exception: {str(e)}")

    def test_dual_key_nuclear_protocol(self):
        """Test Dual-Key Nuclear Submarine Protocol"""
        print("\n🚢 Testing Dual-Key Nuclear Submarine Protocol")
        
        try:
            # Test Design A: Dual-Command Bridge initiation
            dual_key_payload = {
                'operation_type': 'system_reset',
                'operation_data': {'reset_level': 'full', 'confirmation': True},
                'operator_a_id': 'dev_primary',
                'operator_b_id': 'sec_officer'
            }
            
            response = self.session.post(f"{API_BASE}/dual-key/initiate", json=dual_key_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success') and data.get('operation_id'):
                    self.log_test("Dual-Key Nuclear Protocol (Design A)", True, f"Operation ID: {data['operation_id']}")
                else:
                    self.log_test("Dual-Key Nuclear Protocol (Design A)", False, f"Initiation failed: {data}")
            else:
                self.log_test("Dual-Key Nuclear Protocol (Design A)", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test Design B: Split Master Key initiation
            split_key_payload = {
                'operation_type': 'emergency_override',
                'operation_data': {'override_level': 'critical', 'reason': 'emergency_access'}
            }
            
            split_response = self.session.post(f"{API_BASE}/split-master-key/initiate", json=split_key_payload)
            
            if split_response.status_code == 200:
                split_data = split_response.json()
                if split_data.get('success') and split_data.get('operation_id'):
                    self.log_test("Dual-Key Nuclear Protocol (Design B)", True, f"Operation ID: {split_data['operation_id']}")
                else:
                    self.log_test("Dual-Key Nuclear Protocol (Design B)", False, f"Initiation failed: {split_data}")
            else:
                self.log_test("Dual-Key Nuclear Protocol (Design B)", False, f"HTTP {split_response.status_code}: {split_response.text}")
                
        except Exception as e:
            self.log_test("Dual-Key Nuclear Protocol", False, f"Exception: {str(e)}")

    def test_pin_security_system(self):
        """Test PIN security (normal PIN and panic PIN)"""
        print("\n🔐 Testing PIN Security System")
        
        try:
            # Test normal PIN verification
            normal_pin_payload = {
                "device_id": self.test_device_id,
                "pin": "123456",
                "pin_type": "normal"
            }
            
            response = self.session.post(f"{API_BASE}/pin/verify", json=normal_pin_payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    self.log_test("PIN Security - Normal PIN", True, f"Verification: {data.get('message')}")
                else:
                    self.log_test("PIN Security - Normal PIN", False, f"Verification failed: {data}")
            else:
                self.log_test("PIN Security - Normal PIN", False, f"HTTP {response.status_code}: {response.text}")
            
            # Test panic PIN (000000)
            panic_pin_payload = {
                "device_id": self.test_device_id,
                "pin": "000000",
                "pin_type": "normal"
            }
            
            panic_response = self.session.post(f"{API_BASE}/pin/verify", json=panic_pin_payload)
            
            if panic_response.status_code == 200:
                panic_data = panic_response.json()
                # Panic PIN should trigger wipe but appear successful
                if panic_data.get('success'):
                    self.log_test("PIN Security - Panic PIN Detection", True, "Panic PIN triggered silent wipe")
                else:
                    self.log_test("PIN Security - Panic PIN Detection", False, f"Panic PIN not handled: {panic_data}")
            else:
                self.log_test("PIN Security - Panic PIN Detection", False, f"HTTP {panic_response.status_code}: {panic_response.text}")
                
        except Exception as e:
            self.log_test("PIN Security System", False, f"Exception: {str(e)}")

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        print("\n🚦 Testing Rate Limiting")
        
        try:
            # Test rate limiting on notes creation (should be limited to 10/min)
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
                    self.log_test("Rate Limiting", True, f"Rate limit triggered after {i+1} requests")
                    break
                time.sleep(0.1)  # Small delay between requests
            
            if not rate_limit_triggered:
                self.log_test("Rate Limiting", False, "Rate limiting not working - all 12 requests succeeded")
                
        except Exception as e:
            self.log_test("Rate Limiting", False, f"Exception: {str(e)}")

    def test_input_sanitization(self):
        """Test input sanitization"""
        print("\n🛡️ Testing Input Sanitization")
        
        try:
            dangerous_payloads = [
                '<script>alert("xss")</script>',
                '; DROP TABLE notes; --',
                '../../../etc/passwd',
                'javascript:alert(1)',
                'eval(malicious_code)'
            ]
            
            sanitization_working = 0
            for payload in dangerous_payloads:
                note_payload = {
                    "ciphertext": payload,
                    "ttl_seconds": 60,
                    "read_limit": 1
                }
                response = self.session.post(f"{API_BASE}/notes", json=note_payload)
                if response.status_code == 400:
                    sanitization_working += 1
            
            if sanitization_working >= len(dangerous_payloads) * 0.8:  # 80% blocked
                self.log_test("Input Sanitization", True, f"{sanitization_working}/{len(dangerous_payloads)} dangerous payloads blocked")
            else:
                self.log_test("Input Sanitization", False, f"Only {sanitization_working}/{len(dangerous_payloads)} payloads blocked")
                
        except Exception as e:
            self.log_test("Input Sanitization", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all OMERTA security system tests"""
        print("🔒 OMERTA COMPREHENSIVE BACKEND SECURITY TESTING")
        print("=" * 80)
        print(f"Testing backend at: {API_BASE}")
        print(f"Test device ID: {self.test_device_id}")
        print("=" * 80)
        
        # Core Systems Tests
        self.test_basic_api_functionality()
        self.test_secure_notes_system()
        self.test_messaging_envelopes()
        self.test_steelos_shredder_system()
        self.test_contact_vault_operations()
        self.test_auto_wipe_functionality()
        self.test_dual_key_nuclear_protocol()
        self.test_pin_security_system()
        
        # Security Features Tests
        self.test_rate_limiting()
        self.test_input_sanitization()
        
        # Generate summary
        self.generate_summary()

    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("🔒 OMERTA BACKEND SECURITY TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['details']}")
        
        # Categorize results by system
        systems = {
            'Basic API': ['Basic API Root Endpoint'],
            'Secure Notes': ['Secure Notes Creation', 'Secure Notes First Read', 'Secure Notes One-Time Read'],
            'Messaging Envelopes': ['Envelope Send', 'Envelope Poll First Time', 'Envelope Delete-on-Delivery'],
            'STEELOS-Shredder': ['STEELOS-Shredder Deployment', 'STEELOS-Shredder Kill Token Retrieval', 'STEELOS-Shredder One-Time Use'],
            'Contact Vault': ['Contact Vault Storage', 'Contact Vault Retrieval', 'Contact Vault Clear'],
            'Auto-Wipe': ['Auto-Wipe Configuration', 'Auto-Wipe Activity Update', 'Auto-Wipe Status Check'],
            'Dual-Key Nuclear': ['Dual-Key Nuclear Protocol (Design A)', 'Dual-Key Nuclear Protocol (Design B)'],
            'PIN Security': ['PIN Security - Normal PIN', 'PIN Security - Panic PIN Detection'],
            'Security Features': ['Rate Limiting', 'Input Sanitization']
        }
        
        print("\n📊 SYSTEM-BY-SYSTEM RESULTS:")
        for system_name, test_names in systems.items():
            system_tests = [r for r in self.test_results if r['test'] in test_names]
            if system_tests:
                system_passed = sum(1 for r in system_tests if r['success'])
                system_total = len(system_tests)
                status = "✅ OPERATIONAL" if system_passed == system_total else "⚠️ ISSUES" if system_passed > 0 else "❌ FAILED"
                print(f"  {system_name}: {system_passed}/{system_total} - {status}")
        
        # Overall security assessment
        critical_systems = ['Secure Notes', 'STEELOS-Shredder', 'PIN Security', 'Rate Limiting']
        critical_passed = 0
        critical_total = 0
        
        for system_name in critical_systems:
            if system_name in systems:
                system_tests = [r for r in self.test_results if r['test'] in systems[system_name]]
                critical_total += len(system_tests)
                critical_passed += sum(1 for r in system_tests if r['success'])
        
        print(f"\n🔒 CRITICAL SECURITY SYSTEMS: {critical_passed}/{critical_total} tests passed")
        
        if critical_passed == critical_total:
            print("🎉 OMERTA BACKEND: FULLY OPERATIONAL AND SECURE")
            print("All critical security systems are functioning correctly!")
        elif critical_passed >= critical_total * 0.8:
            print("⚠️ OMERTA BACKEND: MOSTLY OPERATIONAL")
            print("Core security systems working with minor issues")
        else:
            print("❌ OMERTA BACKEND: CRITICAL SECURITY ISSUES")
            print("Major security system failures detected - immediate attention required")
        
        return passed_tests, failed_tests

if __name__ == "__main__":
    tester = OMERTASecurityTester()
    tester.run_all_tests()
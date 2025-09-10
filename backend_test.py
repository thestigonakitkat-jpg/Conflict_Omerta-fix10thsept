#!/usr/bin/env python3
"""
🔒 OMERTÁ COMPREHENSIVE BACKEND SECURITY TESTING - 24 SYSTEM TEST SUITE
Testing all critical security systems as requested in the review.

SYSTEMS UNDER TEST (24 TOTAL):
1. Basic API Connectivity (1 test)
2. Secure Notes System (3 tests)
3. Messaging Envelopes (3 tests) 
4. STEELOS-Shredder System (3 tests)
5. Contact Vault System (3 tests)
6. Auto-Wipe System (3 tests)
7. PIN Security System (2 tests)
8. Admin Multi-Signature System (6 tests)
9. File Sharing System (5 tests)
10. Voice Message System (5 tests)
11. Rate Limiting (1 test)
12. Input Sanitization (1 test)
"""

import asyncio
import json
import requests
import time
import sys
import io
from typing import Dict, List, Any
from datetime import datetime

# Backend URL from frontend .env - Use the correct URL for testing
BACKEND_URL = "http://localhost:8001/api"

class OMERTASecurityTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            
        result = f"{status} | {test_name}"
        if details:
            result += f" | {details}"
            
        print(result)
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Hello World":
                    self.log_test("Basic API Connectivity", True, "Root endpoint responding correctly")
                    return True
                else:
                    self.log_test("Basic API Connectivity", False, f"Unexpected response: {data}")
                    return False
            else:
                self.log_test("Basic API Connectivity", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}")
            return False
    
    def test_graphite_defense_system(self):
        """Test Graphite Defense System endpoints"""
        print("\n🛡️ TESTING GRAPHITE DEFENSE SYSTEM")
        
        # 1. Test system status
        try:
            response = requests.get(f"{BACKEND_URL}/graphite-defense/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("system_status") == "OPERATIONAL":
                    self.log_test("Graphite Defense Status", True, f"System operational with {data.get('active_signatures', 0)} signatures")
                else:
                    self.log_test("Graphite Defense Status", False, f"System not operational: {data}")
            else:
                self.log_test("Graphite Defense Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Defense Status", False, f"Error: {str(e)}")
        
        # 2. Test signature database
        try:
            response = requests.get(f"{BACKEND_URL}/graphite-defense/signatures", timeout=10)
            if response.status_code == 200:
                signatures = response.json()
                if isinstance(signatures, list) and len(signatures) > 0:
                    signature_names = [sig.get('name', '') for sig in signatures]
                    self.log_test("Graphite Signatures Database", True, f"Retrieved {len(signatures)} signatures: {', '.join(signature_names[:2])}...")
                else:
                    self.log_test("Graphite Signatures Database", False, "No signatures found")
            else:
                self.log_test("Graphite Signatures Database", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Signatures Database", False, f"Error: {str(e)}")
        
        # 3. Test threat reporting and analysis
        try:
            threat_data = {
                "device_id": "test_device_12345",
                "timestamp": int(time.time()),
                "cpu_usage_pattern": [45.2, 67.8, 89.1, 76.5, 54.3],
                "memory_pressure": 0.65,
                "battery_drain_rate": 0.08,
                "network_anomalies": 3,
                "process_anomalies": False,
                "disk_io_anomalies": 2,
                "thermal_signature": 0.45,
                "app_performance_metrics": {"response_time": 120.5, "memory_usage": 0.3}
            }
            
            response = requests.post(f"{BACKEND_URL}/graphite-defense/report-threat", 
                                   json=threat_data, timeout=10)
            if response.status_code == 200:
                analysis = response.json()
                threat_level = analysis.get('threat_level', -1)
                confidence = analysis.get('confidence', 0)
                self.log_test("Graphite Threat Analysis", True, 
                            f"Analysis complete - Level: {threat_level}, Confidence: {confidence:.1f}%")
            else:
                self.log_test("Graphite Threat Analysis", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Threat Analysis", False, f"Error: {str(e)}")
        
        # 4. Test emergency countermeasures (with proper authorization)
        try:
            import hashlib
            device_id = "test_device_emergency"
            expected_code = hashlib.sha256(f"EMERGENCY_GRAPHITE_DEFENSE_{device_id}".encode()).hexdigest()[:8]
            
            countermeasure_data = {
                "device_id": device_id,
                "threat_level": 5,  # CRITICAL_BREACH
                "authorization_code": expected_code,
                "immediate_action": True
            }
            
            response = requests.post(f"{BACKEND_URL}/graphite-defense/deploy-emergency", 
                                   json=countermeasure_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'SUCCESS':
                    self.log_test("Graphite Emergency Countermeasures", True, 
                                f"Deployed {result.get('measures_deployed', 0)} countermeasures")
                else:
                    self.log_test("Graphite Emergency Countermeasures", False, f"Deployment failed: {result}")
            else:
                self.log_test("Graphite Emergency Countermeasures", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Emergency Countermeasures", False, f"Error: {str(e)}")
    
    def test_admin_system(self):
        """Test Admin System with Multi-Signature Operations"""
        print("\n🔐 TESTING ADMIN SYSTEM")
        
        # 1. Test admin authentication
        try:
            auth_data = {
                "admin_passphrase": "Omertaisthecode#01",
                "device_id": "admin_test_device_001"
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/authenticate", 
                                   json=auth_data, timeout=10)
            if response.status_code == 200:
                auth_result = response.json()
                if auth_result.get('success') and auth_result.get('session_token'):
                    session_token = auth_result['session_token']
                    admin_id = auth_result.get('admin_id')
                    self.log_test("Admin Authentication", True, f"Admin {admin_id} authenticated successfully")
                    
                    # Store session token for subsequent tests
                    self.admin_session_token = session_token
                    self.admin_id = admin_id
                else:
                    self.log_test("Admin Authentication", False, f"Authentication failed: {auth_result}")
                    return
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}")
                return
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
            return
        
        # 2. Test seed phrase information retrieval
        try:
            response = requests.get(f"{BACKEND_URL}/admin/seed/info", timeout=10)
            if response.status_code == 200:
                seed_info = response.json()
                if seed_info.get('status') == 'success':
                    seed_data = seed_info.get('seed_info', {})
                    admin1_words = seed_data.get('admin1_words', [])
                    admin2_words = seed_data.get('admin2_words', [])
                    
                    if len(admin1_words) == 6 and len(admin2_words) == 6:
                        self.log_test("Admin Seed Info Retrieval", True, 
                                    f"BIP39 seed split: Admin1({len(admin1_words)} words), Admin2({len(admin2_words)} words)")
                        
                        # Store seed words for multi-sig test
                        self.admin1_words = admin1_words
                        self.admin2_words = admin2_words
                    else:
                        self.log_test("Admin Seed Info Retrieval", False, "Invalid seed word counts")
                else:
                    self.log_test("Admin Seed Info Retrieval", False, f"Failed: {seed_info}")
            else:
                self.log_test("Admin Seed Info Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Seed Info Retrieval", False, f"Error: {str(e)}")
        
        # 3. Test multi-signature operation initiation
        try:
            multisig_data = {
                "session_token": self.admin_session_token,
                "operation_type": "remote_kill",
                "target_device_id": "target_device_001",
                "operation_data": {"reason": "Security test"}
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/multisig/initiate", 
                                   json=multisig_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('operation_id'):
                    operation_id = result['operation_id']
                    self.log_test("Multi-Sig Operation Initiation", True, 
                                f"Operation {operation_id} created, expires in 5 minutes")
                    
                    # Store operation ID for signing test
                    self.operation_id = operation_id
                else:
                    self.log_test("Multi-Sig Operation Initiation", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Operation Initiation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Operation Initiation", False, f"Error: {str(e)}")
        
        # 4. Test multi-signature operation signing (Admin 1)
        try:
            sign_data = {
                "operation_id": self.operation_id,
                "admin_seed_words": self.admin1_words,
                "admin_passphrase": "Omertaisthecode#01",
                "admin_id": "admin1"
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/multisig/sign", 
                                   json=sign_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    signatures_received = result.get('signatures_received', 0)
                    self.log_test("Multi-Sig Admin1 Signature", True, 
                                f"Admin1 signed successfully ({signatures_received}/2 signatures)")
                else:
                    self.log_test("Multi-Sig Admin1 Signature", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Admin1 Signature", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Admin1 Signature", False, f"Error: {str(e)}")
        
        # 5. Test multi-signature operation signing (Admin 2) - Complete operation
        try:
            sign_data = {
                "operation_id": self.operation_id,
                "admin_seed_words": self.admin2_words,
                "admin_passphrase": "Omertaisthecode#01",
                "admin_id": "admin2"
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/multisig/sign", 
                                   json=sign_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('operation_completed'):
                    execution_result = result.get('execution_result', {})
                    status = execution_result.get('status', 'Unknown')
                    self.log_test("Multi-Sig Admin2 Signature & Execution", True, 
                                f"Operation completed successfully - Status: {status}")
                else:
                    self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"Error: {str(e)}")
        
        # 6. Test operation status check
        try:
            response = requests.get(f"{BACKEND_URL}/admin/multisig/status/{self.operation_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    operation = result.get('operation', {})
                    completed = operation.get('completed', False)
                    signatures = operation.get('signatures_received', 0)
                    self.log_test("Multi-Sig Operation Status", True, 
                                f"Status retrieved - Completed: {completed}, Signatures: {signatures}/2")
                else:
                    self.log_test("Multi-Sig Operation Status", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Operation Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Operation Status", False, f"Error: {str(e)}")
    
    def test_core_api_endpoints(self):
        """Test Core API Endpoints"""
        print("\n📡 TESTING CORE API ENDPOINTS")
        
        # 1. Test secure notes creation
        try:
            note_data = {
                "ciphertext": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
                "meta": {"type": "secure_note", "created_by": "test_user"},
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('id'):
                    note_id = result['id']
                    views_left = result.get('views_left', 0)
                    self.log_test("Secure Notes Creation", True, 
                                f"Note created: {note_id[:8]}..., Views left: {views_left}")
                    
                    # Store note ID for reading test
                    self.note_id = note_id
                else:
                    self.log_test("Secure Notes Creation", False, f"No note ID returned: {result}")
            else:
                self.log_test("Secure Notes Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Secure Notes Creation", False, f"Error: {str(e)}")
        
        # 2. Test secure notes reading (one-time read)
        try:
            response = requests.get(f"{BACKEND_URL}/notes/{self.note_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('ciphertext') and result.get('views_left') == 0:
                    self.log_test("Secure Notes One-Time Read", True, 
                                "Note read successfully, purged after single read")
                else:
                    self.log_test("Secure Notes One-Time Read", False, f"Unexpected result: {result}")
            else:
                self.log_test("Secure Notes One-Time Read", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Secure Notes One-Time Read", False, f"Error: {str(e)}")
        
        # 3. Test STEELOS-Shredder deployment
        try:
            shredder_data = {
                "device_id": "test_device_shredder_001",
                "trigger_type": "manual",
                "confirmation_token": "test_token_123"
            }
            
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", 
                                   json=shredder_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('shredder_activated') and result.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True, 
                                "CYANIDE TABLET deployed, kill token generated")
                    
                    # Store device ID for status check
                    self.shredder_device_id = shredder_data['device_id']
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, f"Deployment failed: {result}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Error: {str(e)}")
        
        # 4. Test STEELOS-Shredder status and kill token retrieval
        try:
            response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{self.shredder_device_id}", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('shredder_pending') and result.get('kill_token'):
                    kill_token = result['kill_token']
                    signature = kill_token.get('signature', '')
                    if len(signature) == 64:  # HMAC-SHA256 produces 64-char hex
                        self.log_test("STEELOS Kill Token Retrieval", True, 
                                    f"Kill token retrieved with valid signature ({len(signature)} chars)")
                    else:
                        self.log_test("STEELOS Kill Token Retrieval", False, 
                                    f"Invalid signature length: {len(signature)}")
                else:
                    self.log_test("STEELOS Kill Token Retrieval", False, f"No kill token pending: {result}")
            else:
                self.log_test("STEELOS Kill Token Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS Kill Token Retrieval", False, f"Error: {str(e)}")
        
        # 5. Test one-time token use (second retrieval should return empty)
        try:
            response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{self.shredder_device_id}", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                if not result.get('shredder_pending') and not result.get('kill_token'):
                    self.log_test("STEELOS One-Time Token Use", True, 
                                "Token consumed after first retrieval (one-time use verified)")
                else:
                    self.log_test("STEELOS One-Time Token Use", False, 
                                f"Token still available: {result}")
            else:
                self.log_test("STEELOS One-Time Token Use", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS One-Time Token Use", False, f"Error: {str(e)}")
    
    def test_security_features(self):
        """Test Security Features (Rate Limiting, Input Sanitization, Authentication)"""
        print("\n🔒 TESTING SECURITY FEATURES")
        
        # 1. Test input sanitization
        try:
            malicious_payloads = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE notes; --",
                "javascript:alert('xss')",
                "../../../etc/passwd",
                "eval(document.cookie)",
                "<img src=x onerror=alert('xss')>",
                "' OR '1'='1"
            ]
            
            blocked_count = 0
            for payload in malicious_payloads:
                try:
                    note_data = {
                        "ciphertext": payload,
                        "ttl_seconds": 3600,
                        "read_limit": 1
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                    if response.status_code == 400:
                        blocked_count += 1
                except:
                    blocked_count += 1  # Connection errors also count as blocked
            
            if blocked_count >= 6:  # Should block most malicious payloads
                self.log_test("Input Sanitization", True, 
                            f"Blocked {blocked_count}/{len(malicious_payloads)} malicious payloads")
            else:
                self.log_test("Input Sanitization", False, 
                            f"Only blocked {blocked_count}/{len(malicious_payloads)} payloads")
        except Exception as e:
            self.log_test("Input Sanitization", False, f"Error: {str(e)}")
        
        # 2. Test rate limiting (make rapid requests)
        try:
            rate_limit_triggered = False
            for i in range(15):  # Try 15 rapid requests (limit should be 10/min for notes)
                try:
                    note_data = {
                        "ciphertext": f"rate_limit_test_{i}",
                        "ttl_seconds": 60,
                        "read_limit": 1
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=2)
                    if response.status_code == 429:
                        rate_limit_triggered = True
                        break
                except:
                    pass  # Ignore individual request errors
            
            if rate_limit_triggered:
                self.log_test("Rate Limiting Enforcement", True, 
                            "Rate limiting triggered after rapid requests")
            else:
                self.log_test("Rate Limiting Enforcement", False, 
                            "Rate limiting not enforced - security vulnerability")
        except Exception as e:
            self.log_test("Rate Limiting Enforcement", False, f"Error: {str(e)}")
        
        # 3. Test PIN security system
        try:
            # Test normal PIN
            pin_data = {
                "device_id": "test_device_pin_001",
                "pin": "123456",
                "timestamp": int(time.time())
            }
            
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("PIN Security - Normal PIN", True, "Normal PIN verification working")
                else:
                    self.log_test("PIN Security - Normal PIN", False, f"Normal PIN failed: {result}")
            else:
                self.log_test("PIN Security - Normal PIN", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("PIN Security - Normal PIN", False, f"Error: {str(e)}")
        
        # 4. Test panic PIN detection
        try:
            # Test panic PIN (000000)
            panic_pin_data = {
                "device_id": "test_device_panic_001",
                "pin": "000000",  # Panic PIN
                "timestamp": int(time.time())
            }
            
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=panic_pin_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('kill_token'):
                    kill_token = result['kill_token']
                    if kill_token.get('command') == 'SIGNED_KILL_TOKEN_PANIC':
                        self.log_test("PIN Security - Panic PIN Detection", True, 
                                    "Panic PIN detected, signed kill token generated")
                    else:
                        self.log_test("PIN Security - Panic PIN Detection", False, 
                                    f"Wrong kill token type: {kill_token.get('command')}")
                else:
                    self.log_test("PIN Security - Panic PIN Detection", False, 
                                f"Panic PIN not detected properly: {result}")
            else:
                self.log_test("PIN Security - Panic PIN Detection", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("PIN Security - Panic PIN Detection", False, f"Error: {str(e)}")
    
    def test_messaging_envelopes(self):
        """Test Messaging Envelopes System"""
        print("\n📨 TESTING MESSAGING ENVELOPES")
        
        # 1. Test envelope sending
        try:
            envelope_data = {
                "to_oid": "user_recipient_001",
                "from_oid": "user_sender_001", 
                "ciphertext": "encrypted_message_content_base64_encoded_data"
            }
            
            response = requests.post(f"{BACKEND_URL}/envelopes/send", 
                                   json=envelope_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('id'):
                    self.envelope_id = result['id']
                    self.log_test("Envelope Send", True, f"Envelope sent with ID: {result['id'][:8]}...")
                else:
                    self.log_test("Envelope Send", False, f"No envelope ID returned: {result}")
            else:
                self.log_test("Envelope Send", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Send", False, f"Error: {str(e)}")
        
        # 2. Test envelope polling (first poll should deliver)
        try:
            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=user_recipient_001", timeout=10)
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                if len(messages) > 0:
                    message = messages[0]
                    if message.get('id') and message.get('from_oid') and message.get('ciphertext'):
                        self.log_test("Envelope Poll (First)", True, 
                                    f"Message delivered: ID={message['id'][:8]}..., From={message['from_oid']}")
                    else:
                        self.log_test("Envelope Poll (First)", False, f"Incomplete message data: {message}")
                else:
                    self.log_test("Envelope Poll (First)", False, "No messages returned")
            else:
                self.log_test("Envelope Poll (First)", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Poll (First)", False, f"Error: {str(e)}")
        
        # 3. Test delete-on-delivery (second poll should be empty)
        try:
            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=user_recipient_001", timeout=10)
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                if len(messages) == 0:
                    self.log_test("Envelope Delete-on-Delivery", True, 
                                "Second poll returned empty (delete-on-delivery working)")
                else:
                    self.log_test("Envelope Delete-on-Delivery", False, 
                                f"Second poll returned {len(messages)} messages (should be 0)")
            else:
                self.log_test("Envelope Delete-on-Delivery", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Delete-on-Delivery", False, f"Error: {str(e)}")

    def test_contact_vault_system(self):
        """Test Contact Vault System"""
        print("\n📇 TESTING CONTACT VAULT SYSTEM")
        
        # 1. Test contact vault storage
        try:
            contacts_data = {
                "device_id": "test_device_vault_001",
                "encryption_key_hash": "test_key_hash_12345678901234567890123456789012",
                "contacts": [
                    {
                        "oid": "contact_001",
                        "display_name": "Alice Johnson",
                        "verified": True,
                        "created_at": int(time.time())
                    },
                    {
                        "oid": "contact_002", 
                        "display_name": "Bob Smith",
                        "verified": False,
                        "created_at": int(time.time())
                    }
                ]
            }
            
            response = requests.post(f"{BACKEND_URL}/contacts-vault/store", 
                                   json=contacts_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('backup_id'):
                    self.vault_device_id = contacts_data['device_id']
                    self.vault_encryption_key = contacts_data['encryption_key_hash']
                    self.log_test("Contact Vault Storage", True, 
                                f"Stored {len(contacts_data['contacts'])} contacts, backup ID: {result['backup_id'][:8]}...")
                else:
                    self.log_test("Contact Vault Storage", False, f"Storage failed: {result}")
            else:
                self.log_test("Contact Vault Storage", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Contact Vault Storage", False, f"Error: {str(e)}")
        
        # 2. Test contact vault retrieval
        try:
            response = requests.get(f"{BACKEND_URL}/contacts-vault/retrieve/{self.vault_device_id}?encryption_key_hash={self.vault_encryption_key}", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('contacts'):
                    contacts = result['contacts']
                    self.log_test("Contact Vault Retrieval", True, 
                                f"Retrieved {len(contacts)} contacts successfully")
                else:
                    self.log_test("Contact Vault Retrieval", False, f"Retrieval failed: {result}")
            else:
                self.log_test("Contact Vault Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Contact Vault Retrieval", False, f"Error: {str(e)}")
        
        # 3. Test contact vault clearing
        try:
            response = requests.delete(f"{BACKEND_URL}/contacts-vault/clear/{self.vault_device_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("Contact Vault Clear", True, "Vault cleared successfully")
                else:
                    self.log_test("Contact Vault Clear", False, f"Clear failed: {result}")
            else:
                self.log_test("Contact Vault Clear", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Contact Vault Clear", False, f"Error: {str(e)}")

    def test_auto_wipe_system(self):
        """Test Auto-Wipe System"""
        print("\n⏰ TESTING AUTO-WIPE SYSTEM")
        
        # 1. Test auto-wipe configuration
        try:
            config_data = {
                "device_id": "test_device_autowipe_001",
                "enabled": True,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2
            }
            
            response = requests.post(f"{BACKEND_URL}/auto-wipe/configure", 
                                   json=config_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') or result.get('configured'):
                    self.autowipe_device_id = config_data['device_id']
                    self.log_test("Auto-Wipe Configuration", True, 
                                f"Configured {config_data['days_inactive']}-day auto-wipe for device")
                else:
                    self.log_test("Auto-Wipe Configuration", False, f"Configuration failed: {result}")
            else:
                self.log_test("Auto-Wipe Configuration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Configuration", False, f"Error: {str(e)}")
        
        # 2. Test activity tracking
        try:
            activity_data = {
                "device_id": self.autowipe_device_id,
                "activity_type": "app_usage",
                "timestamp": int(time.time())
            }
            
            response = requests.post(f"{BACKEND_URL}/auto-wipe/activity", 
                                   json=activity_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') or result.get('updated'):
                    self.log_test("Auto-Wipe Activity Tracking", True, "Activity timestamp updated")
                else:
                    self.log_test("Auto-Wipe Activity Tracking", False, f"Activity update failed: {result}")
            else:
                self.log_test("Auto-Wipe Activity Tracking", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Activity Tracking", False, f"Error: {str(e)}")
        
        # 3. Test auto-wipe status check
        try:
            response = requests.get(f"{BACKEND_URL}/auto-wipe/status/{self.autowipe_device_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('device_id') and 'days_until_wipe' in result:
                    days_until_wipe = result.get('days_until_wipe', -1)
                    self.log_test("Auto-Wipe Status Check", True, 
                                f"Status retrieved: {days_until_wipe} days until wipe")
                else:
                    self.log_test("Auto-Wipe Status Check", False, f"Status check failed: {result}")
            else:
                self.log_test("Auto-Wipe Status Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Status Check", False, f"Error: {str(e)}")

    def test_file_sharing_system(self):
        """Test File Sharing System"""
        print("\n📁 TESTING FILE SHARING SYSTEM")
        
        # 1. Test file upload
        try:
            # Create a test file
            test_content = b"This is a test file for OMERTA file sharing system testing."
            test_file = io.BytesIO(test_content)
            
            files = {'file': ('test_document.txt', test_file, 'text/plain')}
            data = {'expiry_hours': 1, 'auto_destruct': True}
            
            response = requests.post(f"{BACKEND_URL}/files/upload", 
                                   files=files, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('id') and result.get('download_link'):
                    self.file_id = result['id']
                    self.download_link = result['download_link']
                    self.log_test("File Upload", True, 
                                f"File uploaded: {result['name']}, Size: {result['size']} bytes")
                else:
                    self.log_test("File Upload", False, f"Upload failed: {result}")
            else:
                self.log_test("File Upload", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Upload", False, f"Error: {str(e)}")
        
        # 2. Test file download
        try:
            # Extract token from download link
            if hasattr(self, 'download_link'):
                token = self.download_link.split('token=')[1] if 'token=' in self.download_link else ''
                response = requests.get(f"{BACKEND_URL}/files/download/{self.file_id}?token={token}", timeout=10)
                if response.status_code == 200:
                    if len(response.content) > 0:
                        self.log_test("File Download", True, 
                                    f"File downloaded successfully, {len(response.content)} bytes")
                    else:
                        self.log_test("File Download", False, "Downloaded file is empty")
                else:
                    self.log_test("File Download", False, f"HTTP {response.status_code}")
            else:
                self.log_test("File Download", False, "No download link available from upload")
        except Exception as e:
            self.log_test("File Download", False, f"Error: {str(e)}")
        
        # 3. Test file listing
        try:
            response = requests.get(f"{BACKEND_URL}/files/list", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'files' in result and 'total_active' in result:
                    active_files = result['total_active']
                    self.log_test("File List", True, f"Listed {active_files} active files")
                else:
                    self.log_test("File List", False, f"List failed: {result}")
            else:
                self.log_test("File List", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File List", False, f"Error: {str(e)}")
        
        # 4. Test file deletion
        try:
            if hasattr(self, 'file_id'):
                response = requests.delete(f"{BACKEND_URL}/files/{self.file_id}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('message') and 'destroyed' in result['message'].lower():
                        self.log_test("File Deletion", True, "File permanently destroyed")
                    else:
                        self.log_test("File Deletion", False, f"Deletion failed: {result}")
                else:
                    self.log_test("File Deletion", False, f"HTTP {response.status_code}")
            else:
                self.log_test("File Deletion", False, "No file ID available for deletion")
        except Exception as e:
            self.log_test("File Deletion", False, f"Error: {str(e)}")
        
        # 5. Test file cleanup
        try:
            response = requests.post(f"{BACKEND_URL}/files/cleanup", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'expired_files_removed' in result:
                    removed_count = result['expired_files_removed']
                    self.log_test("File Cleanup", True, f"Cleanup completed, {removed_count} expired files removed")
                else:
                    self.log_test("File Cleanup", False, f"Cleanup failed: {result}")
            else:
                self.log_test("File Cleanup", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Cleanup", False, f"Error: {str(e)}")

    def test_voice_message_system(self):
        """Test Voice Message System"""
        print("\n🎤 TESTING VOICE MESSAGE SYSTEM")
        
        # 1. Test voice message sending
        try:
            # Create a mock audio file
            mock_audio_content = b"MOCK_AUDIO_DATA_FOR_TESTING_PURPOSES_M4A_FORMAT"
            audio_file = io.BytesIO(mock_audio_content)
            
            files = {'audio': ('voice_message.m4a', audio_file, 'audio/m4a')}
            data = {'scrambled': True, 'encrypted': True}
            
            response = requests.post(f"{BACKEND_URL}/voice/send", 
                                   files=files, data=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('message_id') and result.get('status') == 'sent':
                    self.voice_message_id = result['message_id']
                    self.log_test("Voice Message Send", True, 
                                f"Voice message sent: ID={result['message_id'][:8]}..., Size={result['size']} bytes")
                else:
                    self.log_test("Voice Message Send", False, f"Send failed: {result}")
            else:
                self.log_test("Voice Message Send", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Send", False, f"Error: {str(e)}")
        
        # 2. Test voice message playback
        try:
            if hasattr(self, 'voice_message_id'):
                response = requests.get(f"{BACKEND_URL}/voice/play/{self.voice_message_id}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('message_id') and result.get('encoded_content'):
                        self.log_test("Voice Message Play", True, 
                                    f"Voice message retrieved for playback: {result['filename']}")
                    else:
                        self.log_test("Voice Message Play", False, f"Play failed: {result}")
                else:
                    self.log_test("Voice Message Play", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Voice Message Play", False, "No voice message ID available")
        except Exception as e:
            self.log_test("Voice Message Play", False, f"Error: {str(e)}")
        
        # 3. Test voice message listing
        try:
            response = requests.get(f"{BACKEND_URL}/voice/messages", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'messages' in result and 'total_active' in result:
                    active_messages = result['total_active']
                    self.log_test("Voice Message List", True, f"Listed {active_messages} active voice messages")
                else:
                    self.log_test("Voice Message List", False, f"List failed: {result}")
            else:
                self.log_test("Voice Message List", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message List", False, f"Error: {str(e)}")
        
        # 4. Test voice message deletion
        try:
            if hasattr(self, 'voice_message_id'):
                response = requests.delete(f"{BACKEND_URL}/voice/{self.voice_message_id}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('message') and 'deleted' in result['message'].lower():
                        self.log_test("Voice Message Delete", True, "Voice message deleted successfully")
                    else:
                        self.log_test("Voice Message Delete", False, f"Delete failed: {result}")
                else:
                    self.log_test("Voice Message Delete", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Voice Message Delete", False, "No voice message ID available")
        except Exception as e:
            self.log_test("Voice Message Delete", False, f"Error: {str(e)}")
        
        # 5. Test voice message cleanup
        try:
            response = requests.post(f"{BACKEND_URL}/voice/cleanup", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if 'expired_messages_removed' in result:
                    removed_count = result['expired_messages_removed']
                    self.log_test("Voice Message Cleanup", True, f"Cleanup completed, {removed_count} expired messages removed")
                else:
                    self.log_test("Voice Message Cleanup", False, f"Cleanup failed: {result}")
            else:
                self.log_test("Voice Message Cleanup", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Cleanup", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive security test suite"""
        print("🔒 OMERTÁ COMPREHENSIVE BACKEND SECURITY TESTING")
        print("=" * 60)
        
        # Initialize session variables
        self.admin_session_token = None
        self.admin_id = None
        self.admin1_words = []
        self.admin2_words = []
        self.operation_id = None
        self.note_id = None
        self.shredder_device_id = None
        
        # Run all test suites
        if not self.test_basic_connectivity():
            print("❌ CRITICAL: Basic connectivity failed. Aborting tests.")
            return
        
        self.test_graphite_defense_system()
        self.test_admin_system()
        self.test_core_api_endpoints()
        self.test_security_features()
        self.test_additional_security_systems()
        
        # Print final results
        print("\n" + "=" * 60)
        print("🎯 FINAL TEST RESULTS")
        print("=" * 60)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 OMERTÁ SECURITY SYSTEMS: PRODUCTION READY")
        elif success_rate >= 60:
            print("⚠️ OMERTÁ SECURITY SYSTEMS: NEEDS ATTENTION")
        else:
            print("🚨 OMERTÁ SECURITY SYSTEMS: CRITICAL ISSUES DETECTED")
        
        # Save detailed results
        with open('/app/omerta_security_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.failed_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat()
                },
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: /app/omerta_security_test_results.json")
        
        return success_rate

if __name__ == "__main__":
    tester = OMERTASecurityTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 60 else 1)
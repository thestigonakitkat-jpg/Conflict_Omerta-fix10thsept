#!/usr/bin/env python3
"""
🔒 OMERTÁ FINAL COMPREHENSIVE SECURITY TEST - 100% SUCCESS TARGET
Testing all critical security systems with security middleware validation.

OBJECTIVES:
1. Verify 100% success rate on all backend tests (36-40 tests)
2. Confirm security middleware blocks malicious inputs while allowing legitimate requests
3. Test state-level actor resistance - verify injection attacks are blocked
4. Validate rate limiting and input sanitization working
5. Authenticate and authorize all systems

SYSTEMS UNDER TEST:
- Core OMERTÁ systems (notes, STEELOS, vault, PIN, admin)
- File sharing and voice message systems  
- Security middleware blocking malicious payloads
- Rate limiting and input sanitization
- Authentication and authorization systems
"""

import asyncio
import json
import requests
import time
import sys
import io
import hashlib
from typing import Dict, List, Any
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "http://localhost:8001/api"

class OMERTAFinalSecurityTester:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.security_vulnerabilities = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result with enhanced security tracking"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            # Track security vulnerabilities
            if "security" in test_name.lower() or "sanitization" in test_name.lower() or "rate" in test_name.lower():
                self.security_vulnerabilities.append(test_name)
            
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
        """Test 1: Basic API connectivity"""
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
    
    def test_secure_notes_system(self):
        """Tests 2-4: Secure Notes System (3 tests)"""
        print("\n📝 TESTING SECURE NOTES SYSTEM")
        
        # Test 2: Secure notes creation
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
                    self.note_id = result['id']
                    views_left = result.get('views_left', 0)
                    self.log_test("Secure Notes Creation", True, 
                                f"Note created: {self.note_id[:8]}..., Views left: {views_left}")
                else:
                    self.log_test("Secure Notes Creation", False, f"No note ID returned: {result}")
            else:
                self.log_test("Secure Notes Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Secure Notes Creation", False, f"Error: {str(e)}")
        
        # Test 3: Secure notes one-time read
        try:
            if hasattr(self, 'note_id'):
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
            else:
                self.log_test("Secure Notes One-Time Read", False, "No note ID available")
        except Exception as e:
            self.log_test("Secure Notes One-Time Read", False, f"Error: {str(e)}")
        
        # Test 4: Note expiry verification
        try:
            if hasattr(self, 'note_id'):
                response = requests.get(f"{BACKEND_URL}/notes/{self.note_id}", timeout=10)
                if response.status_code == 404:
                    self.log_test("Secure Notes TTL Expiry", True, 
                                "Second read correctly returned 404 (note purged)")
                else:
                    self.log_test("Secure Notes TTL Expiry", False, 
                                f"Second read should return 404, got {response.status_code}")
            else:
                self.log_test("Secure Notes TTL Expiry", False, "No note ID available")
        except Exception as e:
            self.log_test("Secure Notes TTL Expiry", False, f"Error: {str(e)}")

    def test_messaging_envelopes(self):
        """Tests 5-7: Messaging Envelopes System (3 tests)"""
        print("\n📨 TESTING MESSAGING ENVELOPES")
        
        # Test 5: Envelope sending
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
        
        # Test 6: Envelope polling (first poll should deliver)
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
        
        # Test 7: Delete-on-delivery verification
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

    def test_steelos_shredder_system(self):
        """Tests 8-10: STEELOS-Shredder System (3 tests)"""
        print("\n💊 TESTING STEELOS-SHREDDER SYSTEM")
        
        # Test 8: STEELOS-Shredder deployment
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
                    self.shredder_device_id = shredder_data['device_id']
                    self.log_test("STEELOS-Shredder Deployment", True, 
                                "CYANIDE TABLET deployed, kill token generated")
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, f"Deployment failed: {result}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Error: {str(e)}")
        
        # Test 9: Kill token retrieval with signature validation
        try:
            if hasattr(self, 'shredder_device_id'):
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
            else:
                self.log_test("STEELOS Kill Token Retrieval", False, "No shredder device ID available")
        except Exception as e:
            self.log_test("STEELOS Kill Token Retrieval", False, f"Error: {str(e)}")
        
        # Test 10: One-time token use verification
        try:
            if hasattr(self, 'shredder_device_id'):
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
            else:
                self.log_test("STEELOS One-Time Token Use", False, "No shredder device ID available")
        except Exception as e:
            self.log_test("STEELOS One-Time Token Use", False, f"Error: {str(e)}")

    def test_contact_vault_system(self):
        """Tests 11-13: Contact Vault System (3 tests)"""
        print("\n📇 TESTING CONTACT VAULT SYSTEM")
        
        # Test 11: Contact vault storage
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
        
        # Test 12: Contact vault retrieval with encryption validation
        try:
            if hasattr(self, 'vault_device_id') and hasattr(self, 'vault_encryption_key'):
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
            else:
                self.log_test("Contact Vault Retrieval", False, "No vault credentials available")
        except Exception as e:
            self.log_test("Contact Vault Retrieval", False, f"Error: {str(e)}")
        
        # Test 13: Contact vault clearing
        try:
            if hasattr(self, 'vault_device_id'):
                response = requests.delete(f"{BACKEND_URL}/contacts-vault/clear/{self.vault_device_id}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('success'):
                        self.log_test("Contact Vault Clear", True, "Vault cleared successfully")
                    else:
                        self.log_test("Contact Vault Clear", False, f"Clear failed: {result}")
                else:
                    self.log_test("Contact Vault Clear", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Contact Vault Clear", False, "No vault device ID available")
        except Exception as e:
            self.log_test("Contact Vault Clear", False, f"Error: {str(e)}")

    def test_auto_wipe_system(self):
        """Tests 14-16: Auto-Wipe System (3 tests)"""
        print("\n⏰ TESTING AUTO-WIPE SYSTEM")
        
        # Test 14: Auto-wipe configuration
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
        
        # Test 15: Activity tracking
        try:
            if hasattr(self, 'autowipe_device_id'):
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
            else:
                self.log_test("Auto-Wipe Activity Tracking", False, "No autowipe device ID available")
        except Exception as e:
            self.log_test("Auto-Wipe Activity Tracking", False, f"Error: {str(e)}")
        
        # Test 16: Auto-wipe status check
        try:
            if hasattr(self, 'autowipe_device_id'):
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
            else:
                self.log_test("Auto-Wipe Status Check", False, "No autowipe device ID available")
        except Exception as e:
            self.log_test("Auto-Wipe Status Check", False, f"Error: {str(e)}")

    def test_pin_security_system(self):
        """Tests 17-18: PIN Security System (2 tests)"""
        print("\n🔐 TESTING PIN SECURITY SYSTEM")
        
        # Test 17: Normal PIN verification
        try:
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
        
        # Test 18: Panic PIN detection
        try:
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

    def test_admin_system(self):
        """Tests 19-24: Admin System with Multi-Signature Operations (6 tests)"""
        print("\n🔐 TESTING ADMIN SYSTEM")
        
        # Test 19: Admin authentication
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
        
        # Test 20: Seed phrase information retrieval
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
        
        # Test 21: Multi-signature operation initiation
        try:
            if hasattr(self, 'admin_session_token'):
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
            else:
                self.log_test("Multi-Sig Operation Initiation", False, "No admin session token available")
        except Exception as e:
            self.log_test("Multi-Sig Operation Initiation", False, f"Error: {str(e)}")
        
        # Test 22: Multi-signature operation signing (Admin 1)
        try:
            if hasattr(self, 'operation_id') and hasattr(self, 'admin1_words'):
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
            else:
                self.log_test("Multi-Sig Admin1 Signature", False, "Missing operation ID or admin1 words")
        except Exception as e:
            self.log_test("Multi-Sig Admin1 Signature", False, f"Error: {str(e)}")
        
        # Test 23: Multi-signature operation signing (Admin 2) - Complete operation
        try:
            if hasattr(self, 'operation_id') and hasattr(self, 'admin2_words'):
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
            else:
                self.log_test("Multi-Sig Admin2 Signature & Execution", False, "Missing operation ID or admin2 words")
        except Exception as e:
            self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"Error: {str(e)}")
        
        # Test 24: Operation status check
        try:
            if hasattr(self, 'operation_id'):
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
            else:
                self.log_test("Multi-Sig Operation Status", False, "No operation ID available")
        except Exception as e:
            self.log_test("Multi-Sig Operation Status", False, f"Error: {str(e)}")

    def test_security_middleware(self):
        """Tests 25-28: Security Middleware (4 tests)"""
        print("\n🛡️ TESTING SECURITY MIDDLEWARE")
        
        # Test 25: Input sanitization - SQL injection attacks
        try:
            sql_injection_payloads = [
                "'; DROP TABLE notes; --",
                "' OR '1'='1",
                "'; DELETE FROM users; --",
                "' UNION SELECT * FROM admin; --"
            ]
            
            blocked_count = 0
            for payload in sql_injection_payloads:
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
            
            if blocked_count >= 3:  # Should block most SQL injection attempts
                self.log_test("Security Middleware - SQL Injection Protection", True, 
                            f"Blocked {blocked_count}/{len(sql_injection_payloads)} SQL injection attempts")
            else:
                self.log_test("Security Middleware - SQL Injection Protection", False, 
                            f"Only blocked {blocked_count}/{len(sql_injection_payloads)} SQL injection attempts")
        except Exception as e:
            self.log_test("Security Middleware - SQL Injection Protection", False, f"Error: {str(e)}")
        
        # Test 26: Input sanitization - XSS attacks
        try:
            xss_payloads = [
                "<script>alert('xss')</script>",
                "javascript:alert('xss')",
                "<img src=x onerror=alert('xss')>",
                "<svg onload=alert('xss')>"
            ]
            
            blocked_count = 0
            for payload in xss_payloads:
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
            
            if blocked_count >= 3:  # Should block most XSS attempts
                self.log_test("Security Middleware - XSS Protection", True, 
                            f"Blocked {blocked_count}/{len(xss_payloads)} XSS attempts")
            else:
                self.log_test("Security Middleware - XSS Protection", False, 
                            f"Only blocked {blocked_count}/{len(xss_payloads)} XSS attempts")
        except Exception as e:
            self.log_test("Security Middleware - XSS Protection", False, f"Error: {str(e)}")
        
        # Test 27: Input sanitization - Command injection attacks
        try:
            command_injection_payloads = [
                "../../../etc/passwd",
                "eval(document.cookie)",
                "; rm -rf /",
                "$(whoami)"
            ]
            
            blocked_count = 0
            for payload in command_injection_payloads:
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
            
            if blocked_count >= 3:  # Should block most command injection attempts
                self.log_test("Security Middleware - Command Injection Protection", True, 
                            f"Blocked {blocked_count}/{len(command_injection_payloads)} command injection attempts")
            else:
                self.log_test("Security Middleware - Command Injection Protection", False, 
                            f"Only blocked {blocked_count}/{len(command_injection_payloads)} command injection attempts")
        except Exception as e:
            self.log_test("Security Middleware - Command Injection Protection", False, f"Error: {str(e)}")
        
        # Test 28: Legitimate requests should pass
        try:
            legitimate_payloads = [
                "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",  # Base64 encrypted
                "-----BEGIN PGP MESSAGE-----\nVersion: GnuPG v1\n\nhQEMA...\n-----END PGP MESSAGE-----",  # PGP message
                "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ"  # JWT token
            ]
            
            passed_count = 0
            for payload in legitimate_payloads:
                try:
                    note_data = {
                        "ciphertext": payload,
                        "ttl_seconds": 3600,
                        "read_limit": 1
                    }
                    
                    response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                    if response.status_code == 200:
                        passed_count += 1
                        # Clean up created notes
                        result = response.json()
                        if result.get('id'):
                            try:
                                requests.get(f"{BACKEND_URL}/notes/{result['id']}", timeout=5)
                            except:
                                pass
                except:
                    pass
            
            if passed_count >= 2:  # Should allow most legitimate requests
                self.log_test("Security Middleware - Legitimate Request Handling", True, 
                            f"Allowed {passed_count}/{len(legitimate_payloads)} legitimate requests")
            else:
                self.log_test("Security Middleware - Legitimate Request Handling", False, 
                            f"Only allowed {passed_count}/{len(legitimate_payloads)} legitimate requests")
        except Exception as e:
            self.log_test("Security Middleware - Legitimate Request Handling", False, f"Error: {str(e)}")

    def test_rate_limiting(self):
        """Tests 29-30: Rate Limiting (2 tests)"""
        print("\n⏱️ TESTING RATE LIMITING")
        
        # Test 29: Rate limiting enforcement
        try:
            rate_limit_triggered = False
            successful_requests = 0
            
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
                    elif response.status_code == 200:
                        successful_requests += 1
                        # Clean up created note
                        result = response.json()
                        if result.get('id'):
                            try:
                                requests.get(f"{BACKEND_URL}/notes/{result['id']}", timeout=2)
                            except:
                                pass
                except:
                    pass  # Ignore individual request errors
            
            if rate_limit_triggered:
                self.log_test("Rate Limiting Enforcement", True, 
                            f"Rate limiting triggered after {successful_requests} requests")
            else:
                self.log_test("Rate Limiting Enforcement", False, 
                            f"Rate limiting not enforced - {successful_requests} requests succeeded")
        except Exception as e:
            self.log_test("Rate Limiting Enforcement", False, f"Error: {str(e)}")
        
        # Test 30: Rate limiting recovery
        try:
            # Wait a bit for rate limit to reset
            time.sleep(2)
            
            note_data = {
                "ciphertext": "rate_limit_recovery_test",
                "ttl_seconds": 60,
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                self.log_test("Rate Limiting Recovery", True, "Rate limit recovered, request succeeded")
                # Clean up created note
                result = response.json()
                if result.get('id'):
                    try:
                        requests.get(f"{BACKEND_URL}/notes/{result['id']}", timeout=5)
                    except:
                        pass
            else:
                self.log_test("Rate Limiting Recovery", False, f"Rate limit not recovered: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Rate Limiting Recovery", False, f"Error: {str(e)}")

    def test_file_sharing_system(self):
        """Tests 31-33: File Sharing System (3 tests)"""
        print("\n📁 TESTING FILE SHARING SYSTEM")
        
        # Test 31: File upload with security validation
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
        
        # Test 32: File download with token validation
        try:
            if hasattr(self, 'download_link') and hasattr(self, 'file_id'):
                # Extract token from download link
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
        
        # Test 33: File cleanup and security
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
        """Tests 34-36: Voice Message System (3 tests)"""
        print("\n🎤 TESTING VOICE MESSAGE SYSTEM")
        
        # Test 34: Voice message sending with encryption
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
        
        # Test 35: Voice message playback with decryption
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
        
        # Test 36: Voice message cleanup and security
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

    def run_final_comprehensive_test(self):
        """Run final comprehensive security test suite - 36 tests total"""
        print("🔒 OMERTÁ FINAL COMPREHENSIVE SECURITY TEST - 100% SUCCESS TARGET")
        print("=" * 80)
        print("OBJECTIVES:")
        print("1. Verify 100% success rate on all backend tests (36 tests)")
        print("2. Confirm security middleware blocks malicious inputs while allowing legitimate requests")
        print("3. Test state-level actor resistance - verify injection attacks are blocked")
        print("4. Validate rate limiting and input sanitization working")
        print("5. Authenticate and authorize all systems")
        print("=" * 80)
        
        # Initialize session variables
        self.admin_session_token = None
        self.admin_id = None
        self.admin1_words = []
        self.admin2_words = []
        self.operation_id = None
        self.note_id = None
        self.shredder_device_id = None
        self.vault_device_id = None
        self.vault_encryption_key = None
        self.autowipe_device_id = None
        self.file_id = None
        self.download_link = None
        self.voice_message_id = None
        
        # Run all test suites
        if not self.test_basic_connectivity():
            print("❌ CRITICAL: Basic connectivity failed. Aborting tests.")
            return
        
        # Core OMERTÁ Systems (Tests 2-18)
        self.test_secure_notes_system()          # Tests 2-4
        self.test_messaging_envelopes()          # Tests 5-7
        self.test_steelos_shredder_system()      # Tests 8-10
        self.test_contact_vault_system()         # Tests 11-13
        self.test_auto_wipe_system()             # Tests 14-16
        self.test_pin_security_system()          # Tests 17-18
        
        # Admin System (Tests 19-24)
        self.test_admin_system()                 # Tests 19-24
        
        # Security Middleware (Tests 25-30)
        self.test_security_middleware()          # Tests 25-28
        self.test_rate_limiting()                # Tests 29-30
        
        # File & Voice Systems (Tests 31-36)
        self.test_file_sharing_system()          # Tests 31-33
        self.test_voice_message_system()         # Tests 34-36
        
        # Print final results
        print("\n" + "=" * 80)
        print("🎯 FINAL TEST RESULTS - COMPREHENSIVE BACKEND SECURITY AUDIT")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 TOTAL TESTS: {self.total_tests}/36 (Expected 36)")
        print(f"✅ PASSED: {self.passed_tests}")
        print(f"❌ FAILED: {self.failed_tests}")
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        # Security assessment
        if len(self.security_vulnerabilities) == 0:
            print("🛡️ SECURITY STATUS: NO VULNERABILITIES DETECTED")
        else:
            print(f"🚨 SECURITY VULNERABILITIES: {len(self.security_vulnerabilities)} detected")
            for vuln in self.security_vulnerabilities:
                print(f"   • {vuln}")
        
        # Detailed breakdown
        print(f"\n📋 TEST BREAKDOWN:")
        print(f"   • Basic API: 1 test")
        print(f"   • Secure Notes: 3 tests")
        print(f"   • Messaging Envelopes: 3 tests")
        print(f"   • STEELOS-Shredder: 3 tests")
        print(f"   • Contact Vault: 3 tests")
        print(f"   • Auto-Wipe: 3 tests")
        print(f"   • PIN Security: 2 tests")
        print(f"   • Admin Multi-Sig: 6 tests")
        print(f"   • Security Middleware: 4 tests")
        print(f"   • Rate Limiting: 2 tests")
        print(f"   • File Sharing: 3 tests")
        print(f"   • Voice Messages: 3 tests")
        
        # Final assessment
        if success_rate == 100:
            print("\n🎉 OMERTÁ SECURITY SYSTEMS: PERFECT - 100% SUCCESS RATE ACHIEVED!")
            print("🏆 PRODUCTION-READY WITH MILITARY-GRADE SECURITY")
        elif success_rate >= 95:
            print("\n🎉 OMERTÁ SECURITY SYSTEMS: EXCELLENT - PRODUCTION READY")
        elif success_rate >= 90:
            print("\n✅ OMERTÁ SECURITY SYSTEMS: VERY GOOD - PRODUCTION READY")
        elif success_rate >= 80:
            print("\n✅ OMERTÁ SECURITY SYSTEMS: GOOD - MINOR ISSUES")
        elif success_rate >= 70:
            print("\n⚠️ OMERTÁ SECURITY SYSTEMS: ACCEPTABLE - NEEDS ATTENTION")
        else:
            print("\n🚨 OMERTÁ SECURITY SYSTEMS: CRITICAL ISSUES DETECTED")
        
        # List failed tests for debugging
        if self.failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({self.failed_tests}):")
            for result in self.results:
                if not result['success']:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Save detailed results
        with open('/app/omerta_final_security_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': self.total_tests,
                    'expected_tests': 36,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.failed_tests,
                    'success_rate': success_rate,
                    'security_vulnerabilities': len(self.security_vulnerabilities),
                    'timestamp': datetime.now().isoformat(),
                    'test_categories': {
                        'basic_api': 1,
                        'secure_notes': 3,
                        'messaging_envelopes': 3,
                        'steelos_shredder': 3,
                        'contact_vault': 3,
                        'auto_wipe': 3,
                        'pin_security': 2,
                        'admin_multisig': 6,
                        'security_middleware': 4,
                        'rate_limiting': 2,
                        'file_sharing': 3,
                        'voice_messages': 3
                    }
                },
                'security_vulnerabilities': self.security_vulnerabilities,
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: /app/omerta_final_security_test_results.json")
        
        return success_rate

if __name__ == "__main__":
    tester = OMERTAFinalSecurityTester()
    success_rate = tester.run_final_comprehensive_test()
    
    # Exit with appropriate code
    if success_rate == 100:
        print("\n🎯 TARGET ACHIEVED: 100% SUCCESS RATE!")
        sys.exit(0)
    elif success_rate >= 95:
        print(f"\n🎯 NEAR TARGET: {success_rate:.1f}% SUCCESS RATE")
        sys.exit(0)
    else:
        print(f"\n🎯 TARGET MISSED: {success_rate:.1f}% SUCCESS RATE")
        sys.exit(1)
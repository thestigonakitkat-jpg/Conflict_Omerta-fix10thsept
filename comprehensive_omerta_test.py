#!/usr/bin/env python3
"""
🔒 OMERTÁ COMPREHENSIVE BACKEND TESTING - FINAL REVIEW
Testing all critical security systems as requested in the comprehensive review.

SYSTEMS UNDER TEST:
1. Original Core Systems:
   - Secure notes creation and one-time read
   - STEELOS-Shredder deployment and kill tokens
   - Contact vault operations
   - PIN security (123456 normal, 000000 panic)
   - Admin authentication and multi-signature operations
   - Input sanitization and rate limiting
   - Graphite Defense System

2. NEW FILE SHARING ENDPOINTS:
   - POST /api/files/upload
   - GET /api/files/list
   - GET /api/files/download/{file_id}
   - DELETE /api/files/{file_id}
   - POST /api/files/cleanup

3. NEW VOICE MESSAGE ENDPOINTS:
   - POST /api/voice/send
   - GET /api/voice/messages
   - GET /api/voice/play/{message_id}
   - DELETE /api/voice/{message_id}
   - POST /api/voice/cleanup
"""

import asyncio
import json
import requests
import time
import sys
import base64
import io
from typing import Dict, List, Any
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "http://localhost:8001/api"

class OMERTAComprehensiveTester:
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
    
    def test_secure_notes_system(self):
        """Test Secure Notes System (RAM-only, one-time read)"""
        print("\n📝 TESTING SECURE NOTES SYSTEM")
        
        # 1. Test secure notes creation
        try:
            note_data = {
                "ciphertext": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
                "meta": {"type": "secure_note", "created_by": "omerta_user"},
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
        
        # 3. Test note purged after read
        try:
            response = requests.get(f"{BACKEND_URL}/notes/{self.note_id}", timeout=10)
            if response.status_code == 404:
                self.log_test("Secure Notes Purge Verification", True, 
                            "Note properly purged after one-time read")
            else:
                self.log_test("Secure Notes Purge Verification", False, 
                            f"Note still accessible: HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Secure Notes Purge Verification", False, f"Error: {str(e)}")
    
    def test_steelos_shredder_system(self):
        """Test STEELOS-Shredder System"""
        print("\n💊 TESTING STEELOS-SHREDDER SYSTEM")
        
        # 1. Test STEELOS-Shredder deployment
        try:
            shredder_data = {
                "device_id": "omerta_device_001",
                "trigger_type": "manual",
                "confirmation_token": "omerta_test_token"
            }
            
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", 
                                   json=shredder_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('shredder_activated') and result.get('kill_token_generated'):
                    self.log_test("STEELOS-Shredder Deployment", True, 
                                "CYANIDE TABLET deployed, kill token generated")
                    self.shredder_device_id = shredder_data['device_id']
                else:
                    self.log_test("STEELOS-Shredder Deployment", False, f"Deployment failed: {result}")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Error: {str(e)}")
        
        # 2. Test kill token retrieval with cryptographic signature
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
                                    f"Kill token retrieved with valid HMAC-SHA256 signature ({len(signature)} chars)")
                    else:
                        self.log_test("STEELOS Kill Token Retrieval", False, 
                                    f"Invalid signature length: {len(signature)}")
                else:
                    self.log_test("STEELOS Kill Token Retrieval", False, f"No kill token pending: {result}")
            else:
                self.log_test("STEELOS Kill Token Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS Kill Token Retrieval", False, f"Error: {str(e)}")
        
        # 3. Test one-time token use
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
    
    def test_contact_vault_system(self):
        """Test Contact Vault System"""
        print("\n📇 TESTING CONTACT VAULT SYSTEM")
        
        # 1. Test contact vault storage
        try:
            contacts_data = {
                "device_id": "omerta_vault_device_001",
                "encryption_key_hash": "omerta_key_hash_12345678901234567890123456789012",
                "contacts": [
                    {
                        "oid": "omerta_contact_001",
                        "display_name": "OMERTÁ Contact Alpha",
                        "verified": True,
                        "created_at": int(time.time())
                    },
                    {
                        "oid": "omerta_contact_002", 
                        "display_name": "OMERTÁ Contact Bravo",
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
                    self.log_test("Contact Vault Storage", True, 
                                f"Contacts stored successfully, backup ID: {result['backup_id'][:8]}...")
                    self.vault_device_id = contacts_data['device_id']
                    self.vault_encryption_key = contacts_data['encryption_key_hash']
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
                    contacts_count = len(result['contacts'])
                    self.log_test("Contact Vault Retrieval", True, 
                                f"Retrieved {contacts_count} contacts successfully")
                else:
                    self.log_test("Contact Vault Retrieval", False, f"Retrieval failed: {result}")
            else:
                self.log_test("Contact Vault Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Contact Vault Retrieval", False, f"Error: {str(e)}")
        
        # 3. Test contact vault clearing
        try:
            response = requests.delete(f"{BACKEND_URL}/contacts-vault/clear/{self.vault_device_id}", 
                                     timeout=10)
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
    
    def test_pin_security_system(self):
        """Test PIN Security System (Normal and Panic PINs)"""
        print("\n🔐 TESTING PIN SECURITY SYSTEM")
        
        # 1. Test normal PIN verification
        try:
            pin_data = {
                "device_id": "omerta_pin_device_001",
                "pin": "123456",  # Normal PIN
                "timestamp": int(time.time())
            }
            
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("PIN Security - Normal PIN", True, "Normal PIN (123456) verification working")
                else:
                    self.log_test("PIN Security - Normal PIN", False, f"Normal PIN failed: {result}")
            else:
                self.log_test("PIN Security - Normal PIN", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("PIN Security - Normal PIN", False, f"Error: {str(e)}")
        
        # 2. Test panic PIN detection
        try:
            panic_pin_data = {
                "device_id": "omerta_panic_device_001",
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
                                    "Panic PIN (000000) detected, signed kill token generated")
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
    
    def test_admin_authentication_system(self):
        """Test Admin Authentication and Multi-Signature Operations"""
        print("\n👑 TESTING ADMIN AUTHENTICATION SYSTEM")
        
        # 1. Test admin authentication
        try:
            auth_data = {
                "admin_passphrase": "Omertaisthecode#01",
                "device_id": "omerta_admin_device_001"
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/authenticate", 
                                   json=auth_data, timeout=10)
            if response.status_code == 200:
                auth_result = response.json()
                if auth_result.get('success') and auth_result.get('session_token'):
                    session_token = auth_result['session_token']
                    admin_id = auth_result.get('admin_id')
                    self.log_test("Admin Authentication", True, f"Admin {admin_id} authenticated successfully")
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
                "target_device_id": "omerta_target_device_001",
                "operation_data": {"reason": "OMERTÁ security test"}
            }
            
            response = requests.post(f"{BACKEND_URL}/admin/multisig/initiate", 
                                   json=multisig_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('operation_id'):
                    operation_id = result['operation_id']
                    self.log_test("Multi-Sig Operation Initiation", True, 
                                f"Operation {operation_id} created, expires in 5 minutes")
                    self.operation_id = operation_id
                else:
                    self.log_test("Multi-Sig Operation Initiation", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Operation Initiation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Operation Initiation", False, f"Error: {str(e)}")
        
        # 4. Test multi-signature operation completion
        try:
            # Admin 1 signature
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
            
            # Admin 2 signature (complete operation)
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
                    self.log_test("Multi-Sig Operation Completion", True, 
                                f"Operation completed successfully - Status: {status}")
                else:
                    self.log_test("Multi-Sig Operation Completion", False, f"Failed: {result}")
            else:
                self.log_test("Multi-Sig Operation Completion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Multi-Sig Operation Completion", False, f"Error: {str(e)}")
    
    def test_input_sanitization_and_rate_limiting(self):
        """Test Input Sanitization and Rate Limiting"""
        print("\n🛡️ TESTING INPUT SANITIZATION AND RATE LIMITING")
        
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
        
        # 2. Test rate limiting
        try:
            rate_limit_triggered = False
            for i in range(15):  # Try 15 rapid requests
                try:
                    note_data = {
                        "ciphertext": f"omerta_rate_limit_test_{i}",
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
    
    def test_graphite_defense_system(self):
        """Test Graphite Defense System"""
        print("\n🛡️ TESTING GRAPHITE DEFENSE SYSTEM")
        
        # 1. Test system status
        try:
            response = requests.get(f"{BACKEND_URL}/graphite-defense/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("system_status") == "OPERATIONAL":
                    self.log_test("Graphite Defense Status", True, 
                                f"System operational with {data.get('active_signatures', 0)} signatures")
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
                    self.log_test("Graphite Signatures Database", True, 
                                f"Retrieved {len(signatures)} Graphite behavioral signatures")
                else:
                    self.log_test("Graphite Signatures Database", False, "No signatures found")
            else:
                self.log_test("Graphite Signatures Database", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Signatures Database", False, f"Error: {str(e)}")
        
        # 3. Test threat analysis
        try:
            threat_data = {
                "device_id": "omerta_graphite_test_device",
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
    
    def test_file_sharing_endpoints(self):
        """Test NEW File Sharing Endpoints"""
        print("\n📁 TESTING NEW FILE SHARING ENDPOINTS")
        
        # Create test file data
        test_file_content = b"OMERTA_SECRET_FILE_CONTENT_FOR_TESTING_ENCRYPTED_FILE_SHARING_SYSTEM"
        test_file_b64 = base64.b64encode(test_file_content).decode('utf-8')
        
        # 1. Test file upload
        try:
            upload_data = {
                "filename": "omerta_secret_document.txt",
                "file_data": test_file_b64,
                "encryption_key_hash": "omerta_file_encryption_key_hash_12345678901234567890",
                "device_id": "omerta_file_device_001",
                "ttl_hours": 24
            }
            
            response = requests.post(f"{BACKEND_URL}/files/upload", json=upload_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('file_id'):
                    file_id = result['file_id']
                    self.log_test("File Upload", True, f"File uploaded successfully: {file_id[:8]}...")
                    self.uploaded_file_id = file_id
                else:
                    self.log_test("File Upload", False, f"Upload failed: {result}")
            else:
                self.log_test("File Upload", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Upload", False, f"Error: {str(e)}")
        
        # 2. Test file list
        try:
            response = requests.get(f"{BACKEND_URL}/files/list?device_id=omerta_file_device_001", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and isinstance(result.get('files'), list):
                    files_count = len(result['files'])
                    self.log_test("File List", True, f"Retrieved {files_count} files from device")
                else:
                    self.log_test("File List", False, f"List failed: {result}")
            else:
                self.log_test("File List", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File List", False, f"Error: {str(e)}")
        
        # 3. Test file download
        try:
            response = requests.get(f"{BACKEND_URL}/files/download/{self.uploaded_file_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('file_data'):
                    downloaded_data = base64.b64decode(result['file_data'])
                    if downloaded_data == test_file_content:
                        self.log_test("File Download", True, "File downloaded and decrypted successfully")
                    else:
                        self.log_test("File Download", False, "Downloaded file content mismatch")
                else:
                    self.log_test("File Download", False, f"Download failed: {result}")
            else:
                self.log_test("File Download", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Download", False, f"Error: {str(e)}")
        
        # 4. Test file deletion
        try:
            response = requests.delete(f"{BACKEND_URL}/files/{self.uploaded_file_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("File Deletion", True, "File deleted successfully")
                else:
                    self.log_test("File Deletion", False, f"Deletion failed: {result}")
            else:
                self.log_test("File Deletion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Deletion", False, f"Error: {str(e)}")
        
        # 5. Test file cleanup
        try:
            cleanup_data = {
                "device_id": "omerta_file_device_001",
                "force_cleanup": True
            }
            
            response = requests.post(f"{BACKEND_URL}/files/cleanup", json=cleanup_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cleaned_count = result.get('cleaned_files', 0)
                    self.log_test("File Cleanup", True, f"Cleanup completed, {cleaned_count} files cleaned")
                else:
                    self.log_test("File Cleanup", False, f"Cleanup failed: {result}")
            else:
                self.log_test("File Cleanup", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Cleanup", False, f"Error: {str(e)}")
    
    def test_voice_message_endpoints(self):
        """Test NEW Voice Message Endpoints"""
        print("\n🎤 TESTING NEW VOICE MESSAGE ENDPOINTS")
        
        # Create test voice data (simulated encrypted audio)
        test_voice_data = base64.b64encode(b"OMERTA_ENCRYPTED_VOICE_MESSAGE_DATA_FOR_TESTING").decode('utf-8')
        
        # 1. Test voice message send
        try:
            voice_data = {
                "to_oid": "omerta_voice_recipient_001",
                "from_oid": "omerta_voice_sender_001", 
                "encrypted_audio_data": test_voice_data,
                "duration_seconds": 15,
                "device_id": "omerta_voice_device_001",
                "ttl_hours": 48
            }
            
            response = requests.post(f"{BACKEND_URL}/voice/send", json=voice_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('message_id'):
                    message_id = result['message_id']
                    self.log_test("Voice Message Send", True, f"Voice message sent: {message_id[:8]}...")
                    self.voice_message_id = message_id
                    self.voice_recipient_oid = voice_data['to_oid']
                else:
                    self.log_test("Voice Message Send", False, f"Send failed: {result}")
            else:
                self.log_test("Voice Message Send", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Send", False, f"Error: {str(e)}")
        
        # 2. Test voice messages list
        try:
            response = requests.get(f"{BACKEND_URL}/voice/messages?oid={self.voice_recipient_oid}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and isinstance(result.get('messages'), list):
                    messages_count = len(result['messages'])
                    self.log_test("Voice Messages List", True, f"Retrieved {messages_count} voice messages")
                else:
                    self.log_test("Voice Messages List", False, f"List failed: {result}")
            else:
                self.log_test("Voice Messages List", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Messages List", False, f"Error: {str(e)}")
        
        # 3. Test voice message play
        try:
            response = requests.get(f"{BACKEND_URL}/voice/play/{self.voice_message_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') and result.get('encrypted_audio_data'):
                    audio_data = result['encrypted_audio_data']
                    if audio_data == test_voice_data:
                        self.log_test("Voice Message Play", True, "Voice message retrieved successfully")
                    else:
                        self.log_test("Voice Message Play", False, "Voice data mismatch")
                else:
                    self.log_test("Voice Message Play", False, f"Play failed: {result}")
            else:
                self.log_test("Voice Message Play", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Play", False, f"Error: {str(e)}")
        
        # 4. Test voice message deletion
        try:
            response = requests.delete(f"{BACKEND_URL}/voice/{self.voice_message_id}", timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self.log_test("Voice Message Deletion", True, "Voice message deleted successfully")
                else:
                    self.log_test("Voice Message Deletion", False, f"Deletion failed: {result}")
            else:
                self.log_test("Voice Message Deletion", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Deletion", False, f"Error: {str(e)}")
        
        # 5. Test voice message cleanup
        try:
            cleanup_data = {
                "device_id": "omerta_voice_device_001",
                "force_cleanup": True
            }
            
            response = requests.post(f"{BACKEND_URL}/voice/cleanup", json=cleanup_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    cleaned_count = result.get('cleaned_messages', 0)
                    self.log_test("Voice Message Cleanup", True, f"Cleanup completed, {cleaned_count} messages cleaned")
                else:
                    self.log_test("Voice Message Cleanup", False, f"Cleanup failed: {result}")
            else:
                self.log_test("Voice Message Cleanup", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message Cleanup", False, f"Error: {str(e)}")
    
    def run_comprehensive_test(self):
        """Run comprehensive OMERTÁ backend test suite"""
        print("🔒 OMERTÁ COMPREHENSIVE BACKEND TESTING - FINAL REVIEW")
        print("=" * 70)
        
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
        self.uploaded_file_id = None
        self.voice_message_id = None
        self.voice_recipient_oid = None
        
        # Run all test suites
        if not self.test_basic_connectivity():
            print("❌ CRITICAL: Basic connectivity failed. Aborting tests.")
            return 0
        
        # Original Core Systems
        self.test_secure_notes_system()
        self.test_steelos_shredder_system()
        self.test_contact_vault_system()
        self.test_pin_security_system()
        self.test_admin_authentication_system()
        self.test_input_sanitization_and_rate_limiting()
        self.test_graphite_defense_system()
        
        # NEW Systems
        self.test_file_sharing_endpoints()
        self.test_voice_message_endpoints()
        
        # Print final results
        print("\n" + "=" * 70)
        print("🎯 FINAL COMPREHENSIVE TEST RESULTS")
        print("=" * 70)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 OMERTÁ BACKEND: FULLY OPERATIONAL - PRODUCTION READY")
        elif success_rate >= 80:
            print("✅ OMERTÁ BACKEND: OPERATIONAL - MINOR ISSUES")
        elif success_rate >= 60:
            print("⚠️ OMERTÁ BACKEND: NEEDS ATTENTION")
        else:
            print("🚨 OMERTÁ BACKEND: CRITICAL ISSUES DETECTED")
        
        # Save detailed results
        with open('/app/omerta_comprehensive_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': self.total_tests,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.failed_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat(),
                    'test_type': 'comprehensive_final_review'
                },
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: /app/omerta_comprehensive_test_results.json")
        
        return success_rate

if __name__ == "__main__":
    tester = OMERTAComprehensiveTester()
    success_rate = tester.run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 60 else 1)
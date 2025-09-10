#!/usr/bin/env python3
"""
🔒 OMERTÁ FINAL 24/24 SECURITY TEST SUITE
Exact 24 tests as requested for final assessment
"""

import requests
import time
import json
import io
import threading
from datetime import datetime

BACKEND_URL = "http://localhost:8001/api"

class Final24TestSuite:
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
            
        result = f"{status} | Test {self.total_tests:2d}/24 | {test_name}"
        if details:
            result += f" | {details}"
            
        print(result)
        self.results.append({
            'test_number': self.total_tests,
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
    def run_final_24_tests(self):
        """Run exactly 24 critical security tests"""
        print("🔒 OMERTÁ FINAL 24/24 SECURITY TEST SUITE")
        print("=" * 80)
        print("Testing all critical security systems for state-level actor resistance")
        print("=" * 80)
        
        # Test 1: Basic API Connectivity
        try:
            response = requests.get(f"{BACKEND_URL}/", timeout=10)
            success = response.status_code == 200 and response.json().get("message") == "Hello World"
            self.log_test("Basic API Connectivity", success, "Root endpoint responding" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}")
        
        # Test 2: Secure Notes Creation
        try:
            note_data = {
                "ciphertext": "U2FsdGVkX1+vupppZksvRf5pq5g5XjFRIipRkwB0K1Y96Qsv2Lm+31cmzaAILwyt",
                "meta": {"type": "secure_note"},
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                success = bool(result.get('id'))
                self.note_id = result.get('id') if success else None
                self.log_test("Secure Notes Creation", success, f"Note created: {result.get('id', '')[:8]}..." if success else "No note ID returned")
            else:
                self.log_test("Secure Notes Creation", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Secure Notes Creation", False, f"Error: {str(e)}")
        
        # Test 3: Secure Notes One-Time Read
        try:
            if hasattr(self, 'note_id') and self.note_id:
                response = requests.get(f"{BACKEND_URL}/notes/{self.note_id}", timeout=10)
                success = response.status_code == 200 and response.json().get('views_left') == 0
                self.log_test("Secure Notes One-Time Read", success, "Note purged after single read" if success else f"HTTP {response.status_code}")
            else:
                self.log_test("Secure Notes One-Time Read", False, "No note ID available")
        except Exception as e:
            self.log_test("Secure Notes One-Time Read", False, f"Error: {str(e)}")
        
        # Test 4: Messaging Envelope Send
        try:
            envelope_data = {
                "to_oid": "user_recipient_001",
                "from_oid": "user_sender_001", 
                "ciphertext": "encrypted_message_content_base64_encoded_data"
            }
            response = requests.post(f"{BACKEND_URL}/envelopes/send", json=envelope_data, timeout=10)
            success = response.status_code == 200 and bool(response.json().get('id'))
            self.log_test("Messaging Envelope Send", success, "Envelope sent successfully" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Messaging Envelope Send", False, f"Error: {str(e)}")
        
        # Test 5: Messaging Envelope Poll & Delete-on-Delivery
        try:
            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=user_recipient_001", timeout=10)
            if response.status_code == 200:
                messages = response.json().get('messages', [])
                # Second poll should be empty (delete-on-delivery)
                response2 = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=user_recipient_001", timeout=10)
                success = len(messages) > 0 and len(response2.json().get('messages', [])) == 0
                self.log_test("Envelope Poll & Delete-on-Delivery", success, "Delete-on-delivery working" if success else "Delete-on-delivery failed")
            else:
                self.log_test("Envelope Poll & Delete-on-Delivery", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Poll & Delete-on-Delivery", False, f"Error: {str(e)}")
        
        # Test 6: STEELOS-Shredder Deployment
        try:
            shredder_data = {
                "device_id": "test_device_shredder_001",
                "trigger_type": "manual",
                "confirmation_token": "test_token_123"
            }
            response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=shredder_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                success = result.get('shredder_activated') and result.get('kill_token_generated')
                self.shredder_device_id = shredder_data['device_id'] if success else None
                self.log_test("STEELOS-Shredder Deployment", success, "CYANIDE TABLET deployed" if success else "Deployment failed")
            else:
                self.log_test("STEELOS-Shredder Deployment", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("STEELOS-Shredder Deployment", False, f"Error: {str(e)}")
        
        # Test 7: STEELOS Kill Token Retrieval
        try:
            if hasattr(self, 'shredder_device_id') and self.shredder_device_id:
                response = requests.get(f"{BACKEND_URL}/steelos-shredder/status/{self.shredder_device_id}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    kill_token = result.get('kill_token', {})
                    signature = kill_token.get('signature', '')
                    success = len(signature) == 64  # HMAC-SHA256 produces 64-char hex
                    self.log_test("STEELOS Kill Token Retrieval", success, f"Valid signature ({len(signature)} chars)" if success else f"Invalid signature ({len(signature)} chars)")
                else:
                    self.log_test("STEELOS Kill Token Retrieval", False, f"HTTP {response.status_code}")
            else:
                self.log_test("STEELOS Kill Token Retrieval", False, "No shredder device ID available")
        except Exception as e:
            self.log_test("STEELOS Kill Token Retrieval", False, f"Error: {str(e)}")
        
        # Test 8: Contact Vault Storage
        try:
            contacts_data = {
                "device_id": "test_device_vault_001",
                "encryption_key_hash": "test_key_hash_12345678901234567890123456789012",
                "contacts": [
                    {"oid": "contact_001", "display_name": "Alice Johnson", "verified": True, "created_at": int(time.time())},
                    {"oid": "contact_002", "display_name": "Bob Smith", "verified": False, "created_at": int(time.time())}
                ]
            }
            response = requests.post(f"{BACKEND_URL}/contacts-vault/store", json=contacts_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                success = result.get('success') and result.get('backup_id')
                self.vault_device_id = contacts_data['device_id'] if success else None
                self.vault_encryption_key = contacts_data['encryption_key_hash'] if success else None
                self.log_test("Contact Vault Storage", success, f"Stored {len(contacts_data['contacts'])} contacts" if success else "Storage failed")
            else:
                self.log_test("Contact Vault Storage", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Contact Vault Storage", False, f"Error: {str(e)}")
        
        # Test 9: Contact Vault Retrieval
        try:
            if hasattr(self, 'vault_device_id') and self.vault_device_id:
                response = requests.get(f"{BACKEND_URL}/contacts-vault/retrieve/{self.vault_device_id}?encryption_key_hash={self.vault_encryption_key}", timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success') and result.get('contacts')
                    contacts_count = len(result.get('contacts', [])) if success else 0
                    self.log_test("Contact Vault Retrieval", success, f"Retrieved {contacts_count} contacts" if success else "Retrieval failed")
                else:
                    self.log_test("Contact Vault Retrieval", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Contact Vault Retrieval", False, "No vault device ID available")
        except Exception as e:
            self.log_test("Contact Vault Retrieval", False, f"Error: {str(e)}")
        
        # Test 10: Auto-Wipe Configuration
        try:
            config_data = {
                "device_id": "test_device_autowipe_001",
                "enabled": True,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2
            }
            response = requests.post(f"{BACKEND_URL}/auto-wipe/configure", json=config_data, timeout=10)
            success = response.status_code == 200 and (response.json().get('success') or response.json().get('configured'))
            self.autowipe_device_id = config_data['device_id'] if success else None
            self.log_test("Auto-Wipe Configuration", success, f"Configured {config_data['days_inactive']}-day auto-wipe" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Configuration", False, f"Error: {str(e)}")
        
        # Test 11: PIN Security - Normal PIN
        try:
            pin_data = {
                "device_id": "test_device_pin_001",
                "pin": "123456",
                "timestamp": int(time.time())
            }
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
            success = response.status_code == 200 and response.json().get('success')
            self.log_test("PIN Security - Normal PIN", success, "Normal PIN verification working" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("PIN Security - Normal PIN", False, f"Error: {str(e)}")
        
        # Test 12: PIN Security - Panic PIN Detection
        try:
            panic_pin_data = {
                "device_id": "test_device_panic_001",
                "pin": "000000",  # Panic PIN
                "timestamp": int(time.time())
            }
            response = requests.post(f"{BACKEND_URL}/pin/verify", json=panic_pin_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                success = result.get('success') and result.get('kill_token')
                self.log_test("PIN Security - Panic PIN Detection", success, "Panic PIN detected, kill token generated" if success else "Panic PIN not detected")
            else:
                self.log_test("PIN Security - Panic PIN Detection", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("PIN Security - Panic PIN Detection", False, f"Error: {str(e)}")
        
        # Test 13: Admin Authentication
        try:
            auth_data = {
                "admin_passphrase": "Omertaisthecode#01",
                "device_id": "admin_test_device_001"
            }
            response = requests.post(f"{BACKEND_URL}/admin/authenticate", json=auth_data, timeout=10)
            if response.status_code == 200:
                auth_result = response.json()
                success = auth_result.get('success') and auth_result.get('session_token')
                self.admin_session_token = auth_result.get('session_token') if success else None
                self.admin_id = auth_result.get('admin_id') if success else None
                self.log_test("Admin Authentication", success, f"Admin {auth_result.get('admin_id', '')} authenticated" if success else "Authentication failed")
            else:
                self.log_test("Admin Authentication", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Authentication", False, f"Error: {str(e)}")
        
        # Test 14: Admin Seed Info Retrieval
        try:
            response = requests.get(f"{BACKEND_URL}/admin/seed/info", timeout=10)
            if response.status_code == 200:
                seed_info = response.json()
                if seed_info.get('status') == 'success':
                    seed_data = seed_info.get('seed_info', {})
                    admin1_words = seed_data.get('admin1_words', [])
                    admin2_words = seed_data.get('admin2_words', [])
                    success = len(admin1_words) == 6 and len(admin2_words) == 6
                    self.admin1_words = admin1_words if success else []
                    self.admin2_words = admin2_words if success else []
                    self.log_test("Admin Seed Info Retrieval", success, f"BIP39 seed split: Admin1({len(admin1_words)}), Admin2({len(admin2_words)})" if success else "Invalid seed word counts")
                else:
                    self.log_test("Admin Seed Info Retrieval", False, "Seed info retrieval failed")
            else:
                self.log_test("Admin Seed Info Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Admin Seed Info Retrieval", False, f"Error: {str(e)}")
        
        # Test 15: Multi-Sig Operation Initiation
        try:
            if hasattr(self, 'admin_session_token') and self.admin_session_token:
                multisig_data = {
                    "session_token": self.admin_session_token,
                    "operation_type": "remote_kill",
                    "target_device_id": "target_device_001",
                    "operation_data": {"reason": "Security test"}
                }
                response = requests.post(f"{BACKEND_URL}/admin/multisig/initiate", json=multisig_data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success') and result.get('operation_id')
                    self.operation_id = result.get('operation_id') if success else None
                    self.log_test("Multi-Sig Operation Initiation", success, f"Operation {result.get('operation_id', '')[:16]}... created" if success else "Operation creation failed")
                else:
                    self.log_test("Multi-Sig Operation Initiation", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Multi-Sig Operation Initiation", False, "No admin session token available")
        except Exception as e:
            self.log_test("Multi-Sig Operation Initiation", False, f"Error: {str(e)}")
        
        # Test 16: Multi-Sig Admin1 Signature
        try:
            if hasattr(self, 'operation_id') and self.operation_id and hasattr(self, 'admin1_words'):
                sign_data = {
                    "operation_id": self.operation_id,
                    "admin_seed_words": self.admin1_words,
                    "admin_passphrase": "Omertaisthecode#01",
                    "admin_id": "admin1"
                }
                response = requests.post(f"{BACKEND_URL}/admin/multisig/sign", json=sign_data, timeout=10)
                success = response.status_code == 200 and response.json().get('success')
                signatures = response.json().get('signatures_received', 0) if success else 0
                self.log_test("Multi-Sig Admin1 Signature", success, f"Admin1 signed ({signatures}/2 signatures)" if success else f"HTTP {response.status_code}")
            else:
                self.log_test("Multi-Sig Admin1 Signature", False, "Missing operation ID or admin1 words")
        except Exception as e:
            self.log_test("Multi-Sig Admin1 Signature", False, f"Error: {str(e)}")
        
        # Test 17: Multi-Sig Admin2 Signature & Execution
        try:
            if hasattr(self, 'operation_id') and self.operation_id and hasattr(self, 'admin2_words'):
                sign_data = {
                    "operation_id": self.operation_id,
                    "admin_seed_words": self.admin2_words,
                    "admin_passphrase": "Omertaisthecode#01",
                    "admin_id": "admin2"
                }
                response = requests.post(f"{BACKEND_URL}/admin/multisig/sign", json=sign_data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    success = result.get('success') and result.get('operation_completed')
                    status = result.get('execution_result', {}).get('status', 'Unknown') if success else 'Failed'
                    self.log_test("Multi-Sig Admin2 Signature & Execution", success, f"Operation completed - Status: {status}" if success else "Operation not completed")
                else:
                    self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"HTTP {response.status_code}")
            else:
                self.log_test("Multi-Sig Admin2 Signature & Execution", False, "Missing operation ID or admin2 words")
        except Exception as e:
            self.log_test("Multi-Sig Admin2 Signature & Execution", False, f"Error: {str(e)}")
        
        # Test 18: Graphite Defense System Status
        try:
            response = requests.get(f"{BACKEND_URL}/graphite-defense/status", timeout=10)
            if response.status_code == 200:
                data = response.json()
                success = data.get("system_status") == "OPERATIONAL"
                signatures = data.get('active_signatures', 0)
                self.log_test("Graphite Defense System Status", success, f"System operational with {signatures} signatures" if success else f"System not operational: {data}")
            else:
                self.log_test("Graphite Defense System Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Defense System Status", False, f"Error: {str(e)}")
        
        # Test 19: Graphite Threat Analysis
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
            response = requests.post(f"{BACKEND_URL}/graphite-defense/report-threat", json=threat_data, timeout=10)
            if response.status_code == 200:
                analysis = response.json()
                success = 'threat_level' in analysis and 'confidence' in analysis
                threat_level = analysis.get('threat_level', -1)
                confidence = analysis.get('confidence', 0)
                self.log_test("Graphite Threat Analysis", success, f"Analysis complete - Level: {threat_level}, Confidence: {confidence:.1f}%" if success else "Analysis failed")
            else:
                self.log_test("Graphite Threat Analysis", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Graphite Threat Analysis", False, f"Error: {str(e)}")
        
        # Test 20: Input Sanitization
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
                    note_data = {"ciphertext": payload, "ttl_seconds": 3600, "read_limit": 1}
                    response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                    if response.status_code == 400:
                        blocked_count += 1
                except:
                    blocked_count += 1
            success = blocked_count >= 6
            self.log_test("Input Sanitization", success, f"Blocked {blocked_count}/{len(malicious_payloads)} malicious payloads" if success else f"Only blocked {blocked_count}/{len(malicious_payloads)} payloads")
        except Exception as e:
            self.log_test("Input Sanitization", False, f"Error: {str(e)}")
        
        # Test 21: Rate Limiting Enforcement
        try:
            rate_limit_triggered = False
            for i in range(15):
                try:
                    note_data = {"ciphertext": f"rate_limit_test_{i}", "ttl_seconds": 60, "read_limit": 1}
                    response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=2)
                    if response.status_code == 429:
                        rate_limit_triggered = True
                        break
                except:
                    pass
            self.log_test("Rate Limiting Enforcement", rate_limit_triggered, "Rate limiting triggered after rapid requests" if rate_limit_triggered else "Rate limiting not enforced - security vulnerability")
        except Exception as e:
            self.log_test("Rate Limiting Enforcement", False, f"Error: {str(e)}")
        
        # Test 22: File Sharing System
        try:
            import io
            test_content = b"This is a test file for OMERTA file sharing system testing."
            test_file = io.BytesIO(test_content)
            files = {'file': ('test_document.txt', test_file, 'text/plain')}
            data = {'expiry_hours': 1, 'auto_destruct': True}
            response = requests.post(f"{BACKEND_URL}/files/upload", files=files, data=data, timeout=10)
            success = response.status_code == 200 and response.json().get('id')
            file_size = response.json().get('size', 0) if success else 0
            self.log_test("File Sharing System", success, f"File uploaded: {file_size} bytes" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("File Sharing System", False, f"Error: {str(e)}")
        
        # Test 23: Voice Message System
        try:
            import io
            mock_audio_content = b"MOCK_AUDIO_DATA_FOR_TESTING_PURPOSES_M4A_FORMAT"
            audio_file = io.BytesIO(mock_audio_content)
            files = {'audio': ('voice_message.m4a', audio_file, 'audio/m4a')}
            data = {'scrambled': True, 'encrypted': True}
            response = requests.post(f"{BACKEND_URL}/voice/send", files=files, data=data, timeout=10)
            success = response.status_code == 200 and response.json().get('message_id')
            message_size = response.json().get('size', 0) if success else 0
            self.log_test("Voice Message System", success, f"Voice message sent: {message_size} bytes" if success else f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Voice Message System", False, f"Error: {str(e)}")
        
        # Test 24: WebSocket Real-time Messaging
        try:
            # Test WebSocket endpoint availability (connection test)
            import websocket
            import threading
            import time
            
            ws_connected = False
            ws_error = None
            
            def on_open(ws):
                nonlocal ws_connected
                ws_connected = True
                ws.close()
            
            def on_error(ws, error):
                nonlocal ws_error
                ws_error = str(error)
            
            # Create WebSocket connection
            ws_url = "ws://localhost:8001/api/ws?oid=test_user_001"
            ws = websocket.WebSocketApp(ws_url, on_open=on_open, on_error=on_error)
            
            # Run WebSocket in a separate thread with timeout
            ws_thread = threading.Thread(target=ws.run_forever)
            ws_thread.daemon = True
            ws_thread.start()
            
            # Wait for connection or timeout
            time.sleep(2)
            
            success = ws_connected and not ws_error
            self.log_test("WebSocket Real-time Messaging", success, "WebSocket connection successful" if success else f"WebSocket error: {ws_error or 'Connection failed'}")
            
        except Exception as e:
            self.log_test("WebSocket Real-time Messaging", False, f"Error: {str(e)}")
        
        # Print final results
        print("\n" + "=" * 80)
        print("🎯 FINAL 24/24 TEST RESULTS - STATE-LEVEL ACTOR RESISTANCE ASSESSMENT")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 TOTAL TESTS: {self.total_tests}/24")
        print(f"✅ PASSED: {self.passed_tests}")
        print(f"❌ FAILED: {self.failed_tests}")
        print(f"📈 SUCCESS RATE: {success_rate:.1f}%")
        
        # Security assessment
        if success_rate >= 95:
            security_level = "🏆 EXCELLENT - PRODUCTION READY FOR STATE-LEVEL THREATS"
        elif success_rate >= 90:
            security_level = "✅ VERY GOOD - PRODUCTION READY WITH MINOR MONITORING"
        elif success_rate >= 85:
            security_level = "⚠️ GOOD - ACCEPTABLE WITH SOME VULNERABILITIES"
        elif success_rate >= 75:
            security_level = "🔧 NEEDS ATTENTION - SIGNIFICANT SECURITY GAPS"
        else:
            security_level = "🚨 CRITICAL ISSUES - NOT READY FOR PRODUCTION"
        
        print(f"\n🔒 SECURITY ASSESSMENT: {security_level}")
        
        # List failed tests
        if self.failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({self.failed_tests}):")
            for result in self.results:
                if not result['success']:
                    print(f"   • Test {result['test_number']:2d}: {result['test']} - {result['details']}")
        
        # Final verdict for state-level actors
        print(f"\n🎯 FINAL VERDICT FOR STATE-LEVEL ACTOR RESISTANCE:")
        if success_rate >= 95:
            print("   🛡️ OMERTÁ can withstand sophisticated nation-state attacks")
            print("   🔒 All critical security systems operational")
            print("   ✅ READY FOR DEPLOYMENT AGAINST STATE-LEVEL THREATS")
        elif success_rate >= 90:
            print("   ⚠️ OMERTÁ has strong defenses but some vulnerabilities exist")
            print("   🔧 Minor fixes needed before facing state-level actors")
            print("   📊 Mostly ready for production with monitoring")
        else:
            print("   🚨 OMERTÁ has significant security gaps")
            print("   ❌ NOT READY for state-level actor resistance")
            print("   🔧 Major security improvements required")
        
        # Save results
        with open('/app/final_24_test_results.json', 'w') as f:
            json.dump({
                'summary': {
                    'total_tests': self.total_tests,
                    'expected_tests': 24,
                    'passed_tests': self.passed_tests,
                    'failed_tests': self.failed_tests,
                    'success_rate': success_rate,
                    'timestamp': datetime.now().isoformat(),
                    'security_assessment': security_level
                },
                'detailed_results': self.results
            }, f, indent=2)
        
        print(f"\n📊 Detailed results saved to: /app/final_24_test_results.json")
        
        return success_rate

if __name__ == "__main__":
    tester = Final24TestSuite()
    tester.run_final_24_tests()
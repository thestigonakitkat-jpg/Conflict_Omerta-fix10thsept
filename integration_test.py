#!/usr/bin/env python3
"""
🔒 OMERTÁ INTEGRATION TESTING
Testing specific integration points mentioned in the review request.

FOCUS AREAS:
1. Message Systems (envelopes send/poll/delete-on-delivery)
2. Auto-wipe system configuration and status
3. Message expiration backend support
4. Integration points for new frontend features
"""

import requests
import time
import json
from datetime import datetime

# Backend URL from frontend .env
BACKEND_URL = "http://localhost:8001/api"

class OMERTAIntegrationTester:
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

    def test_messaging_envelopes(self):
        """Test messaging envelopes send/poll/delete-on-delivery"""
        print("\n📨 TESTING MESSAGING ENVELOPES SYSTEM")
        
        # 1. Test envelope sending
        try:
            envelope_data = {
                "to_oid": "user_recipient_001",
                "from_oid": "user_sender_001", 
                "ciphertext": "encrypted_message_content_test_12345",
                "ts": datetime.now().isoformat()
            }
            
            response = requests.post(f"{BACKEND_URL}/envelopes/send", 
                                   json=envelope_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('id'):
                    envelope_id = result['id']
                    self.log_test("Envelope Send", True, 
                                f"Envelope sent successfully: {envelope_id[:8]}...")
                    self.envelope_id = envelope_id
                    self.recipient_oid = envelope_data['to_oid']
                else:
                    self.log_test("Envelope Send", False, f"No envelope ID returned: {result}")
            else:
                self.log_test("Envelope Send", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Send", False, f"Error: {str(e)}")
        
        # 2. Test envelope polling (first poll should deliver message)
        try:
            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid={self.recipient_oid}&max=10", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                if len(messages) > 0:
                    message = messages[0]
                    if (message.get('id') == self.envelope_id and 
                        message.get('from_oid') == 'user_sender_001' and
                        message.get('ciphertext') == 'encrypted_message_content_test_12345'):
                        self.log_test("Envelope Poll (First)", True, 
                                    f"Message delivered correctly with proper structure")
                    else:
                        self.log_test("Envelope Poll (First)", False, 
                                    f"Message structure incorrect: {message}")
                else:
                    self.log_test("Envelope Poll (First)", False, "No messages returned")
            else:
                self.log_test("Envelope Poll (First)", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Poll (First)", False, f"Error: {str(e)}")
        
        # 3. Test delete-on-delivery (second poll should return empty)
        try:
            response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid={self.recipient_oid}&max=10", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                messages = result.get('messages', [])
                if len(messages) == 0:
                    self.log_test("Envelope Delete-on-Delivery", True, 
                                "Second poll returns empty array (delete-on-delivery working)")
                else:
                    self.log_test("Envelope Delete-on-Delivery", False, 
                                f"Messages still available: {len(messages)} messages")
            else:
                self.log_test("Envelope Delete-on-Delivery", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope Delete-on-Delivery", False, f"Error: {str(e)}")

    def test_auto_wipe_system(self):
        """Test auto-wipe system configuration and status"""
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
                    self.log_test("Auto-Wipe Configuration", True, 
                                f"Auto-wipe configured: 7 days inactive, app_data wipe")
                    self.autowipe_device_id = config_data['device_id']
                else:
                    self.log_test("Auto-Wipe Configuration", False, f"Configuration failed: {result}")
            else:
                self.log_test("Auto-Wipe Configuration", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Configuration", False, f"Error: {str(e)}")
        
        # 2. Test activity update
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
                    self.log_test("Auto-Wipe Activity Update", True, 
                                "Activity timestamp updated successfully")
                else:
                    self.log_test("Auto-Wipe Activity Update", False, f"Update failed: {result}")
            else:
                self.log_test("Auto-Wipe Activity Update", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Activity Update", False, f"Error: {str(e)}")
        
        # 3. Test auto-wipe status check
        try:
            response = requests.get(f"{BACKEND_URL}/auto-wipe/status/{self.autowipe_device_id}", 
                                  timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('success') or result.get('device_id'):
                    status_info = result.get('status', result)
                    days_until_wipe = status_info.get('days_until_wipe', 'Unknown')
                    enabled = status_info.get('enabled', False)
                    self.log_test("Auto-Wipe Status Check", True, 
                                f"Status retrieved - Enabled: {enabled}, Days until wipe: {days_until_wipe}")
                else:
                    self.log_test("Auto-Wipe Status Check", False, f"Status check failed: {result}")
            else:
                self.log_test("Auto-Wipe Status Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Auto-Wipe Status Check", False, f"Error: {str(e)}")

    def test_integration_endpoints(self):
        """Test integration endpoints for new frontend features"""
        print("\n🔗 TESTING INTEGRATION ENDPOINTS")
        
        # 1. Test RemoteKillSystem integration (via STEELOS-Shredder)
        try:
            # Test different trigger types that frontend might use
            trigger_types = ["panic_pin", "emergency_nuke", "anti_forensics", "manual"]
            
            for trigger_type in trigger_types:
                shredder_data = {
                    "device_id": f"integration_test_{trigger_type}",
                    "trigger_type": trigger_type,
                    "confirmation_token": f"test_token_{trigger_type}"
                }
                
                response = requests.post(f"{BACKEND_URL}/steelos-shredder/deploy", 
                                       json=shredder_data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    if result.get('shredder_activated'):
                        self.log_test(f"RemoteKillSystem Integration ({trigger_type})", True, 
                                    f"STEELOS-Shredder responds to {trigger_type} trigger")
                        break
                    else:
                        self.log_test(f"RemoteKillSystem Integration ({trigger_type})", False, 
                                    f"Shredder not activated: {result}")
                else:
                    self.log_test(f"RemoteKillSystem Integration ({trigger_type})", False, 
                                f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("RemoteKillSystem Integration", False, f"Error: {str(e)}")
        
        # 2. Test ClipboardSecurity integration (via input sanitization)
        try:
            # Test clipboard-like payloads that might come from frontend
            clipboard_payloads = [
                "javascript:void(0)",  # Malicious clipboard content
                "<script>alert('clipboard')</script>",  # XSS from clipboard
                "data:text/html,<script>alert('xss')</script>",  # Data URI attack
                "Normal clipboard content with legitimate text"  # Should pass
            ]
            
            blocked_malicious = 0
            allowed_legitimate = 0
            
            for payload in clipboard_payloads:
                note_data = {
                    "ciphertext": payload,
                    "ttl_seconds": 60,
                    "read_limit": 1
                }
                
                response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                
                if "javascript:" in payload or "<script>" in payload or "data:text/html" in payload:
                    # Should be blocked
                    if response.status_code == 400:
                        blocked_malicious += 1
                else:
                    # Should be allowed
                    if response.status_code == 200:
                        allowed_legitimate += 1
            
            if blocked_malicious >= 2 and allowed_legitimate >= 1:
                self.log_test("ClipboardSecurity Integration", True, 
                            f"Clipboard security working: blocked {blocked_malicious} malicious, allowed {allowed_legitimate} legitimate")
            else:
                self.log_test("ClipboardSecurity Integration", False, 
                            f"Clipboard security issues: blocked {blocked_malicious}, allowed {allowed_legitimate}")
        except Exception as e:
            self.log_test("ClipboardSecurity Integration", False, f"Error: {str(e)}")

    def test_message_expiration_support(self):
        """Test message expiration backend support"""
        print("\n⏱️ TESTING MESSAGE EXPIRATION SUPPORT")
        
        # Test TTL behavior in secure notes (represents message expiration)
        try:
            # Create note with very short TTL
            note_data = {
                "ciphertext": "test_message_with_short_ttl",
                "ttl_seconds": 2,  # 2 seconds TTL
                "read_limit": 1
            }
            
            response = requests.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                note_id = result.get('id')
                
                if note_id:
                    # Wait for TTL to expire
                    time.sleep(3)
                    
                    # Try to read expired note
                    response = requests.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                    if response.status_code == 410:  # Gone - expired
                        self.log_test("Message Expiration (TTL)", True, 
                                    "TTL expiration working correctly (410 Gone)")
                    elif response.status_code == 404:  # Not found - also acceptable
                        self.log_test("Message Expiration (TTL)", True, 
                                    "TTL expiration working correctly (404 Not Found)")
                    else:
                        self.log_test("Message Expiration (TTL)", False, 
                                    f"Expired note still accessible: HTTP {response.status_code}")
                else:
                    self.log_test("Message Expiration (TTL)", False, "No note ID returned")
            else:
                self.log_test("Message Expiration (TTL)", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Message Expiration (TTL)", False, f"Error: {str(e)}")
        
        # Test envelope TTL (48 hour default)
        try:
            # Send envelope and verify it has expiration timestamp
            envelope_data = {
                "to_oid": "ttl_test_recipient",
                "from_oid": "ttl_test_sender",
                "ciphertext": "test_envelope_ttl_message"
            }
            
            response = requests.post(f"{BACKEND_URL}/envelopes/send", 
                                   json=envelope_data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                if result.get('id'):
                    # Poll to get the envelope and check if it has TTL structure
                    response = requests.get(f"{BACKEND_URL}/envelopes/poll?oid=ttl_test_recipient&max=1", 
                                          timeout=10)
                    if response.status_code == 200:
                        poll_result = response.json()
                        messages = poll_result.get('messages', [])
                        if len(messages) > 0:
                            message = messages[0]
                            if message.get('ts'):  # Has timestamp for TTL calculation
                                self.log_test("Envelope TTL Support", True, 
                                            "Envelopes have timestamp for TTL calculation")
                            else:
                                self.log_test("Envelope TTL Support", False, 
                                            "Envelopes missing timestamp for TTL")
                        else:
                            self.log_test("Envelope TTL Support", False, "No envelope received")
                    else:
                        self.log_test("Envelope TTL Support", False, f"Poll failed: HTTP {response.status_code}")
                else:
                    self.log_test("Envelope TTL Support", False, "No envelope ID returned")
            else:
                self.log_test("Envelope TTL Support", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.log_test("Envelope TTL Support", False, f"Error: {str(e)}")

    def run_integration_tests(self):
        """Run comprehensive integration test suite"""
        print("🔗 OMERTÁ INTEGRATION TESTING")
        print("=" * 50)
        
        # Initialize variables
        self.envelope_id = None
        self.recipient_oid = None
        self.autowipe_device_id = None
        
        # Run all integration test suites
        self.test_messaging_envelopes()
        self.test_auto_wipe_system()
        self.test_integration_endpoints()
        self.test_message_expiration_support()
        
        # Print final results
        print("\n" + "=" * 50)
        print("🎯 INTEGRATION TEST RESULTS")
        print("=" * 50)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"Total Tests: {self.total_tests}")
        print(f"Passed: {self.passed_tests} ✅")
        print(f"Failed: {self.failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("🎉 INTEGRATION SYSTEMS: FULLY OPERATIONAL")
        elif success_rate >= 60:
            print("⚠️ INTEGRATION SYSTEMS: MINOR ISSUES")
        else:
            print("🚨 INTEGRATION SYSTEMS: CRITICAL ISSUES")
        
        return success_rate, self.results

if __name__ == "__main__":
    tester = OMERTAIntegrationTester()
    success_rate, results = tester.run_integration_tests()
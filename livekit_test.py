#!/usr/bin/env python3
"""
LiveKit Video Calling System Test Suite for OMERTÀ
Tests all LiveKit endpoints with security validation and rate limiting
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List

# Configuration
BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

class LiveKitTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_rooms = []
        self.generated_sessions = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
    
    def test_livekit_token_generation(self):
        """Test POST /api/livekit/token endpoint"""
        print("\n🎥 Testing LiveKit Token Generation...")
        
        # Test 1: Valid token request
        try:
            payload = {
                "room_name": f"test-room-{uuid.uuid4().hex[:8]}",
                "participant_name": "TestUser",
                "metadata": {"test": True},
                "ttl_hours": 2
            }
            
            response = self.session.post(f"{BACKEND_URL}/livekit/token", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["token", "ws_url", "session_id", "room_name", "participant_identity", "expires_at"]
                
                if all(field in data for field in required_fields):
                    self.generated_sessions.append(data["session_id"])
                    self.log_test("LiveKit Token Generation - Valid Request", True, 
                                f"Token generated with session_id: {data['session_id']}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("LiveKit Token Generation - Valid Request", False, 
                                f"Missing fields: {missing}")
            else:
                self.log_test("LiveKit Token Generation - Valid Request", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("LiveKit Token Generation - Valid Request", False, str(e))
        
        # Test 2: Invalid room name format
        try:
            payload = {
                "room_name": "invalid room name with spaces!@#",
                "participant_name": "TestUser"
            }
            
            response = self.session.post(f"{BACKEND_URL}/livekit/token", json=payload)
            
            if response.status_code == 400:
                self.log_test("LiveKit Token Generation - Invalid Room Name", True, 
                            "Correctly rejected invalid room name")
            else:
                self.log_test("LiveKit Token Generation - Invalid Room Name", False, 
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("LiveKit Token Generation - Invalid Room Name", False, str(e))
        
        # Test 3: Rate limiting (10/minute)
        try:
            rate_limit_exceeded = False
            for i in range(12):  # Try 12 requests to exceed 10/minute limit
                payload = {
                    "room_name": f"rate-test-{i}",
                    "participant_name": f"User{i}"
                }
                response = self.session.post(f"{BACKEND_URL}/livekit/token", json=payload)
                
                if response.status_code == 429:
                    rate_limit_exceeded = True
                    break
                time.sleep(0.1)  # Small delay between requests
            
            if rate_limit_exceeded:
                self.log_test("LiveKit Token Generation - Rate Limiting", True, 
                            "Rate limiting active (10/minute)")
            else:
                self.log_test("LiveKit Token Generation - Rate Limiting", False, 
                            "Rate limiting not enforced")
        except Exception as e:
            self.log_test("LiveKit Token Generation - Rate Limiting", False, str(e))
    
    def test_livekit_room_creation(self):
        """Test POST /api/livekit/room/create endpoint"""
        print("\n🏠 Testing LiveKit Room Creation...")
        
        # Test 1: Valid room creation
        try:
            room_name = f"test-room-{uuid.uuid4().hex[:8]}"
            payload = {
                "room_name": room_name,
                "max_participants": 6,
                "is_private": True,
                "requires_approval": False,
                "voice_scrambler_enabled": True,
                "face_blur_enabled": True,
                "recording_enabled": False
            }
            
            response = self.session.post(f"{BACKEND_URL}/livekit/room/create", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "room" in data:
                    self.created_rooms.append(room_name)
                    room_info = data["room"]
                    self.log_test("LiveKit Room Creation - Valid Request", True, 
                                f"Room created: {room_name} with {room_info.get('max_participants')} max participants")
                else:
                    self.log_test("LiveKit Room Creation - Valid Request", False, 
                                f"Invalid response format: {data}")
            else:
                self.log_test("LiveKit Room Creation - Valid Request", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("LiveKit Room Creation - Valid Request", False, str(e))
        
        # Test 2: Invalid room configuration
        try:
            payload = {
                "room_name": "invalid-config-room",
                "max_participants": 15,  # Exceeds limit of 10
                "is_private": True
            }
            
            response = self.session.post(f"{BACKEND_URL}/livekit/room/create", json=payload)
            
            if response.status_code == 400:
                self.log_test("LiveKit Room Creation - Invalid Config", True, 
                            "Correctly rejected invalid configuration")
            else:
                self.log_test("LiveKit Room Creation - Invalid Config", False, 
                            f"Expected 400, got {response.status_code}")
        except Exception as e:
            self.log_test("LiveKit Room Creation - Invalid Config", False, str(e))
        
        # Test 3: Rate limiting (5/minute)
        try:
            rate_limit_exceeded = False
            for i in range(7):  # Try 7 requests to exceed 5/minute limit
                payload = {
                    "room_name": f"rate-room-{i}",
                    "max_participants": 4
                }
                response = self.session.post(f"{BACKEND_URL}/livekit/room/create", json=payload)
                
                if response.status_code == 429:
                    rate_limit_exceeded = True
                    break
                time.sleep(0.1)
            
            if rate_limit_exceeded:
                self.log_test("LiveKit Room Creation - Rate Limiting", True, 
                            "Rate limiting active (5/minute)")
            else:
                self.log_test("LiveKit Room Creation - Rate Limiting", False, 
                            "Rate limiting not enforced")
        except Exception as e:
            self.log_test("LiveKit Room Creation - Rate Limiting", False, str(e))
    
    def test_livekit_room_listing(self):
        """Test GET /api/livekit/rooms endpoint"""
        print("\n📋 Testing LiveKit Room Listing...")
        
        # Test 1: List active rooms
        try:
            response = self.session.get(f"{BACKEND_URL}/livekit/rooms")
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and "rooms" in data:
                    rooms = data["rooms"]
                    self.log_test("LiveKit Room Listing - Valid Request", True, 
                                f"Retrieved {len(rooms)} active rooms")
                    
                    # Verify room information format
                    if rooms:
                        room = rooms[0]
                        required_fields = ["room_name", "created_at", "participant_count", "max_participants"]
                        if all(field in room for field in required_fields):
                            self.log_test("LiveKit Room Listing - Data Format", True, 
                                        "Room data format is correct")
                        else:
                            missing = [f for f in required_fields if f not in room]
                            self.log_test("LiveKit Room Listing - Data Format", False, 
                                        f"Missing fields: {missing}")
                else:
                    self.log_test("LiveKit Room Listing - Valid Request", False, 
                                f"Invalid response format: {data}")
            else:
                self.log_test("LiveKit Room Listing - Valid Request", False, 
                            f"HTTP {response.status_code}: {response.text}")
        except Exception as e:
            self.log_test("LiveKit Room Listing - Valid Request", False, str(e))
        
        # Test 2: Rate limiting (20/minute)
        try:
            rate_limit_exceeded = False
            for i in range(25):  # Try 25 requests to exceed 20/minute limit
                response = self.session.get(f"{BACKEND_URL}/livekit/rooms")
                
                if response.status_code == 429:
                    rate_limit_exceeded = True
                    break
                time.sleep(0.05)  # Small delay
            
            if rate_limit_exceeded:
                self.log_test("LiveKit Room Listing - Rate Limiting", True, 
                            "Rate limiting active (20/minute)")
            else:
                self.log_test("LiveKit Room Listing - Rate Limiting", False, 
                            "Rate limiting not enforced")
        except Exception as e:
            self.log_test("LiveKit Room Listing - Rate Limiting", False, str(e))
    
    def test_livekit_room_info(self):
        """Test GET /api/livekit/room/{room_name} endpoint"""
        print("\n🔍 Testing LiveKit Room Info Retrieval...")
        
        # Test 1: Get existing room info
        if self.created_rooms:
            try:
                room_name = self.created_rooms[0]
                response = self.session.get(f"{BACKEND_URL}/livekit/room/{room_name}")
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and "room" in data:
                        room_info = data["room"]
                        required_fields = ["room_name", "created_at", "participant_count", "max_participants"]
                        
                        if all(field in room_info for field in required_fields):
                            self.log_test("LiveKit Room Info - Existing Room", True, 
                                        f"Retrieved info for room: {room_name}")
                        else:
                            missing = [f for f in required_fields if f not in room_info]
                            self.log_test("LiveKit Room Info - Existing Room", False, 
                                        f"Missing fields: {missing}")
                    else:
                        self.log_test("LiveKit Room Info - Existing Room", False, 
                                    f"Invalid response format: {data}")
                else:
                    self.log_test("LiveKit Room Info - Existing Room", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("LiveKit Room Info - Existing Room", False, str(e))
        
        # Test 2: Non-existent room
        try:
            fake_room = f"non-existent-room-{uuid.uuid4().hex[:8]}"
            response = self.session.get(f"{BACKEND_URL}/livekit/room/{fake_room}")
            
            if response.status_code == 404:
                self.log_test("LiveKit Room Info - Non-existent Room", True, 
                            "Correctly returned 404 for non-existent room")
            else:
                self.log_test("LiveKit Room Info - Non-existent Room", False, 
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("LiveKit Room Info - Non-existent Room", False, str(e))
        
        # Test 3: Rate limiting (30/minute)
        try:
            rate_limit_exceeded = False
            test_room = self.created_rooms[0] if self.created_rooms else "test-room"
            
            for i in range(35):  # Try 35 requests to exceed 30/minute limit
                response = self.session.get(f"{BACKEND_URL}/livekit/room/{test_room}")
                
                if response.status_code == 429:
                    rate_limit_exceeded = True
                    break
                time.sleep(0.03)  # Small delay
            
            if rate_limit_exceeded:
                self.log_test("LiveKit Room Info - Rate Limiting", True, 
                            "Rate limiting active (30/minute)")
            else:
                self.log_test("LiveKit Room Info - Rate Limiting", False, 
                            "Rate limiting not enforced")
        except Exception as e:
            self.log_test("LiveKit Room Info - Rate Limiting", False, str(e))
    
    def test_livekit_session_management(self):
        """Test POST /api/livekit/session/end endpoint"""
        print("\n🔚 Testing LiveKit Session Management...")
        
        # Test 1: End valid session
        if self.generated_sessions:
            try:
                session_id = self.generated_sessions[0]
                payload = {"session_id": session_id}
                
                response = self.session.post(f"{BACKEND_URL}/livekit/session/end", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success":
                        self.log_test("LiveKit Session End - Valid Session", True, 
                                    f"Successfully ended session: {session_id}")
                    else:
                        self.log_test("LiveKit Session End - Valid Session", False, 
                                    f"Invalid response: {data}")
                else:
                    self.log_test("LiveKit Session End - Valid Session", False, 
                                f"HTTP {response.status_code}: {response.text}")
            except Exception as e:
                self.log_test("LiveKit Session End - Valid Session", False, str(e))
        
        # Test 2: End non-existent session
        try:
            fake_session = str(uuid.uuid4())
            payload = {"session_id": fake_session}
            
            response = self.session.post(f"{BACKEND_URL}/livekit/session/end", json=payload)
            
            if response.status_code == 404:
                self.log_test("LiveKit Session End - Invalid Session", True, 
                            "Correctly returned 404 for invalid session")
            else:
                self.log_test("LiveKit Session End - Invalid Session", False, 
                            f"Expected 404, got {response.status_code}")
        except Exception as e:
            self.log_test("LiveKit Session End - Invalid Session", False, str(e))
        
        # Test 3: Rate limiting (60/minute)
        try:
            rate_limit_exceeded = False
            
            for i in range(65):  # Try 65 requests to exceed 60/minute limit
                payload = {"session_id": str(uuid.uuid4())}
                response = self.session.post(f"{BACKEND_URL}/livekit/session/end", json=payload)
                
                if response.status_code == 429:
                    rate_limit_exceeded = True
                    break
                time.sleep(0.02)  # Small delay
            
            if rate_limit_exceeded:
                self.log_test("LiveKit Session End - Rate Limiting", True, 
                            "Rate limiting active (60/minute)")
            else:
                self.log_test("LiveKit Session End - Rate Limiting", False, 
                            "Rate limiting not enforced")
        except Exception as e:
            self.log_test("LiveKit Session End - Rate Limiting", False, str(e))
    
    def test_security_features(self):
        """Test security features across all LiveKit endpoints"""
        print("\n🔒 Testing LiveKit Security Features...")
        
        # Test 1: Input sanitization
        malicious_payloads = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE rooms; --",
            "../../../etc/passwd",
            "javascript:alert(1)"
        ]
        
        sanitization_working = True
        for payload in malicious_payloads:
            try:
                # Test token endpoint
                response = self.session.post(f"{BACKEND_URL}/livekit/token", json={
                    "room_name": payload,
                    "participant_name": "test"
                })
                
                if response.status_code == 400:
                    continue  # Good, input was rejected
                elif response.status_code == 200:
                    sanitization_working = False
                    break
            except:
                pass
        
        if sanitization_working:
            self.log_test("LiveKit Security - Input Sanitization", True, 
                        "Malicious payloads properly rejected")
        else:
            self.log_test("LiveKit Security - Input Sanitization", False, 
                        "Some malicious payloads were accepted")
        
        # Test 2: Security headers
        try:
            response = self.session.get(f"{BACKEND_URL}/livekit/rooms")
            headers = response.headers
            
            security_headers = [
                "X-Content-Type-Options",
                "X-Frame-Options", 
                "X-XSS-Protection",
                "Strict-Transport-Security"
            ]
            
            present_headers = [h for h in security_headers if h in headers]
            
            if len(present_headers) >= 3:
                self.log_test("LiveKit Security - Security Headers", True, 
                            f"Security headers present: {present_headers}")
            else:
                self.log_test("LiveKit Security - Security Headers", False, 
                            f"Missing security headers: {set(security_headers) - set(present_headers)}")
        except Exception as e:
            self.log_test("LiveKit Security - Security Headers", False, str(e))
    
    def run_all_tests(self):
        """Run all LiveKit tests"""
        print("🎥 OMERTÀ LiveKit Video Calling System Test Suite")
        print("=" * 60)
        
        start_time = time.time()
        
        # Run all test suites
        self.test_livekit_token_generation()
        self.test_livekit_room_creation()
        self.test_livekit_room_listing()
        self.test_livekit_room_info()
        self.test_livekit_session_management()
        self.test_security_features()
        
        # Calculate results
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        elapsed_time = time.time() - start_time
        
        # Print summary
        print("\n" + "=" * 60)
        print("🎥 LIVEKIT VIDEO CALLING SYSTEM TEST SUMMARY")
        print("=" * 60)
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📊 Success Rate: {success_rate:.1f}%")
        print(f"⏱️  Execution Time: {elapsed_time:.2f} seconds")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['details']}")
        
        # Determine overall status
        if success_rate >= 90:
            print(f"\n🎉 LIVEKIT SYSTEM STATUS: EXCELLENT ({success_rate:.1f}%)")
        elif success_rate >= 75:
            print(f"\n✅ LIVEKIT SYSTEM STATUS: GOOD ({success_rate:.1f}%)")
        elif success_rate >= 50:
            print(f"\n⚠️  LIVEKIT SYSTEM STATUS: NEEDS IMPROVEMENT ({success_rate:.1f}%)")
        else:
            print(f"\n❌ LIVEKIT SYSTEM STATUS: CRITICAL ISSUES ({success_rate:.1f}%)")
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "execution_time": elapsed_time,
            "test_results": self.test_results
        }

if __name__ == "__main__":
    tester = LiveKitTester()
    results = tester.run_all_tests()
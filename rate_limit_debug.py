#!/usr/bin/env python3
"""
Debug rate limiting implementation
"""

import requests
import time
import json

BACKEND_URL = "https://graphite-killer.preview.emergentagent.com/api"

def test_rate_limit_debug():
    """Debug rate limiting with detailed output"""
    print("=== Rate Limiting Debug Test ===")
    
    # Test with rapid requests
    for i in range(15):
        payload = {
            "ciphertext": f"debug_test_{i}",
            "ttl_seconds": 60,
            "read_limit": 1
        }
        
        try:
            start_time = time.time()
            response = requests.post(f"{BACKEND_URL}/notes", json=payload)
            end_time = time.time()
            
            print(f"Request {i+1}: Status={response.status_code}, Time={end_time-start_time:.3f}s")
            
            # Print all headers
            if i < 3 or response.status_code == 429:
                print(f"  Headers: {dict(response.headers)}")
            
            if response.status_code == 429:
                print(f"  Rate limited at request {i+1}")
                break
            elif response.status_code != 200:
                print(f"  Unexpected status: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Request {i+1}: Error - {e}")
        
        # Small delay to avoid overwhelming
        time.sleep(0.1)

if __name__ == "__main__":
    test_rate_limit_debug()
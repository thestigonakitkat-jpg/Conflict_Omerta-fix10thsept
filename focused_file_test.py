#!/usr/bin/env python3
"""
Focused test for file sharing system issues
"""

import requests
import json
import io

BACKEND_URL = "http://localhost:8001/api"

def test_file_sharing():
    print("🔍 FOCUSED FILE SHARING SYSTEM TEST")
    
    # Test file upload
    try:
        # Create a test file
        test_content = b"This is a test file content"
        files = {'file': ('test.txt', io.BytesIO(test_content), 'text/plain')}
        data = {'expiry_hours': 24, 'auto_destruct': True}
        
        print("Testing file upload...")
        response = requests.post(f"{BACKEND_URL}/files/upload", files=files, data=data)
        print(f"Upload response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Upload result: {result}")
            
            file_id = result.get('id')
            download_link = result.get('download_link')
            
            if file_id and download_link:
                # Test file download
                print(f"Testing file download with link: {download_link}")
                download_response = requests.get(f"{BACKEND_URL}{download_link}")
                print(f"Download response: {download_response.status_code}")
                if download_response.status_code != 200:
                    print(f"Download error: {download_response.text}")
                
                # Test file deletion
                print(f"Testing file deletion...")
                delete_response = requests.delete(f"{BACKEND_URL}/files/{file_id}")
                print(f"Delete response: {delete_response.status_code}")
                if delete_response.status_code != 200:
                    print(f"Delete error: {delete_response.text}")
            else:
                print("No file ID or download link returned")
        else:
            print(f"Upload error: {response.text}")
            
    except Exception as e:
        print(f"File sharing test error: {e}")

def test_voice_messages():
    print("\n🔍 FOCUSED VOICE MESSAGE SYSTEM TEST")
    
    try:
        # Create a test audio file
        test_audio = b"fake_audio_content_for_testing"
        files = {'audio': ('test_voice.m4a', io.BytesIO(test_audio), 'audio/m4a')}
        data = {'scrambled': True, 'encrypted': True}
        
        print("Testing voice message send...")
        response = requests.post(f"{BACKEND_URL}/voice/send", files=files, data=data)
        print(f"Send response: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"Send result: {result}")
            
            message_id = result.get('message_id')
            
            if message_id:
                # Test voice message play
                print(f"Testing voice message play...")
                play_response = requests.get(f"{BACKEND_URL}/voice/play/{message_id}")
                print(f"Play response: {play_response.status_code}")
                if play_response.status_code != 200:
                    print(f"Play error: {play_response.text}")
                
                # Test voice message deletion
                print(f"Testing voice message deletion...")
                delete_response = requests.delete(f"{BACKEND_URL}/voice/{message_id}")
                print(f"Delete response: {delete_response.status_code}")
                if delete_response.status_code != 200:
                    print(f"Delete error: {delete_response.text}")
            else:
                print("No message ID returned")
        else:
            print(f"Send error: {response.text}")
            
    except Exception as e:
        print(f"Voice message test error: {e}")

if __name__ == "__main__":
    test_file_sharing()
    test_voice_messages()
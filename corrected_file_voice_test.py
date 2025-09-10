#!/usr/bin/env python3
"""
🔒 OMERTÁ FILE SHARING AND VOICE MESSAGE ENDPOINTS TEST
Testing the new file sharing and voice message endpoints with correct API signatures.
"""

import requests
import base64
import io
import time
from datetime import datetime

BACKEND_URL = "http://localhost:8001/api"

def test_file_sharing_endpoints():
    """Test File Sharing Endpoints with correct API signatures"""
    print("📁 TESTING FILE SHARING ENDPOINTS")
    
    # Create test file content
    test_file_content = b"OMERTA_SECRET_FILE_CONTENT_FOR_TESTING_ENCRYPTED_FILE_SHARING_SYSTEM"
    
    # 1. Test file upload using multipart/form-data
    try:
        files = {
            'file': ('omerta_secret_document.txt', io.BytesIO(test_file_content), 'text/plain')
        }
        data = {
            'expiry_hours': 24,
            'auto_destruct': True
        }
        
        response = requests.post(f"{BACKEND_URL}/files/upload", files=files, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('id'):
                file_id = result['id']
                print(f"✅ File Upload: File uploaded successfully: {file_id[:8]}...")
                
                # Extract download token from download_link
                download_link = result.get('download_link', '')
                if '?token=' in download_link:
                    download_token = download_link.split('?token=')[1]
                    
                    # 2. Test file download
                    try:
                        response = requests.get(f"{BACKEND_URL}/files/download/{file_id}?token={download_token}", timeout=10)
                        if response.status_code == 200:
                            if response.content == test_file_content:
                                print("✅ File Download: File downloaded and decrypted successfully")
                            else:
                                print("❌ File Download: Downloaded file content mismatch")
                        else:
                            print(f"❌ File Download: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"❌ File Download: Error: {str(e)}")
                    
                    # 3. Test file deletion
                    try:
                        response = requests.delete(f"{BACKEND_URL}/files/{file_id}", timeout=10)
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('message'):
                                print("✅ File Deletion: File deleted successfully")
                            else:
                                print(f"❌ File Deletion: Deletion failed: {result}")
                        else:
                            print(f"❌ File Deletion: HTTP {response.status_code}")
                    except Exception as e:
                        print(f"❌ File Deletion: Error: {str(e)}")
                else:
                    print("❌ File Upload: No download token found in response")
            else:
                print(f"❌ File Upload: Upload failed: {result}")
        else:
            print(f"❌ File Upload: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ File Upload: Error: {str(e)}")
    
    # 4. Test file list
    try:
        response = requests.get(f"{BACKEND_URL}/files/list", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if 'files' in result:
                files_count = len(result['files'])
                print(f"✅ File List: Retrieved {files_count} files")
            else:
                print(f"❌ File List: List failed: {result}")
        else:
            print(f"❌ File List: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ File List: Error: {str(e)}")
    
    # 5. Test file cleanup
    try:
        response = requests.post(f"{BACKEND_URL}/files/cleanup", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('message'):
                cleaned_count = result.get('expired_files_removed', 0)
                print(f"✅ File Cleanup: Cleanup completed, {cleaned_count} files cleaned")
            else:
                print(f"❌ File Cleanup: Cleanup failed: {result}")
        else:
            print(f"❌ File Cleanup: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ File Cleanup: Error: {str(e)}")

def test_voice_message_endpoints():
    """Test Voice Message Endpoints with correct API signatures"""
    print("\n🎤 TESTING VOICE MESSAGE ENDPOINTS")
    
    # Create test voice data (simulated audio file)
    test_voice_data = b"OMERTA_ENCRYPTED_VOICE_MESSAGE_DATA_FOR_TESTING_AUDIO_SYSTEM"
    
    # 1. Test voice message send using multipart/form-data
    try:
        files = {
            'audio': ('omerta_voice_message.m4a', io.BytesIO(test_voice_data), 'audio/m4a')
        }
        data = {
            'scrambled': True,
            'encrypted': True
        }
        
        response = requests.post(f"{BACKEND_URL}/voice/send", files=files, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('message_id'):
                message_id = result['message_id']
                print(f"✅ Voice Message Send: Voice message sent: {message_id[:8]}...")
                
                # 2. Test voice message play
                try:
                    response = requests.get(f"{BACKEND_URL}/voice/play/{message_id}", timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('encoded_content'):
                            # Decode and verify content
                            decoded_content = base64.b64decode(result['encoded_content'])
                            if decoded_content == test_voice_data:
                                print("✅ Voice Message Play: Voice message retrieved successfully")
                            else:
                                print("❌ Voice Message Play: Voice data mismatch")
                        else:
                            print(f"❌ Voice Message Play: Play failed: {result}")
                    else:
                        print(f"❌ Voice Message Play: HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ Voice Message Play: Error: {str(e)}")
                
                # 3. Test voice message deletion
                try:
                    response = requests.delete(f"{BACKEND_URL}/voice/{message_id}", timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        if result.get('message'):
                            print("✅ Voice Message Deletion: Voice message deleted successfully")
                        else:
                            print(f"❌ Voice Message Deletion: Deletion failed: {result}")
                    else:
                        print(f"❌ Voice Message Deletion: HTTP {response.status_code}")
                except Exception as e:
                    print(f"❌ Voice Message Deletion: Error: {str(e)}")
            else:
                print(f"❌ Voice Message Send: Send failed: {result}")
        else:
            print(f"❌ Voice Message Send: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Voice Message Send: Error: {str(e)}")
    
    # 4. Test voice messages list
    try:
        response = requests.get(f"{BACKEND_URL}/voice/messages", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if 'messages' in result:
                messages_count = len(result['messages'])
                print(f"✅ Voice Messages List: Retrieved {messages_count} voice messages")
            else:
                print(f"❌ Voice Messages List: List failed: {result}")
        else:
            print(f"❌ Voice Messages List: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Voice Messages List: Error: {str(e)}")
    
    # 5. Test voice message cleanup
    try:
        response = requests.post(f"{BACKEND_URL}/voice/cleanup", timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get('message'):
                cleaned_count = result.get('expired_messages_removed', 0)
                print(f"✅ Voice Message Cleanup: Cleanup completed, {cleaned_count} messages cleaned")
            else:
                print(f"❌ Voice Message Cleanup: Cleanup failed: {result}")
        else:
            print(f"❌ Voice Message Cleanup: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Voice Message Cleanup: Error: {str(e)}")

if __name__ == "__main__":
    print("🔒 OMERTÁ FILE SHARING AND VOICE MESSAGE ENDPOINTS TEST")
    print("=" * 60)
    
    test_file_sharing_endpoints()
    test_voice_message_endpoints()
    
    print("\n" + "=" * 60)
    print("🎯 FILE SHARING AND VOICE MESSAGE ENDPOINTS TEST COMPLETED")
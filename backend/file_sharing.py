from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import FileResponse, Response
import os
import uuid
import time
import hashlib
from typing import Optional
import aiofiles
from cryptography.fernet import Fernet
import base64
from security_middleware import FileUploadSecurityValidator

router = APIRouter()

# In-memory file storage (RAM-only)
files_storage = {}
encryption_keys = {}

def generate_encryption_key():
    """Generate a new encryption key"""
    return Fernet.generate_key()

def encrypt_file_content(content: bytes, key: bytes) -> bytes:
    """Encrypt file content"""
    f = Fernet(key)
    return f.encrypt(content)

def decrypt_file_content(encrypted_content: bytes, key: bytes) -> bytes:
    """Decrypt file content"""
    f = Fernet(key)
    return f.decrypt(encrypted_content)

@router.post("/files/upload")
async def upload_file(
    file: UploadFile = File(...),
    expiry_hours: int = Form(24),
    auto_destruct: bool = Form(True)
):
    """Upload and encrypt a file"""
    try:
        # SECURITY VALIDATION - Critical for state-level protection
        content = await file.read()
        FileUploadSecurityValidator.validate_file(file.filename, content)
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        
        # Generate encryption key
        encryption_key = generate_encryption_key()
        
        # Encrypt content
        encrypted_content = encrypt_file_content(content, encryption_key)
        
        # Calculate expiry time
        expiry_time = int(time.time()) + (expiry_hours * 3600)
        
        # Store file metadata and encrypted content in RAM
        files_storage[file_id] = {
            'filename': file.filename,
            'content_type': file.content_type,
            'encrypted_content': encrypted_content,
            'size': len(content),
            'uploaded_at': int(time.time()),
            'expiry_time': expiry_time,
            'auto_destruct': auto_destruct,
            'access_count': 0,
            'max_access': 1 if auto_destruct else 999
        }
        
        # Store encryption key separately
        encryption_keys[file_id] = encryption_key
        
        # Generate secure download link
        download_token = hashlib.sha256(f"{file_id}{encryption_key}".encode()).hexdigest()
        
        return {
            'id': file_id,
            'name': file.filename,
            'size': len(content),
            'expiry_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(expiry_time)),
            'download_link': f"/files/download/{file_id}?token={download_token}",
            'view_count': 0,
            'auto_destruct': auto_destruct,
            'encrypted': True
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/files/download/{file_id}")
async def download_file(file_id: str, token: str):
    """Download and decrypt a file"""
    try:
        # Check if file exists
        if file_id not in files_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        file_data = files_storage[file_id]
        
        # Check expiry
        if time.time() > file_data['expiry_time']:
            # Clean up expired file
            del files_storage[file_id]
            if file_id in encryption_keys:
                del encryption_keys[file_id]
            raise HTTPException(status_code=410, detail="File expired and destroyed")
        
        # Verify token
        encryption_key = encryption_keys.get(file_id)
        if not encryption_key:
            raise HTTPException(status_code=404, detail="Encryption key not found")
        
        expected_token = hashlib.sha256(f"{file_id}{encryption_key}".encode()).hexdigest()
        if token != expected_token:
            raise HTTPException(status_code=403, detail="Invalid download token")
        
        # Check access limits
        if file_data['access_count'] >= file_data['max_access']:
            raise HTTPException(status_code=410, detail="File access limit exceeded")
        
        # Increment access count
        file_data['access_count'] += 1
        
        # Decrypt content
        decrypted_content = decrypt_file_content(file_data['encrypted_content'], encryption_key)
        
        # Auto-destruct if enabled
        if file_data['auto_destruct'] and file_data['access_count'] >= file_data['max_access']:
            del files_storage[file_id]
            del encryption_keys[file_id]
        
        # Return file content as bytes
        from fastapi.responses import Response
        
        return Response(
            content=decrypted_content,
            media_type=file_data['content_type'],
            headers={
                'Content-Disposition': f'attachment; filename="{file_data["filename"]}"'
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")

@router.delete("/files/{file_id}")
async def delete_file(file_id: str):
    """Permanently delete a file"""
    try:
        if file_id not in files_storage:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Delete file and encryption key
        del files_storage[file_id]
        if file_id in encryption_keys:
            del encryption_keys[file_id]
        
        return {'message': 'File permanently destroyed', 'file_id': file_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.get("/files/list")
async def list_files():
    """List all uploaded files (metadata only)"""
    try:
        current_time = int(time.time())
        active_files = []
        
        # Clean up expired files and return active ones
        expired_files = []
        for file_id, file_data in files_storage.items():
            if current_time > file_data['expiry_time']:
                expired_files.append(file_id)
            else:
                active_files.append({
                    'id': file_id,
                    'name': file_data['filename'],
                    'size': file_data['size'],
                    'uploaded_at': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_data['uploaded_at'])),
                    'expiry_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_data['expiry_time'])),
                    'access_count': file_data['access_count'],
                    'max_access': file_data['max_access'],
                    'auto_destruct': file_data['auto_destruct']
                })
        
        # Clean up expired files
        for file_id in expired_files:
            del files_storage[file_id]
            if file_id in encryption_keys:
                del encryption_keys[file_id]
        
        return {
            'files': active_files,
            'total_active': len(active_files),
            'total_expired_cleaned': len(expired_files)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"List failed: {str(e)}")

@router.post("/files/cleanup")
async def cleanup_expired_files():
    """Manually cleanup expired files"""
    try:
        current_time = int(time.time())
        expired_files = []
        
        # Find expired files
        for file_id, file_data in list(files_storage.items()):
            if current_time > file_data['expiry_time']:
                expired_files.append(file_id)
                del files_storage[file_id]
                if file_id in encryption_keys:
                    del encryption_keys[file_id]
        
        return {
            'message': 'Cleanup completed',
            'expired_files_removed': len(expired_files),
            'active_files_remaining': len(files_storage)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
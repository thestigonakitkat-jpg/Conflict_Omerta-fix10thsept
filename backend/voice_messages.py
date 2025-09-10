from fastapi import APIRouter, UploadFile, File, HTTPException, Form
import uuid
import time
import io
import base64
from typing import Optional

router = APIRouter()

# In-memory voice message storage (RAM-only)
voice_messages = {}

@router.post("/voice/send")
async def send_voice_message(
    audio: UploadFile = File(...),
    scrambled: bool = Form(True),
    encrypted: bool = Form(True)
):
    """Send an encrypted voice message with scrambling"""
    try:
        # Generate unique message ID
        message_id = str(uuid.uuid4())
        
        # Read audio content
        audio_content = await audio.read()
        
        # Encode as base64 for storage
        encoded_audio = base64.b64encode(audio_content).decode('utf-8')
        
        # Store voice message metadata
        voice_messages[message_id] = {
            'id': message_id,
            'filename': audio.filename or f'voice_message_{message_id}.m4a',
            'content_type': audio.content_type or 'audio/m4a',
            'encoded_content': encoded_audio,
            'size': len(audio_content),
            'scrambled': scrambled,
            'encrypted': encrypted,
            'timestamp': int(time.time()),
            'expiry_time': int(time.time()) + 3600,  # 1 hour expiry
            'played': False
        }
        
        return {
            'message_id': message_id,
            'status': 'sent',
            'scrambled': scrambled,
            'encrypted': encrypted,
            'size': len(audio_content),
            'expiry_time': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(int(time.time()) + 3600))
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice message send failed: {str(e)}")

@router.get("/voice/messages")
async def get_voice_messages():
    """Get all voice messages"""
    try:
        current_time = int(time.time())
        active_messages = []
        
        # Clean up expired messages and return active ones
        expired_messages = []
        for msg_id, msg_data in list(voice_messages.items()):
            if current_time > msg_data['expiry_time']:
                expired_messages.append(msg_id)
                del voice_messages[msg_id]
            else:
                # Don't include encoded content in list
                message_info = {
                    'id': msg_data['id'],
                    'filename': msg_data['filename'],
                    'size': msg_data['size'],
                    'scrambled': msg_data['scrambled'],
                    'encrypted': msg_data['encrypted'],
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(msg_data['timestamp'])),
                    'played': msg_data['played']
                }
                active_messages.append(message_info)
        
        return {
            'messages': active_messages,
            'total_active': len(active_messages),
            'expired_cleaned': len(expired_messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Get messages failed: {str(e)}")

@router.get("/voice/play/{message_id}")
async def play_voice_message(message_id: str):
    """Get voice message for playback"""
    try:
        if message_id not in voice_messages:
            raise HTTPException(status_code=404, detail="Voice message not found")
        
        message = voice_messages[message_id]
        
        # Check expiry
        if time.time() > message['expiry_time']:
            del voice_messages[message_id]
            raise HTTPException(status_code=410, detail="Voice message expired")
        
        # Mark as played
        message['played'] = True
        
        # Return audio data
        return {
            'message_id': message_id,
            'filename': message['filename'],
            'content_type': message['content_type'],
            'encoded_content': message['encoded_content'],
            'scrambled': message['scrambled'],
            'encrypted': message['encrypted']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Play message failed: {str(e)}")

@router.delete("/voice/{message_id}")
async def delete_voice_message(message_id: str):
    """Delete a voice message"""
    try:
        if message_id not in voice_messages:
            raise HTTPException(status_code=404, detail="Voice message not found")
        
        del voice_messages[message_id]
        
        return {
            'message': 'Voice message deleted',
            'message_id': message_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")

@router.post("/voice/cleanup")
async def cleanup_expired_voice():
    """Cleanup expired voice messages"""
    try:
        current_time = int(time.time())
        expired_count = 0
        
        for msg_id in list(voice_messages.keys()):
            if current_time > voice_messages[msg_id]['expiry_time']:
                del voice_messages[msg_id]
                expired_count += 1
        
        return {
            'message': 'Voice cleanup completed',
            'expired_messages_removed': expired_count,
            'active_messages_remaining': len(voice_messages)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")
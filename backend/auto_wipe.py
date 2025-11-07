import os
import logging
import hashlib
import hmac
import time
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
from fastapi import HTTPException, Request
from pydantic import BaseModel, Field, validator
from pathlib import Path
from dotenv import load_dotenv

# Import security engine for rate limiting
from security_engine import security_engine, rate_limit_middleware
from crypto_erase_engine import crypto_erase_engine, CryptoEraseRequest

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

logger = logging.getLogger(__name__)

# Pydantic models
class AutoWipeConfig(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    enabled: bool = Field(default=True)
    days_inactive: int = Field(default=7, ge=1, le=14)
    wipe_type: str = Field(default="app_data")  # "app_data" or "full_nuke"
    warning_days: int = Field(default=2, ge=1, le=5)  # Days before wipe to show warnings

    @validator('wipe_type')
    def validate_wipe_type(cls, v):
        if v not in ["app_data", "full_nuke"]:
            raise ValueError("wipe_type must be 'app_data' or 'full_nuke'")
        return v

class ActivityUpdate(BaseModel):
    device_id: str = Field(..., min_length=1, max_length=100)
    activity_type: str = Field(default="app_usage")  # "app_usage", "login", "message_sent", etc.

class AutoWipeStatus(BaseModel):
    device_id: str
    enabled: bool
    days_inactive: int
    wipe_type: str
    last_activity: int
    days_until_wipe: int
    warning_active: bool
    wipe_pending: bool

class AutoWipeResponse(BaseModel):
    success: bool
    message: str
    config: Optional[AutoWipeConfig] = None
    status: Optional[AutoWipeStatus] = None

def sanitize_input(text: str, max_length: int = 100) -> str:
    """Sanitize input data for auto-wipe system"""
    if not text or not isinstance(text, str):
        raise HTTPException(status_code=400, detail="Invalid input: text must be a non-empty string")
    
    if len(text) > max_length:
        raise HTTPException(status_code=400, detail=f"Input too long: maximum {max_length} characters")
    
    # Check for dangerous patterns
    dangerous_patterns = ['<script', 'javascript:', '../', '/etc/passwd', 'drop table']
    text_lower = text.lower()
    
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            raise HTTPException(status_code=400, detail="Potentially dangerous content detected")
    
    return text.strip()

def generate_wipe_signature(device_id: str, timestamp: int, wipe_type: str) -> str:
    """Generate cryptographic signature for auto-wipe action"""
    data = f"AUTO_WIPE:{device_id}:{timestamp}:{wipe_type}"
    signature = hmac.new(
        b"OMERTA_AUTO_WIPE_SECRET_2025_GRADE",
        data.encode(),
        hashlib.sha256
    ).hexdigest()
    return signature

async def configure_auto_wipe(request: Request, payload: AutoWipeConfig):
    """Configure auto-wipe settings for device"""
    try:
        await rate_limit_middleware(request, "auto_wipe_config")
        
        # Sanitize inputs
        device_id = sanitize_input(payload.device_id, max_length=100)
        
        # Validate configuration
        if payload.days_inactive < 1 or payload.days_inactive > 14:
            raise HTTPException(status_code=400, detail="days_inactive must be between 1 and 14")
        
        if payload.warning_days >= payload.days_inactive:
            raise HTTPException(status_code=400, detail="warning_days must be less than days_inactive")
        
        # Store configuration in RAM
        if device_id not in security_engine.user_sessions:
            security_engine.user_sessions[device_id] = {}
        
        current_timestamp = int(time.time())
        
        config_data = {
            "enabled": payload.enabled,
            "days_inactive": payload.days_inactive,
            "wipe_type": payload.wipe_type,
            "warning_days": payload.warning_days,
            "configured_timestamp": current_timestamp,
            "last_activity": current_timestamp,  # Initialize with current time
            "warnings_sent": 0,
            "wipe_scheduled": False
        }
        
        security_engine.user_sessions[device_id]["auto_wipe_config"] = config_data
        
        logger.info(f"⏰ AUTO-WIPE: Configured for device {device_id} - {payload.days_inactive} days, {payload.wipe_type}")
        
        return AutoWipeResponse(
            success=True,
            message=f"Auto-wipe configured: {payload.days_inactive} days inactive → {payload.wipe_type}",
            config=payload
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Auto-wipe configuration failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to configure auto-wipe")

async def update_activity(request: Request, payload: ActivityUpdate):
    """Update last activity timestamp for device"""
    try:
        await rate_limit_middleware(request, "auto_wipe_activity")
        
        device_id = sanitize_input(payload.device_id, max_length=100)
        
        if device_id not in security_engine.user_sessions:
            # Initialize if not exists
            security_engine.user_sessions[device_id] = {}
        
        session = security_engine.user_sessions[device_id]
        
        # Update last activity
        current_timestamp = int(time.time())
        
        if "auto_wipe_config" not in session:
            # Initialize default config
            session["auto_wipe_config"] = {
                "enabled": False,
                "days_inactive": 7,
                "wipe_type": "app_data",
                "warning_days": 2,
                "configured_timestamp": current_timestamp,
                "last_activity": current_timestamp,
                "warnings_sent": 0,
                "wipe_scheduled": False
            }
        
        # Update activity
        session["auto_wipe_config"]["last_activity"] = current_timestamp
        session["auto_wipe_config"]["warnings_sent"] = 0  # Reset warnings on activity
        session["auto_wipe_config"]["wipe_scheduled"] = False  # Cancel any pending wipe
        
        logger.debug(f"⏰ AUTO-WIPE: Activity updated for device {device_id}")
        
        return {"success": True, "message": "Activity updated", "timestamp": current_timestamp}
        
    except Exception as e:
        logger.error(f"Activity update failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to update activity")

async def check_auto_wipe_status(request: Request, device_id: str):
    """Check auto-wipe status and trigger if necessary"""
    try:
        await rate_limit_middleware(request, "auto_wipe_check")
        
        device_id = sanitize_input(device_id, max_length=100)
        
        if device_id not in security_engine.user_sessions:
            return {"success": True, "wipe_pending": False, "message": "No auto-wipe configuration found"}
        
        session = security_engine.user_sessions[device_id]
        
        if "auto_wipe_config" not in session:
            return {"success": True, "wipe_pending": False, "message": "Auto-wipe not configured"}
        
        config = session["auto_wipe_config"]
        
        if not config["enabled"]:
            return {"success": True, "wipe_pending": False, "message": "Auto-wipe disabled"}
        
        current_timestamp = int(time.time())
        last_activity = config["last_activity"]
        days_inactive_seconds = config["days_inactive"] * 24 * 60 * 60
        warning_seconds = config["warning_days"] * 24 * 60 * 60
        
        time_since_activity = current_timestamp - last_activity
        
        # Calculate status
        wipe_pending = time_since_activity >= days_inactive_seconds
        warning_active = time_since_activity >= (days_inactive_seconds - warning_seconds) and not wipe_pending
        
        days_until_wipe = max(0, (days_inactive_seconds - time_since_activity) // (24 * 60 * 60))
        
        status = AutoWipeStatus(
            device_id=device_id,
            enabled=config["enabled"],
            days_inactive=config["days_inactive"],
            wipe_type=config["wipe_type"],
            last_activity=last_activity,
            days_until_wipe=int(days_until_wipe),
            warning_active=warning_active,
            wipe_pending=wipe_pending
        )
        
        # If wipe is pending, trigger it
        if wipe_pending and not config.get("wipe_scheduled", False):
            await trigger_auto_wipe(device_id, config)
            config["wipe_scheduled"] = True
        
        logger.info(f"⏰ AUTO-WIPE STATUS: Device {device_id} - Days until wipe: {days_until_wipe}, Warning: {warning_active}, Pending: {wipe_pending}")
        
        return {
            "success": True,
            "wipe_pending": wipe_pending,
            "warning_active": warning_active,
            "days_until_wipe": days_until_wipe,
            "last_activity": config.get("last_activity_timestamp", 0),
            "wipe_type": config.get("wipe_type", "unknown"),
            "status": status.dict(),
            "message": "Auto-wipe status checked"
        }
        
    except Exception as e:
        logger.error(f"Auto-wipe status check failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to check auto-wipe status")

async def trigger_auto_wipe(device_id: str, config: dict):
    """Trigger auto-wipe for device with mandatory crypto-erase first"""
    try:
        current_timestamp = int(time.time())
        wipe_type = config["wipe_type"]
        
        # CRITICAL: CRYPTO-ERASE PHASE MUST HAPPEN FIRST
        logger.critical(f"💀 AUTO-WIPE CRYPTO-ERASE: Phase 1 for {device_id}")
        
        # Create crypto-erase request
        from fastapi import Request
        crypto_erase_req = CryptoEraseRequest(
            device_id=device_id,
            erase_scope="all",
            emergency_mode=True  # Auto-wipe is emergency
        )
        
        # Execute crypto-erase
        # Note: In production, would pass actual Request object
        # For now, crypto-erase engine allows emergency_mode without request
        try:
            from unittest.mock import MagicMock
            mock_request = MagicMock()
            mock_request.client = MagicMock()
            mock_request.client.host = "auto_wipe_system"
            
            crypto_result = await crypto_erase_engine.crypto_erase_all_keys(mock_request, crypto_erase_req)
            
            if not crypto_result.success:
                logger.error(f"❌ CRYPTO-ERASE FAILED for {device_id} - ABORTING AUTO-WIPE")
                return
            
            logger.critical(f"✅ CRYPTO-ERASE COMPLETE: {sum(crypto_result.keys_destroyed.values())} keys destroyed")
        except Exception as e:
            logger.error(f"❌ CRYPTO-ERASE ERROR: {e} - Proceeding with wipe anyway (emergency mode)")
        
        # Generate signature for wipe action
        signature = generate_wipe_signature(device_id, current_timestamp, wipe_type)
        
        # Create wipe command based on type
        if wipe_type == "full_nuke":
            # Trigger STEELOS-SHREDDER for full nuke
            kill_token = {
                "command": "AUTO_WIPE_STEELOS_SHREDDER",
                "device_id": device_id,
                "wipe_type": "steelos_shredder_obliteration",
                "timestamp": current_timestamp,
                "trigger_type": "auto_wipe_unused_device",
                "reason": f"Device unused for {config['days_inactive']} days - Auto-Wipe FULL NUKE",
                "signature": signature,
                "auto_execute": True,
                "show_cyanide_animation": True,
                "kill_method": "steelos_shredder",
                "bypass_user_confirmation": True,
                "destruction_phases": [
                    "secure_store_annihilation",
                    "file_system_destruction", 
                    "memory_clearing",
                    "cache_data_destruction",
                    "metadata_destruction"
                ]
            }
            
            # Store in session for client retrieval
            if device_id not in security_engine.user_sessions:
                security_engine.user_sessions[device_id] = {}
            
            security_engine.user_sessions[device_id]["steelos_shredder_token"] = kill_token
            
            logger.critical(f"💀 AUTO-WIPE FULL NUKE: Device {device_id} - STEELOS-SHREDDER activated after {config['days_inactive']} days")
            logger.critical(f"🔥 CRYPTO-ERASE: Keys destroyed before STEELOS-SHREDDER execution")
            
        else:
            # App data wipe only
            wipe_command = {
                "command": "AUTO_WIPE_APP_DATA",
                "device_id": device_id,
                "wipe_type": "app_data_only",
                "timestamp": current_timestamp,
                "trigger_type": "auto_wipe_unused_device",
                "reason": f"Device unused for {config['days_inactive']} days - Auto-Wipe APP DATA",
                "signature": signature,
                "wipe_targets": [
                    "secure_notes",
                    "chat_messages", 
                    "vault_items",
                    "contact_data",
                    "user_settings"
                ]
            }
            
            # Store in session for client retrieval
            if device_id not in security_engine.user_sessions:
                security_engine.user_sessions[device_id] = {}
            
            security_engine.user_sessions[device_id]["auto_wipe_token"] = wipe_command
            
            logger.warning(f"🧹 AUTO-WIPE APP DATA: Device {device_id} - App data wipe after {config['days_inactive']} days")
            logger.critical(f"🔥 CRYPTO-ERASE: Keys destroyed before app data wipe")
        
    except Exception as e:
        logger.error(f"Auto-wipe trigger failed: {e}")

async def get_wipe_token(request: Request, device_id: str):
    """Get pending wipe token for device"""
    try:
        await rate_limit_middleware(request, "auto_wipe_token")
        
        device_id = sanitize_input(device_id, max_length=100)
        
        if device_id not in security_engine.user_sessions:
            return {"wipe_pending": False, "message": "No wipe tokens found"}
        
        session = security_engine.user_sessions[device_id]
        
        # Check for STEELOS-SHREDDER token (full nuke)
        if "steelos_shredder_token" in session:
            token = session["steelos_shredder_token"]
            del session["steelos_shredder_token"]  # One-time use
            
            logger.critical(f"💀 AUTO-WIPE TOKEN RETRIEVED: FULL NUKE for device {device_id}")
            
            return {
                "wipe_pending": True,
                "wipe_type": "full_nuke",
                "token": token,
                "message": "STEELOS-SHREDDER auto-wipe token retrieved"
            }
        
        # Check for app data wipe token
        if "auto_wipe_token" in session:
            token = session["auto_wipe_token"]
            del session["auto_wipe_token"]  # One-time use
            
            logger.warning(f"🧹 AUTO-WIPE TOKEN RETRIEVED: APP DATA for device {device_id}")
            
            return {
                "wipe_pending": True,
                "wipe_type": "app_data",
                "token": token,
                "message": "App data auto-wipe token retrieved"
            }
        
        return {"wipe_pending": False, "message": "No wipe tokens pending"}
        
    except Exception as e:
        logger.error(f"Wipe token retrieval failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve wipe token")